#!/usr/local/bin/python3
# pylint: disable=function-redefined
# pylint: disable=inconsistent-return-statements
"""This module contains File, Dir, TreeGenerator classes."""
import argparse
import copy
import datetime
import json
import string
import sys
from concurrent.futures import ThreadPoolExecutor
from os import chdir, chown, getlogin, link, mkdir, path, stat, symlink, utime
from pwd import getpwnam
from random import choice, randint, sample, seed
from shutil import rmtree
from threading import Lock
from time import mktime, time
from typing import Dict, List, Tuple, Union

from tree_generator.utils.reporter import JsonTreeReporter


# Workaround for python 3.6 without using requirements.txt
try:
    from dataclasses import asdict, dataclass
except ImportError:
    from pip._internal.cli.main import main

    main(['install', 'dataclasses'])
    from dataclasses import asdict, dataclass

START_PATH = path.dirname(__file__)
lock = Lock()
JP_LETTERS = '世界中に存在するウェブサイトのうち'
CYR_LETTERS = 'ЎBKEПPнroлшдў'
LETTERS = string.ascii_letters + string.digits + JP_LETTERS + CYR_LETTERS

TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
HOURS_DELTA = (1, 23)
MINS_DELTA = (1, 60)
DAYS_DELTA = (0, 1825)  # 5 years

SIZE_SMALL = 1024 * 100
SIZE_MEDIUM = SIZE_SMALL * 1024
SIZE_LARGE = SIZE_MEDIUM * 1024

AUDIO_EXTENSIONS = ('aac', 'mp3', 'oga', 'wav')
VIDEO_EXTENSIONS = ('avi', 'mpeg', '3gp', 'webm')
DOCS_EXTENSIONS = ('doc', 'docx', 'txt', 'pdf', 'rtf', 'ppt')
PICTURES_EXTENSIONS = ('bmp', 'gif', 'jpeg', 'png', 'tif')
APPS_EXTENSIONS = ('exe', 'bat', 'sh')
SCRIPTS_EXTENSIONS = ('py', 'js', 'php', 'tcl')
SRC_EXTENSIONS = ('c', 'h', 'cpp')
BAD_EXTENSIONS = ('', 'a5t3', 'ss', '000', 'Pнr', '世界中')
CURRENT_TIME = datetime.datetime.now()
DEBUG_FLAG = False
NAME_LENGTH = 4

OWNERS_IDS = {'nmolchanov': {'uid': 33343, 'gid': 12650}, 'ademura': {'uid': 33342, 'gid': 12650}}


def _get_user_ids(username) -> tuple:
    """
    Get user UID and GID.

    :param username:    user name
    :return:            own_uid, own_gid
    """
    if username in OWNERS_IDS:
        own_uid = OWNERS_IDS[username]['uid']
        own_gid = OWNERS_IDS[username]['gid']
    else:
        own_uid = getpwnam(username).pw_uid
        own_gid = getpwnam(username).pw_gid
    return own_uid, own_gid


