import heapq
import argparse
from parser import Parser, ParsingError
from models import Graph, Hub
from simulation import Simulation


COLORS = {
    "red": "\033[31m",
    "white": "\033[0m",
}


def dijkstra(graph: Graph) -> list[tuple[float, Hub]] | None:
    """Pathfinding Algorithm"""
    total_weight = {name: float("inf") for name in graph.hubs}
    total_weight[graph.start.name] = 0.0
    # (weight, link_capacity, hub)
    pq = [(0.0, 0, graph.start)]
    came_from: dict[Hub, tuple[Hub, int]] = {}

    while pq:
        weight, _, hub = heapq.heappop(pq)
        if hub == graph.end:
            path = []
            link_capacity = 0
            while hub != graph.start:
                path.append((link_capacity, hub))
                hub, link_capacity = came_from[hub]
            return list(reversed(path))

        if weight > total_weight[hub.name]:
            continue

        for neighbour, capacity in hub.connections.values():
            new_w = weight + neighbour.get_weight()
            if new_w < total_weight[neighbour.name]:
                total_weight[neighbour.name] = new_w
                came_from[neighbour] = (hub, capacity)
                heapq.heappush(pq, (new_w, -capacity, neighbour))
    return None


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("file", help="Input file with map")
    args = arg_parser.parse_args()

    try:
        parser = Parser()
        graph = parser.parse(args.file)
        path = dijkstra(graph)

        if path:
            sim = Simulation.create(graph, path)
            total_ticks = sim.run()
        else:
            print("No path found!")
    except ParsingError as e:
        print(f"{COLORS['red']}ParserError: {e}{COLORS['white']}")
