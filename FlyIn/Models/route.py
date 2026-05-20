from pydantic import BaseModel, Field
from FlyIn import Drone, Zone, Connection


class Move(BaseModel):
    drone: Drone
    destination: Zone | Connection
 
    def format(self) -> str:
        if isinstance(self.destination, Zone):
            return f"D{self.drone.id}-{self.destination.name}"
        else:
            conn = self.destination
            return f"D{self.drone.id}-{conn.zone_a.name}-{conn.zone_b.name}"
 
 
class Tick(BaseModel):
    turn: int
    moves: list[Move] = Field(default_factory=list)
 
    def format(self) -> str:
        return " ".join(move.format() for move in self.moves)
 
    def is_empty(self) -> bool:
        return len(self.moves) == 0
 
 
class Route(BaseModel):
    ticks: list[Tick] = Field(default_factory=list)
 
    @property
    def total_turns(self) -> int:
        return len(self.ticks)
 
    def format(self) -> str:
        return "\n".join(tick.format() for tick in self.ticks if not tick.is_empty())
 
    def __repr__(self) -> str:
        return f"Route(turns={self.total_turns})"
