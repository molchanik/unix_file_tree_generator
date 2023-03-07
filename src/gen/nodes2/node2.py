"""File contains logic of nodes(Directory, File, etc.) structure."""
from __future__ import annotations

import copy

import typing
from os import path

T = typing.TypeVar('T', bound='AbstractNode')


class AbstractNode(typing.Generic[T]):
    """Basic node entity params in unix system."""

    def __init__(self, dest: str, name: str, owner: str):
        self.dest = dest
        self.name = name
        self.owner = owner
        self._sub_nodes: list[T] = list()

    def add_node(self, node: T) -> None:
        """Add AbstractNode instance."""
        self._sub_nodes.append(node)

    def full_path(self) -> str:
        """Get full path of a file."""
        return path.join(self.dest, self.name)

    def sub_nodes_generator(
            self, type_constraint: type[T] | None = None, recursive: bool = False  # noqa: FBT001, FBT002
    ) -> typing.Generator[T, None, None]:
        """
        Allow iterating through all sub-nodes either directly or recursively.
        Allow type constraint for the nodes to limit the lookup results.
        """
        for sub_node in self._sub_nodes:
            if type_constraint is None or isinstance(sub_node, type_constraint):
                yield sub_node

            if recursive:
                yield from sub_node.sub_nodes_generator(recursive=True, type_constraint=type_constraint)

    def get_nodes_count(self, type_constraint: type[T] | None = None) -> int:
        """Get count of nodes in current node."""
        return sum(1 for _ in self.sub_nodes_generator(recursive=False, type_constraint=type_constraint))

    def get_all_nodes_count(self, type_constraint: type[T] | None = None) -> int:
        """Get count of nodes in current node and in the sub nodes."""
        return sum(1 for _ in self.sub_nodes_generator(recursive=True, type_constraint=type_constraint))


EMPTY_NODES: list[AbstractNode] = []


class AbstractLeafNode(AbstractNode):
    """Represent a Leaf node base - a node that cannot have sub-nodes."""

    _sub_nodes = EMPTY_NODES

    def add_node(self, node: object) -> typing.NoReturn:
        """Block adding sub-nodes for a Leaf."""
        err = f'Node type {type(self).__name__} cannot have sub-nodes!'
        raise TypeError(err)


class File(AbstractLeafNode):
    """Class represents file entity."""

    def __init__(self, dest: str, name: str, owner: str, size: int, atime: str, mtime: str):
        super().__init__(dest, name, owner)
        self.size = size
        self.atime = atime
        self.mtime = mtime


class HardLink(AbstractLeafNode):
    """Class represents hard link entity."""

    file_obj: AbstractNode

    def __init__(self, dest: str, name: str, owner: str, file_obj: AbstractNode | dict):
        super().__init__(dest, name, owner)
        self.file_obj = file_obj


class SymLink(AbstractLeafNode):
    """Class represents symlink entity."""

    file_obj: AbstractNode | dict

    def __init__(self, dest: str, name: str, owner: str, size: int, atime: str, mtime: str, file_obj: AbstractNode | dict):
        super().__init__(dest, name, owner)
        self.file_obj = file_obj
        self.size = size
        self.atime = atime
        self.mtime = mtime