@dataclass
class File:
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
        Get full path of a file.

        :return:    full path of file
        """
        return path.join(self.dest, self.name)


@dataclass
class HardLink:
    """Class represents hard link entity."""

    dest: str
    name: str
    file_obj: File
    owner: str

    @property
    def full_path(self) -> str:
        """
        Get full path of a hard link.

        :return:    full path of hard link
        """
        return path.join(self.dest, self.name)


@dataclass
class SymLink:
    """Class represents symlink entity."""

    dest: str
    name: str
    file_obj: Union['File', 'Dir']
    owner: str
    size: int
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
class Dir:
    """Class represents dir entity."""

    dest: str
    name: str
    owner: str
    possible_owners: list[str]
    sub_dirs: list['Dir']
    files: list['File']
    hard_links: list['HardLink']
    symlinks: list['SymLink']
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
        sub_dirs: list['Dir'] = None,
        files: list['File'] = None,
        hard_links: list['HardLink'] = None,
        symlinks: list['SymLink'] = None,
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

        def get_sub_dirs(directory: 'Dir'):
            """
            Recursive function to count files in subdirectories.

            :param directory:   working directory
            """
            for dr in directory.sub_dirs:
                get_sub_dirs(dr)
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

    def get_all_files(self) -> list['File']:
        """
        Get files objects in the current dir and all subdirectories.

        :return:    list of file objects
        """
        fls = []

        def get_sub_dirs(directory: 'Dir'):
            """
            Recursive function to get files in subdirectories.

            :param directory:   working directory
            """
            for dr in directory.sub_dirs:
                get_sub_dirs(dr)
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

        def get_sub_dirs(directory: 'Dir'):
            """
            Recursive function to get file sizes in subdirectories.

            :param directory:   working directory
            """
            for dr in directory.sub_dirs:
                get_sub_dirs(dr)
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

        def get_sub_dirs(directory: 'Dir'):
            """
            Recursive function to get file sizes in subdirectories.

            :param directory:   working directory
            """
            for dr in directory.sub_dirs:
                get_sub_dirs(dr)
                file_sizes.append(dr.total_file_size_in_dir)

        get_sub_dirs(self)
        return sum(file_sizes)

    @property
    def total_sub_dirs_count(self) -> int:
        """
        Get num of dirs in the current dir and all subdirectories.

        :return:    count of dirs
        """
        drs_count = []

        def get_sub_dirs(directory: 'Dir'):
            """
            Recursive function to count subdirectories.

            :param directory:   working directory
            """
            drs_count.append(directory.name)
            for dr in directory.sub_dirs:
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

    def get_all_dirs(self) -> list['Dir']:
        """
        Get all directories objects in the current dir.

        :return:    list of directories objects
        """
        drs = []

        def get_sub_dirs(directory: 'Dir'):
            """
            Recursive function to get subdirectories.

            :param directory:   working directory
            """
            drs.append(directory)
            for dr in directory.sub_dirs:
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

        def get_sub_dirs(directory: 'Dir'):
            """
            Recursive function to count hard links in subdirectories.

            :param directory:   working directory
            """
            for dr in directory.sub_dirs:
                get_sub_dirs(dr)
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

        def get_sub_dirs(directory: 'Dir'):
            """
            Recursive function to count hard links in subdirectories.

            :param directory:   working directory
            """
            for dr in directory.sub_dirs:
                get_sub_dirs(dr)
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

        def get_sub_dirs(current_dir: 'Dir'):
            """
            Recursive function to get all subdirectories.

            :param current_dir:   working directory
            """
            sub_dirs.append(current_dir)
            for dr in current_dir.sub_dirs:
                get_sub_dirs(dr)

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
    def total_entries(self):
        """
        Get total num of entries in the current dir and all subdirectories.

        :return:    count of entries
        """
        return self.total_files_count + self.total_hard_links_count + self.total_sub_dirs_count


class TreeGenerator:
    """Tree generator class."""

    def __init__(
        self,
        name: str,
        dest: str,
        tree_depth: int,
        owners: list[str],
        file_sizes: list[str],
        dirs_count: int = None,
        min_dirs_count: int = None,
        max_dirs_count: int = None,
        files_count: int = None,
        min_files_count: int = None,
        max_files_count: int = None,
        hard_links_count: int = None,
        symlinks_count: int = None,
        random: bool = False,
        report_path: str = None,
    ) -> None:
        """
        Initialize tree generator attributes.

        :param dest:                full path to destination start tree folder
        :param name:                name for root tree folder
        :param tree_depth:          depth of test tree
        :param dirs_count:          count of dirs in test tree
        :param min_dirs_count:      min count of dirs in test tree
        :param max_dirs_count:      max count of dirs in test tree
        :param files_count:         count of files in test tree
        :param min_files_count:     min count of files in test tree
        :param max_files_count:     max count of files in test tree
        :param hard_links_count:    count of hard links in test tree
        :param symlinks_count:      count of symlinks in test tree
        :param owners:              someone of the users: root etc.
        :param report_path:         path for create report
        :param file_sizes:          someone of the large, medium, small
        :param random:              if true randint will be used to determine
                                    the count of files and directories:
                                    min_dirs_count/max_dirs_count and
                                    min_files_count/max_files_count
        """
        self.dest = dest
        self.name = name
        self.tree_depth = tree_depth
        self.dirs_count = dirs_count
        self.min_dirs_count = min_dirs_count
        self.max_dirs_count = max_dirs_count
        self.files_count = files_count
        self.min_files_count = min_files_count
        self.max_files_count = max_files_count
        self.file_sizes = file_sizes
        self.hard_links_count = hard_links_count
        self.symlinks_count = symlinks_count
        self.report_path = report_path
        self.owners = owners
        self.random = random

    @property
    def get_full_path(self) -> str:
        """
        Get full dir path.

        :return:    full path
        """
        return path.join(self.dest, self.name)

    @property
    def full_report_path(self):
        """Full path to tree report."""
        return f'{path.join(self.report_path, self.name)}_report.json'

    @staticmethod
    def _name_generator(length: int = NAME_LENGTH) -> str:
        """
        Name generator.

        :param length:  length of the generated name Python can't store names larger than 4
                        characters when tree depth is greater than 25 directories
        :return:        name
        """
        return ''.join(choice(LETTERS) for _ in range(length))

    @staticmethod
    def get_random_timestamp() -> datetime:
        """
        Get random timestamp.

        Get a random timestamp for the access time change and last modified
        time of a file from a year and a half to the current moment

        :return:    datetime stamp
        """
        time_stamp = CURRENT_TIME - datetime.timedelta(
            minutes=randint(*MINS_DELTA), hours=randint(*HOURS_DELTA), days=randint(*DAYS_DELTA)
        )
        return time_stamp

    @staticmethod
    def make_hard_link(src: str, dst: str):
        """
        Make hard link.

        :param src:    source file path
        :param dst:    destination file path
        """
        link(src, dst)
        if DEBUG_FLAG:
            print(f'Has been created hard link: {dst}')

    @staticmethod
    def make_symlink(src: str, sym_link: SymLink, owner, atime: datetime, mtime: datetime):
        """
        Make symlink.

        :param owner:       symlink owner
        :param src:         source file path
        :param sym_link:    SymLink object
        :param atime:       timestamp to modify file access timestamp
        :param mtime:       timestamp to modify file modified timestamp
        """
        target_is_dir = False
        if isinstance(sym_link.file_obj, Dir):
            target_is_dir = True
            sym_link.file_obj = {
                'name': sym_link.file_obj.name,
                'dest': sym_link.file_obj.dest,
                'owner': sym_link.file_obj.owner,
            }
        dst = sym_link.full_path
        symlink(src, dst, target_is_directory=target_is_dir)
        # Workaround the size of the symlink needs to be increased by 2 bytes,
        # a feature of FS
        sym_link.size = stat(dst, follow_symlinks=False).st_size + 2
        atime = int(mktime(atime.timetuple()))
        mtime = int(mktime(mtime.timetuple()))
        utime(dst, (atime, mtime), follow_symlinks=False)
        own_uid, own_gid = _get_user_ids(owner)
        chown(dst, own_uid, own_gid, follow_symlinks=False)
        sym_link.owner = owner
        if DEBUG_FLAG:
            print(f'Has been created symlink: {dst}, owner {owner}')

    def _gen_level_params(self) -> dict[str, int | str]:
        """
        Parameters of the generated directory.

        :return:    dict with parameters for dir generating
        """
        params = {
            'dirs_count': self.dirs_count,
            'files_count': self.files_count,
            'owners': sample(self.owners, randint(1, len(self.owners))),
        }
        if self.random:
            params['dirs_count'] = randint(self.min_dirs_count, self.max_dirs_count)
            params['files_count'] = randint(self.min_files_count, self.max_files_count)
        return params

    def _gen_file_params(self) -> dict[str, int | str]:
        """
        Parameters of the generated file.

        :return:    dict with parameters for file generating
        """
        file_params = {
            'size': {'large': SIZE_LARGE, 'medium': SIZE_MEDIUM, 'small': SIZE_SMALL},
            'type': {
                'audio': AUDIO_EXTENSIONS,
                'video': VIDEO_EXTENSIONS,
                'txt': DOCS_EXTENSIONS,
                'img': PICTURES_EXTENSIONS,
                'app': APPS_EXTENSIONS,
                'script': SCRIPTS_EXTENSIONS,
                'src': SRC_EXTENSIONS,
                'bad': BAD_EXTENSIONS,
            },
        }

        file_type = choice(list(file_params['type'].keys()))
        file_ext = choice(file_params['type'][file_type])

        size = choice(self.file_sizes)
        size = file_params['size'][size]
        final_size = randint(int(size * 0.7), int(size * 1.3))

        return {'final_size': final_size, 'file_type': file_ext}

    @staticmethod
    def make_json_report(dir_obj: Dir, report_path: str = None):
        """
        Make JSON report about the tree.

        :param dir_obj:        directory object
        :param report_path:    path for create report
        """
        full_rep_path = f'{path.join(report_path, dir_obj.name)}_report.json'
        with open(full_rep_path, 'w', encoding='utf-8') as fl:
            json.dump(asdict(dir_obj), fl, indent=4, ensure_ascii=False)
            print(f'Report on the generated file tree: {full_rep_path}')

    def generate_tree(self) -> Dir:
        """
        Generate files tree.

        :return:    directory object that contains full tree which was created
        """
        start_params = self._gen_level_params()
        start_dir_owner = choice(start_params['owners'])
        dirs_count = start_params['dirs_count']
        files_count = start_params['files_count']

        def create_file(full_path: str, file_size: int, atime: datetime, mtime: datetime, owner: str):
            """
            Create file.

            :param full_path:    path to file
            :param file_size:    size of file
            :param atime:        timestamp to modify file access timestamp
            :param mtime:        timestamp to modify file modified timestamp
            :param owner:        owner name
            """
            _full_path = full_path
            list_of_dirs = []
            try:
                with lock:
                    if len(full_path.split('/')) > 100:
                        dirs_list = full_path.split('/')
                        dirs_list[0] = '/'

                        while len(dirs_list) > 50:
                            list_of_dirs.append(path.join(*dirs_list[:50]))
                            dirs_list = dirs_list[50:]
                        full_path = path.join(*dirs_list)

                        for path_name in list_of_dirs:
                            chdir(path_name)

                    with open(full_path, 'wb') as file:
                        file.seek(file_size - 1)
                        file.write(b'0')
                    atime = int(mktime(atime.timetuple()))
                    mtime = int(mktime(mtime.timetuple()))
                    utime(full_path, (atime, mtime))
                    own_uid, own_gid = _get_user_ids(owner)
                    chown(full_path, own_uid, own_gid)
                    if DEBUG_FLAG:
                        print(f'Has been created file: {_full_path}')
                        _full_path.strip()
                    chdir(START_PATH)
            except (PermissionError, ValueError, LookupError) as err:
                raise SystemExit(f'\nUser {owner} was selected to create the file\n{err}')
            except KeyboardInterrupt:
                raise KeyboardInterrupt('KeyboardInterrupt')

        def create_dir(dir_path: str, owner: str):
            """
            Create dir.

            :param dir_path:    path of directory
            :param owner:       directory owner
            """
            _dir_path = dir_path
            list_of_dirs = []
            if len(dir_path.split('/')) > 100:
                dirs_list = dir_path.split('/')
                dirs_list[0] = '/'

                while len(dirs_list) > 50:
                    list_of_dirs.append(path.join(*dirs_list[:50]))
                    dirs_list = dirs_list[50:]
                dir_path = path.join(*dirs_list)

                for path_name in list_of_dirs:
                    chdir(path_name)
            mkdir(dir_path)
            own_uid, own_gid = _get_user_ids(owner)
            chown(dir_path, own_uid, own_gid)
            chdir(START_PATH)
            if DEBUG_FLAG:
                print(f'Has been created directory: {_dir_path}')

        def create_files_at_level(current_dir: Dir, fls_count: int, executor: ThreadPoolExecutor):
            """
            Create files in the current directory.

            :param current_dir:    current working directory
            :param fls_count:      number of files to create
            :param executor:       ThreadPoolExecutor for files creating
            """
            if fls_count != 0:
                params_for_creating_files = []

                for _ in range(fls_count):
                    file_params = self._gen_file_params()
                    file_owner = choice(self._gen_level_params()['owners'])

                    file_name = self._name_generator(NAME_LENGTH)
                    file_name = f'F{file_name}.{file_params["file_type"]}'
                    while file_name in [fl.name for fl in current_dir.files]:
                        file_params = self._gen_file_params()
                        file_name = self._name_generator(NAME_LENGTH)
                        file_name = f'F{file_name}.{file_params["file_type"]}'

                    file_size = file_params['final_size']
                    atime = self.get_random_timestamp()
                    mtime = self.get_random_timestamp()
                    new_file = File(
                        current_dir.full_path,
                        file_name,
                        file_size,
                        file_owner,
                        atime.strftime(TIME_FORMAT),
                        mtime.strftime(TIME_FORMAT),
                    )
                    current_dir.files.append(new_file)
                    params_for_creating_files.append((new_file.full_path, file_size, atime, mtime, new_file.owner))
                # Workaround for ThreadPoolExecutor exception handling
                for _ in executor.map(lambda params: create_file(*params), params_for_creating_files):
                    pass

        def create_dirs_at_level(current_dir: Dir, drs_count: int, executor: ThreadPoolExecutor):
            """
            Create dirs in the current directory.

            :param current_dir:    current working directory
            :param drs_count:      number of directories to create
            :param executor:       ThreadPoolExecutor for dirs creating
            """
            params_for_creating_dirs = []
            for _ in range(drs_count):
                level_parameters = self._gen_level_params()
                dir_owner = choice(level_parameters['owners'])

                dir_name = f'D{self._name_generator(NAME_LENGTH)}'
                while dir_name in [dr.name for dr in current_dir.sub_dirs]:
                    dir_name = self._name_generator(NAME_LENGTH)
                sub_directory = Dir(current_dir.full_path, dir_name, dir_owner, self.owners, [], [], [], [])
                params_for_creating_dirs.append((sub_directory.full_path, sub_directory.owner))

                current_dir.sub_dirs.append(sub_directory)
            # Workaround for ThreadPoolExecutor exception handling
            for _ in executor.map(lambda params: create_dir(*params), params_for_creating_dirs):
                pass

        def create_level(current_dir: Dir, count_of_dirs: int, count_of_files: int, tread_exec: ThreadPoolExecutor):
            """
            Create files and dirs in the current directory.

            :param current_dir:        current working directory
            :param count_of_dirs:      number of directories to create
            :param count_of_files:     number of files to create
            :param tread_exec:         ThreadPoolExecutor for dirs creating
            """
            create_dirs_at_level(current_dir, count_of_dirs, tread_exec)
            create_files_at_level(current_dir, count_of_files, tread_exec)

        def create_hard_links_in_tree(root_directory: Dir, count: int, executor: ThreadPoolExecutor):
            """
            Create hard links in a file tree.

            :param root_directory:    root Dir object
            :param count:             count of hard links for making
            :param executor:          ThreadPoolExecutor for hardlinks creating
            """
            all_drs_in_tree = root_directory.get_all_dirs()
            all_drs_in_tree.append(root_directory)
            all_files_in_tree = root_directory.get_all_files()
            params_for_creating_links = []

            if count:
                for num in range(count):
                    target_dir = choice(all_drs_in_tree)
                    target_file = choice(all_files_in_tree)

                    hard_link = HardLink(
                        name=f'HL{num}_{target_file.name}',
                        file_obj=target_file,
                        owner=target_file.owner,
                        dest=target_dir.full_path,
                    )
                    target_dir.hard_links.append(hard_link)
                    params_for_creating_links.append((target_file.full_path, hard_link.full_path))

                for _ in executor.map(lambda params: self.make_hard_link(*params), params_for_creating_links):
                    pass

        def create_symlinks_in_tree(root_directory: Dir, count: int, executor: ThreadPoolExecutor):
            """
            Create symlinks in a file tree.

            :param root_directory:    root Dir object
            :param count:             count of hard links for making
            :param executor:          ThreadPoolExecutor for symlinks creating
            """
            all_drs_in_tree = root_directory.get_all_dirs()
            all_drs_in_tree.append(root_directory)
            all_files_in_tree = root_directory.get_all_files()
            params_for_creating_links = []

            if count:
                for num in range(count):
                    target_dir = choice(all_drs_in_tree)
                    target_file = choice([*all_drs_in_tree, *all_files_in_tree])

                    atime = self.get_random_timestamp()
                    mtime = self.get_random_timestamp()
                    sym_link = SymLink(
                        name=f'SL{num}_{target_file.name}',
                        file_obj=target_file,
                        owner='',
                        dest=target_dir.full_path,
                        size=0,
                        atime=atime.strftime(TIME_FORMAT),
                        mtime=mtime.strftime(TIME_FORMAT),
                    )
                    target_dir.symlinks.append(sym_link)
                    owner = choice(self._gen_level_params()['owners'])
                    params_for_creating_links.append((target_file.full_path, sym_link, owner, atime, mtime))

                for _ in executor.map(lambda params: self.make_symlink(*params), params_for_creating_links):
                    pass

        try:
            with ThreadPoolExecutor(max_workers=10) as tread_executor:
                root_dir = Dir(self.dest, self.name, start_dir_owner, self.owners, [], [], [], [])
                if not path.exists(root_dir.full_path):
                    create_dir(root_dir.full_path, start_dir_owner)

                create_level(root_dir, dirs_count, files_count, tread_executor)
                current_dirs_level = root_dir.sub_dirs

                for _ in range(self.tree_depth - 1):
                    next_dirs_level = []

                    for sub_dir in current_dirs_level:
                        level_params = self._gen_level_params()
                        dirs_to_create_count = level_params['dirs_count']
                        files_to_create_count = level_params['files_count']

                        create_level(sub_dir, dirs_to_create_count, files_to_create_count, tread_executor)
                        for dr in sub_dir.sub_dirs:
                            next_dirs_level.append(dr)

                    current_dirs_level = next_dirs_level.copy()

                for sub_dr in current_dirs_level:
                    level_params = self._gen_level_params()
                    files_to_create_count = level_params['files_count']
                    create_files_at_level(sub_dr, files_to_create_count, tread_executor)

                create_hard_links_in_tree(root_dir, self.hard_links_count, tread_executor)
                create_symlinks_in_tree(root_dir, self.symlinks_count, tread_executor)
                JsonTreeReporter(self.report_path, f'{self.name}_report.json', root_dir).save_report()
                self.make_json_report(root_dir, self.report_path)
                return root_dir

        except (SystemExit, InterruptedError, FileNotFoundError, KeyboardInterrupt) as error:
            sys_exit(str(error))


if __name__ == '__main__':
    description = (
        'This script is designed to generate a directory tree and'
        ' files of different sizes, you can set the depth of the '
        'file tree, the number of files in each directory, and the'
        ' number of directories at each level of the tree.\n\n'
        'There are 2 ways to generate a tree:\n'
        ' 1: Strictly set the number of directories and files at '
        'each level of the tree.\n    --dest /home/ '
        '--tree_name Test_tree --tree_depth 3 --dirs_count 1 '
        '--files_count 1000 --hard_links_count 100 '
        '--owners root admin --file_sizes large medium small\n'
        ' 2: Use the --random key and set the range of the number'
        ' of directories and files per tree level.\n    '
        '--dest /home/ --tree_name Test_tree --tree_depth 3 '
        '--min_dirs_count 1 --max_dirs_count 1 '
        '--min_files_count 999 --max_files_count 1000 '
        '--hard_links_count 100 --random --owners root admin '
        '--file_sizes large medium small\n'
        ' Optional: If you want to reproduce a previously created '
        'file tree, use the --default_time and --seed keys and '
        'values specified in the tree report\n'
        '\nAttention!\n With a tree depth of more than 50 levels, '
        'creation of symlinks and hard links is impossible, because'
        ' python is not able to store full paths that take more '
        'than 256 bytes. Parameters hard_links_count and '
        'sym_links_count must be set to 0'
    )
    parser = argparse.ArgumentParser(
        add_help=False,
        description=description,
        usage='use "./%(prog)s --help" for more information',
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument('--dest', default='', help='root dir for tree creation')
    parser.add_argument('--tree_depth', default=1, type=int, help='depth of tree')
    parser.add_argument('--dirs_count', default=1, type=int, help='count of directories on the level')
    parser.add_argument('--files_count', default=1, type=int, help='count of files on the level')
    parser.add_argument('--hard_links_count', default=0, type=int, help='count of hard links in the file tree')
    parser.add_argument('--sym_links_count', default=0, type=int, help='count of symlinks in the file tree')
    parser.add_argument(
        '--min_dirs_count',
        default=None,
        type=int,
        help='minimum directories count in directory, ' 'value must not be less than 1',
    )
    parser.add_argument('--max_dirs_count', default=None, type=int, help='maximum directories count in directory')
    parser.add_argument('--min_files_count', default=None, type=int, help='minimum files count in directory')
    parser.add_argument('--max_files_count', default=None, type=int, help='maximum files count in directory')
    parser.add_argument('--owners', nargs='*', default='root admin', help='list of owners\n--owners root admin')
    parser.add_argument(
        '--file_sizes',
        nargs='*',
        default='large medium small',
        help='list of file sizes\n --file_sizes large medium small',
    )
    parser.add_argument('--tree_name', default='Test_tree', help='root dir name')
    parser.add_argument('--report_path', help='report path, will use --dest value by default')
    parser.add_argument(
        '--default_time',
        type=int,
        default=None,
        help='initial timestamp for setting the time period '
        'within 5 years from which the dates of '
        'creation and modification of files, '
        'for example: 1662707899\n do not set a value '
        'less than 157766400 (1.1.1975)',
    )
    parser.add_argument(
        '--random',
        action='store_true',
        help='if --random is called, then min_dirs_count/'
        'max_dirs_count and min_files_count/'
        'max_files_count values will be used to '
        'determine the count of files and directories',
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=None,
        help='if --random is called, you may use --seed '
        'to allow to repeat the same random actions or '
        'the value will be set randomly',
    )
    parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS, help='show usage message')
    parser.add_argument('-v', '--verbose', action='store_true', help='enable debug output')
    args = parser.parse_args()

    def sys_exit(err_msg: str):
        """
        Stop process with error message.

        :param err_msg:   error message
        """
        print(err_msg)
        if path.exists(path.join(args.dest, args.tree_name)):
            rmtree(path.join(args.dest, args.tree_name))
            print(f'\n{path.join(args.dest, args.tree_name)} has been removed.')
        sys.exit()

    def validate_args(arguments):
        """
        Check arguments to generate file tree.

        :param arguments:   arguments from parser.parse_args
        """
        if arguments.tree_depth < 1:
            sys_exit(f'Warning! The tree_depth must be greater than 0\n' f'Has been set:\n{arguments.tree_depth}')

        if not arguments.owners:
            sys_exit(f'Owners have not been set, you can use the current user: {getlogin()}')
        if not arguments.report_path:
            arguments.report_path = arguments.dest

        if arguments.random:
            necessary_args = [
                arguments.min_dirs_count,
                arguments.max_dirs_count,
                arguments.min_files_count,
                arguments.max_files_count,
            ]
            if None in necessary_args:
                sys_exit(
                    f'The process has been stopped!\n'
                    f'With the argument --random, the values for the '
                    f'following keys must be set:\n(dest, name, '
                    f'tree_depth, owners, file_sizes, min_dirs_count, '
                    f'max_dirs_count, min_files_count, max_files_count)'
                    f'\nHave been set: {arguments}'
                )

            if arguments.max_files_count < arguments.min_files_count:
                sys_exit(
                    f'Warning! The min_files_count must not be greater '
                    f'than max_files_count\nHave been set:\n{arguments}'
                )

            if arguments.max_dirs_count < arguments.min_dirs_count:
                sys_exit(
                    f'Warning! The min_dirs_count must not be greater '
                    f'than max_dirs_count\nHave been set:\n{arguments}'
                )
            if arguments.seed is not None and arguments.seed < 1:
                sys_exit('Warning --seed must be more than 0')
        else:
            if arguments.dirs_count < 1:
                sys_exit(f'Warning! The dirs_count must be greater than 0\n' f'Has been set:\n{arguments.dirs_count}')

        if arguments.tree_depth > 150:
            sys.setrecursionlimit(arguments.tree_depth * 5)
        if arguments.tree_name.startswith('/'):
            arguments.tree_name = arguments.tree_name.lstrip('/')
            print(f'Warning: The value of the "tree_name" parameter has been ' f'changed to {arguments.tree_name}')

    def add_input_args_to_report(report_path: str, arguments: str, default_time: int, seed_value: int):
        """
        Save the passed parameters to tree json report.

        :param report_path:    json tree report path
        :param arguments:      passed parameters
        :param default_time:   timestamp to tree reproduce
        :param seed_value:     random seed value to tree reproduce
        """
        with open(report_path, encoding='utf-8') as json_file:
            tree_struct = json.load(json_file)

        final_tree = {
            'command_line': arguments,
            'default_time': default_time,
            'seed': seed_value,
            'tree_structure': tree_struct,
        }

        with open(report_path, 'w', encoding='utf-8') as json_file:
            json.dump(final_tree, json_file, indent=4, ensure_ascii=False)

    def get_tree_dirs_count(tree_depth, dirs_count) -> int:
        """
        Get the number of directories to be created.

        :param tree_depth:      tree depth
        :param dirs_count:      dirs in level
        :return:                directories count
        """
        if dirs_count > 1:
            res = int(((dirs_count ** (tree_depth + 1)) - 1) / (dirs_count - 1))
        else:
            res = dirs_count * (tree_depth + 1)
        return res

    validate_args(args)

    CURRENT_TIME = datetime.datetime.fromtimestamp(args.default_time) if args.default_time is not None else CURRENT_TIME
    args.default_time = int(CURRENT_TIME.timestamp()) if args.default_time is None else args.default_time

    command_line_args = ' '.join(sys.argv[1:])
    seed_val = int(time()) if args.seed is None else int(args.seed)
    seed(seed_val, version=1)
    # NAME_LENGTH = 2 if args.tree_depth >= 50 else NAME_LENGTH

    if args.verbose:
        DEBUG_FLAG = True

    if args.random:
        start = time()
        tree = TreeGenerator(
            dest=args.dest,
            name=args.tree_name,
            tree_depth=args.tree_depth,
            dirs_count=args.dirs_count,
            files_count=args.files_count,
            min_dirs_count=args.min_dirs_count,
            max_dirs_count=args.max_dirs_count,
            min_files_count=args.min_files_count,
            max_files_count=args.max_files_count,
            hard_links_count=args.hard_links_count,
            symlinks_count=args.sym_links_count,
            owners=args.owners,
            file_sizes=args.file_sizes,
            report_path=args.report_path,
            random=True,
        )
        res_dir = tree.generate_tree()
        thlc = res_dir.total_hard_links_count
        tfc = res_dir.total_files_count
        tsc = res_dir.total_symlinks_count
        end = time()
        print(
            f'It took {round(end - start, 0)} sec to make content in '
            f'{res_dir.name} with the following parameters:\ntree_depth='
            f'{args.tree_depth}\nrandom seed={seed_val}\n'
            f'initial timestamp={int(CURRENT_TIME.timestamp())}\n'
            f'min_dirs_count={args.min_dirs_count}, '
            f'max_dirs_count={args.max_dirs_count}, '
            f'min_files_count={args.min_files_count}, '
            f'max_files_count={args.max_files_count}, '
            f'hard links={args.hard_links_count} '
            f'symlinks={args.sym_links_count}\n'
            f'Have been created:\nFiles(including symlinks): {tfc}\n'
            f'Dirs: {res_dir.total_sub_dirs_count + 1}\n'
            f'Hard links: {thlc}\n'
            f'Sym links: {tsc}\n'
            f'Files + Hard links + Symlinks: {(thlc + tfc)}\n'
            f'Total entries: {res_dir.total_entries + 1}\n'
            f'Total size of all files: {res_dir.total_size_all_files}'
        )
    else:
        num_of_created_dirs = get_tree_dirs_count(args.tree_depth, args.dirs_count)
        num_of_created_files = num_of_created_dirs * args.files_count + args.hard_links_count + args.sym_links_count
        print(f'\nNumber of directories to be created in the tree: {num_of_created_dirs}')
        print(f'Number of files to be created in the tree: {num_of_created_files}\n')
        start = time()
        tree = TreeGenerator(
            dest=args.dest,
            name=args.tree_name,
            tree_depth=args.tree_depth,
            dirs_count=args.dirs_count,
            files_count=args.files_count,
            hard_links_count=args.hard_links_count,
            symlinks_count=args.sym_links_count,
            owners=args.owners,
            file_sizes=args.file_sizes,
            report_path=args.report_path,
            random=False,
        )

        res_dir = tree.generate_tree()
        end = time()
        thlc = res_dir.total_hard_links_count
        tfc = res_dir.total_files_count
        tsc = res_dir.total_symlinks_count
        print(
            f'It took {round(end - start, 0)} sec to make content in '
            f'{res_dir.name} with the following parameters:\ntree_depth='
            f'{args.tree_depth}, dirs_count={args.dirs_count}, '
            f'files_count={args.files_count}, '
            f'hard links={args.hard_links_count} '
            f'symlinks={args.sym_links_count}\n'
            f'random seed={seed_val}\n'
            f'initial timestamp={int(CURRENT_TIME.timestamp())}\n\n'
            f'Have been created:\nFiles(including symlinks): {tfc}\n'
            f'Dirs: {res_dir.total_sub_dirs_count + 1}\n'
            f'Hard links: {thlc}\n'
            f'Sym links: {tsc}\n'
            f'Files + Hard links + Symlinks: {(thlc + tfc)}\n'
            f'Total entries: {res_dir.total_entries + 1}\n'
            f'Total size of all files: {res_dir.total_size_all_files}'
        )

    add_input_args_to_report(tree.full_report_path, command_line_args, args.default_time, seed_val)
