from pydantic import BaseModel, Field
from enum import Enum
import argparse


class HubType(Enum):
    RESTRICTED = "restricted"
    NORMAL = "normal"
    PRIORITY = "priority"


class Hub(BaseModel):
    name: str
    x: int
    y: int
    color: str = "white"
    max_capacity: int = Field(ge=1, default=1)
    hub_type: HubType = HubType.NORMAL
    connections: dict[str, tuple["Hub", int]] = {}

    def get_weight(self) -> float:
        if self.hub_type == HubType.RESTRICTED:
            return 2.0
        elif self.hub_type == HubType.PRIORITY:
            return 0.99
        return 1.0


class Graph(BaseModel):
    nb_drones: int = Field(ge=1, default=1)
    hubs: dict[str, Hub] = {}
    start: Hub | None = None
    end: Hub | None = None

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

        graph = Graph()
        connections = []

        for line in lines[1:]:
            line = line.strip()
            object, _, data = line.partition(':')
            data = data.strip()

            match object:
                case 'nb_drones':
                    nb_drones = int(line.split(' ')[1].strip())
                    graph.nb_drones = nb_drones
                case 'hub':
                    hub = Parser.parse_hub(data)
                    graph.add_hub(hub)
                case 'connection':
                    connections.append(data)
                case 'start_hub':
                    if graph.start is not None:
                        raise Exception('More than one start hub provided.')
                    hub = Parser.parse_hub(data)
                    graph.add_hub(hub)
                    graph.start = graph.hubs[hub.name]
                case 'end_hub':
                    if graph.end is not None:
                        raise Exception('More than one end hub provided.')
                    hub = Parser.parse_hub(data)
                    graph.add_hub(hub)
                    graph.end = graph.hubs[hub.name]

        for connection in connections:
            basic, _, meta = connection.partition('[')
            metas = meta.rstrip(']').strip().split(' ')
            nameA, nameB = basic.strip(' ').split('-')
            link_capacity = 1
            if (metas):
                for smth in metas:
                    if smth:
                        obj, val = smth.split('=')
                        if obj == 'max_link_capacity':
                            link_capacity = int(val)

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
            raise Exception("hub definition misses some values "
                            "(should be [name] [x] [y]).")

        hub = Hub(name=values[0], x=int(values[1]), y=int(values[2]))

        for m in meta_values:
            m = m.strip()
            if m:
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
                            raise Exception("Wrong HubType provided ({val}). "
                                            "Hub type should be one of the "
                                            "following: priority/normal/"
                                            "restricted/blocked")
                    case _:
                        print(f"Unknown hub property provided ({obj}),"
                              "ignoring it.")
        return hub


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Input file with map")
    args = parser.parse_args()

    graph = Parser.parse(args.file)