class Directory(AbstractNode):  # pylint: disable=too-many-instance-attributes, function-redefined
    """Class represents directory entity."""

    def __init__(self, dest: str, name: str, owner: str,
                 possible_owners: list[str]) -> None:
        """
        Initialize Directory class attributes.

        :param dest:        full path to destination start tree folder
        :param name:        name for root tree folder
        :param owner:       owner name
        """
        super().__init__(dest, name, owner)
        self.possible_owners = possible_owners

    def __str__(self) -> str:
        return (
            f'Directory dest: {self.dest}\nDirectory name: {self.name}\nOwner: {self.owner}\n'
            f'Sub dirs: {self.sub_dirs}\nFiles: {self.files}\nHard Links: {self.hard_links}\n'
            f'SymLinks: {self.symlinks}\n'
        )

    def sub_dirs(self) -> list[Directory]:
        """
        Getter method by subdirectories.

        :return: list of Directory instances
        """
        return list(self.sub_nodes_generator(type_constraint=Directory))

    def files(self) -> list[File]:
        """Getter method by files."""
        return list(self.sub_nodes_generator(type_constraint=File))

    def symlinks(self) -> list[SymLink]:
        """Getter method by symlinks."""
        return list(self.sub_nodes_generator(type_constraint=SymLink))

    def hard_links(self) -> list[HardLink]:
        """Getter method by hard links."""
        return list(self.sub_nodes_generator(type_constraint=HardLink))

    def total_files_count(self) -> int:
        """
        Get num of files in the current dir and all subdirectories.

        :return:    count of files
        """
        files = self.get_all_nodes_count(type_constraint=File)
        symlinks = self.get_all_nodes_count(type_constraint=SymLink)
        return files + symlinks

    def current_dir_files_count(self) -> int:
        """
        Get num of files in the current dir.

        :return:    count of files
        """
        files = self.get_nodes_count(type_constraint=File)
        symlinks = self.get_nodes_count(type_constraint=SymLink)
        return files + symlinks

    def sub_dirs_files_count(self) -> int:
        """
        Get num of files in the subdirectories.

        :return:    count of files
        """
        return self.total_files_count() - self.current_dir_files_count()

    def get_all_files(self) -> list[File]:
        """
        Get files objects in the current dir and all subdirectories.

        :return:    list of file objects
        """
        return list(self.sub_nodes_generator(recursive=True, type_constraint=File))

    def total_file_size_in_dir(self) -> int:
        """
        Get total size of all files in current dir.

        :return:    total size of files
        """
        files_sum = sum(file.size for file in self.sub_nodes_generator(type_constraint=File))
        sym_links_sum = sum(sym_link.size for sym_link in self.sub_nodes_generator(type_constraint=SymLink))
        return int(files_sum) + int(sym_links_sum)

    def total_size_all_files(self) -> int:
        """
        Get total size of all files in current dir and all subdirectories.

        :return:    total size of all files
        """
        files_size = sum(_.size for _ in self.sub_nodes_generator(recursive=True, type_constraint=File))
        symlinks_size = sum(_.size for _ in self.sub_nodes_generator(recursive=True, type_constraint=SymLink))
        return int(files_size) + int(symlinks_size)

    def sub_directories_files_size(self) -> int:
        """
        Get total size of all files in all subdirectories.

        :return:    total size of sub-dirs files
        """
        return self.total_size_all_files() - self.total_file_size_in_dir()

    def total_sub_dirs_count(self) -> int:
        """
        Get num of dirs in the current dir and all subdirectories.

        :return:    count of dirs
        """
        return sum(1 for _ in self.sub_nodes_generator(recursive=True, type_constraint=Directory))

    def sub_dirs_count(self) -> int:
        """
        Get num of subdirectories in current directory.

        :return:    count of dirs
        """
        return self.get_nodes_count(type_constraint=Directory)

    def get_all_dirs(self) -> list[Directory]:
        """
        Get all directories objects in the current dir.

        :return:    list of directories objects
        """
        return list(self.sub_nodes_generator(recursive=True, type_constraint=Directory))

    def total_hard_links_count(self) -> int:
        """
        Get num of hard links in the current dir and all subdirectories.

        :return:    count of hard links
        """
        return self.get_all_nodes_count(type_constraint=HardLink)

    def total_symlinks_count(self) -> int:
        """
        Get num of symlinks in the current dir and all subdirectories.

        :return:    count of symlinks
        """
        return self.get_all_nodes_count(type_constraint=SymLink)

    def current_dir_hard_links_count(self) -> int:
        """
        Get num of hard links in the current dir.

        :return:    count of hard links
        """
        return self.get_nodes_count(type_constraint=HardLink)

    def current_dir_symlinks_count(self) -> int:
        """
        Get num of symlinks in the current dir.

        :return:    count of symlinks
        """
        return self.get_nodes_count(type_constraint=SymLink)

    def sub_dirs_hard_links_count(self) -> int:
        """
        Get num of hard links in the subdirectories.

        :return:    count of hard links
        """
        return self.total_hard_links_count() - self.current_dir_hard_links_count()

    def sub_dirs_symlinks_count(self) -> int:
        """
        Get num of symlinks in the subdirectories.

        :return:    count of symlinks
        """
        return self.total_symlinks_count() - self.current_dir_symlinks_count()

    def metrics_by_owners(self) -> dict:
        """
        Metrics in current dir for all possible owners.

        :return:   dict with metrics for each owner
        """
        sub_dirs = []
        metrics = {}
        own_metrics = {
            'own_files_size': 0,
            'sub_files_size': 0,
            'own_files_count': 0,
            'sub_files_count': 0,
            'own_dirs_count': 0,
            'sub_dirs_count': 0,
        }

        def get_sub_dirs(current_dir: Directory) -> None:
            """
            Recursive function to get all subdirectories.

            :param current_dir:   working directory
            """
            sub_dirs.append(current_dir)
            for sub_directory in current_dir.sub_nodes_generator(recursive=False, type_constraint=Directory):
                get_sub_dirs(sub_directory)

        for sub_dir in self.sub_nodes_generator(recursive=False, type_constraint=Directory):
            get_sub_dirs(sub_dir)

        for owner in self.possible_owners:
            metrics.update({owner: copy.deepcopy(own_metrics)})

        for file in [*self.files(), *self.symlinks()]:
            metrics[file.owner]['own_files_size'] += int(file.size)
            metrics[file.owner]['sub_files_size'] += int(file.size)
            metrics[file.owner]['own_files_count'] += 1
            metrics[file.owner]['sub_files_count'] += 1
        for directory in self.sub_nodes_generator(recursive=False, type_constraint=Directory):
            metrics[directory.owner]['own_dirs_count'] += 1

        for sub_dir in sub_dirs:
            metrics[sub_dir.owner]['sub_dirs_count'] += 1
            for file in [*sub_dir.files(), *sub_dir.symlinks()]:
                metrics[file.owner]['sub_files_size'] += int(file.size)
                metrics[file.owner]['sub_files_count'] += 1

        return metrics

    def total_entries(self) -> int:
        """
        Get total num of entries in the current dir and all subdirectories.

        :return:    count of entries
        """
        return sum(1 for _ in self.sub_nodes_generator(recursive=True, type_constraint=None))

    def get_sub_dirs_with_empty_sub_dirs(self) -> list[Directory]:
        """Get all subdirectories with empty sub_dirs."""
        nodes = []
        for node in self.sub_nodes_generator(recursive=True, type_constraint=Directory):
            if not node.sub_dirs:
                nodes.append(node)
        return nodes
