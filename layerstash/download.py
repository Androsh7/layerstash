"""Functions for downloading from docker hub"""

# Standard libraries
import os
from http import HTTPStatus
from pathlib import Path
from time import sleep

# Third-party libraries
from requests.exceptions import HTTPError
from urllib3.exceptions import ProtocolError

# Project libraries
from layerstash.constants import RETRIES, config
from layerstash.docker_api import get_manifest, get_tag_list, pull_blob_file
from layerstash.docker_api_models import calculate_sha256_digest_from_file
from layerstash.utils import humanize_bytes, humanize_seconds


def download_file_from_images(out_file_path: Path):
    print("Loading download targets")
    tag_list = get_tag_list(config.base_tag)
    print(f"File: {out_file_path}")
    print(f"Total chunks: {len(tag_list)}")
    
    # Create the file if it doesn't exist
    if not os.path.exists(out_file_path):
        out_file_path.touch()

    byte_offset = 0
    for index, tag in enumerate(tag_list, start=1):
        # Get tag manifest
        manifest = get_manifest(tag=tag)
        layer_size = manifest.layers[0].size
        layer_digest = manifest.layers[0].digest

        # Check if chunk exists
        if out_file_path.exists() and os.path.getsize(out_file_path) > byte_offset:
            chunk_hash = calculate_sha256_digest_from_file(
                file_path=out_file_path, byte_offset=byte_offset, byte_count=layer_size
            )
            if chunk_hash == layer_digest:
                print(
                    f"Local chunk {tag} ({index}/{len(tag_list)}) in {out_file_path} matches remote hash {layer_digest}, skipping download"
                )
                byte_offset += layer_size
                continue
            else:
                print(
                    f"Local chunk {tag} ({index}/{len(tag_list)}) in {out_file_path} does not match remote hash {layer_digest}, overwriting local chunk"
                )

        # Pull blob with retries
        for retry_seconds in RETRIES:
            try:
                pull_blob_file(
                    file_path=out_file_path,
                    byte_offset=byte_offset,
                    digest=layer_digest,
                    progress_bar_description=f"Downloading {tag} ({index}/{len(tag_list)})",
                )
            except ProtocolError:
                if retry_seconds is not None:
                    print(
                        f"pull_blob_file() encountered connection read error, retrying in {humanize_seconds(retry_seconds)}"
                    )
                    sleep(retry_seconds)
                    continue
                raise
            except HTTPError as ex:
                if ex.response.status_code == HTTPStatus.BAD_GATEWAY and retry_seconds is not None:
                    print(
                        f"pull_blob_file() encountered bad gateway HTTP error, retrying in {humanize_seconds(retry_seconds)}"
                    )
                    sleep(retry_seconds)
                    continue
                raise
            break

        byte_offset += layer_size

    # Fix file size
    file_size = os.path.getsize(out_file_path)
    if file_size > byte_offset:
        print(f"Truncating file to {humanize_bytes(file_size)}, removing {file_size - byte_offset} bytes")
        with open(file=out_file_path, mode="r+b") as file:
            file.truncate(byte_offset)

    print(f"Download complete: {out_file_path.resolve()}")
