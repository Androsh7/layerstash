"""Build the executable with nuitka"""

# Standard libraries
import argparse
import subprocess
from pathlib import Path

PARENT_DIRECTORY = Path(__file__).parent


def build_linux():
    subprocess.run(
        "docker run --name nuitka-compiler --detach androsh7/nuitka-compiler:latest-x86_64-glibc-2.17-py3.13 sleep infinity "
        "&& docker cp docker_archiver nuitka-compiler:/src/docker_archiver "
        "&& docker cp pyproject.toml nuitka-compiler:/src/pyproject.toml "
        "&& docker exec nuitka-compiler python3 -m pip install . "
        "&& docker exec nuitka-compiler python3 -m nuitka "
        "   --standalone "
        "   --onefile "
        "   --output-filename=/src/docker_archiver.bin "
        "   /src/docker_archiver/main.py "
        "   --onefile-tempdir-spec={HOME}/.docker_archiver_bin"
        "&& docker cp nuitka-compiler:/src/docker_archiver.bin docker_archiver.bin "
        "&& docker rm --force nuitka-compiler",
        cwd=PARENT_DIRECTORY,
        shell=True,
        check=True,
    )

def build_windows():
    subprocess.run(
        "nuitka "
        "--standalone "
        "--onefile "
        "--output-filename=docker_archiver.exe "
        "--onefile-tempdir-spec={HOME}/.docker_archiver_bin "
        "docker_archiver/main.py",
        cwd=PARENT_DIRECTORY,
        shell=True,
        check=True,
    )

def main():
    """Main logic"""
    parser = argparse.ArgumentParser(prog="build.py")
    parser.add_argument("--windows", action="store_true", help="Build the windows executable")
    parser.add_argument("--linux", action="store_true", help="Build the linux executable")
    parser.add_argument("--build-all", action="store_true", help="Build the windows and linux executable")
    args = parser.parse_args()

    if args.windows or args.build_all:
        build_windows()
    if args.linux or args.build_all:
        build_linux()
    if not args.linux and not args.windows and not args.build_all:
        parser.print_help()

if __name__ == "__main__":
    main()