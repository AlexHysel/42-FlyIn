from pydantic import BaseModel, ConfigDict
from FlyIn import Zone


class Connection(BaseModel):
    zone_a: Zone
    zone_b: Zone
    max_link_capacity: int = 1
    current_drones: int = 0
 
    def other(self, zone: Zone) -> Zone:
        return self.zone_b if zone is self.zone_a else self.zone_a
 
    def has_capacity(self) -> bool:
        return self.current_drones < self.max_link_capacity
 
    def connects(self, zone: Zone) -> bool:
        return zone is self.zone_a or zone is self.zone_b
 
    def enter(self) -> None:
        self.current_drones += 1
 
    def leave(self) -> None:
        self.current_drones -= 1
 
    def __hash__(self) -> int:
        return hash((self.zone_a.name, self.zone_b.name))
 
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Connection):
            return False
        return (
            (self.zone_a.name == other.zone_a.name and self.zone_b.name == other.zone_b.name)
            or
            (self.zone_a.name == other.zone_b.name and self.zone_b.name == other.zone_a.name)
        )
 
    def __repr__(self) -> str:
        return f"Connection({self.zone_a.name}-{self.zone_b.name})"
 
 
Zone.model_rebuild()
Connection.model_rebuild()
