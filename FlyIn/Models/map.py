from pydantic import BaseModel, Field
from FlyIn import Connection, Zone


class Map(BaseModel):
    nb_drones: int
    zones: dict[str, Zone]
    connections: list[Connection]
    start: Zone
    end: Zone
    zone_colors: dict[str, str] = Field(default_factory=dict)
 
    def get_zone(self, name: str) -> Zone | None:
        return self.zones.get(name)
 
    def get_connection(self, zone_a: Zone, zone_b: Zone) -> Connection | None:
        for conn in zone_a.neighbors:
            if conn.connects(zone_b):
                return conn
        return None
 
    def __repr__(self) -> str:
        return (
            f"Map(drones={self.nb_drones}, "
            f"zones={len(self.zones)}, "
            f"connections={len(self.connections)})"
        )
