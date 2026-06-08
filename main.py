import heapq
import argparse
from parser import Parser
from models import Graph, Hub
from simulation import Simulation

COLORS = {
    "yellow": "\033[34m",
    "red": "\033[31m",
    "green": "\033[32m",
    "white": "\033[0m",
}


def dijkstra(graph: Graph) -> list[tuple[float, Hub]] | None:
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Input file with map")
    args = parser.parse_args()

    try:
        graph = Parser.parse(args.file)
        path = dijkstra(graph)

        if path:
            sim = Simulation.create(graph, path)
            total_ticks = sim.run()
        else:
            print("No path found!")
    except Exception as e:
        print(f"{COLORS['red']}Error: {e}{COLORS['white']}")
