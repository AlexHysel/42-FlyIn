from pydantic import BaseModel, Field
from models import Graph, Hub, HubType

COLORS = {
    "yellow": "\033[33m",
    "red": "\033[31m",
    "green": "\033[32m",
    "white": "\033[0m",
    "blue": "\033[34m",
    "orange": "\033[38;5;208m",
    "cyan": "\x1b[36m",
    "lime": "\033[92m",
    "magenta": "\x1b[35m",
    "gold": "\x1b[38;5;220m",
    "purple": "\x1b[35m",
    "violet": "\033[0;35m",
    "crimson": "\033[38;2;220;20;60m",
}


class Simulation(BaseModel):
    graph: Graph
    path: list[Hub]
    nb_drones: int
    d_at_hubs: dict[str, int] = Field(default_factory=dict)
    drone_states: list[list[int | bool]] = Field(default_factory=list)
    finished_count: int = 0
    ticks: int = 0

    @classmethod
    def create(cls,
               graph: Graph,
               path_data: list[tuple[float, Hub]]
               ) -> "Simulation":
        """Constructor, returns Simulation object"""
        path = [p[1] for p in path_data]
        d_at_hubs = {name: 0 for name in graph.hubs}
        d_at_hubs[graph.start.name] = graph.nb_drones
        drone_states = [[-1, False] for _ in range(graph.nb_drones)]
        return cls(
            graph=graph,
            path=path,
            nb_drones=graph.nb_drones,
            d_at_hubs=d_at_hubs,
            drone_states=drone_states,
        )

    def run(self) -> int:
        """Runs simulation"""
        while self.finished_count < self.nb_drones:
            self.ticks += 1
            turn_output = []

            for i in range(self.nb_drones):
                
                idx, on_transit = self.drone_states[i]

                # If the drone is already at the end hub, skip it
                if idx == len(self.path) - 1:
                    continue
                
                next_idx = idx + 1
                curr = self.graph.start if idx == -1 else self.path[idx]
                next_hub = self.path[next_idx]

                if on_transit:
                    if self.d_at_hubs[next_hub.name] < next_hub.capacity:
                        self.drone_states[i][1] = False
                        #raise RuntimeError(f"Deadlock: D{i+1} must arrive at {next_hub.name} but it's full")

                # Check if the drone can move from the transit to the next hub
                if self.d_at_hubs[next_hub.name] < next_hub.capacity or next_hub == self.graph.end:
                    self.d_at_hubs[curr.name] -= 1

                    if next_hub.hub_type != HubType.RESTRICTED:
                        self.drone_states[i] = [next_idx, 0]
                        if next_hub.color == "rainbow":
                            rainbow = [
                                "red",
                                "orange",
                                "yellow",
                                "green",
                                "blue",
                                "violet",
                            ]
                            n = ""
                            for f, ch in enumerate(next_hub.name):
                                n += COLORS[rainbow[f % len(rainbow)]] + ch
                            turn_output.append(f"D{i+1}-{n}{COLORS['white']}")
                        else:
                            turn_output.append(
                                f"D{i+1}-{COLORS[next_hub.color]}"
                                f"{next_hub.name}{COLORS['white']}"
                            )
                        if next_hub == self.graph.end:
                            self.finished_count += 1
                    else:
                        self.drone_states[i][1] = True
                        self.d_at_hubs[curr.name] -= 1
                        turn_output.append(f"D{i+1}-{curr.name}-{next_hub.name}")
                    self.d_at_hubs[next_hub.name] += 1

            if turn_output:
                turn_output.sort(key=lambda x: int(x.split("-")[0][1:]))
                print(f"{' '.join(turn_output)}")
        return self.ticks
