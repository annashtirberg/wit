from __future__ import annotations

import difflib
import os
import sys
from typing import List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from wit import Wit
    from wit_classes import ImageDirectory
    from wit_commit import WitCommit


class WitDiffNoSuchCommitException(KeyError):
    pass


class WitDiffCommitArgumentNotSpecificEnoughException(IndexError):
    pass


class WitDiffInvalidArgumentsException(IndexError):
    pass


class Diff(object):

    def diff_file(self, file_path1: Optional[str], file_path2: Optional[str]):
        file_name1 = ""
        file_name2 = ""
        file_lines1 = []
        file_lines2 = []
        if file_path1 is not None:
            file_name1 = os.path.split(file_path1)[1]
            with open(file_path1, encoding="utf8") as f:
                file_lines1 = f.readlines()
        if file_path2 is not None:
            file_name2 = os.path.split(file_path2)[1]
            with open(file_path2, encoding="utf8") as f:
                file_lines2 = f.readlines()
        return list(difflib.unified_diff(file_lines1, file_lines2, fromfile=file_name1, tofile=file_name2, n=3))

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
        left_only_files_list = list(
            filter(lambda left_file_name: os.path.isfile(os.path.join(dir_path1, left_file_name)),
                   left_only_files_list))
        right_only_files_list = list(
            filter(lambda right_file_name: os.path.isfile(os.path.join(dir_path2, right_file_name)),
                   right_only_files_list))
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

    def __init__(self, wit: Wit):
        super().__init__()
        self.wit = wit

    def get_working_directory_path(self) -> ImageDirectory:
        return self.wit.wit_parent_directory

    def get_staging_area_path(self) -> ImageDirectory:
        return self.wit.staging_area

    def get_named_commit_image_directory(self, commit_name) -> WitCommit:
        # check if commit_name is a branch name
        if commit_name in self.wit.references:
            branch_commit_id = self.wit.references[commit_name]
            branch_commit = self.wit.commits[branch_commit_id]  # type: WitCommit
            return branch_commit
        # otherwise check if it is a commit id or the beginning of a commit id
        else:
            commit = self._get_commit_by_partial_id(commit_name)
            return commit

    def _get_commit_by_partial_id(self, partial_commit_id: str) -> WitCommit:
        commit_ids = self.wit.commits.keys()
        fitting_commit_ids = list(filter(lambda commit_id: commit_id.startswith(partial_commit_id), commit_ids))
        if 0 == len(fitting_commit_ids):
            raise WitDiffNoSuchCommitException(partial_commit_id)
        elif 1 < len(fitting_commit_ids):
            raise WitDiffCommitArgumentNotSpecificEnoughException(partial_commit_id)
        else:
            return self.wit.commits[fitting_commit_ids[0]]

    def _parse_arguments(self) -> Tuple[ImageDirectory, ImageDirectory]:
        is_cached = False
        arguments = sys.argv[2:]
        argument1 = None  # type: Optional[str]
        argument2 = None  # type: Optional[str]
        old_directory = None  # type: Optional[ImageDirectory]
        new_directory = None  # type: Optional[ImageDirectory]
        # argv[0] == "wit.py"
        # argv[1] == "diff"
        # argv[2] might be "--cached"
        # argv[2/3] might be the first argument
        # argv[3/4] might e the second argument

        if 3 <= len(sys.argv):
            if "--cached" == sys.argv[2]:
                is_cached = True
                arguments = sys.argv[3:]

        if 1 <= len(arguments):
            argument1 = arguments[0]
        if 2 <= len(arguments):
            argument2 = arguments[1]

        if is_cached:
            new_directory = self.wit.staging_area
            if argument1 is None:
                # wit diff --cached
                # compare HEAD<->staging_area
                old_directory = self.get_named_commit_image_directory("HEAD").commit_dir
            elif argument2 is None:
                # wit diff --cached arg1
                # compare named-commit<->staging_area
                old_directory = self.get_named_commit_image_directory(argument1).commit_dir
            else:
                # wit diff --cached arg1 arg2
                # this is not a valid option
                raise WitDiffInvalidArgumentsException("wit diff -cached can only handle a single argument")
        else:
            new_directory = self.wit.wit_parent_directory
            if argument1 is None:
                # wit diff
                # compare staging_area<->working_directory
                old_directory = self.wit.staging_area
            elif argument2 is None:
                # wit diff arg1
                # compare named-commit<->working_directory
                old_directory = self.get_named_commit_image_directory(argument1).commit_dir
            else:
                # wit diff arg1 arg2
                # compare named-commit1<->named-commit2
                old_directory = self.get_named_commit_image_directory(argument1).commit_dir
                new_directory = self.get_named_commit_image_directory(argument2).commit_dir
        return old_directory, new_directory

    def diff(self):
        old_directory, new_directory = self._parse_arguments()

        diff = old_directory.compare_directory(new_directory)

        diff_lines = self.diff_file_list(old_directory.get_path(), new_directory.get_path(), diff.diff_files,
                                         diff.funny_files, diff.left_only, diff.right_only)

        print("".join(diff_lines))
