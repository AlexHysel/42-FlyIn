from pydantic import BaseModel, Field
from FlyIn import Zone, Connection, DroneState


class Drone(BaseModel):
    id: int
    position: Zone | Connection
    status: DroneState = DroneState.WAITING
    turns_in_transit: int = 0
    path: list[Zone] = Field(default_factory=list)

    def is_delivered(self) -> bool:
        return self.status == DroneState.DELIVERED

    def is_in_transit(self) -> bool:
        return self.status == DroneState.IN_TRANSIT

    def __repr__(self) -> str:
        pos = self.position.name if isinstance(self.position, Zone) else repr(self.position)
        return f"D{self.id}({pos}, {self.status.value})"
