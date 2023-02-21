#!/usr/local/bin/python3
"""File contain main logic for creating file tree."""
import argparse
import datetime
import sys
from random import seed
from time import time

from gen.arg_parser import TreeGenArgParserValidator
from gen.logger_util import logger
from gen.main_txt_msgs import HelpMsg
from gen.main_utils import add_input_args_to_json_report
from gen.tree_gen import TreeGenerator


CURRENT_TIME = datetime.datetime.now()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        add_help=False,
        description=HelpMsg.DESCRIPTION,
        usage='use "./%(prog)s --help" for more information',
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument('--dest', default='', help=HelpMsg.DEST)
    parser.add_argument('--tree_depth', default=1, type=int, help=HelpMsg.TREE_DEPTH)
    parser.add_argument('--dirs_count', default=1, type=int, help=HelpMsg.DIRS_COUNT)
    parser.add_argument('--files_count', default=1, type=int, help=HelpMsg.FILES_COUNT)
    parser.add_argument('--hard_links_count', default=0, type=int, help=HelpMsg.HARD_LINKS_COUNT)
    parser.add_argument('--sym_links_count', default=0, type=int, help=HelpMsg.SYM_LINKS_COUNT)
    parser.add_argument('--min_dirs_count', default=None, type=int, help=HelpMsg.MIN_DIRS_COUNT)
    parser.add_argument('--max_dirs_count', default=None, type=int, help=HelpMsg.MAX_DIRS_COUNT)
    parser.add_argument('--min_files_count', default=None, type=int, help=HelpMsg.MIN_FILES_COUNT)
    parser.add_argument('--max_files_count', default=None, type=int, help=HelpMsg.MAX_FILES_COUNT)
    parser.add_argument('--owners', nargs='*', default='root admin', help=HelpMsg.OWNERS)
    parser.add_argument('--file_sizes', nargs='*', default='large medium small', help=HelpMsg.FILE_SIZES)
    parser.add_argument('--tree_name', default='Test_tree', help=HelpMsg.TREE_NAME)
    parser.add_argument('--report_path', help=HelpMsg.REPORT_PATH)
    parser.add_argument('--default_time', type=int, default=None, help=HelpMsg.DEFAULT_TIME)
    parser.add_argument('--random', action='store_true', help=HelpMsg.RANDOM)
    parser.add_argument('--seed', type=int, default=None, help=HelpMsg.SEED)
    parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS, help=HelpMsg.HELP)
    args = parser.parse_args()
    validator = TreeGenArgParserValidator(args)
    validator.validate_args()

    CURRENT_TIME = datetime.datetime.fromtimestamp(args.default_time) if args.default_time is not None else CURRENT_TIME
    args.default_time = int(CURRENT_TIME.timestamp()) if args.default_time is None else args.default_time

    COMMAND_LINE_ARGS = ' '.join(sys.argv[1:])
    seed_val = int(time()) if args.seed is None else int(args.seed)
    seed(seed_val, version=1)

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
            default_time=args.default_time,
            file_sizes=args.file_sizes,
            report_path=args.report_path,
            random=True,
        )
        res_dir = tree.generate_tree()
        total_hard_links_count = int(res_dir.total_hard_links_count)
        total_files_count = int(res_dir.total_files_count)
        total_symlinks_count = int(res_dir.total_symlinks_count)
        end = time()
        log = (
            f'It took {round(end - start, 0)} sec to make content in '
            f'{res_dir.name} with the following parameters:\ntree_depth='
            f'{args.tree_depth}\nrandom seed={seed_val}\n'
            f'initial timestamp={args.default_time}\n'
            f'min_dirs_count={args.min_dirs_count}, '
            f'max_dirs_count={args.max_dirs_count}, '
            f'min_files_count={args.min_files_count}, '
            f'max_files_count={args.max_files_count}, '
            f'hard links={args.hard_links_count} '
            f'symlinks={args.sym_links_count}\n'
            f'Have been created:\nFiles(including symlinks): {total_files_count}\n'
            f'Dirs: {res_dir.total_sub_dirs_count + 1}\n'
            f'Hard links: {total_hard_links_count}\n'
            f'Sym links: {total_symlinks_count}\n'
            f'Files + Hard links + Symlinks: {(total_hard_links_count + total_files_count)}\n'
            f'Total entries: {res_dir.total_entries + 1}\n'
            f'Total size of all files: {res_dir.total_size_all_files}'
        )
        logger.info(log)
    else:
        num_of_created_dirs = validator.expected_tree_dirs_count()
        num_of_created_files = validator.expected_tree_files_count()
        logger.info('Number of directories to be created in the tree: %s\n', num_of_created_dirs)
        logger.info('Number of files to be created in the tree: %s\n', num_of_created_files)
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
            default_time=args.default_time,
            file_sizes=args.file_sizes,
            report_path=args.report_path,
            random=False,
        )

        res_dir = tree.generate_tree()
        end = time()
        total_hard_links_count = int(res_dir.total_hard_links_count)
        total_files_count = int(res_dir.total_files_count)
        total_symlinks_count = int(res_dir.total_symlinks_count)
        log = (
            f'It took {round(end - start, 0)} sec to make content in '
            f'{res_dir.name} with the following parameters:\ntree_depth='
            f'{args.tree_depth}, dirs_count={args.dirs_count}, '
            f'files_count={args.files_count}, '
            f'hard links={args.hard_links_count} '
            f'symlinks={args.sym_links_count}\n'
            f'random seed={seed_val}\n'
            f'initial timestamp={args.default_time}\n\n'
            f'Have been created:\nFiles(including symlinks): {total_files_count}\n'
            f'Dirs: {res_dir.total_sub_dirs_count + 1}\n'
            f'Hard links: {total_hard_links_count}\n'
            f'Sym links: {total_symlinks_count}\n'
            f'Files + Hard links + Symlinks: {(total_hard_links_count + total_files_count)}\n'
            f'Total entries: {res_dir.total_entries + 1}\n'
            f'Total size of all files: {res_dir.total_size_all_files}'
        )
        logger.info(log)

    add_input_args_to_json_report(tree.full_report_path, COMMAND_LINE_ARGS, args.default_time, seed_val)
