"""File contains texts for main level of program."""


class HelpMsg:
    """Container for text messages."""

    DESCRIPTION = """
    This script is designed to generate a directory tree and files of different sizes, you can set
     the depth of the file tree, the number of files in each directory, and the number of
     directories at each level of the tree.\n\n
    There are 2 ways to generate a tree:\n
    1: Strictly set the number of directories and files at
    each level of the tree.\n
    --dest ./ --tree_name Test_tree --tree_depth 3 --dirs_count 1 --files_count 1000
    --hard_links_count 100 --owners root admin --file_sizes large medium small --report_path ./\n
    2: Use the --random key and set the range of the number
    of directories and files per tree level.\n
    --dest /home/ --tree_name Test_tree --tree_depth 3
    --min_dirs_count 1 --max_dirs_count 1
    --min_files_count 999 --max_files_count 1000
    --hard_links_count 100 --random --owners root admin
    --file_sizes large medium small\n
    Optional: If you want to reproduce a previously created file tree, use the --default_time and
    --seed keys and values specified in the tree report.\n\nAttention!\n With a tree depth of more
    than 50 levels, creation of symlinks and hard links is impossible, because python is not able
    to store full paths that take more than 256 bytes. Parameters hard_links_count and
    sym_links_count must be set to 0.
    """
    DEST = 'root dir for tree creation'
    TREE_DEPTH = 'depth of tree'
    DIRS_COUNT = 'count of directories on the level'
    FILES_COUNT = 'count of files on the level'
    HARD_LINKS_COUNT = 'count of hard links in the file tree'
    SYM_LINKS_COUNT = 'count of symlinks in the file tree'
    MIN_DIRS_COUNT = 'minimum directories count in directory, value must not be less than 1'
    MAX_DIRS_COUNT = 'maximum directories count in directory'
    MIN_FILES_COUNT = 'minimum files count in directory'
    MAX_FILES_COUNT = 'maximum files count in directory'
    OWNERS = 'list of owners\n--owners root admin'
    FILE_SIZES = 'list of file sizes\n --file_sizes large medium small'
    TREE_NAME = 'root dir name'
    REPORT_PATH = 'report path, will use --dest value by default'
    DEFAULT_TIME = (
        'initial timestamp for setting the time period within 5 years from which the '
        'dates of creation and modification of files, for example: 1662707899\n do '
        'not set a value less than 157766400 (1.1.1975)'
    )
    RANDOM = (
        'if --random is called, then min_dirs_count/max_dirs_count and '
        'min_files_count/max_files_count values will be used to determine '
        'the count of files and directories'
    )
    SEED = (
        'if --random is called, you may use --seed to allow to repeat the same random actions'
        ' or the value will be set randomly'
    )
    HELP = 'show usage message'
    LOG_LEVEL = 'Provide logging level. Example -loglevel debug, default=info'
