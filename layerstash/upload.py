"""Functions for uploading to docker hub"""

# Standard libraries
import math
import os
from http import HTTPStatus
from pathlib import Path
from time import sleep

# Third-party libraries
from requests.exceptions import HTTPError

# Project libraries
from layerstash.constants import DEFAULT_CHUNK_SIZE, RETRIES, config
from layerstash.docker_api import get_manifest, push_blob_config, push_blob_file, push_manifest
from layerstash.docker_api_models import (
    Blob,
    BlobRootFS,
    Manifest,
    ManifestConfig,
    ManifestLayer,
    calculate_sha256_digest_from_file,
)
from layerstash.utils import humanize_bytes, humanize_seconds


def push_image(file_path: Path, byte_offset: int, byte_count: int, tag_name: str, progress_bar_description: str):
    """Pushes an image with a file to docker hub

    Args:
        file_path: The file to push
        tag_name: The tag name
        progress_bar_description: The tqdm progress bar description
    """

    # Check for existing tags
    chunk_digest = calculate_sha256_digest_from_file(file_path, byte_offset, byte_count)
    if (manifest := get_manifest(tag=tag_name)) is not None:
        if manifest.layers[0].digest == chunk_digest:
            print(f"Repository image {tag_name} already exists with matching SHA256 hash")
            return None
        if not config.overwrite_image:
            raise ValueError(f"Remote image {tag_name} already exists, with different hash")
        print(f"Overwriting image {tag_name}")

    # Push blob config
    blob = Blob(architecture="x86_64", os="linux", rootfs=BlobRootFS(type="layers"))
    blob_size = len(blob.as_json_bytes())
    blob_digest = blob.get_sha256_digest()
    push_blob_config(blob=blob, digest=blob_digest)

    # Push blob file (layer 1)
    push_blob_file(
        file_path=file_path,
        byte_offset=byte_offset,
        byte_count=byte_count,
        digest=chunk_digest,
        progress_bar_description=progress_bar_description,
    )

    # Push manifest (create tag)
    manifest = Manifest(
        schemaVersion=2,
        mediaType="application/vnd.docker.distribution.manifest.v2+json",
        config=ManifestConfig(
            mediaType="application/vnd.docker.container.image.v1+json",
            size=blob_size,
            digest=blob_digest,
        ),
        layers=[
            ManifestLayer(
                mediaType="application/octet-stream",
                size=byte_count,
                digest=chunk_digest,
            )
        ],
    )
    push_manifest(manifest=manifest, tag=tag_name)


def push_file_as_image_chunks(file_path: Path, chunk_size_bytes: int = DEFAULT_CHUNK_SIZE):
    parent_file_size = os.path.getsize(file_path)
    chunk_count = math.ceil(parent_file_size / chunk_size_bytes)
    print(f"File: {file_path.resolve()}")
    print(f"File size: {humanize_bytes(parent_file_size)}")

    for index in range(1, chunk_count + 1):
        chunk_tag = f"{config.base_tag}-{index}"
        byte_offset = (index - 1) * chunk_size_bytes
        byte_count = min(parent_file_size - byte_offset, chunk_size_bytes)

        for retry_seconds in RETRIES:
            try:
                push_image(
                    file_path=file_path,
                    byte_offset=byte_offset,
                    byte_count=byte_count,
                    tag_name=chunk_tag,
                    progress_bar_description=f"Uploading image {chunk_tag} ({index}/{chunk_count})",
                )
            except HTTPError as ex:
                if ex.response.status_code == HTTPStatus.BAD_GATEWAY and retry_seconds is not None:
                    print(
                        f"push_image() encountered bad gateway HTTP error, retrying in {humanize_seconds(retry_seconds)}"
                    )
                    sleep(retry_seconds)
                    continue
                raise
            break
