from enum import Enum


class ZoneType(Enum):
    START = "start"
    END = "end"
    RESTRICTED = "restricted"
    NORMAL = "normal"
    BLOCKED = "blocked"
    PRIORITY = "priority"
