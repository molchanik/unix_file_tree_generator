import ctypes
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import datetime
from os import chdir, chown, mkdir, path, utime
from random import choice, randint, sample
from threading import Lock
from time import mktime
from typing import Dict, List

from logger_util import logger
from main_utils import sys_exit
from node import Dir, File, HardLink, SymLink
from reporter import JsonTreeReporter
from utilits import TIME_FORMAT, get_random_timestamp, get_user_ids, make_hard_link, make_symlink, name_generator


START_PATH = path.dirname(__file__)
lock = Lock()
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
NAME_LENGTH = 4


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
        default_time: int = None,
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
        :param default_time:        timestamp for generating files timestamps
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
        self.default_time = default_time
        self.NAME_LENGTH = 2 if self.tree_depth >= 50 else NAME_LENGTH

    @property
    def full_path(self) -> str:
        """
        Get full dir path.

        :return:    full path
        """
        return path.join(self.dest, self.name)

    @property
    def full_report_path(self):
        """Full path to tree report."""
        return f'{path.join(self.report_path, self.name)}_report.json'

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
                # with lock:
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
                own_uid, own_gid = get_user_ids(owner)
                chown(full_path, own_uid, own_gid)
                logger.debug('Has been created file: %s', _full_path)
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
            own_uid, own_gid = get_user_ids(owner)
            chown(dir_path, own_uid, own_gid)
            chdir(START_PATH)
            logger.debug('Has been created directory: %s', _dir_path)

        def create_files_at_level(current_dir: int, fls_count: int, executor: ThreadPoolExecutor):
            """
            Create files in the current directory.

            :param current_dir:    current working directory
            :param fls_count:      number of files to create
            :param executor:       ThreadPoolExecutor for files creating
            """
            current_dir = ctypes.cast(current_dir, ctypes.py_object).value
            if fls_count != 0:
                params_for_creating_files = []

                for _ in range(fls_count):
                    file_params = self._gen_file_params()
                    file_owner = choice(self._gen_level_params()['owners'])

                    file_name = name_generator(self.NAME_LENGTH)
                    file_name = f'F{file_name}.{file_params["file_type"]}'
                    if current_dir.files:
                        current_file_names = [ctypes.cast(fl, ctypes.py_object).value.name for fl in current_dir.files]
                        while file_name in current_file_names:
                            file_params = self._gen_file_params()
                            file_name = name_generator(self.NAME_LENGTH)
                            file_name = f'F{file_name}.{file_params["file_type"]}'

                    file_size = file_params['final_size']
                    atime = get_random_timestamp(self.default_time)
                    mtime = get_random_timestamp(self.default_time)
                    new_file = File(
                        current_dir.full_path,
                        file_name,
                        file_size,
                        file_owner,
                        atime.strftime(TIME_FORMAT),
                        mtime.strftime(TIME_FORMAT),
                    )
                    current_dir.files.append(id(new_file))
                    params_for_creating_files.append((new_file.full_path, file_size, atime, mtime, file_owner))
                # Workaround for ThreadPoolExecutor exception handling
                for _ in executor.map(lambda params: create_file(*params), params_for_creating_files):
                    pass

        def create_dirs_at_level(current_dir_id: int, drs_count: int, executor: ThreadPoolExecutor):
            """
            Create dirs in the current directory.

            :param current_dir_id:    current working directory
            :param drs_count:         number of directories to create
            :param executor:          ThreadPoolExecutor for dirs creating
            """
            params_for_creating_dirs = []
            current_dir = ctypes.cast(current_dir_id, ctypes.py_object).value
            for _ in range(drs_count):
                level_parameters = self._gen_level_params()
                dir_owner = choice(level_parameters['owners'])

                dir_name = f'D{name_generator(self.NAME_LENGTH)}'
                if current_dir.sub_dirs:
                    current_file_names = [ctypes.cast(dr, ctypes.py_object).value.name for dr in current_dir.sub_dirs]
                    while dir_name in [dr.name for dr in current_file_names]:
                        dir_name = name_generator(self.NAME_LENGTH)
                sub_directory = Dir(current_dir.full_path, dir_name, dir_owner, self.owners, [], [], [], [])
                params_for_creating_dirs.append((sub_directory.full_path, sub_directory.owner))

                current_dir.sub_dirs.append(id(sub_directory))
            # Workaround for ThreadPoolExecutor exception handling
            for _ in executor.map(lambda params: create_dir(*params), params_for_creating_dirs):
                pass

        def create_level(current_dir: int, count_of_dirs: int, count_of_files: int, tread_exec: ThreadPoolExecutor):
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
            all_drs_in_tree.append(id(root_directory))
            all_files_in_tree = root_directory.get_all_files_ids()
            params_for_creating_links = []

            if count:
                for num in range(count):
                    target_dir_id = choice(all_drs_in_tree)
                    target_dir = ctypes.cast(target_dir_id, ctypes.py_object).value
                    target_file_id = choice(all_files_in_tree)
                    target_file = ctypes.cast(target_file_id, ctypes.py_object).value

                    hard_link = HardLink(
                        name=f'HL{num}_{target_file.name}',
                        file_obj=target_file,
                        owner=target_file.owner,
                        dest=target_dir.full_path,
                    )
                    target_dir.hard_links.append(id(hard_link))
                    params_for_creating_links.append((target_file.full_path, hard_link.full_path))

                for _ in executor.map(lambda params: make_hard_link(*params), params_for_creating_links):
                    pass

        def create_symlinks_in_tree(root_directory: Dir, count: int, executor: ThreadPoolExecutor):
            """
            Create symlinks in a file tree.

            :param root_directory:    root Dir object
            :param count:             count of hard links for making
            :param executor:          ThreadPoolExecutor for symlinks creating
            """
            all_drs_in_tree = root_directory.get_all_dirs()
            all_drs_in_tree.append(id(root_directory))
            all_files_in_tree = root_directory.get_all_files_ids()
            params_for_creating_links = []

            if count:
                for num in range(count):
                    target_dir = choice(all_drs_in_tree)
                    target_dir = ctypes.cast(target_dir, ctypes.py_object).value
                    target_file_id = choice([*all_drs_in_tree, *all_files_in_tree])
                    target_file = ctypes.cast(target_file_id, ctypes.py_object).value

                    atime = get_random_timestamp(self.default_time)
                    mtime = get_random_timestamp(self.default_time)
                    sym_link = SymLink(
                        name=f'SL{num}_{target_file.name}',
                        file_obj=target_file,
                        owner='',
                        dest=target_dir.full_path,
                        size=0,
                        atime=atime.strftime(TIME_FORMAT),
                        mtime=mtime.strftime(TIME_FORMAT),
                    )
                    target_dir.symlinks.append(id(sym_link))
                    owner = choice(self._gen_level_params()['owners'])
                    params_for_creating_links.append((target_file.full_path, sym_link, owner, atime, mtime))

                for _ in executor.map(lambda params: make_symlink(*params), params_for_creating_links):
                    pass

        try:
            with ThreadPoolExecutor(max_workers=10) as tread_executor:
                root_dir = Dir(self.dest, self.name, start_dir_owner, self.owners, [], [], [], [])
                if not path.exists(root_dir.full_path):
                    create_dir(root_dir.full_path, start_dir_owner)

                create_level(id(root_dir), dirs_count, files_count, tread_executor)
                current_dirs_level = root_dir.sub_dirs

                for _ in range(self.tree_depth - 1):
                    next_dirs_level = []

                    for sub_dir in current_dirs_level:
                        level_params = self._gen_level_params()
                        dirs_to_create_count = level_params['dirs_count']
                        files_to_create_count = level_params['files_count']

                        create_level(sub_dir, dirs_to_create_count, files_to_create_count, tread_executor)

                        sub_dir = ctypes.cast(sub_dir, ctypes.py_object).value
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
                return root_dir

        except (SystemExit, InterruptedError, FileNotFoundError, KeyboardInterrupt) as error:
            sys_exit(str(error))