"""Utils tests"""

# Standard libraries
import hashlib

# Project libraries
from layerstash.utils import get_sha256_file_hash, humanize_bytes


def test_humanize_bytes_basic_units():
    assert humanize_bytes(0) == "0.00B"
    assert humanize_bytes(1024) == "1.00KB"
    assert humanize_bytes(1024 * 1024) == "1.00MB"
    assert humanize_bytes(1024 * 1024 * 1024) == "1.00GB"


def test_get_sha256_file_hash_matches_hashlib(tmp_path):
    data = b"layerstash-test-data" * 1024
    file_path = tmp_path / "payload.bin"
    file_path.write_bytes(data)

    expected = hashlib.sha256(data).hexdigest()
    assert get_sha256_file_hash(file_path) == expected
