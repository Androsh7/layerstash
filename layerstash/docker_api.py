"""Functions for pulling image tags from docker hub"""

# Standard libraries
from http import HTTPStatus
from pathlib import Path

# Third-party libraries
import requests
from requests.auth import HTTPBasicAuth
from tqdm import tqdm

# Project libraries
from layerstash.constants import DEFAULT_REQUESTS_TIMEOUT, DEFAULT_WRITER_CHUNK_SIZE, config
from layerstash.docker_api_models import Blob, Manifest
from layerstash.utils import TqdmFileReader


class DockerException(Exception):
    pass


def get_docker_pull_token() -> str:
    """Returns a pull token for the repository"""
    response = requests.get(
        "https://auth.docker.io/token",
        params={
            "service": "registry.docker.io",
            "scope": f"repository:{config.namespace}/{config.repository}:pull",
        },
        timeout=DEFAULT_REQUESTS_TIMEOUT,
        auth=HTTPBasicAuth(username=config.namespace, password=config.docker_pat_token),
    )
    response.raise_for_status()

    return response.json()["token"]


def get_docker_push_token() -> str:
    """Returns a push/pull token for the repository"""
    response = requests.get(
        "https://auth.docker.io/token",
        params={
            "service": "registry.docker.io",
            "scope": f"repository:{config.namespace}/{config.repository}:push,pull",
        },
        timeout=DEFAULT_REQUESTS_TIMEOUT,
        auth=HTTPBasicAuth(username=config.namespace, password=config.docker_pat_token),
    )
    response.raise_for_status()

    return response.json()["token"]


def get_manifest(tag: str) -> Manifest | None:
    """Returns the manifest for a specific tag"""
    response = requests.get(
        url=f"https://registry-1.docker.io/v2/{config.namespace}/{config.repository}/manifests/{tag}",
        headers={"Authorization": f"Bearer {get_docker_pull_token()}"},
    )
    if response.status_code == HTTPStatus.OK:
        return Manifest.from_dict(response.json())
    elif response.status_code == HTTPStatus.NOT_FOUND:
        return None
    else:
        response.raise_for_status()


def does_blob_exist(digest: str) -> bool:
    """Returns True if the digest exists"""
    response = requests.get(
        url=f"https://registry-1.docker.io/v2/{config.namespace}/{config.repository}/blobs/{digest}",
        headers={"Authorization": f"Bearer {get_docker_pull_token()}"},
    )
    if response.status_code == HTTPStatus.OK:
        return True
    elif response.status_code == HTTPStatus.NOT_FOUND:
        return False
    else:
        response.raise_for_status()


def get_blob_upload_url() -> str:
    location_response = requests.post(
        url=f"https://registry-1.docker.io/v2/{config.namespace}/{config.repository}/blobs/uploads/",
        headers={"Authorization": f"Bearer {get_docker_push_token()}"},
        allow_redirects=False,
    )

    if location_response.status_code != HTTPStatus.ACCEPTED:
        raise DockerException("Failed to initialize upload")
    if (location_url := location_response.headers.get("location")) is None:
        raise DockerException(f"Missing location header. Headers: {location_response.headers}")

    return location_url


def push_blob_config(blob: Blob, digest: str, timeout: int = DEFAULT_REQUESTS_TIMEOUT):
    """Pushes the blob config to the repository"""
    upload_response = requests.put(
        url=get_blob_upload_url(),
        headers={
            "Authorization": f"Bearer {get_docker_push_token()}",
            "Content-Type": "application/octet-stream",
        },
        params={
            "digest": digest,
        },
        data=blob.as_json_bytes(),
        timeout=timeout,
    )

    if upload_response.status_code not in (HTTPStatus.CREATED, HTTPStatus.ACCEPTED):
        raise DockerException(f"Blob config upload failed: {upload_response.status_code} {upload_response.text}")


def push_blob_file(file_path: Path, digest: str, timeout: int, progress_bar_description: str):
    """Pushes a layer to the repository"""
    tqdm_file_reader = TqdmFileReader(path=file_path, description=progress_bar_description)
    upload_response = requests.put(
        url=get_blob_upload_url(),
        headers={
            "Authorization": f"Bearer {get_docker_push_token()}",
            "Content-Type": "application/octet-stream",
        },
        params={
            "digest": digest,
        },
        data=tqdm_file_reader,
        timeout=timeout,
    )
    tqdm_file_reader.close()

    if upload_response.status_code not in (HTTPStatus.CREATED, HTTPStatus.ACCEPTED):
        raise DockerException(f"File upload failed: {upload_response.status_code} {upload_response.text}")


def pull_blob_file(file_path: Path, digest: str, timeout: int, progress_bar_description: str):
    with requests.get(
        f"https://registry-1.docker.io/v2/{config.namespace}/{config.repository}/blobs/{digest}",
        headers={
            "Authorization": f"Bearer {get_docker_pull_token()}",
        },
        stream=True,
        timeout=timeout,
    ) as response:
        response.raise_for_status()

        total = int(response.headers.get("Content-Length", 0))

        with (
            open(file=file_path, mode="wb") as f,
            tqdm(
                total=total,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                desc=progress_bar_description,
            ) as progress_bar,
        ):
            for chunk in response.iter_content(chunk_size=DEFAULT_WRITER_CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
                    progress_bar.update(len(chunk))


def push_manifest(manifest: Manifest, tag: str):
    response = requests.put(
        url=f"https://registry-1.docker.io/v2/{config.namespace}/{config.repository}/manifests/{tag}",
        headers={
            "Authorization": f"Bearer {get_docker_push_token()}",
            "Content-Type": "application/vnd.docker.distribution.manifest.v2+json",
        },
        data=manifest.as_json_bytes(),
    )

    if response.status_code not in (HTTPStatus.CREATED, HTTPStatus.ACCEPTED):
        raise DockerException(f"Manifest upload failed: {response.status_code} {response.text}")
