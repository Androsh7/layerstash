"""Defines functions for listing files"""

# Project libraries
from layerstash.docker_api import get_manifest, get_tag_list
from layerstash.utils import humanize_bytes


def list_files(exact_size: bool = False):
    tag_list = get_tag_list()
    base_tag_dict = dict()
    for tag in tag_list:
        base_tag = tag.rsplit(sep="-", maxsplit=1)[0]
        if base_tag not in base_tag_dict.keys():
            base_tag_dict.update({base_tag: 1})
        else:
            base_tag_dict[base_tag] += 1

    for base_tag, chunks in base_tag_dict.items():
        if exact_size:
            last_manifest = get_manifest(tag=f"{base_tag}-{chunks}")
            size = (
                5 * 1024 * 1024 * 1024 * (chunks - 1) + last_manifest.layers[0].size
            )  # 5GB * number of full chunks + last chunk size
            print(f"{base_tag} ({chunks} chunk{'s' if chunks > 1 else ''}): {humanize_bytes(size)}")
        elif chunks == 1:
            print(f"{base_tag} ({chunks} chunk): <5GB")
        else:
            print(f"{base_tag} ({chunks} chunks): ~{chunks * 5}GB")
