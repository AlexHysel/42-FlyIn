*This project has been created as part of the 42 curriculum by afomin.*

# Fly-in — Drones are interesting

## Description

A drone routing simulator that moves a fleet of drones from a start hub to an end hub across a weighted graph, minimizing the total number of simulation turns.

Each hub has a type that affects movement cost and capacity. Connections between hubs can have throughput limits. The simulation runs turn by turn — every drone that can move does so simultaneously, respecting all capacity constraints.

**Hub types:**
- `normal` — 1 turn to enter (default)
- `priority` — 1 turn to enter, preferred by pathfinding
- `restricted` — 2 turns to enter, drone occupies the connection during transit
- `blocked` — inaccessible, ignored by the parser

## Instructions

### Installation

```bash
uv sync
```

### Running

```bash
uv run python main.py <map_file>
```

Example:

```bash
uv run python main.py maps/easy/01_linear_path.txt
```

### Linting

```bash
make lint
```

### Output format

Each line represents one simulation turn. Each movement follows the format `D<ID>-<zone>` or `D<ID>-<connection>` for drones in transit toward a restricted zone. Drones that do not move are omitted.

```
D1-waypoint1
D1-waypoint2 D2-waypoint1
D1-goal D2-waypoint2
D2-goal
```

## Algorithm

Pathfinding is done with **Dijkstra's algorithm** using a min-heap (`heapq`). The graph is traversed from the start hub, always expanding the node with the lowest accumulated cost. The cost of entering a hub is determined by its type — restricted hubs cost 2, priority hubs cost 0.99, normal hubs cost 1. This naturally makes the algorithm prefer priority paths when available.

The path is reconstructed using a `came_from` dictionary that tracks which hub each node was reached from.

**Simulation** runs the found path as a conveyor — drones are dispatched one by one as capacity allows. Each turn, every drone that can move attempts to advance to the next hub. If the destination is at capacity, the drone waits. For restricted hubs, the drone occupies the connection for 1 turn before arriving.

**Drone state** is tracked as `[path_index, transit_remaining]` — where `path_index` is the drone's current position in the path and `transit_remaining` counts how many turns remain before arriving at a restricted hub.

## Visual Representation

Terminal output lists all drone movements per turn in a compact, readable format. Drone IDs are sorted numerically within each turn for clarity. The simulation prints only turns where at least one drone moves, keeping the output clean.

## Performance

| Map | Drones | Target | Result |
|-----|--------|--------|--------|
| Easy — Linear path | 2 | ≤ 6 | ✓ |
| Easy — Simple fork | 4 | ≤ 8 | ✓ |
| Easy — Basic capacity | 4 | ≤ 6 | ✓ |
| Medium — Dead end trap | 5 | ≤ 12 | ✓ |
| Medium — Circular loop | 6 | ≤ 15 | ✓ |
| Medium — Priority puzzle | 5 | ≤ 12 | ✓ |
| Hard — Maze nightmare | 8 | ≤ 30 | ✓ |
| Hard — Capacity hell | 12 | ≤ 35 | ✓ |
| Hard — Ultimate challenge | 15 | ≤ 45 | ✓ |
| Challenger — Impossible Dream | 25 | ≤ 45 | 67 |

## Resources

- [Dijkstra's algorithm — Wikipedia](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)
- [Python heapq documentation](https://docs.python.org/3/library/heapq.html)
- [Pydantic documentation](https://docs.pydantic.dev)

**AI usage:** Claude (Anthropic) was used throughout the project for architectural discussions, understanding algorithm mechanics (Dijkstra, heaps, graph representation), debugging parser and simulation logic, and code review. All code was written manually — AI was used as a learning and discussion tool, not for code generation.
