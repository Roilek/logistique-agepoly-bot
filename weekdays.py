from enum import Enum

class Weekday(Enum):
    """Weekdays with way of describing them for users"""
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

    def __int__(self) -> int:
        return self.value

    @classmethod
    def of(cls, arg: str):
        if arg in ("lu", "lundi", "mo", "monday"):
            return Weekday.MONDAY
        elif arg in ("ma", "mardi", "tu", "tuesday"):
            return Weekday.TUESDAY
        elif arg in ("me", "mercredi", "we", "wednesday"):
            return Weekday.WEDNESDAY
        elif arg in ("je", "jeudi", "th", "thursday"):
            return Weekday.THURSDAY
        elif arg in ("ve", "vendredi", "fr", "friday"):
            return Weekday.FRIDAY
        elif arg in ("sa", "samedi", "saturday"):
            return Weekday.SATURDAY
        elif arg in ("di", "dimanche", "su", "sunday"):
            return Weekday.SUNDAY
