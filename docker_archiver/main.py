"""Main logic"""

# Standard libraries
import argparse
import sys
from pathlib import Path

# Third-party libraries
from loguru import logger

# Project libraries
from docker_archiver.constants import LOG_LEVELS, VERSION, config
from docker_archiver.download import download_file_from_images
from docker_archiver.upload import push_file_as_image_chunks


def main():
    """Main logic"""

    # Primary parser
    parser = argparse.ArgumentParser(prog="docker_archiver")
    parser.add_argument("--version", action="version", version=f"Docker Archiver v{VERSION}")
    parser.add_argument(
        "--log-level", type=str, choices=LOG_LEVELS, default="info", help="Set the application log level"
    )
    subparsers = parser.add_subparsers(title="commands", dest="command", required=True)

    # Upload parser
    upload_parser = subparsers.add_parser("upload", help="Upload a file as a series of images to docker hub")
    upload_parser.add_argument("-i", "--infile", required=True, type=Path, help="The file to upload")
    upload_parser.add_argument("-n", "--namespace", required=True, type=str, help="Namespace for the docker account")
    upload_parser.add_argument(
        "-r", "--repository", required=True, type=str, help="Name of the repository to upload to"
    )
    upload_parser.add_argument(
        "-t",
        "--base-tag",
        required=True,
        type=str,
        help='The base tag, I.E: "python-ftp" , each chunk will have "-<INDEX>" appended to the end',
    )
    upload_parser.add_argument("--token", required=True, type=str, help="Docker PAT token")

    # Download parser
    download_parser = subparsers.add_parser("download", help="Download a file from a series of images from docker hub")
    download_parser.add_argument(
        "-o", "--outfile", required=True, type=Path, help="The file to write the downloaded chunks to"
    )
    download_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing images if they have a different hash")
    download_parser.add_argument("-n", "--namespace", required=True, type=str, help="Namespace for the docker account")
    download_parser.add_argument(
        "-r", "--repository", required=True, type=str, help="Name of the repository to download from"
    )
    download_parser.add_argument(
        "-t",
        "--base-tag",
        required=True,
        type=str,
        help='The base tag for the repository, I.E: "python-ftp"',
    )
    download_parser.add_argument("--token", required=True, type=str, help="Docker PAT token")

    args = parser.parse_args()

    # Set the log level
    logger.remove(0)
    logger.add(sys.stderr, level=args.log_level.upper())

    # Set the config
    config.namespace = args.namespace
    config.repository = args.repository
    config.base_tag = args.base_tag
    config.docker_pat_token = args.token
    config.overwrite_image = args.overwrite

    if args.command == "upload":
        push_file_as_image_chunks(file_path=args.infile)
    if args.command == "download":
        download_file_from_images(out_file_path=args.outfile)


if __name__ == "__main__":
    main()
