"""This file contains some help utils."""
import string
from datetime import datetime, timedelta
from os import chown, link, path, stat, symlink, utime
from pwd import getpwnam
from random import choice, randint
from threading import Lock
from time import mktime
from typing import Tuple

from logger_util import logger
from node import Dir, SymLink


START_PATH = path.dirname(__file__)
lock = Lock()
HOURS_DELTA = (1, 23)
MINS_DELTA = (1, 60)
DAYS_DELTA = (0, 1825)  # 5 years
JP_LETTERS = '世界中に存在するウェブサイトのうち'
CYR_LETTERS = 'ЎBKEПPнroлшдў'
LETTERS = string.ascii_letters + string.digits + JP_LETTERS + CYR_LETTERS

TIME_FORMAT = '%Y-%m-%d %H:%M:%S'


def get_user_ids(username) -> tuple:
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
    time_stamp = datetime.fromtimestamp(start_time) - timedelta(
        minutes=randint(*MINS_DELTA), hours=randint(*HOURS_DELTA), days=randint(*DAYS_DELTA)
    )
    return time_stamp


def make_hard_link(src: str, dst: str):
    """
    Make hard link.

    :param src:    source file path
    :param dst:    destination file path
    """
    link(src, dst)
    logger.debug(f'Has been created hard link: {dst}')


def make_symlink(src: str, sym_link: SymLink, owner: str, atime: datetime, mtime: datetime):
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
    # Workaround the size of the symlink needs to be increased by 2 bytes, a feature of FS
    sym_link.size = stat(dst, follow_symlinks=False).st_size + 2
    atime = int(mktime(atime.timetuple()))
    mtime = int(mktime(mtime.timetuple()))
    utime(dst, (atime, mtime), follow_symlinks=False)
    own_uid, own_gid = get_user_ids(owner)
    chown(dst, own_uid, own_gid, follow_symlinks=False)
    sym_link.owner = owner
    logger.debug(f'Has been created symlink: {dst}, owner {owner}')
