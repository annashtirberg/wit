from __future__ import annotations

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from wit import WitStagingArea
    from wit_commit import WitCommit


class WitStatus(object):
    def __init__(self, head_commit: WitCommit, staging_area: WitStagingArea):
        self.head_commit = head_commit
        self.staging_area = staging_area
        self.changes_to_be_committed = self.get_changes_to_be_committed()
        self.changes_not_staged_for_commit = self.get_changes_not_staged_for_commit()
        self.untracked_files = self.get_untracked_files()
        self.missing_files = self.get_missing_files()

    def get_changes_to_be_committed(self) -> List[str]:
        dir_cmp = self.staging_area.compare_directory(self.head_commit.commit_dir)
        result = dir_cmp.diff_files + dir_cmp.left_only
        return result

    def get_changes_not_staged_for_commit(self) -> List[str]:
        dir_cmp = self.staging_area.compare_directory(self.staging_area.wit_parent_directory)
        result = dir_cmp.diff_files
        return result

    def get_untracked_files(self) -> List[str]:
        dir_cmp = self.staging_area.compare_directory(self.staging_area.wit_parent_directory)
        result = dir_cmp.right_only
        return result

    def get_missing_files(self) -> List[str]:
        dir_cmp = self.staging_area.compare_directory(self.staging_area.wit_parent_directory)
        result = dir_cmp.left_only
        return result

    def print_status(self):
        print(f"{self.head_commit.commit_id}")
        if 0 < len(self.changes_to_be_committed):
            print("Changes to be committed:")
            for file_name in self.changes_to_be_committed:
                print(file_name)
        if 0 < len(self.changes_not_staged_for_commit):
            print("Changes not staged for commit:")
            for file_name in self.changes_not_staged_for_commit:
                print(file_name)
        if 0 < len(self.untracked_files):
            print("Untracked files:")
            for file_name in self.untracked_files:
                print(file_name)
        if 0 < len(self.missing_files):
            print("Missing files:")
            for file_name in self.missing_files:
                print(file_name)
