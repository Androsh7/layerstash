"""Build the executable with nuitka"""

# Standard libraries
import subprocess
from pathlib import Path

PARENT_DIRECTORY = Path(__file__).parent

LINUX_NUITKA_ARGS = [
    "--standalone",
    "--onefile",
    "--output-filename=/src/docker_archiver.bin",
]

def build_linux():
    subprocess.run(
        'docker run --name nuitka-compiler --detach androsh7/nuitka-compiler:latest-x86_64-glibc-2.17-py3.13 sleep infinity '
        '&& docker cp docker_archiver nuitka-compiler:/src/docker_archiver '
        '&& docker cp pyproject.toml nuitka-compiler:/src/pyproject.toml '
        '&& docker exec nuitka-compiler python3 -m pip install . '
        f'&& docker exec nuitka-compiler python3 -m nuitka {" ".join(LINUX_NUITKA_ARGS)} /src/docker_archiver/main.py '
        f'&& docker cp nuitka-compiler:/src/docker_archiver.bin docker_archiver.bin '
        '&& docker rm --force nuitka-compiler',
        cwd=PARENT_DIRECTORY,
        shell=True,
        check=True
    )

build_linux()