# coding=utf-8
"""
Provide useful functions to obtain absolute path(s) of certain file(s)
"""

import os


def get_path(*, target_dir: str, file_init: str, file_ext: str) -> str:
    for (dir_name, dirs_here, files_here) in os.walk(target_dir):
        for file in files_here:
            if file.endswith(file_ext) and file.startswith(file_init):
                path = os.path.join(dir_name, file)
                return path


def get_paths(*, target_dir: str, file_init: str, file_ext: str) -> list:
    paths = []
    for (dir_name, dirs_here, files_here) in os.walk(target_dir):
        for file in files_here:
            if file.endswith(file_ext) and file.startswith(file_init):
                path = os.path.join(dir_name, file)
                paths.append(path)
    return paths
