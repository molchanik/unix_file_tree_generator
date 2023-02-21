"""This file contains utils for the main function."""
import json
import sys
from os import path
from shutil import rmtree

from logger_util import logger


class CleanUp:
    """Class contains methods for cleaning the system after tree generating."""

    def __init__(self, tree_full_path: str) -> None:
        self.tree_full_path = tree_full_path

    def is_tree_exist(self) -> bool:
        """Check is tree exist."""
        return path.exists(self.tree_full_path)

    def remove_tree(self):
        """Remove file tree."""
        if self.is_tree_exist():
            rmtree(self.tree_full_path)
            print(f'\n{self.tree_full_path} has been removed.')


def sys_exit(err_msg: str = 'Unexpected exit!', tree_full_path: str | None = None):
    """
    Stop process with error message.

    :param err_msg:             error message
    :param tree_full_path:      TreeGenerator full path or None
    """
    if tree_full_path:
        sys_clean = CleanUp(tree_full_path)
        sys_clean.remove_tree()
    logger.error(err_msg)
    sys.exit()


def add_input_args_to_json_report(full_report_path: str, arguments: str, default_time: int, seed_value: int):
    """
    Save the passed parameters to tree json report.

    :param full_report_path:  json tree report path
    :param arguments:         passed parameters
    :param default_time:      timestamp to tree reproduce
    :param seed_value:        random seed value to tree reproduce
    """
    with open(full_report_path, encoding='utf-8') as json_file:
        tree_struct = json.load(json_file)

    final_tree = {
        'command_line': arguments,
        'default_time': default_time,
        'seed': seed_value,
        'tree_structure': tree_struct,
    }

    with open(full_report_path, 'w', encoding='utf-8') as json_file:
        json.dump(final_tree, json_file, indent=4, ensure_ascii=False)
