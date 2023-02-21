"""File contains classes for making reports of TreeGenerator generating results."""
import json
from dataclasses import asdict
from os import path

from gen.logger_util import logger
from gen.node import Directory


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
        with open(self.full_report_path, 'w', encoding='utf-8') as file:
            json.dump(asdict(self.dir_obj), file, skipkeys=True, indent=4, ensure_ascii=False)
            print(f'Report on the generated file tree: {self.full_report_path}')
