"""File contains logic of node(Directory, File, etc.) structure."""
from __future__ import annotations

import copy
from collections.abc import Iterator
from dataclasses import dataclass, field
from os import path


class ProtectedList(list):
    """Protected list class."""

    def append(self, __object: object) -> None:
        pass


@dataclass
class AbstractNode:
    """Class represents basic node entity params in unix system."""

    dest: str
    name: str
    owner: str
    _sub_nodes: list[AbstractNode] = field(default_factory=list)

    def add_node(self, node: AbstractNode) -> None:
        """
        Add AbstractNode instance.
        :param node:      AbstractNode instance.
        """
        self._sub_nodes.append(node)

    def __iter__(self) -> Iterator[AbstractNode]:
        return iter(self._sub_nodes)

    @property
    def full_path(self) -> str:
        """
        Get full path of a file.

        :return:    full path of file
        """
        return path.join(self.dest, self.name)


_EMPTY_NODES: list[AbstractNode] = ProtectedList()


@dataclass
class File(AbstractNode):
    """Class represents file entity."""

    size: int = field(kw_only=True, default=0)
    atime: str = field(kw_only=True, default='')
    mtime: str = field(kw_only=True, default='')
    _sub_nodes = _EMPTY_NODES


@dataclass
class HardLink(AbstractNode):
    """Class represents hard link entity."""

    file_obj: AbstractNode = field(kw_only=True)
    _sub_nodes = _EMPTY_NODES


@dataclass
class SymLink(AbstractNode):
    """Class represents symlink entity."""

    file_obj: AbstractNode | dict = field(kw_only=True)
    atime: str = field(kw_only=True, default='')
    mtime: str = field(kw_only=True, default='')
    size: int = field(kw_only=True, default=0)
    _sub_nodes = _EMPTY_NODES


