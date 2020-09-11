import filecmp
import os
import shutil

from wit_consts import WIT_DIRECTORY_NAME
from wit_exceptions import InvalidKeyValueFileDuplicateKeys, InvalidKeyValueFileFormat

from typing import List, Optional


class WitDirectoryCompare(object):

    def __init__(self, left: str, right: str):
        dircmp = filecmp.dircmp(left, right, ignore=[WIT_DIRECTORY_NAME])

        self.left = dircmp.left
        self.right = dircmp.right

        self.left_list = []  # type: List[str]
        self.right_list = []  # type: List[str]
        self.common = []  # type: List[str]
        self.left_only = []  # type: List[str]
        self.right_only = []  # type: List[str]
        self.common_dirs = []  # type: List[str]
        self.common_files = []  # type: List[str]
        self.common_funny = []  # type: List[str]
        self.same_files = []  # type: List[str]
        self.diff_files = []  # type: List[str]
        self.funny_files = []  # type: List[str]
        self._handle_subdir("", dircmp)

    def _handle_subdir(self, dir_name: str, dir_cmp: filecmp.dircmp):
        self.left_list += map(lambda name: os.path.join(dir_name, name), dir_cmp.left_list)
        self.right_list += map(lambda name: os.path.join(dir_name, name), dir_cmp.right_list)
        self.common += map(lambda name: os.path.join(dir_name, name), dir_cmp.common)
        self.left_only += map(lambda name: os.path.join(dir_name, name), dir_cmp.left_only)
        self.right_only += map(lambda name: os.path.join(dir_name, name), dir_cmp.right_only)
        self.common_dirs += map(lambda name: os.path.join(dir_name, name), dir_cmp.common_dirs)
        self.common_files += map(lambda name: os.path.join(dir_name, name), dir_cmp.common_files)
        self.common_funny += map(lambda name: os.path.join(dir_name, name), dir_cmp.common_funny)
        self.same_files += map(lambda name: os.path.join(dir_name, name), dir_cmp.same_files)
        self.diff_files += map(lambda name: os.path.join(dir_name, name), dir_cmp.diff_files)
        self.funny_files += map(lambda name: os.path.join(dir_name, name), dir_cmp.funny_files)
        for subdir_name, subdir_cmp in dir_cmp.subdirs.items():
            self._handle_subdir(os.path.join(dir_name, subdir_name), subdir_cmp)

    def is_same(self) -> bool:
        if 0 < len(self.left_only):
            return False
        if 0 < len(self.right_only):
            return False
        if 0 < len(self.common_funny):
            return False
        if 0 < len(self.diff_files):
            return False
        return True


class ImageDirectory(object):
    def __init__(self, directory_path: str):
        self._directory_path = directory_path

    def get_path(self) -> str:
        return self._directory_path

    def get_relative_path(self, path: str, other: Optional['ImageDirectory'] = None):
        if other is None:
            return os.path.relpath(path, self.get_path())
        else:
            return os.path.relpath(path, other.get_path())

    def clear_directory(self):
        pass

    def _create_upper_directories(self, directory_path: str):
        os.makedirs(directory_path, exist_ok=True)

    def remove_file(self, relative_path: str):
        path = os.path.join(self.get_path(), relative_path)
        os.remove(path)

    def _copy_file(self, src_path: str, dst_path: str, create_parent_directories=False):
        if create_parent_directories:
            parent_directory = os.path.split(dst_path)[0]
            self._create_upper_directories(parent_directory)
        shutil.copy(src_path, dst_path)

    def copy_file_from(self, other: 'ImageDirectory', relative_path: str):
        src_path = os.path.join(other.get_path(), relative_path)
        dst_path = os.path.join(self.get_path(), relative_path)
        self._copy_file(src_path, dst_path, True)

    def copy_file_to(self, other: 'ImageDirectory', relative_path: str):
        src_path = os.path.join(self.get_path(), relative_path)
        dst_path = os.path.join(other.get_path(), relative_path)
        self._copy_file(src_path, dst_path, True)

    def _copy_directory(self, src: str, dst: str, symlink=False, ignore=None):
        for item in os.listdir(src):
            abs_src = os.path.join(src, item)
            abs_dst = os.path.join(dst, item)
            if os.path.isdir(abs_src):
                shutil.copytree(abs_src, abs_dst, symlinks=symlink, ignore=ignore)
            else:
                self._create_upper_directories(os.path.dirname(abs_dst))
                shutil.copy2(abs_src, abs_dst)

    def copy_directory_from(self, other: 'ImageDirectory'):
        self._copy_directory(other.get_path(), self.get_path())

    def copy_directory_to(self, other: 'ImageDirectory'):
        self._copy_directory(self.get_path(), other.get_path())

    def compare_directory_path(self, other_path: str) -> WitDirectoryCompare:
        return WitDirectoryCompare(self.get_path(), other_path)

    def compare_directory(self, other: 'ImageDirectory') -> WitDirectoryCompare:
        return self.compare_directory_path(other.get_path())

    def is_same(self, other: 'ImageDirectory') -> bool:
        dircmp = self.compare_directory(other)
        return dircmp.is_same()


class KeyValueFile(dict):
    def __init__(self, file_path: str):
        super().__init__()
        self.path = file_path

    def __getitem__(self, key: str) -> str:
        value = super().__getitem__(key)  # type: str
        return value

    def load(self):
        try:
            with open(self.path, "r") as f:
                for line in f.readlines():
                    current_key, current_value = line.strip().split("=")
                    if current_key in self:
                        raise InvalidKeyValueFileDuplicateKeys()
                    self[current_key] = current_value
        except ValueError:
            raise InvalidKeyValueFileFormat()

    def save(self):
        lines = []
        for current_key, current_value in self.items():
            lines.append(f"{current_key}={current_value}\n")
        with open(self.path, "w") as f:
            f.writelines(lines)
