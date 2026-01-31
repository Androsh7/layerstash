"""Utility functions"""

# Standard libraries
import hashlib
import math
import os
from pathlib import Path

# Third-party libraries
from tqdm import tqdm

# Project libraries
from constants import DEFAULT_HASH_CHUNK_SIZE


def sha256_file_hash(file_path: Path, show_progress: bool = False, chunk_size: int = DEFAULT_HASH_CHUNK_SIZE) -> str:
    """Returns the sha256 hash of a file"""
    hash = hashlib.sha256()

    # Determine chunk count
    file_size = os.path.getsize(file_path)
    pass_count = math.ceil(file_size / chunk_size)
    iterable = range(1, pass_count + 1)
    
    # Create the tqdm iterator to show progress visually
    if show_progress:
        iterable = tqdm(iterable, unit="chunk", desc=f"Hashing file {file_path.name}")

    with open(file=file_path, mode="rb", buffering=0) as file:
        
        # Incrementally hash the file
        for _ in iterable:
            hash.update(file.read(chunk_size))
        
        # Validate that all bytes are read
        remaining_bytes = file.read()
        if len(remaining_bytes) != 0:
            raise IndexError(f"Hashing operation excluded {len(remaining_bytes)} bytes")

    return hash.hexdigest()
