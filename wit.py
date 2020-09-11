from __future__ import annotations

import os
import sys
from typing import Optional, Set, TYPE_CHECKING

from wit_checkout import WitCheckout
from wit_classes import ImageDirectory, KeyValueFile
from wit_commit import WitCommits
from wit_consts import IMAGES_DIRECTORY_NAME, STAGING_DIRECTORY_NAME, WIT_COMMANDS_NAMES, WIT_DIRECTORY_NAME
from wit_exceptions import (InvalidWitArguments, InvalidWitCommand, MissingWitCheckoutArgument,
                            MissingWitCommitMessage, NonExistingAddTarget, NoWitRootDirectory, WitNotLoadedException)
from wit_graph import WitGraph
from wit_status import WitStatus
if TYPE_CHECKING:
    from wit_commit import WitCommit


class WitParentDirectory(ImageDirectory):
    def __init__(self, wit_parent_directory_path: str):
        super().__init__(wit_parent_directory_path)


class WitStagingArea(ImageDirectory):
    def __init__(self, wit_parent_directory: WitParentDirectory):
        self.wit_parent_directory = wit_parent_directory
        path = os.path.join(self.wit_parent_directory.get_path(), WIT_DIRECTORY_NAME, STAGING_DIRECTORY_NAME)
        super().__init__(path)
        self._added_files = set()  # type: Set[str]

    def _get_relative_path_to_wit_root(self, path: str) -> str:
        return self.get_relative_path(path, self.wit_parent_directory)

    def _copy_to_staging_area(self, relative_path: str) -> None:
        self.copy_file_from(self.wit_parent_directory, relative_path)

    def _add_file(self, path: str) -> None:
        relative_path = self._get_relative_path_to_wit_root(path)
        self._added_files.add(relative_path)
        self._copy_to_staging_area(relative_path)

    def _add_directory(self, path: str) -> None:
        if not WIT_DIRECTORY_NAME == os.path.split(path)[1]:  # Skip the '.wit' directory itself
            for rel_path in os.listdir(path):
                abs_path = os.path.join(path, rel_path)
                if os.path.isfile(abs_path):
                    self._add_file(abs_path)
                elif os.path.isdir(abs_path):
                    self._add_directory(abs_path)

    def add(self, absolute_path: str) -> None:
        if os.path.isfile(absolute_path):
            self._add_file(absolute_path)
        if os.path.isdir(absolute_path):
            self._add_directory(absolute_path)


class WitReferences(KeyValueFile):
    REFERENCE_FILE_NAME = "references.txt"
    HEAD_KEY = "HEAD"
    MASTER_KEY = "master"
    KEYS = [HEAD_KEY, MASTER_KEY]

    def __init__(self, wit_directory_path: str):
        super().__init__(os.path.join(wit_directory_path, self.REFERENCE_FILE_NAME))
        if os.path.exists(self.path):
            self.load()

    def items(self):
        items = [(self.HEAD_KEY, self[self.HEAD_KEY])]
        for k, v in super().items():
            if k != self.HEAD_KEY:
                items.append((k, v))
        return items

    def commit(self, commit_id: str):
        if self.get_head() is None:
            self.update_head(commit_id)
            self.update_master(commit_id)
        elif self.get_head() == self.get_master():
            self[self.HEAD_KEY] = commit_id
            self[self.MASTER_KEY] = commit_id
        else:
            self[self.HEAD_KEY] = commit_id
        self.save()

    def get_head(self) -> Optional[str]:
        try:
            return self[self.HEAD_KEY]
        except KeyError:
            return None

    def get_master(self) -> str:
        return self[self.MASTER_KEY]

    def update_head(self, new_commit_id: str):
        self[self.HEAD_KEY] = new_commit_id
        self.save()

    def update_master(self, new_commit_id: str):
        self[self.MASTER_KEY] = new_commit_id
        self.save()


