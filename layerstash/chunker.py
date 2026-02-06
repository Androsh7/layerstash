"""Defines chunking/merging function"""

# Standard libraries
import os
from pathlib import Path

# Third-party libraries
from loguru import logger

# Project libraries
from layerstash.utils import humanize_bytes


def chunk_file(input_file_path: Path, output_file_path: Path, read_bytes: int, byte_offset: int):
    """Takes a specific byte range in a file and writes it to another file

    Args:
        input_file_path: The file to create a chunk from
        output_file_path: The path to write the chunk bytes to
        read_bytes: The number of bytes to read
        byte_offset: The byte offset to start reading at
    """
    logger.debug(
        f"Creating chunk {output_file_path} from {input_file_path} at byte offset {byte_offset} with size {read_bytes}"
    )
    with open(file=input_file_path, mode="rb") as input_file:
        input_file.seek(byte_offset)
        with open(file=output_file_path, mode="wb") as output_file:
            output_file.write(input_file.read(read_bytes))


def merge_file(input_file_path: Path, output_file_path: Path):
    """Appends one file to another

    Args:
        input_file_path: The file to append to the output file
        output_file_path: The destination of the input bytes
    """
    logger.debug(f"Merging chunk {input_file_path} into {output_file_path}")
    with open(file=input_file_path, mode="rb") as input_file:
        with open(file=output_file_path, mode="a+b") as output_file:
            output_file.write(input_file.read())
    os.remove(input_file_path)
