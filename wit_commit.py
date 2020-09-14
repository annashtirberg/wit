from __future__ import annotations

import datetime
import os
import random
from typing import Optional, TYPE_CHECKING

import dateutil.tz

from wit_classes import ImageDirectory, KeyValueFile
from wit_exceptions import CommitingSameFilesException
if TYPE_CHECKING:
    from wit import WitReferences, WitStagingArea

COMMIT_ID_CHARS = "1234567890abcdef"
COMMIT_ID_LENGTH = 40


class WitCommitImage(ImageDirectory):
    def __init__(self, image_path: str, commit_id: str):
        super().__init__(os.path.join(image_path, commit_id))
        self.commit_id = commit_id

    def commit(self, staging_area: WitStagingArea, parent_commit: Optional[WitCommit]):
        if parent_commit is not None:
            if parent_commit.commit_dir.compare_directory(staging_area).is_same():
                raise CommitingSameFilesException()
        self._create_commit_dir()
        self.copy_directory_from(staging_area)

    def _create_commit_dir(self) -> None:
        if not os.path.exists:
            os.mkdir(self.get_path())


class WitCommitMetadata(KeyValueFile):
    PARENT_KEY = "parent"
    DATE_KEY = "date"
    MESSAGE_KEY = "message"
    KEYS = [PARENT_KEY, DATE_KEY, MESSAGE_KEY]
    DATE_FORMAT = "%a %b %d %H:%M:%S %Y %z"

    def __init__(self, image_dir: str, commit_id: str):
        super().__init__(os.path.join(image_dir, f"{commit_id}.txt"))
        self.commit_id = commit_id

    def items(self):
        return [(k, self[k]) for k in self.KEYS]

    def commit(self, message: str, parent_commit: Optional[WitCommit]):
        self[self.PARENT_KEY] = "None"
        if parent_commit:
            self[self.PARENT_KEY] = parent_commit.commit_id
        self[self.DATE_KEY] = self.date_format(datetime.datetime.now(tz=dateutil.tz.tzlocal()))
        self[self.MESSAGE_KEY] = message
        self.save()

    def date_parse(self, date_str: str) -> datetime.datetime:
        return datetime.datetime.strptime(date_str, self.DATE_FORMAT)

    def date_format(self, date: datetime.datetime) -> str:
        return date.strftime(self.DATE_FORMAT)

    def get_parent_id(self) -> Optional[str]:
        try:
            return self[self.PARENT_KEY]
        except KeyError:
            return None

    def get_date(self) -> datetime.datetime:
        return self.date_parse(self[self.DATE_KEY])

    def get_message(self) -> str:
        return self[self.MESSAGE_KEY]


class WitCommit(object):
    def __init__(self, image_dir: str, commit_id: str):
        self._image_dir = image_dir
        self.commit_id = commit_id
        self.commit_dir = WitCommitImage(image_dir, commit_id)
        self.commit_file = WitCommitMetadata(image_dir, commit_id)

    def commit(self, message: str, parent_commit: Optional[WitCommit], staging_area: WitStagingArea):
        self.commit_dir.commit(staging_area, parent_commit)
        self.commit_file.commit(message, parent_commit)

    def save(self):
        self.commit_file.save()

    def load(self):
        self.commit_file.load()

    def get_parent(self) -> Optional['WitCommit']:
        parent_id = self.commit_file.get_parent_id()
        if parent_id is not None:
            return WitCommit(self._image_dir, parent_id)
        else:
            return None


class WitCommits(dict):
    def __init__(self, wit_images_path: str):
        super().__init__()
        self.path = wit_images_path
        for commit_id in filter(lambda x: not x.endswith(".txt"), os.listdir(self.path)):
            commit = WitCommit(self.path, commit_id)
            commit.load()
            self[commit_id] = commit

    def _generate_commit_id(self) -> str:
        commit_id = ''.join(random.choices(COMMIT_ID_CHARS, k=COMMIT_ID_LENGTH))
        while commit_id in self:
            commit_id = ''.join(random.choices(COMMIT_ID_CHARS, k=COMMIT_ID_LENGTH))
        return commit_id

    def commit(self, message: str, references: WitReferences, staging_area: WitStagingArea):
        commit_id = self._generate_commit_id()
        commit = WitCommit(self.path, commit_id)
        parent_commit = None
        parent_id = references.get_head()
        if parent_id is not None:
            parent_commit = self[parent_id]
        commit.commit(message, parent_commit, staging_area)
        self[commit_id] = commit
        references.commit(commit_id)
