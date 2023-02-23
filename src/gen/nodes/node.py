"""File contains logic of nodes(Directory, File, etc.) structure."""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from os import path

from gen.nodes.base import AbstractLeafNode, AbstractNode


@dataclass(kw_only=True)
class File(AbstractLeafNode):
    """Class represents file entity."""

    size: int
    atime: str
    mtime: str


@dataclass(kw_only=True)
class HardLink(AbstractLeafNode):
    """Class represents hard link entity."""

    file_obj: AbstractNode = field(kw_only=True)


@dataclass(kw_only=True)
class SymLink(AbstractLeafNode):
    """Class represents symlink entity."""

    file_obj: AbstractNode | dict = field(kw_only=True)
    atime: str
    mtime: str
    size: int


@dataclass
class Directory(AbstractNode):  # pylint: disable=too-many-instance-attributes, function-redefined
    """Class represents directory entity."""

    possible_owners: list[str] = field(kw_only=True, default_factory=list[str])
    sub_dirs: list[Directory] = field(kw_only=False, default_factory=list['Directory'])
    files: list[File] = field(kw_only=False, default_factory=list[File])
    hard_links: list[HardLink] = field(kw_only=False, default_factory=list[HardLink])
    symlinks: list[SymLink] = field(kw_only=False, default_factory=list[SymLink])
    total_files_count: int = field(kw_only=False, default=0)
    current_dir_files_count: int = field(kw_only=False, default=0)
    sub_dirs_files_count: int = field(kw_only=False, default=0)
    total_sub_dirs_count: int = field(kw_only=False, default=0)
    sub_dirs_count: int = field(kw_only=False, default=0)
    total_hard_links_count: int = field(kw_only=False, default=0)
    total_symlinks_count: int = field(kw_only=False, default=0)
    current_dir_hard_links_count: int = field(kw_only=False, default=0)
    current_dir_symlinks_count: int = field(kw_only=False, default=0)
    sub_dirs_hard_links_count: int = field(kw_only=False, default=0)
    sub_dirs_symlinks_count: int = field(kw_only=False, default=0)
    total_size_all_files: int = field(kw_only=False, default=0)
    total_file_size_in_dir: int = field(kw_only=False, default=0)
    sub_directories_files_size: int = field(kw_only=False, default=0)
    total_entries: int = field(kw_only=False, default=0)
    metrics_by_owners: dict = field(kw_only=False, default_factory=dict)

    def __init__(self, dest: str, name: str, owner: str, possible_owners: list[str]) -> None:
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

    @property
    def sub_dirs(self) -> list[Directory]:
        """
        Getter method by subdirectories.

        :return: list of Directory instances
        """
        return list(self.sub_nodes_generator(type_constraint=Directory))

    @sub_dirs.setter
    def sub_dirs(self, sub_dir: Directory) -> None:
        """Setter method to add subdirectories."""
        self.add_node(sub_dir)

    @property
    def files(self) -> list[File]:
        """Getter method by files."""
        return list(self.sub_nodes_generator(type_constraint=File))

    @files.setter
    def files(self, file: File) -> None:
        """Setter method to add files."""
        self.add_node(file)

    @property
    def symlinks(self) -> list[SymLink]:
        """Getter method by symlinks."""
        return list(self.sub_nodes_generator(type_constraint=SymLink))

    @symlinks.setter
    def symlinks(self, symlink: SymLink) -> None:
        """Setter method to add symlinks."""
        self.add_node(symlink)

    @property
    def hard_links(self) -> list[HardLink]:
        """Getter method by hard links."""
        return list(self.sub_nodes_generator(type_constraint=HardLink))

    @hard_links.setter
    def hard_links(self, hard_link: HardLink) -> None:
        """Setter method to add hard links."""
        self.add_node(hard_link)

    @property
    def full_path(self) -> str:
        """
        Get full path of a directory.

        :return:    full path of directory
        """
        return path.join(self.dest, self.name)

    @property
    def total_files_count(self) -> int:
        """
        Get num of files in the current dir and all subdirectories.

        :return:    count of files
        """
        files = self.get_all_nodes_count(type_constraint=File)
        symlinks = self.get_all_nodes_count(type_constraint=SymLink)
        return files + symlinks

    @property
    def current_dir_files_count(self) -> int:
        """
        Get num of files in the current dir.

        :return:    count of files
        """
        files = self.get_nodes_count(type_constraint=File)
        symlinks = self.get_nodes_count(type_constraint=SymLink)
        return files + symlinks

    @property
    def sub_dirs_files_count(self) -> int:
        """
        Get num of files in the subdirectories.

        :return:    count of files
        """
        return self.total_files_count - self.current_dir_files_count

    def get_all_files(self) -> list[File]:
        """
        Get files objects in the current dir and all subdirectories.

        :return:    list of file objects
        """
        return list(self.sub_nodes_generator(recursive=True, type_constraint=File))

    @property
    def total_file_size_in_dir(self) -> int:
        """
        Get total size of all files in current dir.

        :return:    total size of files
        """
        files_sum = sum(file.size for file in self.files)
        sym_links_sum = sum(sym_link.size for sym_link in self.symlinks)
        return files_sum + sym_links_sum

    @property
    def total_size_all_files(self) -> int:
        """
        Get total size of all files in current dir and all subdirectories.

        :return:    total size of all files
        """
        files_size = sum(_.size for _ in self.sub_nodes_generator(recursive=True, type_constraint=File))
        symlinks_size = sum(_.size for _ in self.sub_nodes_generator(recursive=True, type_constraint=SymLink))
        return int(files_size) + int(symlinks_size)

    @property
    def sub_directories_files_size(self) -> int:
        """
        Get total size of all files in all subdirectories.

        :return:    total size of sub-dirs files
        """
        return self.total_size_all_files - self.total_file_size_in_dir

    @property
    def total_sub_dirs_count(self) -> int:
        """
        Get num of dirs in the current dir and all subdirectories.

        :return:    count of dirs
        """
        return self.get_all_nodes_count(type_constraint=Directory) - self.get_nodes_count(type_constraint=Directory)

    @property
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

    @property
    def total_hard_links_count(self) -> int:
        """
        Get num of hard links in the current dir and all subdirectories.

        :return:    count of hard links
        """
        return self.get_all_nodes_count(type_constraint=HardLink)

    @property
    def total_symlinks_count(self) -> int:
        """
        Get num of symlinks in the current dir and all subdirectories.

        :return:    count of symlinks
        """
        return self.get_all_nodes_count(type_constraint=SymLink)

    @property
    def current_dir_hard_links_count(self) -> int:
        """
        Get num of hard links in the current dir.

        :return:    count of hard links
        """
        return self.get_nodes_count(type_constraint=HardLink)

    @property
    def current_dir_symlinks_count(self) -> int:
        """
        Get num of symlinks in the current dir.

        :return:    count of symlinks
        """
        return self.get_nodes_count(type_constraint=SymLink)

    @property
    def sub_dirs_hard_links_count(self) -> int:
        """
        Get num of hard links in the subdirectories.

        :return:    count of hard links
        """
        return self.total_hard_links_count - self.current_dir_hard_links_count

    @property
    def sub_dirs_symlinks_count(self) -> int:
        """
        Get num of symlinks in the subdirectories.

        :return:    count of symlinks
        """
        return self.total_symlinks_count - self.current_dir_symlinks_count

    @property
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
            for sub_directory in current_dir.sub_dirs:
                get_sub_dirs(sub_directory)

        for sub_dir in self.sub_dirs:
            get_sub_dirs(sub_dir)

        for owner in self.possible_owners:
            metrics.update({owner: copy.deepcopy(own_metrics)})

        for file in [*self.files, *self.symlinks]:
            metrics[file.owner]['own_files_size'] += int(file.size)
            metrics[file.owner]['sub_files_size'] += int(file.size)
            metrics[file.owner]['own_files_count'] += 1
            metrics[file.owner]['sub_files_count'] += 1
        for directory in self.sub_dirs:
            metrics[directory.owner]['own_dirs_count'] += 1

        for sub_dir in sub_dirs:
            metrics[sub_dir.owner]['sub_dirs_count'] += 1
            for file in [*sub_dir.files, *sub_dir.symlinks]:
                metrics[file.owner]['sub_files_size'] += int(file.size)
                metrics[file.owner]['sub_files_count'] += 1

        return metrics

    @property
    def total_entries(self) -> int:
        """
        Get total num of entries in the current dir and all subdirectories.

        :return:    count of entries
        """
        return len(self._sub_nodes)
