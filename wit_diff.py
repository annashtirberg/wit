import difflib
import os
from pathlib import Path
from typing import List, Optional

from wit_status import WitStatus
from wit import Wit


class Diff(object):

    def __init__(self, status: WitStatus, wit: Wit):
        self.status = status
        self.wit = wit

    def diff_file(self, file_path1: Optional[str], file_path2: Optional[str]):
        file_name1 = ""
        file_name2 = ""
        file_lines1 = []
        file_lines2 = []
        if file_path1 is not None:
            file_name1 = os.path.split(file_path1)[1]
            with open(file_path1) as f:
                file_lines1 = f.readlines()
        if file_path2 is not None:
            file_name2 = os.path.split(file_path2)[1]
            with open(file_path2) as f:
                file_lines2 = f.readlines()
        return list(difflib.unified_diff(file_lines1, file_lines2, fromfile=file_name1, tofile=file_name2, lineterm='',
                                         n=3))

    def get_list_file_directory(self, directory):
        for curr_dir, _, file_list in os.walk(directory):
            fl_list = []
            for file_name in file_list:
                file_path = os.path.join(curr_dir, file_name)
                fl_list.append(file_path)
            for fl in fl_list:
                if os.path.isdir(fl):
                    self.get_list_file_directory(fl)
            return fl_list

    def diff_file_list(self, dir_path1: str, dir_path2: str, diff_files_list: List[str], funny_files_list: List[str],
                       left_only_files_list: List[str], right_only_files_list: List[str]):
        files_list = diff_files_list + funny_files_list + left_only_files_list + right_only_files_list
        files_list.sort()
        diff_list = []
        for relative_file_path in files_list:
            absolute_file_path1 = os.path.join(dir_path1, relative_file_path)
            absolute_file_path2 = os.path.join(dir_path2, relative_file_path)
            if relative_file_path in diff_files_list or relative_file_path in funny_files_list:
                diff_list += self.diff_file(absolute_file_path1, absolute_file_path2)
            elif relative_file_path in left_only_files_list:
                diff_list += self.diff_file(absolute_file_path1, None)
            elif relative_file_path in right_only_files_list:
                diff_list += self.diff_file(None, absolute_file_path2)
        return diff_list


class WitDiff(Diff):

    def __init__(self, status: WitStatus, wit: Wit):
        super().__init__(status, wit)

    def get_status_for_directories(self, path1: Path, path2: Path) -> WitStatus:
        pass

    def get_commit_path(self, commit_id: str) -> Path:
        pass

    def get_branch_commit(self, branch_name: str) -> str:
        pass

    def get_working_directory_path(self) -> Path:
        return self.wit.wit_parent_directory

    def get_staging_area_path(self) -> Path:
        return self.wit.staging_area.get_path()



