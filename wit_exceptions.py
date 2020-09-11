# General exceptions
class InvalidWitCommand(ValueError):
    pass


class InvalidWitArguments(IndexError):
    pass


class NoWitRootDirectory(IOError):
    pass


class WitNotLoadedException(ValueError):
    pass


class InvalidKeyValueFileFormat(ValueError):
    pass


class InvalidKeyValueFileDuplicateKeys(KeyError):
    pass


# init related exceptions
# add related exceptions
class NonExistingAddTarget(ValueError):
    pass


# commit related exceptions
class MissingWitCommitMessage(InvalidWitArguments):
    pass


class CommitingSameFilesException(ValueError):
    pass


# checkout related code
class MissingWitCheckoutArgument(IndexError):
    pass


class InvalidCheckoutArgument(KeyError):
    pass


class ChangesToBeCommitCheckoutError(ValueError):
    pass


class ChangesNotStagedForCommitCheckoutError(ValueError):
    pass
