"""File contains classes for making reports of TreeGenerator generating results."""
import json
from os import path

from gen.nodes.node import Directory
from gen.utils.logger_util import logger
from gen.utils.utilits import dataclass_to_dict, dir_to_dict


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
        logger.info('Start making json report.')

        with open(self.full_report_path, 'w', encoding='utf-8') as file:
            tmp_dict = dataclass_to_dict(self.dir_obj)
            # tmp_dict = dir_to_dict(self.dir_obj)
            json.dump(tmp_dict, file, indent=1, ensure_ascii=False)
            logger.info('Report on the generated file tree: %s', self.full_report_path)

        logger.info('Stop making json report.')
