"""Build the executable with nuitka"""

# Standard libraries
import argparse
import subprocess
from pathlib import Path

PARENT_DIRECTORY = Path(__file__).parent


def build_linux():
    subprocess.run(
        "docker run --name nuitka-compiler --detach androsh7/nuitka-compiler:latest-x86_64-glibc-2.28-py3.13 sleep infinity "
        "&& docker cp layerstash nuitka-compiler:/src/layerstash "
        "&& docker cp pyproject.toml nuitka-compiler:/src/pyproject.toml "
        "&& docker exec nuitka-compiler python3 -m pip install . "
        "&& docker exec nuitka-compiler python3 -m nuitka[onefile] "
        "   --standalone "
        "   --onefile "
        "   --output-filename=/src/layerstash.bin "
        "   /src/layerstash/main.py "
        "   --onefile-tempdir-spec={HOME}/.layerstash"
        "&& docker cp nuitka-compiler:/src/layerstash.bin layerstash.bin "
        "&& docker rm --force nuitka-compiler",
        cwd=PARENT_DIRECTORY,
        shell=True,
        check=True,
    )


def build_windows():
    subprocess.run(
        "nuitka "
        "--assume-yes-for-downloads "
        "--standalone "
        "--onefile "
        "--output-filename=layerstash.exe "
        "--onefile-tempdir-spec={HOME}/.layerstash "
        "layerstash/main.py",
        cwd=PARENT_DIRECTORY,
        shell=True,
        check=True,
    )


def main():
    """Main logic"""
    parser = argparse.ArgumentParser(prog="build.py")
    parser.add_argument("--windows", action="store_true", help="Build the Windows executable")
    parser.add_argument("--linux", action="store_true", help="Build the Linux executable")
    parser.add_argument("--build-all", action="store_true", help="Build the Windows and Linux executable")
    args = parser.parse_args()

    if args.windows or args.build_all:
        build_windows()
    if args.linux or args.build_all:
        build_linux()
    if not args.linux and not args.windows and not args.build_all:
        parser.print_help()


if __name__ == "__main__":
    main()
