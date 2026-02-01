"""Functions for uploading to docker hub"""

# Standard libraries
import math
import os
from pathlib import Path

# Project libraries
from docker_archiver.chunker import chunk_file
from docker_archiver.constants import CHUNK_DIRECTORY, DEFAULT_CHUNK_SIZE, config
from docker_archiver.docker_api import get_manifest, push_blob_config, push_blob_file, push_manifest
from docker_archiver.docker_api_models import (
    Blob,
    BlobRootFS,
    Manifest,
    ManifestConfig,
    ManifestLayer,
    calculate_sha256_digest_from_file,
)
from docker_archiver.utils import humanize_bytes, sha256_file_hash


def push_image(file_path: Path, tag_name: str, progress_bar_description: str):
    """Pushes an image with a file to docker hub

    Args:
        file_path: The file to push
        tag_name: The tag name
        progress_bar_description: The tqdm progress bar description
    """

    # Check for existing tags
    chunk_digest = calculate_sha256_digest_from_file(file_path)
    if (manifest := get_manifest(tag=tag_name)) is not None:
        if manifest.layers[0].digest == chunk_digest:
            print(f"Repository image {tag_name} already exists with matching SHA256 hash")
            os.remove(file_path)
            return None
        if not config.overwrite_image:
            os.remove(file_path)
            raise ValueError(f"Remove image {tag_name} already exists, with different hash")
        print(f"Overwriting image {tag_name}")

    # Push blob config
    blob = Blob(architecture="x86_64", os="linux", rootfs=BlobRootFS(type="layers"))
    blob_size = len(blob.as_json_bytes())
    blob_digest = blob.get_sha256_digest()
    push_blob_config(blob=blob, digest=blob_digest)

    # Push blob file (layer 1)
    chunk_size = os.path.getsize(file_path)
    push_blob_file(
        file_path=file_path,
        digest=chunk_digest,
        timeout=100,
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
                size=chunk_size,
                digest=chunk_digest,
            )
        ],
    )
    push_manifest(manifest=manifest, tag=tag_name)

    # Cleanup chunk
    os.remove(file_path)


def push_file_as_image_chunks(file_path: Path, chunk_size_bytes: int = DEFAULT_CHUNK_SIZE):
    os.makedirs(CHUNK_DIRECTORY, mode=500, exist_ok=True)
    parent_file_size = os.path.getsize(file_path)
    chunk_count = math.ceil(parent_file_size / chunk_size_bytes)
    print(f"File size: {humanize_bytes(parent_file_size)}")

    for index in range(1, chunk_count + 1):
        chunk_tag = f"{config.base_tag}-{index}"
        chunk_path = CHUNK_DIRECTORY / chunk_tag
        byte_offset = (index - 1) * chunk_size_bytes

        chunk_file(
            input_file_path=file_path, output_file_path=chunk_path, read_bytes=chunk_size_bytes, byte_offset=byte_offset
        )
        push_image(
            file_path=chunk_path,
            tag_name=chunk_tag,
            progress_bar_description=f"Uploading image {chunk_tag} ({index}/{chunk_count})",
        )
