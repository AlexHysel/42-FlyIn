from models import Graph, Hub, HubType


class Parser:
    @staticmethod
    def parse(path: str) -> Graph:
        """Parses file to Graph object"""
        with open(path, "r") as file:
            lines = file.readlines()

        hubs: dict[str, Hub] = {}
        connections_raw: list[str] = []
        start_hub: Hub | None = None
        end_hub: Hub | None = None
        nb_drones: int | None = None

        lines = [
            line.strip()
            for line in lines
        ]
        if not lines:
            raise Exception("Input file is empty")

        for i, line in enumerate(lines):

            obj_type, _, data = line.partition(":")
            data = data.strip()

            match obj_type:

                case "nb_drones":
                    if nb_drones is not None:
                        raise Exception(f'{i}: more than '
                                        'one \'nb_drones\' provided.')
                    nb_drones = int(line.split(":")[1].strip())

                case "hub":
                    hub = Parser.parse_hub(data)
                    if hub.name in hubs:
                        raise Exception(
                            f"{i}: Duplicate hub name '{hub.name}'"
                            "found in the file."
                        )
                    hubs[hub.name] = hub

                case "start_hub":
                    if start_hub is not None:
                        raise Exception(f"{i}: More than one start "
                                        "hub provided.")
                    start_hub = Parser.parse_hub(data)
                    start_hub.capacity = 999999
                    hubs[start_hub.name] = start_hub

                case "end_hub":
                    if end_hub is not None:
                        raise Exception(f"{i}: More than one end "
                                        "hub provided.")
                    end_hub = Parser.parse_hub(data)
                    end_hub.capacity = 999999
                    hubs[end_hub.name] = end_hub

                case "connection":
                    if data in connections_raw:
                        raise Exception(f"{i}: Connection "
                                        f"duplicate found: {data}")
                    basic, _, meta = data.partition("[")
                    hub_names = basic.strip().split("-")
                    if len(hub_names) != 2:
                        continue
                    connections_raw.append(basic)

                    nameA, nameB = hub_names[0].strip(), hub_names[1].strip()
                    if nameA not in hubs.keys():
                        raise Exception(f"{i}: Connecting: Hub "
                                        f"{nameA} deosnt exist.")
                    if nameB not in hubs.keys():
                        raise Exception(f"{i}: Connection: Hub "
                                        f"{nameB} doesnt exist.")
                    l_capacity = 1

                    if "[" in data:
                        metas = meta.rstrip("]").strip().split(" ")
                        for m in metas:
                            if "=" in m:
                                key, val = m.split("=")
                                if key == "max_link_capacity":
                                    l_capacity = int(val)

                    if nameA in hubs and nameB in hubs:
                        hubs[nameA].connect(hubs[nameB], l_capacity)

                case _:
                    if not obj_type.startswith('#') and obj_type != '':
                        raise Exception(f"{i}: Unknown object "
                                        f"'{obj_type}' found.")

        if start_hub is None:
            raise Exception("start_hub is missing in the file.")
        if end_hub is None:
            raise Exception("end_hub is missing in the file.")
        if nb_drones is None:
            raise Exception("nb_drones is missing in the file.")
        if nb_drones < 1:
            raise Exception("nb_drones should be at least 1.")

        graph = Graph(
            nb_drones=nb_drones, hubs=hubs,
            start=start_hub, end=end_hub
        )

        return graph

    @staticmethod
    def parse_hub(data: str) -> Hub:
        """Parses string to Hub object"""
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
