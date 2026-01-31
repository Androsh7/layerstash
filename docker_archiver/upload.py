"""Functions for uploading to docker hub"""

# Standard libraries
import math
import os
import subprocess
from pathlib import Path

# Third-party libraries
from loguru import logger

# Project libraries
from docker_archiver.chunker import chunk_file
from docker_archiver.constants import CHUNK_DIRECTORY, DEFAULT_CHUNK_SIZE, DOCKERFILE_PATH


def upload_chunk(file_path: Path, docker_tag: str):
    """Build, push, and delete a docker image

    Args:
        file_path: Path to the file to upload
        docker_tag: Tag for the docker image
    """
    logger.info(f'Creating and pushing docker image "{docker_tag}" from file {file_path}')

    # Build/push docker image
    subprocess.run(
        "docker build "
        f"--tag {docker_tag} "
        f'--file "{DOCKERFILE_PATH}" '
        f'--build-arg SOURCE_FILE="{file_path.name}" '
        "--push "
        "--no-cache "
        ".",
        cwd=file_path.parent,
        shell=True,
        check=True,
    )

    # Cleanup
    logger.info(f'Pushed image "{docker_tag}" to docker hub, deleting local image and chunk file')
    subprocess.run(
        f"docker image rm  --force {docker_tag}",
        shell=True,
        check=True,
    )
    os.remove(file_path)


def upload_file_as_chunks(file_path: Path, base_tag: str, chunk_size: int = DEFAULT_CHUNK_SIZE):
    """Uploads a file as a series of chunked docker images

    Args:
        file_path: Path to the file to upload
        base_tag: The base tag for the docker images, "-<INDEX>" will be appended to the end
        chunk_size: The size of chunks in bytes
    """
    # Calculate chunks
    byte_count = os.path.getsize(file_path)
    chunk_count = math.ceil(byte_count / chunk_size)

    logger.info(f"Uploading file {file_path} as {chunk_count} chunks")

    for index in range(1, chunk_count + 1):
        # Define chunk vars
        chunk_tag = f"{base_tag}-{index}"
        chunk_path = CHUNK_DIRECTORY / chunk_tag.replace("/", "_").replace(":", "_")
        byte_offset = (index - 1) * chunk_size

        # Chunk file and upload image
        chunk_file(
            input_file_path=file_path, output_file_path=chunk_path, read_bytes=chunk_size, byte_offset=byte_offset
        )
        upload_chunk(file_path=chunk_path, docker_tag=chunk_tag)
