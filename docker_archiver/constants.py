"""Defines constants"""

# Standard libraries
from pathlib import Path

VERSION = "0.1.0"

# Paths
PARENT_DIRECTORY = Path(__file__).parent.parent
CHUNK_DIRECTORY = PARENT_DIRECTORY / "chunks"
DOCKERFILE_PATH = PARENT_DIRECTORY / "build.Dockerfile"

# Chunking
DEFAULT_CHUNK_SIZE = 1024 * 1024 * 1024 * 5  # 5GB
