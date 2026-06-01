from pydantic import BaseModel, Field
from enum import Enum
import re


class HubType(Enum):
    RESTRICTED = "restricted"
    NORMAL = "normal"
    PRIORITY = "priority"


class Hub(BaseModel):
    name: str
    x: int
    y: int
    color: str
    max_capacity: int
    hub_type: HubType = HubType.NORMAL
    connections: dict[str, tuple["Hub", int]] = {}

    def get_weight(self) -> float:
        if self.hub_type == HubType.RESTRICTED:
            return 2.0
        elif self.hub_type == HubType.PRIORITY:
            return 0.99
        return 1.0


class Graph(BaseModel):
    drones_num: int = Field(ge=1)
    hubs: dict[str, Hub] = {}
    start: Hub
    end: Hub

    def add_hub(self, hub: Hub) -> None:
        self.hubs[hub.name] = hub

    def connect(self, hubA: Hub, hubB: Hub, link_capacity: int) -> None:
        hubA.connections[hubB.name] = (hubB, link_capacity)
        hubB.connections[hubA.name] = (hubA, link_capacity)


class Drone(BaseModel):
    name: str


class Parser:
    
    @staticmethod
    def parse(path: str) -> Graph:
        with open(path, 'r') as file:
            lines = file.readlines()

        if not lines[0].startswith('nb_drones:'):
            raise Exception('First line of the file must be \'nb_drones: [number]\'')

        nb_drones = int(lines[0].split(' ')[1].strip())
        graph = Graph(nb_drones)
        connections = []

        for line in lines[1:]:
            line = line.strip()
            object, _, data = line.partition(':')

            match object:
                case 'hub':
                    graph.add_hub(Parser.parse_hub(data))
                case 'connection':
                    connections.append(data)
                case 'start_hub':
                    if graph.start is not None:
                        raise Exception('More than one start hub provided.')
                    graph.start = Parser.parse_hub(data)
                case 'end_hub':
                    if graph.start is not None:
                        raise Exception('More than one end hub provided.')
                    graph.end = Parser.parse_hub(data)
        
        for connection in connections:
            basic, _, meta = connection.partition('[')
            meta = meta.rstrip(']').strip().split(' ')
            nameA, nameB = basic.split('-')
            if (meta):
                for smth in meta.split(' '):
                    obj, val = smth.split('-')
                    if obj == 'max_link_capacity':
                        link_capacity = int(val)
            else:
                link_capacity = 1
            hubA = graph.hubs[nameA]
            hubB = graph.hubs[nameB]
            graph.connect(hubA, hubB, link_capacity)

        return graph
    
    @staticmethod
    def parse_hub(data: str) -> Hub:
        basic, _, meta = data.partition('[')
        values = basic.split(' ')
        meta_values = meta.rstrip(']').strip().split(' ')
        if (len(values) < 3):
            raise Exception("hub definition misses some values (less than 3, should be [name] [x] [y]).")
        hub = Hub()

        hub.name = values[0]
        hub.x = int(values[1])
        hub.y = int(values[2])

        for m in meta_values:
            obj, val = m.split('=')
            match obj:
                case 'max_drones':
                    hub.max_capacity = int(val)
                case 'color':
                    hub.color = val
                case 'zone':
                    if val == 'restricted':
                        hub.hub_type = HubType.RESTRICTED
                    elif val == 'normal':
                        hub.hub_type = HubType.NORMAL
                    elif val == 'priority':
                        hub.hub_type = HubType.PRIORITY
                    elif val != 'blocked':
                        raise Exception("Wrong HubType provided ({val}). hub type should be one of the following: priority/normal/restricted/blocked")
