"""Utility functions"""

# Standard libraries
import hashlib
import io
import os
from pathlib import Path

# Third-party libraries
from attrs import define, field, validators
from loguru import logger
from tqdm import tqdm

# Project libraries
from layerstash.constants import DEFAULT_HASH_CHUNK_SIZE, DEFAULT_READER_CHUNK_SIZE

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


def humanize_seconds(total_seconds: int) -> str:
    """Returns a number of seconds as a human readable string, I.E: '2 hours 46 minutes 40 seconds '"""
    out_string = ""
    seconds = total_seconds % 60
    hour_in_seconds = ((total_seconds - seconds) // 3600) * 3600
    minute_in_seconds = ((total_seconds - hour_in_seconds - seconds) // 60) * 60
    if hour_in_seconds:
        out_string += f"{hour_in_seconds // 3600} hour{'s' if hour_in_seconds > 3600 else ''} "
    if minute_in_seconds:
        out_string += f"{minute_in_seconds // 60} minute{'s' if minute_in_seconds > 60 else ''} "
    if seconds:
        out_string += f"{int(seconds)} second{'s' if seconds > 1 else ''} "
    return out_string


def get_sha256_file_hash(
    file_path: Path, byte_offset: int = 0, byte_count: int = None, hash_chunk_size: int = DEFAULT_HASH_CHUNK_SIZE
) -> str:
    """Returns the sha256 hash of a file"""
    hash = hashlib.sha256()
    if byte_count is None:
        byte_count = os.path.getsize(file_path)
    remaining_bytes = byte_count

    buffer = bytearray(min(hash_chunk_size, byte_count))
    mv = memoryview(buffer)

    with open(file=file_path, mode="rb", buffering=0) as file:
        file.seek(byte_offset)
        while True:
            bytes_to_read = min(remaining_bytes, len(buffer))
            if bytes_to_read == 0:
                break

            read_bytes = file.readinto(mv[:bytes_to_read])
            if read_bytes == 0:
                break
            hash.update(mv[:read_bytes])
            remaining_bytes -= read_bytes

    logger.debug(
        f"Calculated {hash.hexdigest()} SHA256 hash for file {file_path} at byte offset {byte_offset} for {byte_count} bytes"
    )
    return hash.hexdigest()


@define
class TqdmFileReader:
    path: Path = field(validator=validators.instance_of(Path))
    byte_offset: int = field(validator=validators.and_(validators.instance_of(int), validators.ge(0)))
    byte_count: int = field(validator=validators.and_(validators.instance_of(int), validators.ge(1)))
    description: str = field(validator=validators.instance_of(str))
    chunk_size: int = field(
        default=DEFAULT_READER_CHUNK_SIZE, validator=validators.and_(validators.instance_of(int), validators.ge(1))
    )
    _file: io.IOBase = field(validator=validators.instance_of(io.IOBase), init=False)
    _progress_bar: tqdm = field(validator=validators.instance_of(tqdm), init=False)
    _remaining_bytes: int = field(validator=validators.instance_of(int), init=False)

    def __attrs_post_init__(
        self,
    ):
        self._file = open(file=self.path, mode="rb")
        self._file.seek(self.byte_offset)
        self._remaining_bytes = self.byte_count
        self._progress_bar = tqdm(
            total=self.byte_count, unit="B", unit_scale=True, unit_divisor=1024, desc=self.description
        )

    def __len__(self):
        return self.byte_count

    def read(self, size=-1):
        # Return empty bytes object to show EOF
        if self._remaining_bytes <= 0:
            return b""

        # Calculate bytes to read
        if size is None or size < 0:
            bytes_to_read = min(self._remaining_bytes, self.chunk_size)
        else:
            if size == 0:
                return b""
            bytes_to_read = min(self._remaining_bytes, size)

        # Read bytes
        data = self._file.read(bytes_to_read)
        if len(data) < bytes_to_read:
            raise EOFError("Unexpected EOF in read buffer")

        self._progress_bar.update(bytes_to_read)
        self._remaining_bytes -= bytes_to_read
        return data

    def close(self):
        try:
            self._file.close()
        finally:
            self._progress_bar.close()
