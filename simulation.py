from pydantic import BaseModel, Field
from main import Graph, Hub, HubType


class Simulation(BaseModel):
    graph: Graph
    path: list[Hub]
    nb_drones: int
    d_at_hubs: dict[str, int] = Field(default_factory=dict)
    drone_states: list[list[int]] = Field(default_factory=list)
    finished_count: int = 0
    ticks: int = 0

    @classmethod
    def create(cls,
               graph: Graph,
               path_data: list[tuple[float, Hub]]
               ) -> "Simulation":
        path = [p[1] for p in path_data]
        d_at_hubs = {name: 0 for name in graph.hubs}
        d_at_hubs[graph.start.name] = graph.nb_drones
        drone_states = [[-1, 0] for _ in range(graph.nb_drones)]
        return cls(
            graph=graph,
            path=path,
            nb_drones=graph.nb_drones,
            d_at_hubs=d_at_hubs,
            drone_states=drone_states,
        )

    def run(self) -> int:
        while self.finished_count < self.nb_drones:
            self.ticks += 1
            turn_output = []

            for i in range(self.nb_drones):
                idx, transit_left = self.drone_states[i]

                # If the drone is already at the end hub, skip it
                if idx == len(self.path) - 1:
                    continue

                # If the drone is in transit, decrease the transit time and check if it arrives at the next hub
                if transit_left > 0:
                    self.drone_states[i][1] -= 1
                    if self.drone_states[i][1] == 0:
                        new_idx = idx + 1
                        v = self.path[new_idx]
                        self.drone_states[i][0] = new_idx
                        turn_output.append(f"D{i+1}-{v.name}")
                        if v == self.graph.end:
                            self.finished_count += 1
                    continue
                
                next_idx = idx + 1
                u = self.graph.start if idx == -1 else self.path[idx]
                v = self.path[next_idx]

                # Check if the drone can move from the transit to the next hub
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
                print(f"{' '.join(turn_output)}")
        return self.ticks