from pydantic import BaseModel, Field
from enum import Enum


class ZoneType(Enum):
    RESTRICTED = "restricted"
    NORMAL = "normal"
    PRIORITY = "priority"


class Zone(BaseModel):
    name: str
    x: int
    y: int
    max_capacity: int
    zone_type: ZoneType = ZoneType.NORMAL
    connections: dict[str, tuple["Zone", int]] = {}

    def get_weight(self) -> int:
        if self.zone_type == ZoneType.RESTRICTED:
            return 2
        elif self.zone_type == ZoneType.PRIORITY:
            return 0.99
        return 1


class Graph(BaseModel):
    drones_num: int = Field(ge=1)
    zones: dict[str, Zone] = {}
    start: Zone
    end: Zone

    def add_zone(self, zone: Zone) -> None:
        self.zones[zone.name] = zone

    def connect(self, zoneA: Zone, zoneB: Zone, link_capacity: int) -> None:
        zoneA.connections[zoneB.name] = (zoneB, link_capacity)
        zoneB.connections[zoneA.name] = (zoneA, link_capacity)


class Drone(BaseModel):
    name: str


class Parser:
    
    @staticmethod
    def parse(path: str):
        pass