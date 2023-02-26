"""File contains logic of file tree generating."""
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import datetime
from os import chdir, chown, mkdir, path, utime
from random import choice, randint, sample
from threading import Lock
from time import mktime

from gen.nodes.node import Directory, File, HardLink, SymLink
from gen.utils.logger_util import logger
from gen.utils.main_utils import sys_exit
from gen.utils.reporter import JsonTreeReporter
from gen.utils.utilits import (
    TIME_FORMAT,
    get_random_timestamp,
    get_user_ids,
    make_hard_link,
    make_symlink,
    name_generator,
)


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


class TreeGenerator2:  # pylint: disable=too-many-statements, too-many-instance-attributes, too-many-locals
    """Tree generator class."""

    def __init__(  # pylint: disable=too-many-instance-attributes, too-many-arguments
        self,
        name: str,
        dest: str,
        tree_depth: int,
        owners: list[str],
        file_sizes: list[str],
        dirs_count: int = 0,
        min_dirs_count: int = 0,
        max_dirs_count: int = 0,
        files_count: int = 0,
        min_files_count: int = 0,
        max_files_count: int = 0,
        hard_links_count: int = 0,
        default_time: int = 0,
        symlinks_count: int = 0,
        report_path: str = '',
        random: bool = False,  # noqa: FBT001, FBT002
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
        self.name_length = 2 if self.tree_depth >= 50 else NAME_LENGTH

    @property
    def full_path(self) -> str:
        """
        Get full dir path.

        :return:    full path
        """
        return path.join(self.dest, self.name)

    @property
    def full_report_path(self) -> str:
        """Full path to tree report."""
        return f'{path.join(self.report_path, self.name)}_report.json'

    def get_node_counts(self) -> dict[str, int]:
        """
        Get counts for generating nodes.

        :return:    dict with parameters for nodes generating
        """
        params = {'dirs_count': int(self.dirs_count), 'files_count': int(self.files_count)}
        if self.random:
            params['dirs_count'] = randint(self.min_dirs_count, self.max_dirs_count)
            params['files_count'] = randint(self.min_files_count, self.max_files_count)
        return params

    def get_owners(self) -> list[str]:
        """
        Get owners for generating nodes.

        :return:    dict with owners names for nodes generating
        """
        return list(sample(self.owners, randint(1, len(self.owners))))

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
        file_ext = choice(file_params['type'].get(file_type))

        size = choice(self.file_sizes)
        size = file_params['size'].get(size)
        final_size = randint(int(float(size) * 0.7), int(float(size) * 1.3))

        return {'final_size': final_size, 'file_type': file_ext}

    def generate_tree(self) -> Directory:  # noqa: PLR0915, C901
        """
        Generate files tree.

        :return:    Directory object that contains full tree which was created
        """
        start_params = self.get_node_counts()
        start_dir_owner = choice(self.get_owners())
        dirs_count = int(start_params['dirs_count'])
        files_count = int(start_params['files_count'])

        def create_file(file_obj: File) -> None:
            """
            Create file.

            :param file_obj:        File instance
            """
            _full_path = file_obj.full_path
            full_path = file_obj.full_path
            list_of_dirs = []
            try:
                with lock:
                    if len(file_obj.full_path.split('/')) > 100:
                        dirs_list = file_obj.full_path.split('/')
                        dirs_list[0] = '/'

                        while len(dirs_list) > 50:
                            list_of_dirs.append(path.join(*dirs_list[:50]))
                            dirs_list = dirs_list[50:]
                        full_path = path.join(*dirs_list)

                        for path_name in list_of_dirs:
                            chdir(path_name)

                    with open(full_path, 'wb') as file:
                        file.seek(file_obj.size - 1)
                        file.write(b'0')
                    converted_atime = int(mktime(datetime.fromisoformat(file_obj.atime).timetuple()))
                    converted_mtime = int(mktime(datetime.fromisoformat(file_obj.atime).timetuple()))
                    utime(full_path, (converted_atime, converted_mtime))
                    own_uid, own_gid = get_user_ids(file_obj.owner)
                    chown(full_path, own_uid, own_gid)
                    logger.debug('Has been created file: %s', _full_path)
                    _full_path.strip()
                    chdir(START_PATH)
            except (PermissionError, ValueError, LookupError) as err:
                logger.error('User %s was selected to create the file', file_obj.owner)
                raise SystemExit(err) from SystemExit

        def create_dir(dir_path: str, owner: str) -> None:
            """
            Create dir in the OS.

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

        def create_files_at_level(current_dir: Directory, fls_count: int | str) -> None:
            """
            Create files in the current directory.

            :param current_dir:    current working directory
            :param fls_count:      number of files to create
            """
            if int(fls_count) != 0:
                for _ in range(int(fls_count)):
                    file_params = self._gen_file_params()
                    file_owner = choice(self.get_owners())

                    file_name = name_generator(self.name_length)
                    file_name = f'F{file_name}.{file_params["file_type"]}'
                    while file_name in [fl.name for fl in current_dir.files]:
                        file_params = self._gen_file_params()
                        file_name = name_generator(self.name_length)
                        file_name = f'F{file_name}.{file_params["file_type"]}'

                    file_size = int(file_params['final_size'])
                    atime = get_random_timestamp(self.default_time)
                    mtime = get_random_timestamp(self.default_time)
                    current_dir.add_node(
                        File(
                            dest=current_dir.full_path,
                            name=file_name,
                            size=file_size,
                            owner=file_owner,
                            atime=atime.strftime(TIME_FORMAT),
                            mtime=mtime.strftime(TIME_FORMAT),
                        )
                    )

        def create_dirs_at_level(current_dir: Directory, drs_count: int, executor: ThreadPoolExecutor) -> None:
            """
            Create dirs in the current directory.

            :param current_dir:    current working directory
            :param drs_count:      number of directories to create
            :param executor:       ThreadPoolExecutor for dirs creating
            """
            params_for_creating_dirs = []
            for _ in range(drs_count):
                dir_owner = choice(self.get_owners())

                dir_name = f'D{name_generator(self.name_length)}'
                while dir_name in [dr.name for dr in current_dir.sub_dirs]:
                    dir_name = name_generator(self.name_length)
                directory = Directory(current_dir.full_path, dir_name, dir_owner, self.owners)
                params_for_creating_dirs.append((directory.full_path, directory.owner))

                current_dir.add_node(directory)
            # Workaround for ThreadPoolExecutor exception handling
            for _ in executor.map(lambda params: create_dir(*params), params_for_creating_dirs):
                pass

        def create_level(
            current_dir: Directory, count_of_dirs: int, count_of_files: int, tread_exec: ThreadPoolExecutor
        ) -> None:
            """
            Create files and dirs in the current directory.

            :param current_dir:        current working directory
            :param count_of_dirs:      number of directories to create
            :param count_of_files:     number of files to create
            :param tread_exec:         ThreadPoolExecutor for dirs creating
            """
            create_dirs_at_level(current_dir, count_of_dirs, tread_exec)
            create_files_at_level(current_dir, count_of_files)

        def create_hard_links_in_tree(
            count: int, executor: ThreadPoolExecutor, dirs: list[Directory], files: list[File]
        ) -> None:
            """
            Create hard links in a file tree.

            :param count:             count of hard links for making
            :param executor:          ThreadPoolExecutor for hardlinks creating
            :param dirs:              list of Directory's
            :param files:             list of File's
            """
            params_for_creating_links = []

            for num in range(count):
                target_dir = dirs[randint(0, len(dirs))]
                target_file = files[randint(1, len(files))]

                hard_link = HardLink(
                    name=f'HL{num}_{target_file.name}',
                    file_obj=target_file,
                    owner=target_file.owner,
                    dest=target_dir.full_path,
                )
                target_dir.add_node(hard_link)
                params_for_creating_links.append((target_file.full_path, hard_link.full_path))

            for _ in executor.map(lambda params: make_hard_link(*params), params_for_creating_links):
                pass

        def create_symlinks_in_tree(
            count: int, executor: ThreadPoolExecutor, dirs: list[Directory], files: list[File]
        ) -> None:
            """
            Create symlinks in a file tree.

            :param count:             count of hard links for making
            :param executor:          ThreadPoolExecutor for symlinks creating
            :param dirs:              list of Directory's
            :param files:             list of File's
            """
            params_for_creating_links = []

            for num in range(count):
                target_dir = dirs[randint(0, len(dirs))]
                target_file = files[randint(1, len(files))] if randint(0, 1) else dirs[randint(0, len(dirs))]

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
                target_dir.add_node(sym_link)
                owner = choice(self.get_owners())
                params_for_creating_links.append((target_file.full_path, sym_link, owner, atime, mtime))

            for _ in executor.map(lambda params: make_symlink(*params), params_for_creating_links):
                pass

        try:
            with ThreadPoolExecutor(max_workers=10) as tread_executor:
                logger.info('Start making files')
                root_dir = Directory(self.dest, self.name, start_dir_owner, self.owners)
                if not path.exists(root_dir.full_path):
                    create_dir(root_dir.full_path, start_dir_owner)
                create_level(root_dir, dirs_count, files_count, tread_executor)
                current_dirs_level = root_dir.sub_dirs

                for _ in range(self.tree_depth - 1):
                    next_dirs_level = []

                    for sub_dir in current_dirs_level:
                        nodes_count = self.get_node_counts()
                        dirs_to_create_count = nodes_count['dirs_count']
                        files_to_create_count = nodes_count['files_count']

                        create_level(sub_dir, dirs_to_create_count, files_to_create_count, tread_executor)
                        for sub_directory in sub_dir.sub_dirs:
                            next_dirs_level.append(sub_directory)

                    current_dirs_level = next_dirs_level.copy()

                for sub_dr in current_dirs_level:
                    nodes_count = self.get_node_counts()
                    files_to_create_count = nodes_count['files_count']
                    create_files_at_level(sub_dr, files_to_create_count)

                for _ in tread_executor.map(
                    create_file, root_dir.sub_nodes_generator(recursive=True, type_constraint=File)
                ):
                    pass

                create_hard_links_in_tree(
                    self.hard_links_count, tread_executor, root_dir.get_all_dirs(), root_dir.get_all_files()
                )
                create_symlinks_in_tree(
                    self.symlinks_count, tread_executor, root_dir.get_all_dirs(), root_dir.get_all_files()
                )
            logger.info('Creating files is done')
            if self.report_path:
                JsonTreeReporter(self.report_path, f'{self.name}_report.json', root_dir).save_report()
            return root_dir

        except (SystemExit, InterruptedError, FileNotFoundError, KeyboardInterrupt) as error:
            sys_exit(str(error))
            return root_dir