class Wit(object):

    # General code
    def __init__(self):
        self._is_loaded = False
        self.wit_parent_directory_path = None  # type: Optional[str]
        self.wit_base_directory_path = None  # type: Optional[str]
        self.wit_staging_directory_path = None  # type: Optional[str]
        self.wit_images_directory_path = None  # type: Optional[str]

        self.wit_parent_directory = None  # type: WitParentDirectory
        self.references = None  # type: WitReferences
        self.commits = None  # type: WitCommits
        self.staging_area = None  # type: WitStagingArea

    def _load(self, path: Optional[str] = None):
        self.wit_parent_directory_path = self._find_wit_root_directory(path)
        self.wit_base_directory_path = os.path.join(self.wit_parent_directory_path, WIT_DIRECTORY_NAME)
        self.wit_staging_directory_path = os.path.join(self.wit_base_directory_path, STAGING_DIRECTORY_NAME)
        self.wit_images_directory_path = os.path.join(self.wit_base_directory_path, IMAGES_DIRECTORY_NAME)

        self.wit_parent_directory = WitParentDirectory(self.wit_parent_directory_path)
        self.references = WitReferences(self.wit_base_directory_path)
        self.commits = WitCommits(self.wit_images_directory_path)
        self.staging_area = WitStagingArea(self.wit_parent_directory)
        self._is_loaded = True

    def verify_loaded(self):
        if not self._is_loaded:
            raise WitNotLoadedException()

    def _print_usage(self):
        pass

    def get_command(self) -> str:
        if 1 == len(sys.argv):
            self._print_usage()
            raise InvalidWitArguments()
        command = sys.argv[1].lower()
        if command not in WIT_COMMANDS_NAMES:
            raise InvalidWitCommand(f"Unknown wit command {command}")
        return command

    def _get_parent_directory(self, current_path: str) -> str:
        return os.path.abspath(os.path.join(current_path, os.path.pardir))

    def _is_wit_dir(self, current_path: str) -> bool:
        return os.path.isdir(os.path.join(current_path, WIT_DIRECTORY_NAME))

    def _find_wit_root_directory(self, path: Optional[str] = None) -> str:
        current_dir = os.getcwd()
        if path is not None:
            if os.path.isdir(path):
                current_dir = path
            else:
                current_dir = os.path.dirname(path)
        while True:
            if self._is_wit_dir(current_dir):
                return current_dir
            if current_dir == self._get_parent_directory(current_dir):
                raise NoWitRootDirectory()
            current_dir = self._get_parent_directory(current_dir)

    def get_head(self) -> str:
        return self.references.get_head()

    def update_head(self, commit_id: str):
        self.references.update_head(commit_id)

    # init related code

    def _create_wit_dir(self, wit_parent_directory: str) -> None:
        os.mkdir(os.path.join(wit_parent_directory, WIT_DIRECTORY_NAME))
        os.mkdir(os.path.join(wit_parent_directory, WIT_DIRECTORY_NAME, IMAGES_DIRECTORY_NAME))
        os.mkdir(os.path.join(wit_parent_directory, WIT_DIRECTORY_NAME, STAGING_DIRECTORY_NAME))

    def init(self) -> None:
        try:
            self._load()
        except NoWitRootDirectory:
            self._create_wit_dir(os.getcwd())
            self.wit_parent_directory = os.getcwd()

    # add related code

    def add(self) -> None:
        if len(sys.argv) < 3:
            raise InvalidWitArguments
        path = sys.argv[2]
        absolute_path = os.path.abspath(path)
        if not os.path.exists(absolute_path):
            raise NonExistingAddTarget()

        self._load(absolute_path)

        self.staging_area.add(absolute_path)

    # commit related code
    def commit(self) -> None:
        if len(sys.argv) < 3:
            raise MissingWitCommitMessage()
        message = sys.argv[2]

        self._load()

        self.commits.commit(message, self.references, self.staging_area)

    # status related code
    def status(self) -> None:
        self._load()

        head_id = self.references.get_head()
        head_commit = self.commits[head_id]  # type: WitCommit
        status = WitStatus(head_commit, self.staging_area)
        status.print_status()

    # checkout related code
    def checkout(self) -> None:
        if len(sys.argv) < 3:
            raise MissingWitCheckoutArgument()
        argument = sys.argv[2]

        self._load()

        checkout = WitCheckout(self, argument)
        checkout.checkout()

    # graph related code
    def graph(self) -> None:
        self._load()

        graph = WitGraph(self)
        graph.show()


def main():
    print(f"argv length: {len(sys.argv)}")
    for i, arg in enumerate(sys.argv):
        print(f"sys.argv[{i}]: '{arg}'")
    wit = Wit()
    try:
        command = wit.get_command()
        if "init" == command:
            wit.init()
        elif "add" == command:
            wit.add()
        elif "commit" == command:
            wit.commit()
        elif "status" == command:
            wit.status()
        elif "checkout" == command:
            wit.checkout()
        elif "graph" == command:
            wit.graph()
    except InvalidWitArguments:
        print(f"argv length: {len(sys.argv)}")
        for i, arg in enumerate(sys.argv):
            print(f"sys.argv[{i}]: '{arg}'")


if __name__ == '__main__':
    main()
