"""Defines constants"""

# Standard libraries
import sys
from pathlib import Path

# Third-party libraries
from attrs import define, field, validators

VERSION = "0.1.0"

# dynamically set directory paths for nuitka/dev setup
if getattr(sys, "frozen", False):
    PARENT_DIRECTORY = Path(sys.executable).resolve().parent
else:
    PARENT_DIRECTORY = Path(__file__).resolve().parent.parent
CHUNK_DIRECTORY = PARENT_DIRECTORY / "chunks"
DOCKERFILE_PATH = PARENT_DIRECTORY / "build.Dockerfile"

# Chunking
DEFAULT_CHUNK_SIZE = 1024 * 1024 * 1024 * 5  # 5GB
DEFAULT_HASH_CHUNK_SIZE = 64 * 1024 * 1024  # 64MB
DEFAULT_READER_CHUNK_SIZE = 1024 * 1024 * 16  # 16MB
DEFAULT_WRITER_CHUNK_SIZE = 1024 * 1024 * 16  # 16MB

# Logging
LOG_LEVELS = ["trace", "debug", "info", "warning", "critical"]

# Requests
DEFAULT_REQUESTS_TIMEOUT = 10


@define
class Config:
    namespace: str = field(default="", validator=validators.instance_of(str))
    repository: str = field(default="", validator=validators.instance_of(str))
    base_tag: str = field(default="", validator=validators.instance_of(str))
    overwrite_image: bool = field(default=False, validator=validators.instance_of(bool))
    docker_pat_token: str = field(default="", validator=validators.instance_of(str))


config = Config()
