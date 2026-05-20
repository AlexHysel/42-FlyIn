from enum import Enum


class DroneState(Enum):
    WAITING = "waiting"
    DELIVERED = "delivered"
    IN_TRANSIT = "in_transit"