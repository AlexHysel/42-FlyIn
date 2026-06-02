import heapq
import argparse
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
    start: Hub | None = None
    end: Hub | None = None

    def add_hub(self, hub: Hub) -> None:
        self.hubs[hub.name] = hub

    def connect(self, hubA: Hub, hubB: Hub, cap: int) -> None:
        hubA.connections[hubB.name] = (hubB, cap)
        hubB.connections[hubA.name] = (hubA, cap)


def dijkstra(graph: Graph) -> list[tuple[int, Hub]] | None:
    distances = {name: float('inf') for name in graph.hubs}
    distances[graph.start.name] = 0.0
    pq = [(0.0, 0, graph.start, 999)]
    came_from = {}

    while pq:
        curr_w, _, u, curr_cap = heapq.heappop(pq)
        if u == graph.end:
            path = []
            curr = u
            cap = curr_cap
            while curr != graph.start:
                path.append((cap, curr))
                curr, cap = came_from[curr]
            return list(reversed(path))

        if curr_w > distances[u.name]:
            continue

        for neighbor, capacity in u.connections.values():
            new_w = curr_w + neighbor.get_weight()
            if new_w < distances[neighbor.name]:
                distances[neighbor.name] = new_w
                came_from[neighbor] = (u, capacity)
                heapq.heappush(pq, (new_w, -capacity, neighbor, capacity))
    return None


class Simulation:
    def __init__(self, graph: Graph, path_data: list[tuple[int, Hub]]):
        self.graph = graph
        self.path = [p[1] for p in path_data]
        self.nb_drones = graph.nb_drones
        self.drones_at_hubs = {name: 0 for name in graph.hubs}
        self.drones_at_hubs[graph.start.name] = self.nb_drones

        self.drone_states = [[-1, 0] for _ in range(self.nb_drones)]
        self.finished_count = 0
        self.ticks = 0

    def run(self) -> int:
        while self.finished_count < self.nb_drones:
            self.ticks += 1
            turn_output = []
            curr_hub_caps = dict(self.drones_at_hubs)

            for i in range(self.nb_drones):
                idx, transit_left = self.drone_states[i]

                if idx == len(self.path) - 1:
                    continue

                if transit_left > 0:
                    self.drone_states[i][1] -= 1
                    if self.drone_states[i][1] == 0:
                        new_idx = idx + 1
                        v = self.path[new_idx]
                        self.drone_states[i][0] = new_idx
                        self.drones_at_hubs[v.name] += 1
                        turn_output.append(f"D{i+1}-{v.name}")
                        if v == self.graph.end:
                            self.finished_count += 1
                    continue

                next_idx = idx + 1
                u = self.graph.start if idx == -1 else self.path[idx]
                v = self.path[next_idx]

                if curr_hub_caps[v.name] < v.capacity or v == self.graph.end:
                    self.drones_at_hubs[u.name] -= 1
                    travel_time = 2 if v.hub_type == HubType.RESTRICTED else 1

                    if travel_time == 1:
                        self.drones_at_hubs[v.name] += 1
                        curr_hub_caps[v.name] += 1
                        self.drone_states[i] = [next_idx, 0]
                        turn_output.append(f"D{i+1}-{v.name}")
                        if v == self.graph.end:
                            self.finished_count += 1
                    else:
                        self.drone_states[i][1] = travel_time - 1
                        curr_hub_caps[v.name] += 1

            if turn_output:
                print(f"T{self.ticks}: {' '.join(turn_output)}")
        return self.ticks


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
                        hub.capacity = int(val)
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
        return hub


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Input file with map")
    args = parser.parse_args()

    graph = Parser.parse(args.file)
    path = dijkstra(graph)

    if path:
        print(f"Path found: {' -> '.join([h.name for _, h in path])}")
        sim = Simulation(graph, path)
        total_ticks = sim.run()
        print("\n--- Simulation Result ---")
        print(f"Total drones: {graph.nb_drones}")
        print(f"Total ticks required: {total_ticks}")
    else:
        print("No path found!")
