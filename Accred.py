from enum import Enum


class Accred(Enum):
    """Accreditation status of a user."""
    EXTERNAL = 0,
    INTERNAL = 1,
    TEAM_MEMBER = 2,
    TEAM_LEADER = 3,
    ADMIN = 4
