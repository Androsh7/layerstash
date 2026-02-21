"""Defines constants"""

# Third-party libraries
from attrs import define, field, validators

VERSION = "0.1.1"

# Chunking
DEFAULT_CHUNK_SIZE = 1024 * 1024 * 1024 * 5  # 5GB
DEFAULT_HASH_CHUNK_SIZE = 1024 * 1024 * 16  # 16MB
DEFAULT_READER_CHUNK_SIZE = 1024 * 1024 * 16  # 16MB
DEFAULT_WRITER_CHUNK_SIZE = 1024 * 1024 * 16  # 16MB

# Logging
LOG_LEVELS = ["trace", "debug", "info", "warning", "critical"]

# Retries
RETRIES = (
    15,  # 15 seconds
    30,  # 30 seconds
    60 * 1,  # 1 minute
    60 * 5,  # 5 minutes
    60 * 15,  # 15 minutes
    60 * 30,  # 30 minutes
    None,
)

# Requests
DEFAULT_REQUESTS_TIMEOUT = 10


# Endpoints
@define
class RegistryEndpoint:
    token_endpoint: str = field(validator=validators.instance_of(str))
    registry_endpoint: str = field(validator=validators.instance_of(str))
    service_auth_endpoint: str = field(validator=validators.instance_of(str))


endpoint_dict = {
    "docker": RegistryEndpoint(
        token_endpoint="https://auth.docker.io/token",
        registry_endpoint="https://registry-1.docker.io/v2",
        service_auth_endpoint="registry.docker.io",
    ),
    "ghcr": RegistryEndpoint(
        token_endpoint="https://ghcr.io/token",
        registry_endpoint="https://ghcr.io/v2",
        service_auth_endpoint="ghcr.io",
    ),
}


@define
class Config:
    repository: str = field(default=None, validator=validators.optional(validators.instance_of(str)))
    base_tag: str = field(default=None, validator=validators.optional(validators.instance_of(str)))
    overwrite_image: bool = field(default=None, validator=validators.optional(validators.instance_of(bool)))
    endpoints: RegistryEndpoint = field(
        default=None, validator=validators.optional(validators.instance_of(RegistryEndpoint))
    )
    username: str = field(default=None, validator=validators.optional(validators.instance_of(str)))
    pat_token: str = field(default=None, validator=validators.optional(validators.instance_of(str)))


config = Config()
