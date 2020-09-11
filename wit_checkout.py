from __future__ import annotations

import os
from typing import TYPE_CHECKING


from wit_consts import WIT_DIRECTORY_NAME
from wit_exceptions import (ChangesNotStagedForCommitCheckoutError, ChangesToBeCommitCheckoutError,
                            InvalidCheckoutArgument)
from wit_status import WitStatus
if TYPE_CHECKING:
    from wit import Wit
    from wit_commit import WitCommit


class WitCheckout(object):
    def __init__(self, wit: Wit, argument: str):
        self.wit = wit
        self.commit_id = self._handle_argument(argument)
        self.commit = self.wit.commits[self.commit_id]  # type: WitCommit
        self.image_directory = self.commit.commit_dir

    def _handle_argument(self, argument: str) -> str:
        # if argument is a branch name. translate to a commit_id
        if argument in self.wit.references:
            return self.wit.references[argument]
        # otherwise check if it's a valid commit id
        elif argument in self.wit.commits:
            return argument
        else:
            raise InvalidCheckoutArgument()

    def _remove_tracked_files(self, status: WitStatus):
        for curr_dir, _, file_list in os.walk(self.wit.wit_parent_directory.get_path()):
            for file_name in file_list:
                absolute_file_path = os.path.join(curr_dir, file_name)
                relative_file_path = self.wit.wit_parent_directory.get_relative_path(absolute_file_path)
                if relative_file_path not in status.untracked_files:
                    if not relative_file_path.startswith(WIT_DIRECTORY_NAME):
                        self.wit.wit_parent_directory.remove_file(relative_file_path)

    def _copy_tracked_files(self, status: WitStatus):
        for curr_dir, _, file_names in os.walk(self.image_directory.get_path()):
            for file_name in file_names:
                absolute_image_file_path = os.path.join(curr_dir, file_name)
                relative_file_path = self.image_directory.get_relative_path(absolute_image_file_path)
                if relative_file_path not in status.untracked_files:
                    self.image_directory.copy_file_to(self.wit.wit_parent_directory, relative_file_path)

    def checkout(self):
        head_commit_id = self.wit.references.get_head()
        head_commit = self.wit.commits[head_commit_id]
        status = WitStatus(head_commit, self.wit.staging_area)

        if 0 < len(status.changes_to_be_committed):
            print("Changes to be committed")
            for i, changes in enumerate(status.changes_to_be_committed):
                print(f"{i}) {changes}")
            raise ChangesToBeCommitCheckoutError()
        if 0 < len(status.changes_not_staged_for_commit):
            raise ChangesNotStagedForCommitCheckoutError()

        self._remove_tracked_files(status)
        self._copy_tracked_files(status)

        self.wit.references.update_head(self.commit_id)

        self.wit.staging_area.clear_directory()
        self.wit.staging_area.copy_directory_from(self.commit.commit_dir)
