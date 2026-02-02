"""Functions for pulling image tags from docker hub"""

# Standard libraries
from http import HTTPStatus
from pathlib import Path
from urllib.parse import urljoin

# Third-party libraries
import requests
from loguru import logger
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
    url = config.endpoints.token_endpoint
    params = {
        "service": config.endpoints.service_auth_endpoint,
        "scope": f"repository:{config.repository}:pull",
    }
    response = requests.get(
        url=url,
        params=params,
        timeout=DEFAULT_REQUESTS_TIMEOUT,
        auth=HTTPBasicAuth(username=config.username, password=config.pat_token) if config.pat_token else None,
    )
    logger.debug(f"{url} {params} {response}")
    response.raise_for_status()
    return response.json()["token"]


def get_docker_push_token() -> str:
    """Returns a push/pull token for the repository"""
    url = config.endpoints.token_endpoint
    params = {
        "service": config.endpoints.service_auth_endpoint,
        "scope": f"repository:{config.repository}:push,pull",
    }
    response = requests.get(
        url=url,
        params=params,
        timeout=DEFAULT_REQUESTS_TIMEOUT,
        auth=HTTPBasicAuth(username=config.username, password=config.pat_token),
    )
    logger.debug(f"{url} {params} {response}")
    response.raise_for_status()

    return response.json()["token"]


def get_manifest(tag: str) -> Manifest | None:
    """Returns the manifest for a specific tag"""
    url = f"{config.endpoints.registry_endpoint}/{config.repository}/manifests/{tag}"
    response = requests.get(
        url=url,
        headers={"Authorization": f"Bearer {get_docker_pull_token()}"},
    )
    logger.debug(f"{url} {response}\n{response.text}")
    if response.status_code == HTTPStatus.OK:
        return Manifest.from_dict(response.json())
    elif response.status_code == HTTPStatus.NOT_FOUND:
        return None
    else:
        response.raise_for_status()


def does_blob_exist(digest: str) -> bool:
    """Returns True if the digest exists"""
    url = f"{config.endpoints.registry_endpoint}/{config.repository}/blobs/{digest}"
    response = requests.get(
        url=url,
        headers={"Authorization": f"Bearer {get_docker_pull_token()}"},
    )

    logger.debug(f"{url} {response}\n{response.text}")
    if response.status_code == HTTPStatus.OK:
        return True
    elif response.status_code == HTTPStatus.NOT_FOUND:
        return False
    else:
        response.raise_for_status()


def get_blob_upload_url() -> str:
    location_url = f"{config.endpoints.registry_endpoint}/{config.repository}/blobs/uploads/"
    location_response = requests.post(
        url=location_url,
        headers={"Authorization": f"Bearer {get_docker_push_token()}"},
        allow_redirects=False,
    )

    logger.debug(f"{location_url} {location_response}\nHeaders: {location_response.headers}")
    if location_response.status_code != HTTPStatus.ACCEPTED:
        raise DockerException("Failed to initialize upload")
    if (location_url := location_response.headers.get("location")) is None:
        raise DockerException(f"Missing location header. Headers: {location_response.headers}")

    return urljoin(config.endpoints.registry_endpoint, location_url)


def push_blob_config(blob: Blob, digest: str, timeout: int = DEFAULT_REQUESTS_TIMEOUT):
    """Pushes the blob config to the repository"""
    upload_url = get_blob_upload_url()
    upload_response = requests.put(
        url=upload_url,
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

    logger.debug(f"{upload_url} {upload_response}\n{upload_response.text}")
    if upload_response.status_code not in (HTTPStatus.CREATED, HTTPStatus.ACCEPTED):
        raise DockerException(f"Blob config upload failed: {upload_response.status_code} {upload_response.text}")


def push_blob_file(file_path: Path, digest: str, timeout: int, progress_bar_description: str):
    """Pushes a layer to the repository"""
    url = get_blob_upload_url()
    params = {
        "digest": digest,
    }
    tqdm_file_reader = TqdmFileReader(path=file_path, description=progress_bar_description)
    logger.debug(f"{url} {params} starting transfer of {file_path} with digest {digest}")
    upload_response = requests.put(
        url=url,
        headers={
            "Authorization": f"Bearer {get_docker_push_token()}",
            "Content-Type": "application/octet-stream",
        },
        params=params,
        data=tqdm_file_reader,
        timeout=timeout,
    )
    tqdm_file_reader.close()
    logger.debug(f"{url} {params} {upload_response}\n{upload_response.text}")

    if upload_response.status_code not in (HTTPStatus.CREATED, HTTPStatus.ACCEPTED):
        raise DockerException(f"File upload failed: {upload_response.status_code} {upload_response.text}")


def pull_blob_file(file_path: Path, digest: str, timeout: int, progress_bar_description: str):
    url = f"{config.endpoints.registry_endpoint}/{config.repository}/blobs/{digest}"
    logger.debug(f"{url} Starting download")
    with requests.get(
        url=url,
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

    logger.debug(f"{url} {response}\n{response.text}")


def push_manifest(manifest: Manifest, tag: str):
    response = requests.put(
        url=f"{config.endpoints.registry_endpoint}/{config.repository}/manifests/{tag}",
        headers={
            "Authorization": f"Bearer {get_docker_push_token()}",
            "Content-Type": "application/vnd.docker.distribution.manifest.v2+json",
        },
        data=manifest.as_json_bytes(),
    )

    if response.status_code not in (HTTPStatus.CREATED, HTTPStatus.ACCEPTED):
        raise DockerException(f"Manifest upload failed: {response.status_code} {response.text}")
