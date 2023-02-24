"""File contains some help utils."""
import copy
import string
from dataclasses import fields
from datetime import datetime, timedelta
from os import chown, link, path, stat, symlink, utime
from pwd import getpwnam
from random import choice, randint
from threading import Lock
from time import mktime

from gen.nodes.node import Directory, SymLink
from gen.utils.logger_util import logger


START_PATH = path.dirname(__file__)
lock = Lock()
HOURS_DELTA = (1, 23)
MINS_DELTA = (1, 60)
DAYS_DELTA = (0, 1825)  # 5 years
JP_LETTERS = '世界中に存在するウェブサイトのうち'
CYR_LETTERS = 'ЎBKEПPнroлшдў'
LETTERS = string.ascii_letters + string.digits + JP_LETTERS + CYR_LETTERS

TIME_FORMAT = '%Y-%m-%d %H:%M:%S'


def get_user_ids(username: str) -> tuple:
    """
    Get user UID and GID.

    :param username:    user name
    :return:            own_uid, own_gid
    """
    own_uid = getpwnam(username).pw_uid
    own_gid = getpwnam(username).pw_gid
    return own_uid, own_gid


def name_generator(length: int) -> str:
    """
    Name generator.

    :param length:  length of the generated name Python can't store names larger than 4
                    characters when tree depth is greater than 25 directories
    :return:        name
    """
    return ''.join(choice(LETTERS) for _ in range(length))


def get_random_timestamp(start_time: int) -> datetime:
    """
    Get random timestamp.

    Get a random timestamp for the access time change and last modified
    time of a file from a year and a half to the current moment

    :return:    datetime stamp
    """
    return datetime.fromtimestamp(start_time) - timedelta(
        minutes=randint(*MINS_DELTA), hours=randint(*HOURS_DELTA), days=randint(*DAYS_DELTA)
    )


def make_hard_link(src: str, dst: str) -> None:
    """
    Make hard link.

    :param src:    source file path
    :param dst:    destination file path
    """
    link(src, dst)
    logger.debug('Has been created hard link: %s', dst)


def make_symlink(src: str, sym_link: SymLink, owner: str, atime: datetime, mtime: datetime) -> None:
    """
    Make symlink.

    :param owner:       symlink owner
    :param src:         source file path
    :param sym_link:    SymLink object
    :param atime:       timestamp to modify file access timestamp
    :param mtime:       timestamp to modify file modified timestamp
    """
    target_is_dir = False
    if isinstance(sym_link.file_obj, Directory):
        target_is_dir = True
        sym_link.file_obj = {
            'name': sym_link.file_obj.name,
            'dest': sym_link.file_obj.dest,
            'owner': sym_link.file_obj.owner,
        }
    dst = sym_link.full_path
    symlink(src, dst, target_is_directory=target_is_dir)
    # Workaround the size of the symlink needs to be increased by 2 bytes, a feature of FS
    sym_link.size = stat(dst, follow_symlinks=False).st_size + 2
    converted_atime = int(mktime(atime.timetuple()))
    converted_mtime = int(mktime(mtime.timetuple()))
    utime(dst, (converted_atime, converted_mtime), follow_symlinks=False)
    own_uid, own_gid = get_user_ids(owner)
    chown(dst, own_uid, own_gid, follow_symlinks=False)
    sym_link.owner = owner
    logger.debug('Has been created symlink: %s, owner %s', dst, owner)


def dataclass_to_dict(obj, dict_factory=dict):  # noqa: ANN201
    """
    Convert Directory data class to dict recursively, modified dataclass.asdict method.

    :param obj:             Directory instance
    :param dict_factory:    builtin type for converting, dict, tuple, list
    :return:                dictionary
    """
    if hasattr(type(obj), '__dataclass_fields__'):
        result = []
        for field in fields(obj):
            if field.name == '_sub_nodes':
                continue
            value = dataclass_to_dict(getattr(obj, field.name), dict_factory)
            result.append((field.name, value))
        return dict_factory(result)
    if isinstance(obj, tuple) and hasattr(obj, '_fields'):
        return type(obj)(*[dataclass_to_dict(v, dict_factory) for v in obj])
    if isinstance(obj, (list, tuple)):
        return type(obj)(dataclass_to_dict(v, dict_factory) for v in obj)
    if isinstance(obj, dict):
        return type(obj)(
            (dataclass_to_dict(k, dict_factory), dataclass_to_dict(v, dict_factory)) for k, v in obj.items()
        )
    return copy.deepcopy(obj)
