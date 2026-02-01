"""Utils tests"""

# Standard libraries
import hashlib

# Project libraries
from layerstash.chunker import chunk_file, merge_file
from layerstash.utils import humanize_bytes, sha256_file_hash


def test_humanize_bytes_basic_units():
    assert humanize_bytes(0) == "0.00B"
    assert humanize_bytes(1024) == "1.00KB"
    assert humanize_bytes(1024 * 1024) == "1.00MB"
    assert humanize_bytes(1024 * 1024 * 1024) == "1.00GB"


def test_sha256_file_hash_matches_hashlib(tmp_path):
    data = b"layerstash-test-data" * 1024
    file_path = tmp_path / "payload.bin"
    file_path.write_bytes(data)

    expected = hashlib.sha256(data).hexdigest()
    assert sha256_file_hash(file_path) == expected


def test_chunk_and_merge(tmp_path):
    source = tmp_path / "source.bin"
    chunk = tmp_path / "chunk.bin"
    merged = tmp_path / "merged.bin"

    payload = b"abc123" * 1000
    source.write_bytes(payload)

    chunk_file(source, chunk, read_bytes=1500, byte_offset=0)
    assert chunk.exists()

    merge_file(chunk, merged)
    assert merged.read_bytes() == payload[:1500]
    assert not chunk.exists()
