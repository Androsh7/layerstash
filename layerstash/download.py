"""Functions for downloading from docker hub"""

# Standard libraries
import os
from http import HTTPStatus
from pathlib import Path
from time import sleep

# Third-party libraries
from attrs import define, field, validators
from requests.exceptions import HTTPError

# Project libraries
from layerstash.chunker import merge_file
from layerstash.constants import CHUNK_DIRECTORY, RETRIES, config
from layerstash.docker_api import DockerException, get_manifest, pull_blob_file
from layerstash.docker_api_models import calculate_sha256_digest_from_file
from layerstash.utils import humanize_bytes, humanize_seconds


@define
class DownloadTarget:
    tag: str = field(validator=validators.instance_of(str))
    digest: str = field(validator=validators.instance_of(str))
    size: int = field(validator=validators.instance_of(int))


def get_download_targets() -> list[DownloadTarget]:
    digest_list = []
    index = 1
    while True:
        chunk_tag = f"{config.base_tag}-{index}"
        manifest = get_manifest(tag=chunk_tag)
        if manifest is not None:
            digest_list.append(
                DownloadTarget(tag=chunk_tag, digest=manifest.layers[0].digest, size=manifest.layers[0].size)
            )
        else:
            break
        index += 1
    if len(digest_list) == 0:
        raise DockerException(f"No digests found for base tag {config.base_tag}")
    return digest_list


def download_file_from_images(out_file_path: Path):
    os.makedirs(CHUNK_DIRECTORY, mode=500, exist_ok=True)
    print("Loading download targets")
    download_list = get_download_targets()
    total_size = 0
    for download in download_list:
        total_size += download.size
    print(f"File size: {humanize_bytes(total_size)}")
    print(f"Total chunks: {len(download_list)}")

    chunk_path_list = []
    for index, download in enumerate(download_list, start=1):
        chunk_path = CHUNK_DIRECTORY / f"{download.tag}"
        chunk_path_list.append(chunk_path)

        # Check if chunk exists
        if chunk_path.exists():
            if calculate_sha256_digest_from_file(chunk_path) == download.digest:
                print(f"Local chunk {chunk_path.name} matches remote sha256 hash, skipping download")
                continue
            else:
                print(f"Local chunk {chunk_path.name} does not match remote sha256 hash, overwriting local chunk")

        # Pull blob with retries
        for retry_seconds in RETRIES:
            try:
                pull_blob_file(
                    file_path=chunk_path,
                    digest=download.digest,
                    timeout=9000,
                    progress_bar_description=f"Downloading {download.tag} ({index}/{len(download_list)})",
                )
            except HTTPError as ex:
                if ex.response.status_code == HTTPStatus.BAD_GATEWAY and retry_seconds is not None:
                    print(
                        f"pull_blob_file() encountered bad gateway HTTP error, retrying in {humanize_seconds(retry_seconds)}"
                    )
                    sleep(retry_seconds)
                    continue
                raise
            break

    for chunk_path in chunk_path_list:
        merge_file(
            input_file_path=chunk_path,
            output_file_path=out_file_path,
        )
