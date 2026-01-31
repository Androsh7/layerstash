"""Functions for uploading to docker hub"""

# Standard libraries
import math
import os
import subprocess
import hashlib
from pathlib import Path

# Third-party libraries
from loguru import logger
from tqdm import tqdm

# Project libraries
from docker_archiver.chunker import chunk_file
from docker_archiver.constants import CHUNK_DIRECTORY, DEFAULT_CHUNK_SIZE, DOCKERFILE_PATH, config
from docker_archiver.utils import sha256_file_hash


def upload_chunk(file_path: Path, docker_tag: str, parent_file_path: Path, parent_file_hash: str, parent_file_size: int):
    """Build, push, and delete a docker image

    Args:
        file_path: Path to the file to upload
        docker_tag: Tag for the docker image
        parent_file_path: Path to the parent file
        parent_file_hash: SHA256 hash of the parent file
        parent_file_size: Size in bytes of the parent file
    """
    logger.debug(f'Creating and pushing docker image "{docker_tag}" from file {file_path}')

    # Get file hash
    chunk_hash = sha256_file_hash(file_path)
    chunk_size = os.path.getsize(file_path)

    # Build/push docker image
    subprocess.run(
        "docker build "
        f"--tag {docker_tag} "
        f'--file "{DOCKERFILE_PATH}" '
        f'--build-arg CHUNK_SIZE_BYTES="{chunk_size}" '
        f'--build-arg CHUNK_SHA256_HASH="{chunk_hash}" '
        f'--build-arg PARENT_FILE="{parent_file_path.name}" '
        f'--build-arg PARENT_FILE_SHA256_HASH="{parent_file_hash}" '
        f'--build-arg PARENT_FILE_SIZE_BYTES="{parent_file_size}" '
        f'--progress {"auto" if config.show_docker_progress else "quiet"} '
        "--push "
        "--no-cache "
        ".",
        cwd=file_path.parent,
        shell=True,
        check=True,
    )

    # Cleanup
    logger.debug(f'Pushed image "{docker_tag}" to docker hub, deleting local image and chunk file')
    subprocess.run(
        f"docker image rm  --force {docker_tag}",
        shell=True,
        check=True,
    )
    os.remove(file_path)


def upload_file_as_chunks(file_path: Path, chunk_size: int = DEFAULT_CHUNK_SIZE):
    """Uploads a file as a series of chunked docker images

    Args:
        file_path: Path to the file to upload
        base_tag: The base tag for the docker images, "-<INDEX>" will be appended to the end
        chunk_size: The size of chunks in bytes
    """
    # Calculate chunks
    byte_count = os.path.getsize(file_path)
    chunk_count = math.ceil(byte_count / chunk_size)

    # Get file hash
    hash = sha256_file_hash(file_path, show_progress=True)
    logger.debug(f'File {file_path} has SHA256 hash: {hash}')

    for index in tqdm(range(1, chunk_count + 1), desc=f"Uploading file {file_path.name}", unit="chunk"):
        
        # Define chunk vars
        chunk_tag = f"{config.base_tag}-{index}"
        chunk_path = CHUNK_DIRECTORY / chunk_tag.replace("/", "_").replace(":", "_")
        byte_offset = (index - 1) * chunk_size

        # Chunk file and upload image
        chunk_file(
            input_file_path=file_path, output_file_path=chunk_path, read_bytes=chunk_size, byte_offset=byte_offset
        )
        upload_chunk(file_path=chunk_path, docker_tag=chunk_tag, parent_file_path=file_path, parent_file_hash=hash, parent_file_size=byte_count)
