"""Main logic"""

# Standard libraries
import argparse
import sys
from pathlib import Path

# Third-party libraries
from loguru import logger

# Project libraries
from layerstash.constants import LOG_LEVELS, VERSION, config, endpoint_dict
from layerstash.download import download_file_from_images
from layerstash.list_files import list_files
from layerstash.upload import push_file_as_image_chunks


def main():
    """Main logic"""

    # Primary parser
    parser = argparse.ArgumentParser(prog="layerstash", description="Tool for storing file in docker hub image layers")
    parser.add_argument("--version", action="version", version=f"layerstash v{VERSION}")
    subparsers = parser.add_subparsers(title="commands", dest="command", required=True)

    # Common args
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument(
        "--log-level", type=str, choices=LOG_LEVELS, default="info", help="Set the application log level"
    )
    common_parser.add_argument(
        "-r", "--repository", required=True, type=str, help="Name of the remote repository, i.e., androsh7/archive"
    )
    common_parser.add_argument(
        "--registry",
        type=str,
        default="docker",
        choices=list(endpoint_dict.keys()),
        help=f'The registry to use {tuple(endpoint_dict.keys())}, default: "docker"',
    )
    common_parser.add_argument("-u", "--username", required=False, type=str, help="Docker username")
    common_parser.add_argument("-p", "--token", required=False, type=str, help="Docker PAT token")

    # Upload parser
    upload_parser = subparsers.add_parser(
        "upload", parents=[common_parser], help="Upload a file as a series of chunked images to docker hub"
    )
    upload_parser.add_argument("-i", "--infile", required=True, type=Path, help="The file to upload")
    upload_parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing images if they have a different hash"
    )
    upload_parser.add_argument(
        "-t",
        "--base-tag",
        required=True,
        type=str,
        help='The base tag, i.e., "python-ftp" , each chunk will have "-<INDEX>" appended to the end',
    )

    # Download parser
    download_parser = subparsers.add_parser(
        "download", parents=[common_parser], help="Download a file from a series of images from docker hub"
    )
    download_parser.add_argument(
        "-o", "--outfile", required=True, type=Path, help="The file to write the downloaded chunks to"
    )
    download_parser.add_argument(
        "-t",
        "--base-tag",
        required=True,
        type=str,
        help='The base tag, i.e., "python-ftp" , each chunk will have "-<INDEX>" appended to the end',
    )

    # List files parser
    list_files_parser = subparsers.add_parser(
        "list",
        parents=[common_parser],
        help="Lists files",
    )
    list_files_parser.add_argument("--exact-size", action="store_true", help="Returns the exact size of the files")

    args = parser.parse_args()

    # Set the log level
    logger.remove(0)
    logger.add(sys.stderr, level=args.log_level.upper())

    # Set the config
    config.repository = args.repository
    config.base_tag = getattr(args, "base_tag", None)

    # Set login details
    if args.token or args.username:
        config.pat_token = args.token
        config.username = args.username
        if not args.token or not args.username:
            parser.error("Username or token is missing")

    # Set endpoint
    config.endpoints = endpoint_dict[args.registry]

    if args.command == "list":
        list_files(args.exact_size)
    elif args.command == "upload":
        config.overwrite_image = args.overwrite
        push_file_as_image_chunks(file_path=args.infile)
    elif args.command == "download":
        download_file_from_images(out_file_path=args.outfile)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
