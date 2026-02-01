"""Defines Docker API models"""

# Standard libraries
import hashlib
import json
from pathlib import Path

# Third-party libraries
from attrs import asdict, define, field, validators

# Project libraries
from layerstash.utils import sha256_file_hash


def calculate_sha256_digest_from_bytes(byte_array: bytes):
    return f"sha256:{hashlib.sha256(byte_array).hexdigest()}"


def calculate_sha256_digest_from_file(file_path: Path) -> str:
    return f"sha256:{sha256_file_hash(file_path)}"


@define
class ManifestConfig:
    mediaType: str = field(validator=validators.instance_of(str))
    size: int = field(validator=validators.instance_of(int))
    digest: str = field(validator=validators.instance_of(str))

    @classmethod
    def from_dict(cls, input_dict):
        return cls(
            mediaType=input_dict["mediaType"],
            size=input_dict["size"],
            digest=input_dict["digest"],
        )


@define
class ManifestLayer:
    mediaType: str = field(validator=validators.instance_of(str))
    size: int = field(validator=validators.instance_of(int))
    digest: str = field(validator=validators.instance_of(str))

    @classmethod
    def from_dict(cls, input_dict):
        return cls(
            mediaType=input_dict["mediaType"],
            size=input_dict["size"],
            digest=input_dict["digest"],
        )


@define
class Manifest:
    schemaVersion: int = field(validator=validators.instance_of(int))
    mediaType: str = field(validator=validators.instance_of(str))
    config: ManifestConfig = field(validator=validators.instance_of(ManifestConfig))
    layers: list[ManifestLayer] = field(
        factory=list,
        validator=validators.deep_iterable(
            member_validator=validators.instance_of(ManifestLayer), iterable_validator=validators.instance_of(list)
        ),
    )

    @classmethod
    def from_dict(cls, input_dict):
        layers = []
        for layer_dict in input_dict["layers"]:
            layers.append(ManifestLayer.from_dict(layer_dict))
        return cls(
            schemaVersion=input_dict["schemaVersion"],
            mediaType=input_dict["mediaType"],
            config=ManifestConfig.from_dict(input_dict["config"]),
            layers=layers,
        )

    def as_json_bytes(self) -> bytes:
        """Returns the object as a json byte array"""
        return bytes(json.dumps(asdict(self), separators=(",", ":")), encoding="ascii")


@define
class BlobRootFS:
    type: str = field(validator=validators.instance_of(str))
    diff_ids: list[any] = field(
        factory=list,
        validator=validators.deep_iterable(
            member_validator=validators.instance_of(any), iterable_validator=validators.instance_of(list)
        ),
    )


@define
class Blob:
    architecture: str = field(validator=validators.instance_of(str))
    os: str = field(validator=validators.instance_of(str))
    rootfs: BlobRootFS = field(validator=validators.instance_of(BlobRootFS))
    history: list = field(factory=list, validator=validators.instance_of(list))
    config: dict[str, any] = field(
        factory=dict,
        validator=validators.deep_mapping(
            key_validator=validators.instance_of(str), mapping_validator=validators.instance_of(dict)
        ),
    )

    def as_json_bytes(self) -> bytes:
        """Returns the object as a json byte array"""
        return bytes(json.dumps(asdict(self), separators=(",", ":")), encoding="ascii")

    def get_sha256_digest(self) -> str:
        """Return the blob's sha256 digest"""
        return calculate_sha256_digest_from_bytes(self.as_json_bytes())
