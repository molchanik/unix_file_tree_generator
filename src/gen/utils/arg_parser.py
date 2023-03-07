"""File contains custom TreeGenArgParserValidator."""
import sys
from argparse import Namespace
from os import getlogin

from gen.utils.logger_util import logger
from gen.utils.main_utils import sys_exit


class TreeGenArgParserValidator:
    """Custom arguments parser validator."""

    def __init__(self, arguments: Namespace) -> None:
        self.arguments = arguments

    def validate_args(self) -> None:
        """Check arguments to generate file tree."""
        logger.debug('Validating passed arguments.')
        if self.arguments.tree_depth < 1:
            sys_exit(f'Warning! The tree_depth must be greater than 0\n' f'Has been set:\n{self.arguments.tree_depth}')

        if not self.arguments.owners:
            sys_exit(f'Owners have not been set, you can use the current user: {getlogin()}')

        if self.arguments.random:
            necessary_args = (
                self.arguments.min_dirs_count,
                self.arguments.max_dirs_count,
                self.arguments.min_files_count,
                self.arguments.max_files_count,
            )
            if None in necessary_args:
                sys_exit(
                    f'The process has been stopped!\nWith the argument --random, the values for '
                    f'the following keys must be set:\n(dest, name, tree_depth, owners, '
                    f'file_sizes, min_dirs_count, max_dirs_count, min_files_count, '
                    f'max_files_count)\nHave been set: {self.arguments}'
                )

            if self.arguments.max_files_count < self.arguments.min_files_count:
                sys_exit(
                    f'Warning! The min_files_count must not be greater '
                    f'than max_files_count\nHave been set:\n{self.arguments}'
                )

            if self.arguments.max_dirs_count < self.arguments.min_dirs_count:
                sys_exit(
                    f'Warning! The min_dirs_count must not be greater '
                    f'than max_dirs_count\nHave been set:\n{self.arguments}'
                )

            if self.arguments.seed is not None and self.arguments.seed < 1:
                sys_exit('Warning --seed must be more than 0')
        else:
            if self.arguments.dirs_count < 1:
                sys_exit(
                    f'Warning! The dirs_count must be greater than 0\n' f'Has been set:\n{self.arguments.dirs_count}'
                )

        if self.arguments.tree_depth > 150:
            sys.setrecursionlimit(self.arguments.tree_depth * 5)

        if self.arguments.tree_name.startswith('/'):
            self.arguments.tree_name = self.arguments.tree_name.lstrip('/')
            logger.warning(
                'Warning: The value of the "tree_name" parameter has been changed to %s', self.arguments.tree_name
            )

    def expected_tree_dirs_count(self) -> int:
        """Get the number of directories to be created."""
        if self.arguments.dirs_count > 1:
            return int(
                ((self.arguments.dirs_count ** (self.arguments.tree_depth + 1)) - 1) / (self.arguments.dirs_count - 1)
            )
        return int(self.arguments.dirs_count * (self.arguments.tree_depth + 1))

    def expected_tree_files_count(self) -> int:
        """Get the number of files to be created."""
        return int(
            self.expected_tree_dirs_count() * self.arguments.files_count
            + self.arguments.hard_links_count
            + self.arguments.sym_links_count
        )
