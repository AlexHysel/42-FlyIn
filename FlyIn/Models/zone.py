from pydantic import BaseModel, Field
from FlyIn import ZoneType, Connection


class Zone(BaseModel):
    name: str
    x: int
    y: int
    zone_type: ZoneType = ZoneType.NORMAL
    max_drones: int = 1
    current_drones: int = 0
    is_start: bool = False
    is_end: bool = False
    neighbors: list[Connection] = Field(default_factory=list)
 
    def has_capacity(self) -> bool:
        if self.is_start or self.is_end:
            return True
        return self.current_drones < self.max_drones
 
    def move_cost(self) -> int:
        return 2 if self.zone_type == ZoneType.RESTRICTED else 1
 
    def is_blocked(self) -> bool:
        return self.zone_type == ZoneType.BLOCKED
 
    def is_priority(self) -> bool:
        return self.zone_type == ZoneType.PRIORITY
 
    def enter(self) -> None:
        self.current_drones += 1
 
    def leave(self) -> None:
        self.current_drones -= 1
 
    def __hash__(self) -> int:
        return hash(self.name)
 
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Zone):
            return False
        return self.name == other.name
 
    def __repr__(self) -> str:
        return f"Zone({self.name}, {self.zone_type.value})"
