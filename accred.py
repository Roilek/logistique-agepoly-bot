from enum import Enum


class Accred(Enum):
    """Accreditation status of a user."""
    EXTERNAL = 0
    INTERNAL = 1
    TEAM_MEMBER = 2
    TEAM_LEADER = 3
    ADMIN = 4

    def __str__(self) -> str:
        return self.name.lower()

    def __repr__(self) -> str:
        return self.name.lower()

    def __int__(self) -> int:
        return self.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Accred):
            return self.value == other.value
        return False

    def __ne__(self, other: object) -> bool:
        if isinstance(other, Accred):
            return self.value != other.value
        return True

    def __lt__(self, other: object) -> bool:
        if isinstance(other, Accred):
            return self.value < other.value
        return False

    def __le__(self, other: object) -> bool:
        if isinstance(other, Accred):
            return self.value <= other.value
        return False

    def __gt__(self, other: object) -> bool:
        if isinstance(other, Accred):
            return self.value > other.value
        return False

    def __ge__(self, other: object) -> bool:
        if isinstance(other, Accred):
            return self.value >= other.value
        return False

    @classmethod
    def from_value(cls, value: int) -> "Accred":
        """Return the Accred enum from a value."""
        return cls(value)
