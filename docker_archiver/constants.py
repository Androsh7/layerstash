"""Defines constants"""

# Standard libraries
from pathlib import Path

# Third-party libraries
from attrs import define, field, validators

VERSION = "0.1.0"

# Paths
PARENT_DIRECTORY = Path(__file__).parent.parent
CHUNK_DIRECTORY = PARENT_DIRECTORY / "chunks"
DOCKERFILE_PATH = PARENT_DIRECTORY / "build.Dockerfile"

# Chunking
DEFAULT_CHUNK_SIZE = 1024 * 1024 * 1024 * 5  # 5GB
DEFAULT_HASH_CHUNK_SIZE = 64 * 1024 * 1024 # 64MB

# Logging
LOG_LEVELS = ["trace", "debug", "info", "warning", "critical"]

# Requests
DEFAULT_REQUESTS_TIMEOUT = 10

@define
class Config:
    namespace: str = field(default="", validator=validators.instance_of(str))
    repository: str = field(default="", validator=validators.instance_of(str))
    base_tag: str = field(default="", validator=validators.instance_of(str))
    docker_token: str = field(default="", validator=validators.instance_of(str))
    show_docker_progress: bool = field(default=False, validator=validators.instance_of(bool))

config = Config()