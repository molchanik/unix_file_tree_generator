"""File contains classes for making reports of TreeGenerator generating results."""
import json
from dataclasses import asdict
from datetime import datetime
from os import path

from gen.nodes.node import Directory
from gen.utils.logger_util import logger


class TreeReporter:
    """Class contains methods to save files tree structure."""

    def __init__(self, report_path: str, report_name: str, dir_obj: Directory) -> None:
        """
        Init method.

        :param dir_obj:        directory object
        :param report_name:    report name
        :param report_path:    path for create report
        """
        self.report_path = report_path
        self.report_name = report_name
        self.dir_obj = dir_obj
        self.full_report_path = path.join(self.report_path, self.report_name)

    def save_report(self) -> None:
        """Save report."""
        with open(self.full_report_path, 'w', encoding='utf-8') as file:
            file.write(str(self.dir_obj))
            logger.info('Report on the generated file tree: %s', self.full_report_path)


class JsonTreeReporter(TreeReporter):
    """Class contains methods to save files tree structure in JSON format."""

    def save_report(self) -> None:
        """Save report."""
        logger.info('Start making json report %s', datetime.now())

        def remove_specific_key(the_dict: dict, rubbish: str) -> None:
            """
            Remove specific key from dict.

            :param the_dict:    dict for edit
            :param rubbish:     key for remove
            """
            if rubbish in the_dict:
                del the_dict[rubbish]
            for _, value in the_dict.items():
                # check for rubbish in sub dict
                if isinstance(value, dict):
                    remove_specific_key(value, rubbish)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            remove_specific_key(item, rubbish)

        with open(self.full_report_path, 'w', encoding='utf-8') as file:
            tmp_dict = asdict(self.dir_obj)
            logger.info('Start removing _sub_dirs')
            remove_specific_key(tmp_dict, '_sub_nodes')
            logger.info('Stop removing _sub_dirs')
            json.dump(tmp_dict, file, skipkeys=True, indent=1, ensure_ascii=False)
            logger.info('Report on the generated file tree: %s', self.full_report_path)

        logger.info('Stop making json report %s', datetime.now())
