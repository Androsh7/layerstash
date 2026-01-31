"""Main logic"""

# Standard libraries
import argparse
import sys
from pathlib import Path

# Third-party libraries
from loguru import logger

# Project libraries
from docker_archiver.constants import VERSION, config, LOG_LEVELS
from docker_archiver.upload import upload_file_as_chunks


def main():
    """Main logic"""

    # Primary parser
    parser = argparse.ArgumentParser(prog="docker_archiver")
    parser.add_argument("--version", action="version", version=f"Docker Archiver v{VERSION}")
    subparsers = parser.add_subparsers(title="commands", dest="command", required=True)

    # Upload
    upload_parser = subparsers.add_parser("upload", help="Upload a file as a series of images to docker hub")
    upload_parser.add_argument("-f", "--file", required=True, type=Path, help="The file to upload")
    upload_parser.add_argument("-n", "--namespace", required=True, type=str, help="Namespace for the docker account")
    upload_parser.add_argument("-r", "--repository", required=True, type=str, help="Name of the repository to upload to")
    upload_parser.add_argument(
        "-t",
        "--base-tag",
        required=True,
        type=str,
        help='The base tag, I.E: "python-ftp" , each chunk will have "-<INDEX>" appended to the end',
    )
    upload_parser.add_argument("--token", required=True, type=str, help="Docker PAT token")
    upload_parser.add_argument("--show-docker-progress", action="store_true", help="Shows docker progress for building/pushing images")
    upload_parser.add_argument("--log-level", type=str, choices=LOG_LEVELS, default="info", help="Set the application log level")

    args = parser.parse_args()

    # Set the log level
    logger.remove(0)
    logger.add(sys.stderr, level=args.log_level.upper())

    # Set the config
    config.namespace = args.namespace
    config.repository = args.repository
    config.base_tag = args.base_tag
    config.docker_token = args.token
    config.show_docker_progress = args.show_docker_progress

    if args.command == "upload":
        upload_file_as_chunks(args.file)



if __name__ == "__main__":
    main()
