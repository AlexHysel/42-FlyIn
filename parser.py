from models import Graph, Hub, HubType


class Parser:
    @staticmethod
    def parse(path: str) -> Graph:
        with open(path, "r") as file:
            lines = file.readlines()

        hubs_registry: dict[str, Hub] = {}
        connections_raw: list[str] = []
        start_hub: Hub | None = None
        end_hub: Hub | None = None

        lines = [
            line.strip()
            for line in lines
            if line.strip() and not line.strip().startswith("#")
        ]
        if not lines:
            raise Exception("Input file is empty or contains only comments.")
        if not lines[0].startswith("nb_drones"):
            raise Exception(
                "The first line of the file should specify "
                "the number of drones (e.g., 'nb_drones: 5')."
            )
        nb_drones = int(lines[0].split(":")[1].strip())
        if nb_drones < 1:
            raise Exception("The number of drones must be at least 1.")

        for line in lines[1:]:

            obj_type, _, data = line.partition(":")
            data = data.strip()

            match obj_type:

                case "hub":
                    hub = Parser.parse_hub(data)
                    if hub.name in hubs_registry:
                        raise Exception(
                            f"Duplicate hub name '{hub.name}'"
                            "found in the file."
                        )
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
                    if data in connections_raw:
                        raise Exception(f"Connection duplicate found: {data}")
                    connections_raw.append(data)

                case _:
                    raise Exception(f"Unknown object '{obj_type}' found.")

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
            if nameA not in hubs_registry.keys():
                raise Exception(f"Connecting: Hub {nameA} deosnt exist.")
            if nameB not in hubs_registry.keys():
                raise Exception(f"Connection: Hub {nameB} doesnt exist.")
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
