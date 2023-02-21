"""THis file contains logger init."""
import logging
import sys
from datetime import datetime


__all__ = ['logger']

now_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
global_log = f'logs/{now_date}.log'
logger = logging.getLogger()
logger.setLevel(logging.INFO)

console = logging.StreamHandler(stream=sys.stdout)
console.setLevel('DEBUG')
console.setFormatter(logging.Formatter('[LINE:%(lineno)d]# %(levelname)-8s[%(asctime)s] %(message)s'))
logger.addHandler(console)

# log_file = logging.FileHandler(global_log, encoding='utf-8')
# log_file.setLevel(logging.INFO)
# log_file.setFormatter(logging.Formatter(
#     u'[LINE:%(lineno)d]# %(levelname)-8s[%(asctime)s] %(message)s'))
# logger.addHandler(log_file)