@dataclass
class Directory(AbstractNode):
    """Class represents directory entity."""

    possible_owners: list[str] = field(kw_only=True, default_factory=list[str])
    _sub_nodes: list[AbstractNode] = field(kw_only=False, default_factory=list[AbstractNode])
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

    def __init__(
        self,
        dest: str,
        name: str,
        owner: str,
        possible_owners: list[str],
        sub_dirs: list[Directory],
        files: list[File],
        hard_links: list[HardLink],
        symlinks: list[SymLink],
    ) -> None:
        """
        Initialize Directory class attributes.

        :param dest:        full path to destination start tree folder
        :param name:        name for root tree folder
        :param sub_dirs:    list of Directory instances
        :param files:       list of File instances
        :param hard_links:  list of HardLink instances
        :param symlinks:    list of SymLink instances
        :param owner:       owner name
        """
        super().__init__(dest, name, owner)
        self.possible_owners = possible_owners
        self._sub_nodes = []
        self.sub_dirs = sub_dirs
        self.files = files
        self.hard_links = hard_links
        self.symlinks = symlinks

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
        return [_ for _ in self._sub_nodes if isinstance(_, Directory)]

    @sub_dirs.setter
    def sub_dirs(self, sub_dir: Directory) -> None:
        """Setter method to add subdirectories."""
        self.add_node(sub_dir)

    @property
    def files(self) -> list[File]:
        """Getter method by files."""
        return [_ for _ in self._sub_nodes if isinstance(_, File)]

    @files.setter
    def files(self, file: File) -> None:
        """Setter method to add files."""
        self.add_node(file)

    @property
    def symlinks(self) -> list[SymLink]:
        """Getter method by symlinks."""
        return [_ for _ in self._sub_nodes if isinstance(_, SymLink)]

    @symlinks.setter
    def symlinks(self, symlink: SymLink) -> None:
        """Setter method to add symlinks."""
        self.add_node(symlink)

    @property
    def hard_links(self) -> list[HardLink]:
        """Getter method by hard links."""
        return [_ for _ in self._sub_nodes if isinstance(_, HardLink)]

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
        fls_count = []

        def get_sub_dirs(directory: Directory) -> None:
            """
            Recursive function to count files in subdirectories.

            :param directory:   working directory
            """
            for sub_directory in directory.sub_dirs:
                get_sub_dirs(sub_directory)
            fls_count.append(directory.current_dir_files_count)

        get_sub_dirs(self)
        return sum(fls_count)

    @property
    def current_dir_files_count(self) -> int:
        """
        Get num of files in the current dir.

        :return:    count of files
        """
        return len(self.files) + len(self.symlinks)

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
        fls = []

        def get_sub_dirs(directory: Directory) -> None:
            """
            Recursive function to get files in subdirectories.

            :param directory:   working directory
            """
            for sub_directory in directory.sub_dirs:
                get_sub_dirs(sub_directory)
            for file in directory.files:
                fls.append(file)

        get_sub_dirs(self)
        return fls

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
        file_sizes = []

        def get_sub_dirs(directory: Directory) -> None:
            """
            Recursive function to get file sizes in subdirectories.

            :param directory:   working directory
            """
            for sub_directory in directory.sub_dirs:
                get_sub_dirs(sub_directory)
            for file in directory.files:
                file_sizes.append(int(file.size))
            for sym_link in directory.symlinks:
                file_sizes.append(int(sym_link.size))

        get_sub_dirs(self)
        return sum(file_sizes)

    @property
    def sub_directories_files_size(self) -> int:
        """
        Get total size of all files in all subdirectories.

        :return:    total size of sub-dirs files
        """
        file_sizes = []

        def get_sub_dirs(directory: Directory) -> None:
            """
            Recursive function to get file sizes in subdirectories.

            :param directory:   working directory
            """
            for sub_directory in directory.sub_dirs:
                get_sub_dirs(sub_directory)
                file_sizes.append(sub_directory.total_file_size_in_dir)

        get_sub_dirs(self)
        return sum(file_sizes)

    @property
    def total_sub_dirs_count(self) -> int:
        """
        Get num of dirs in the current dir and all subdirectories.

        :return:    count of dirs
        """
        drs_count = []

        def get_sub_dirs(directory: Directory) -> None:
            """
            Recursive function to count subdirectories.

            :param directory:   working directory
            """
            drs_count.append(directory.name)
            for sub_directory in directory.sub_dirs:
                get_sub_dirs(sub_directory)

        for sub_dir in self.sub_dirs:
            get_sub_dirs(sub_dir)

        return len(drs_count)

    @property
    def sub_dirs_count(self) -> int:
        """
        Get num of subdirectories in current directory.

        :return:    count of dirs
        """
        return len(self.sub_dirs)

    def get_all_dirs(self) -> list[Directory]:
        """
        Get all directories objects in the current dir.

        :return:    list of directories objects
        """
        drs = []

        def get_sub_dirs(directory: Directory) -> None:
            """
            Recursive function to get subdirectories.

            :param directory:   working directory
            """
            drs.append(directory)
            for sub_dir in directory.sub_dirs:
                get_sub_dirs(sub_dir)

        for sub_directory in self.sub_dirs:
            get_sub_dirs(sub_directory)

        return drs

    @property
    def total_hard_links_count(self) -> int:
        """
        Get num of hard links in the current dir and all subdirectories.

        :return:    count of hard links
        """
        hard_links_count = []

        def get_sub_dirs(directory: Directory) -> None:
            """
            Recursive function to count hard links in subdirectories.

            :param directory:   working directory
            """
            for sub_directory in directory.sub_dirs:
                get_sub_dirs(sub_directory)
            hard_links_count.append(len(directory.hard_links))

        get_sub_dirs(self)
        return sum(hard_links_count)

    @property
    def total_symlinks_count(self) -> int:
        """
        Get num of symlinks in the current dir and all subdirectories.

        :return:    count of symlinks
        """
        symlinks_count = []

        def get_sub_dirs(directory: Directory) -> None:
            """
            Recursive function to count hard links in subdirectories.

            :param directory:   working directory
            """
            for sub_directory in directory.sub_dirs:
                get_sub_dirs(sub_directory)
            symlinks_count.append(len(directory.symlinks))

        get_sub_dirs(self)
        return sum(symlinks_count)

    @property
    def current_dir_hard_links_count(self) -> int:
        """
        Get num of hard links in the current dir.

        :return:    count of hard links
        """
        return len(self.hard_links)

    @property
    def current_dir_symlinks_count(self) -> int:
        """
        Get num of symlinks in the current dir.

        :return:    count of symlinks
        """
        return len(self.symlinks)

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
        return self.total_files_count + self.total_hard_links_count + self.total_sub_dirs_count
