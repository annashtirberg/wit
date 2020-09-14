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
class CommitingSameFilesException(ValueError):
    pass


# checkout related code
class InvalidCheckoutArgument(KeyError):
    pass


class ChangesToBeCommitCheckoutError(ValueError):
    pass


class ChangesNotStagedForCommitCheckoutError(ValueError):
    pass


# diff related code
class WitDiffNoSuchCommitException(KeyError):
    pass


class WitDiffCommitArgumentNotSpecificEnoughException(IndexError):
    pass
