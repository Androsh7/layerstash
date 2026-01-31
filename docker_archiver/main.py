"""Main logic"""

# Standard libraries
import argparse

# Project libraries
from docker_archiver.constants import VERSION


def main():
    """Main logic"""
    parser = argparse.ArgumentParser(prog="docker_archiver")
    parser.add_argument("--version", action="version", version=f"Docker Archiver v{VERSION}")
    args = parser.parse_args()


if __name__ == "__main__":
    main()
