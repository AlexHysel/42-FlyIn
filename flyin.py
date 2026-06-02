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
    start: Hub
    end: Hub

    def add_hub(self, hub: Hub) -> None:
        self.hubs[hub.name] = hub

    def connect(self, hubA: Hub, hubB: Hub, cap: int) -> None:
        hubA.connections[hubB.name] = (hubB, cap)
        hubB.connections[hubA.name] = (hubA, cap)


def dijkstra(graph: Graph) -> list[tuple[int, Hub]] | None:
    distances = {name: float("inf") for name in graph.hubs}
    distances[graph.start.name] = 0.0
    pq = [(0.0, 0, graph.start, 999)]
    came_from: dict[Hub, tuple[Hub, int]] = {}

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
        self.d_at_hubs = {name: 0 for name in graph.hubs}
        self.d_at_hubs[graph.start.name] = self.nb_drones

        self.drone_states = [[-1, 0] for _ in range(self.nb_drones)]
        self.finished_count = 0
        self.ticks = 0

    def run(self) -> int:
        while self.finished_count < self.nb_drones:
            self.ticks += 1
            turn_output = []

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
                        self.d_at_hubs[v.name] += 1
                        turn_output.append(f"D{i+1}-{v.name}")
                        if v == self.graph.end:
                            self.finished_count += 1
                    continue

                next_idx = idx + 1
                u = self.graph.start if idx == -1 else self.path[idx]
                v = self.path[next_idx]

                if self.d_at_hubs[v.name] < v.capacity or v == self.graph.end:
                    self.d_at_hubs[u.name] -= 1

                    travel_time = 2 if v.hub_type == HubType.RESTRICTED else 1

                    if travel_time == 1:
                        self.d_at_hubs[v.name] += 1
                        self.drone_states[i] = [next_idx, 0]
                        turn_output.append(f"D{i+1}-{v.name}")
                        if v == self.graph.end:
                            self.finished_count += 1
                    else:
                        self.drone_states[i][1] = travel_time - 1
                        self.d_at_hubs[v.name] += 1

            if turn_output:
                turn_output.sort(key=lambda x: int(x.split("-")[0][1:]))
                print(f"T{self.ticks}: {' '.join(turn_output)}")
        return self.ticks


class Parser:
    @staticmethod
    def parse(path: str) -> Graph:
        with open(path, "r") as file:
            lines = file.readlines()

        hubs_registry: dict[str, Hub] = {}
        connections_raw: list[str] = []
        nb_drones = 1
        start_hub: Hub | None = None
        end_hub: Hub | None = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            obj_type, _, data = line.partition(":")
            data = data.strip()

            match obj_type:
                case "nb_drones":
                    parts = line.split(" ")
                    if len(parts) > 1:
                        nb_drones = int(parts[1].strip())

                case "hub":
                    hub = Parser.parse_hub(data)
                    hubs_registry[hub.name] = hub

                case "start_hub":
                    if start_hub is not None:
                        raise Exception("More than one start hub provided.")
                    start_hub = Parser.parse_hub(data)
                    hubs_registry[start_hub.name] = start_hub

                case "end_hub":
                    if end_hub is not None:
                        raise Exception("More than one end hub provided.")
                    end_hub = Parser.parse_hub(data)
                    hubs_registry[end_hub.name] = end_hub

                case "connection":
                    connections_raw.append(data)

        if start_hub is None or end_hub is None:
            raise Exception("Start or End hub is missing in the file.")

        graph = Graph(
            nb_drones=nb_drones, hubs=hubs_registry,
            start=start_hub, end=end_hub
        )

        for conn_data in connections_raw:
            basic, _, meta = conn_data.partition("[")
            names = basic.strip().split("-")
            if len(names) != 2:
                continue

            nameA, nameB = names[0].strip(), names[1].strip()
            l_capacity = 1

            if "[" in conn_data:
                metas = meta.rstrip("]").strip().split(" ")
                for m in metas:
                    if "=" in m:
                        key, val = m.split("=")
                        if key == "max_link_capacity":
                            l_capacity = int(val)

            if nameA in graph.hubs and nameB in graph.hubs:
                graph.connect(graph.hubs[nameA], graph.hubs[nameB], l_capacity)

        return graph

    @staticmethod
    def parse_hub(data: str) -> Hub:
        basic, _, meta = data.partition("[")
        values = basic.split(" ")
        meta_values = meta.rstrip("]").strip().split(" ")
        if len(values) < 3:
            raise Exception(
                "hub definition misses some values "
                "(should be [name] [x] [y])."
            )

        hub = Hub(name=values[0], x=int(values[1]), y=int(values[2]))

        for m in meta_values:
            m = m.strip()
            if m:
                obj, val = m.split("=")
                match obj:
                    case "max_drones":
                        hub.capacity = int(val)
                    case "color":
                        hub.color = val
                    case "zone":
                        if val == "restricted":
                            hub.hub_type = HubType.RESTRICTED
                        elif val == "normal":
                            hub.hub_type = HubType.NORMAL
                        elif val == "priority":
                            hub.hub_type = HubType.PRIORITY
                        elif val != "blocked":
                            raise Exception(
                                "Wrong HubType provided ({val}). "
                                "Hub type should be one of the "
                                "following: priority/normal/"
                                "restricted/blocked"
                            )
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
