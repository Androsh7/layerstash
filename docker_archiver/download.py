"""Functions for downloading from docker hub"""

# Standard libraries
from pathlib import Path

# Third-party libraries
from attrs import define, field, validators

# Project libraries
from docker_archiver.chunker import merge_file
from docker_archiver.constants import CHUNK_DIRECTORY, config
from docker_archiver.docker_api import DockerException, get_manifest, pull_blob_file
from docker_archiver.utils import humanize_bytes


@define
class DownloadTarget:
    tag: str = field(validator=validators.instance_of(str))
    digest: str = field(validator=validators.instance_of(str))
    size: int = field(validator=validators.instance_of(int))


def get_download_targets() -> list[DownloadTarget]:
    digest_list = []
    index = 1
    while True:
        chunk_tag = f"{config.base_tag}-{index}"
        manifest = get_manifest(tag=chunk_tag)
        if manifest is not None:
            digest_list.append(
                DownloadTarget(tag=chunk_tag, digest=manifest.layers[0].digest, size=manifest.layers[0].size)
            )
        else:
            break
        index += 1
    if len(digest_list) == 0:
        raise DockerException(f"No digests found for base tag {config.base_tag}")
    return digest_list


def download_file_from_images(out_file_path: Path):
    print("Loading download targets")
    download_list = get_download_targets()
    total_size = 0
    for download in download_list:
        total_size += download.size
    print(f"File size: {humanize_bytes(total_size)}")
    print(f"Total chunks: {len(download_list)}")

    chunk_path_list = []
    for index, download in enumerate(download_list, start=1):
        chunk_path = CHUNK_DIRECTORY / f"{download.tag}"
        chunk_path_list.append(chunk_path)
        pull_blob_file(
            file_path=chunk_path,
            digest=download.digest,
            timeout=9000,
            progress_bar_description=f"Downloading {download.tag} ({index}/{len(download_list)})",
        )

    for chunk_path in chunk_path_list:
        merge_file(
            input_file_path=chunk_path,
            output_file_path=out_file_path,
        )
