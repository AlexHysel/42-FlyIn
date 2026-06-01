import heapq
import re


class Hub:
    def __init__(self, name, x, y, zone="normal", max_drones=None):
        self.name = name
        self.coord = (x, y)
        self.zone = zone
        self.max_capacity = max_drones
        self.connections = {}  # hub_name -> (hub, weight, max_capacity)

    def add_connection(self, hub, weight=1, max_capacity=None):
        if hub.zone == "block" or self.zone == "block":
            return
        self.connections[hub.name] = (hub, weight, max_capacity)

    def __repr__(self):
        return f"Hub({self.name})"


class Graph:
    def __init__(self):
        self.hubs: dict[str, Hub] = {}
        self.start: Hub | None = None
        self.end: Hub | None = None
        self.nb_drones: int | None = None

    def add_hub(self, hub):
        self.hubs[hub.name] = hub

    def get_hub(self, name):
        return self.hubs.get(name)

    def connect(self, h1, h2, max_capacity=None):
        hub1 = self.hubs[h1]
        hub2 = self.hubs[h2]

        weight1 = self._weight_for_zone(hub2)
        weight2 = self._weight_for_zone(hub1)

        hub1.add_connection(hub2, weight1, max_capacity)
        hub2.add_connection(hub1, weight2, max_capacity)

    def _weight_for_zone(self, hub):
        if hub.zone == "restricted":
            return 2
        return 1

    def dijkstra(self):
        pq = []
        heapq.heappush(pq, (0, self.start.name, []))
        visited = {}

        while pq:
            dist, current_name, path = heapq.heappop(pq)

            if current_name in visited:
                continue

            visited[current_name] = dist
            path = path + [current_name]

            if current_name == self.end.name:
                return path

            hub = self.hubs[current_name]

            for neigh_name, (neigh, weight, _) in hub.connections.items():

                priority_bias = -0.01 if neigh.zone == "priority" else 0
                new_dist = dist + weight + priority_bias

                heapq.heappush(pq, (new_dist, neigh_name, path))

        return None


class Parser:
    HUB_PATTERN = re.compile(r"(start_hub|end_hub|hub): (\w+) (-?\d+) (-?\d+)(?: \[(.*)\])?")
    CONN_PATTERN = re.compile(r"connection: (\w+)-(\w+)(?: \[(.*)\])?")

    def __init__(self, file_path):
        self.file_path = file_path

    def parse_metadata(self, metadata):
        zone = "normal"
        max_drones = None
        max_link_capacity = None

        if not metadata:
            return zone, max_drones, max_link_capacity

        parts = metadata.split()

        for p in parts:
            if p.startswith("zone="):
                zone = p.split("=")[1]
            if p.startswith("max_drones="):
                max_drones = int(p.split("=")[1])
            if p.startswith("max_link_capacity="):
                max_link_capacity = int(p.split("=")[1])

        return zone, max_drones, max_link_capacity

    def parse(self):
        graph = Graph()

        with open(self.file_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                hub_match = self.HUB_PATTERN.match(line)
                conn_match = self.CONN_PATTERN.match(line)
                if line.startswith("nb_drones"):
                    group = line.split(":")
                    graph.nb_drones = int(group[1])
                if hub_match:
                    hub_type, name, x, y, meta = hub_match.groups()
                    zone, max_drones, _ = self.parse_metadata(meta)

                    hub = Hub(name, int(x), int(y), zone, max_drones)
                    graph.add_hub(hub)

                    if hub_type == "start_hub":
                        graph.start = hub
                    elif hub_type == "end_hub":
                        graph.end = hub

                elif conn_match:
                    h1, h2, meta = conn_match.groups()
                    _, _, max_link_capacity = self.parse_metadata(meta)
                    graph.connect(h1, h2, max_link_capacity)

        return graph

class DroneSimulator:

    def __init__(self, graph, path, nb_drones):
        self.graph = graph
        self.path = path
        self.nb_drones = nb_drones

        self.start = path[0]
        self.end = path[-1]

        self.turn = 1

        self.hubs = {h: [] for h in path}
        self.links = {}  # (h1,h2) -> [(drone1),(drone2)]

        self.finished = set()

        for i in range(1, nb_drones + 1):
            self.hubs[self.start].append(i)

    def hub_capacity(self, name):
        if name in (self.start, self.end):
            return float("inf")

        hub = self.graph.get_hub(name)
        return hub.max_capacity if hub.max_capacity else 1

    def link_capacity(self, h1, h2):
        hub = self.graph.get_hub(h1)
        conn = hub.connections[h2]

        return conn[2] if conn[2] else 1
    
    def incoming_link_count(self, hub_name):
        count = 0
        for (h1, h2), drones in self.links.items():
            if h2 == hub_name:
                count += len(drones)
        return count

    def simulate(self):

        while len(self.finished) < self.nb_drones:

            actions = []
            moved = set()

            for edge in list(self.links.keys()):

                h1, h2 = edge
                waiting = self.links[edge]

                cap = self.hub_capacity(h2)

                new_wait = []

                for drone in waiting:
                    incoming = self.incoming_link_count(h2)
                    if len(self.hubs[h2]) <= cap:
                        self.hubs[h2].append(drone)
                        actions.append(f"D{drone}-{h2}")
                        moved.add(drone)

                        if h2 == self.end:
                            self.finished.add(drone)

                    else:
                        new_wait.append((drone))

                if new_wait:
                    self.links[edge] = new_wait
                else:
                    del self.links[edge]

            for i in reversed(range(len(self.path) - 1)):

                h1 = self.path[i]
                h2 = self.path[i + 1]
                
                hub2 = self.graph.get_hub(h2)

                hub_cap = self.hub_capacity(h2)
                link_cap = self.link_capacity(h1, h2)

                for drone in list(self.hubs[h1]):

                    if drone in moved:
                        continue

                    if hub2.zone == "restricted":

                        edge = (h1, h2)
                        cur = self.links.get(edge, [])
                        incoming = self.incoming_link_count(h2)
                        if len(cur) >= link_cap:
                            continue
                        if incoming >= hub_cap:
                            continue
                        self.hubs[h1].remove(drone)

                        self.links.setdefault(edge, []).append((drone))

                        actions.append(f"D{drone}-{h1}-{h2}")
                        moved.add(drone)
                    else:

                        if len(self.hubs[h2]) >= hub_cap:
                            continue

                        self.hubs[h1].remove(drone)
                        self.hubs[h2].append(drone)

                        actions.append(f"D{drone}-{h2}")
                        moved.add(drone)

                        if h2 == self.end:
                            self.finished.add(drone)

            print(f"T{self.turn}: {' '.join(actions)}")
            print(f"")

            self.turn += 1

if __name__ == "__main__":
    parser = Parser("./maps/challenger/01_the_impossible_dream.txt")
    # parser = Parser("./maps/easy/01_linear_path.txt")
    # parser = Parser("./maps/medium/02_circular_loop.txt")
    graph = parser.parse()

    path = graph.dijkstra()
    simulator = DroneSimulator(graph, path, graph.nb_drones)
    simulator.simulate()

    print("Shortest route:")
    print(" -> ".join(path))