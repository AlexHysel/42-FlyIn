from enum import Enum
from pydantic import BaseModel, Field


class HubType(Enum):
    RESTRICTED = "restricted"
    NORMAL = "normal"
    PRIORITY = "priority"


class Hub(BaseModel):
    name: str
    x: int
    y: int
    color: str = "white"
    capacity: int = Field(ge=1, default=1)
    hub_type: HubType = HubType.NORMAL
    connections: dict[str, tuple["Hub", int]] = {}

    def get_weight(self) -> float:
        if self.hub_type == HubType.RESTRICTED:
            return 2.0
        if self.hub_type == HubType.PRIORITY:
            return 0.99
        return 1.0

    def __lt__(self, other: "Hub") -> bool:
        return self.name < other.name

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Hub) and self.name == other.name


class Graph(BaseModel):
    nb_drones: int = Field(ge=1, default=1)
    hubs: dict[str, Hub] = {}
    start: Hub
    end: Hub

    def add_hub(self, hub: Hub) -> None:
        self.hubs[hub.name] = hub

    def connect(self, hubA: Hub, hubB: Hub, cap: int) -> None:
        hubA.connections[hubB.name] = (hubB, cap)
        hubB.connections[hubA.name] = (hubA, cap)