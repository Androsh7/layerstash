"""Utility functions"""

# Standard libraries
import hashlib
import os
from pathlib import Path

# Project libraries
from constants import DEFAULT_HASH_CHUNK_SIZE, DEFAULT_READER_CHUNK_SIZE

# Third-party libraries
from tqdm import tqdm

BYTE_SUFFIX_LIST = ["B", "KB", "MB", "GB", "TB", "PB"]


def humanize_bytes(byte_count: int) -> str:
    if byte_count < 0:
        raise ValueError("byte_count must be non-negative")
    value = float(byte_count)
    for suffix in BYTE_SUFFIX_LIST:
        if value < 1024:
            return f"{value:.2f}{suffix}"
        value /= 1024
    return f"{value:.2f}EB"


def sha256_file_hash(file_path: Path, show_progress: bool = False, chunk_size: int = DEFAULT_HASH_CHUNK_SIZE) -> str:
    """Returns the sha256 hash of a file"""
    hash = hashlib.sha256()
    file_size = os.path.getsize(file_path)

    # Create the tqdm iterator to show progress visually
    progress_bar = None
    if show_progress:
        progress_bar = tqdm(
            total=file_size, unit="B", unit_scale=True, unit_divisor=1024, desc=f"Hashing file {file_path.name}"
        )

    with open(file=file_path, mode="rb", buffering=0) as file:
        while True:
            hash.update(file.read(chunk_size))

            chunk = file.read(chunk_size)
            if not chunk:
                break
            hash.update(chunk)
            if progress_bar is not None:
                progress_bar.update(len(chunk))

    if progress_bar is not None:
        progress_bar.close()
    return hash.hexdigest()


class TqdmFileReader:
    def __init__(self, path: str, description: str, chunk_size: int = DEFAULT_READER_CHUNK_SIZE):
        self.file = open(file=path, mode="rb")
        self.total = os.path.getsize(path)
        self.chunk_size = chunk_size
        self.progress_bar = tqdm(total=self.total, unit="B", unit_scale=True, unit_divisor=1024, desc=description)

    def __len__(self):
        return self.total

    def read(self, size=-1):
        data = self.file.read(self.chunk_size if size in (-1, None) else size)
        if data:
            self.progress_bar.update(len(data))
        return data

    def close(self):
        try:
            self.file.close()
        finally:
            self.progress_bar.close()
