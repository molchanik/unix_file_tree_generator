import abc
import copy
import ctypes
from dataclasses import dataclass
from os import path
from typing import List, Union


@dataclass
class Node(abc.ABC):
    """Class represents basic node entity params in unix system."""

    dest: str
    name: str
    owner: str


@dataclass
class File(Node):
    """Class represents file entity."""

    dest: str
    name: str
    size: int
    owner: str
    atime: str
    mtime: str

    @property
    def full_path(self) -> str:
        """
        Get full path of a symlink.

        :return:    full path of symlink
        """
        return path.join(self.dest, self.name)


@dataclass
class HardLink(Node):
    """Class represents hard link entity."""

    dest: str
    name: str
    owner: str
    file_obj: File

    @property
    def full_path(self) -> str:
        """
        Get full path of a symlink.

        :return:    full path of symlink
        """
        return path.join(self.dest, self.name)


@dataclass
class SymLink(Node):
    """Class represents symlink entity."""

    dest: str
    name: str
    owner: str
    file_obj: Union['File', 'Dir']
    atime: str
    mtime: str
    size: int

    @property
    def full_path(self) -> str:
        """
        Get full path of a symlink.

        :return:    full path of symlink
        """
        return path.join(self.dest, self.name)


@dataclass
class Dir(Node):
    """Class represents dir entity."""

    possible_owners: list[str]
    sub_dirs: list[int]
    files: list[int]
    hard_links: list[int]
    symlinks: list[int]
    total_files_count: int
    current_dir_files_count: int
    sub_dirs_files_count: int
    total_sub_dirs_count: int
    sub_dirs_count: int
    total_hard_links_count: str
    total_symlinks_count: str
    current_dir_hard_links_count: str
    current_dir_symlinks_count: str
    sub_dirs_hard_links_count: str
    sub_dirs_symlinks_count: str
    total_size_all_files: int
    total_file_size_in_dir: int
    sub_directories_files_size: int
    total_entries: str
    metrics_by_owners: dict

    def __init__(
        self,
        dest: str,
        name: str,
        owner: str,
        possible_owners: list[str],
        sub_dirs: list[int] = None,
        files: list[int] = None,
        hard_links: list[int] = None,
        symlinks: list[int] = None,
    ) -> None:
        """
        Initialize Dir class attributes.

        :param dest:        full path to destination start tree folder
        :param name:        name for root tree folder
        :param sub_dirs:    list of Dir instances
        :param files:       list of File instances
        :param hard_links:  list of HardLink instances
        :param symlinks:    list of SymLink instances
        :param owner:       owner name
        """
        self.dest = dest
        self.name = name
        self.owner = owner
        self.possible_owners = possible_owners
        self.sub_dirs = sub_dirs
        self.files = files
        self.hard_links = hard_links
        self.symlinks = symlinks

    def __str__(self):
        return (
            f'Dir dest: {self.dest}\nDir name: {self.name}\nOwner: {self.owner}\n'
            f'Sub dirs: {self.sub_dirs}\nFiles: {self.files}\nHard Links: {self.hard_links}\n'
            f'SymLinks: {self.symlinks}\n'
        )

    @property
    def full_path(self) -> str:
        """
        Get full path of a symlink.

        :return:    full path of symlink
        """
        return path.join(self.dest, self.name)

    @property
    def total_files_count(self) -> int:
        """
        Get num of files in the current dir and all subdirectories.

        :return:    count of files
        """
        fls_count = []

        def get_sub_dirs(directory_id: int):
            """
            Recursive function to count files in subdirectories.

            :param directory_id:   working directory
            """
            dir_obj = ctypes.cast(directory_id, ctypes.py_object).value
            for dr in dir_obj.sub_dirs:
                get_sub_dirs(dr)
            fls_count.append(dir_obj.current_dir_files_count)

        get_sub_dirs(id(self))
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

    def get_all_files_ids(self) -> list[int]:
        """
        Get files objects ids in the current dir and all subdirectories.

        :return:    list of file objects ids
        """
        fls = []

        def get_sub_dirs(directory_id: int):
            """
            Recursive function to get files in subdirectories.

            :param directory_id:   working directory id
            """
            dir_obj = ctypes.cast(directory_id, ctypes.py_object).value
            for dr in dir_obj.sub_dirs:
                get_sub_dirs(dr)
            for file in dir_obj.files:
                fls.append(file)

        get_sub_dirs(id(self))
        return fls

    @property
    def total_file_size_in_dir(self) -> int:
        """
        Get total size of all files in current dir.

        :return:    total size of files
        """
        files_sum = sum(ctypes.cast(file, ctypes.py_object).value.size for file in self.files)
        sym_links_sum = sum(ctypes.cast(sym_link, ctypes.py_object).value.size for sym_link in self.symlinks)
        return files_sum + sym_links_sum

    @property
    def total_size_all_files(self) -> int:
        """
        Get total size of all files in current dir and all subdirectories.

        :return:    total size of all files
        """
        file_sizes = []

        def get_sub_dirs(directory_id: int):
            """
            Recursive function to get file sizes in subdirectories.

            :param directory_id:   working directory id
            """
            dir_obj = ctypes.cast(directory_id, ctypes.py_object).value
            for dr in dir_obj.sub_dirs:
                get_sub_dirs(dr)
            for file in dir_obj.files:
                file_obj = ctypes.cast(file, ctypes.py_object).value
                file_sizes.append(int(file_obj.size))
            for sym_link in dir_obj.symlinks:
                sym_link_obj = ctypes.cast(sym_link, ctypes.py_object).value
                file_sizes.append(int(sym_link_obj.size))

        get_sub_dirs(id(self))
        return sum(file_sizes)

    @property
    def sub_directories_files_size(self) -> int:
        """
        Get total size of all files in all subdirectories.

        :return:    total size of sub-dirs files
        """
        file_sizes = []

        def get_sub_dirs(directory_id: int):
            """
            Recursive function to get file sizes in subdirectories.

            :param directory_id:   working directory id
            """
            dir_obj = ctypes.cast(directory_id, ctypes.py_object).value
            for dr in dir_obj.sub_dirs:
                get_sub_dirs(dr)
                file_sizes.append(dr.total_file_size_in_dir)

        get_sub_dirs(id(self))
        return sum(file_sizes)

    @property
    def total_sub_dirs_count(self) -> int:
        """
        Get num of dirs in the current dir and all subdirectories.

        :return:    count of dirs
        """
        drs_count = []

        def get_sub_dirs(directory_id: int):
            """
            Recursive function to count subdirectories.

            :param directory_id:   working directory id
            """
            drs_count.append(directory_id)
            dir_obj = ctypes.cast(directory_id, ctypes.py_object).value
            for dr in dir_obj.sub_dirs:
                get_sub_dirs(dr)

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

    def get_all_dirs(self) -> list[int]:
        """
        Get all directories objects in the current dir.

        :return:    list of directories objects
        """
        drs = []

        def get_sub_dirs(directory_id: int):
            """
            Recursive function to get subdirectories.

            :param directory_id:   working directory id
            """
            drs.append(directory_id)
            dir_obj = ctypes.cast(directory_id, ctypes.py_object).value
            for dr in dir_obj.sub_dirs:
                get_sub_dirs(dr)

        for sub_dir in self.sub_dirs:
            get_sub_dirs(sub_dir)

        return drs

    @property
    def total_hard_links_count(self) -> int:
        """
        Get num of hard links in the current dir and all subdirectories.

        :return:    count of hard links
        """
        hard_links_count = []

        def get_sub_dirs(directory_id: int):
            """
            Recursive function to count hard links in subdirectories.

            :param directory_id:   working directory id
            """
            dir_obj = ctypes.cast(directory_id, ctypes.py_object).value
            for dr in dir_obj.sub_dirs:
                get_sub_dirs(dr)
            hard_links_count.append(len(dir_obj.hard_links))

        get_sub_dirs(id(self))
        return sum(hard_links_count)

    @property
    def total_symlinks_count(self) -> int:
        """
        Get num of symlinks in the current dir and all subdirectories.

        :return:    count of symlinks
        """
        symlinks_count = []

        def get_sub_dirs(directory_id: int):
            """
            Recursive function to count hard links in subdirectories.

            :param directory_id:   working directory id
            """
            dir_obj = ctypes.cast(directory_id, ctypes.py_object).value
            for dr in dir_obj.sub_dirs:
                get_sub_dirs(dr)
            symlinks_count.append(len(dir_obj.symlinks))

        get_sub_dirs(id(self))
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

        def get_sub_dirs(current_dir_id: int):
            """
            Recursive function to get all subdirectories.

            :param current_dir_id:   working directory id
            """
            dir_obj = ctypes.cast(current_dir_id, ctypes.py_object).value
            sub_dirs.append(current_dir_id)
            for dr in dir_obj.sub_dirs:
                get_sub_dirs(dr)

        for sub_dir in self.sub_dirs:
            get_sub_dirs(sub_dir)

        for owner in self.possible_owners:
            metrics.update({owner: copy.deepcopy(own_metrics)})

        for file in [*self.files, *self.symlinks]:
            file_obj = ctypes.cast(file, ctypes.py_object).value
            metrics[file_obj.owner]['own_files_size'] += int(file_obj.size)
            metrics[file_obj.owner]['sub_files_size'] += int(file_obj.size)
            metrics[file_obj.owner]['own_files_count'] += 1
            metrics[file_obj.owner]['sub_files_count'] += 1
        for directory in self.sub_dirs:
            dir_obj = ctypes.cast(directory, ctypes.py_object).value
            metrics[dir_obj.owner]['own_dirs_count'] += 1

        for sub_dir in sub_dirs:
            dir_obj = ctypes.cast(sub_dir, ctypes.py_object).value
            metrics[dir_obj.owner]['sub_dirs_count'] += 1
            for file in [*dir_obj.files, *dir_obj.symlinks]:
                file_obj = ctypes.cast(file, ctypes.py_object).value
                metrics[file_obj.owner]['sub_files_size'] += int(file_obj.size)
                metrics[file_obj.owner]['sub_files_count'] += 1

        return metrics

    @property
    def total_entries(self):
        """
        Get total num of entries in the current dir and all subdirectories.

        :return:    count of entries
        """
        return self.total_files_count + self.total_hard_links_count + self.total_sub_dirs_count
