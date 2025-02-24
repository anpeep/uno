from enum import Enum
from typing import TypeVar, Generic

# Defineeri generiline tüüp T
T = TypeVar("T")

# Result tüübi implementatsioon
class Result(Generic[T]):
    def __init__(self, data: T = None, error: str = None):
        if data is not None and error is not None:
            raise ValueError("Result cannot have both data and error.")
        self.data = data
        self.error = error

    def is_success(self) -> bool:
        return self.data is not None

    def is_error(self) -> bool:
        return self.error is not None

class GameCheat(Enum):
    GIVE_WILD_FOUR = "giveWildFour"
    GIVE_WILD_EIGHT = "giveWildEight"