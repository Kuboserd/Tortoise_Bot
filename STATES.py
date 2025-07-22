from enum import Enum


class AddResult(Enum):
    EXISTS = "exists"
    NO_SUCH_PLAYER = "noSuchPlayer"
    NO_SUCH_CHARACTER = "noSuchCharacter"
    ADDED = "added"

class RemoveResult(Enum):
    NOT_EXISTS = "not_exists"
    REMOVED = "removed"

class States(Enum):
    ERROR = "error"