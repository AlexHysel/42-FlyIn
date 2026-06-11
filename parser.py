from models import Graph, Hub, HubType
from pydantic import BaseModel
import re


class ParsingError(Exception):
    def __init__(self,
                 msg: str,
                 line_i: int | None,
                 line: str | None):

        super().__init__(f'\n{line_i}: {line}\n{msg}')


class Parser(BaseModel):
    line_i: int | None = None
    line: str | None = None

    def _error(self, msg: str) -> None:
        """Raises Parsingself._error"""

        raise ParsingError(msg, self.line_i, self.line)

    def parse(self, path: str) -> Graph:
        """Parses file to Graph object"""

        with open(path, "r") as file:
            lines = file.readlines()

        hubs: dict[str, Hub] = {}
        start_hub: Hub | None = None
        end_hub: Hub | None = None
        nb_drones: int | None = None

        lines = [line.strip() for line in lines]
        if not lines:
            self._error("Input file is empty")

        for i, line in enumerate(lines):
            self.line_i = i + 1
            self.line = line

            obj_type, _, data = line.partition(":")
            data = data.strip()

            match obj_type:

                case "nb_drones":
                    if nb_drones is not None:
                        self._error('more than one '
                                    '\'nb_drones\' provided.')
                    nb_drones = self._nb_drones(data)
                case "hub":
                    hub = self._hub(data)
                    if hub.name in hubs:
                        self._error(
                            f'Duplicate hub name \'{hub.name}\''
                            'found in the file.'
                        )
                    hubs[hub.name] = hub

                case "start_hub":
                    if start_hub is not None:
                        self._error('More than one start_hub provided')
                    start_hub = self._hub(data)
                    start_hub.capacity = 999999
                    hubs[start_hub.name] = start_hub

                case "end_hub":
                    if end_hub is not None:
                        self._error('More than one end_hub provided')
                    end_hub = self._hub(data)
                    end_hub.capacity = 999999
                    hubs[end_hub.name] = end_hub

                case "connection":
                    if not re.fullmatch(r'\S+-\S+( \[.*\])?', data):
                        self._error('Connection is in wrong format. '
                                    'Should be \'connection '
                                    '<hubA>-<hubB> [property=value]')

                    properties = re.findall(r'\[.*?\]|\S+', data)
                    nb_properties = len(properties)

                    meta_dict = {}

                    nameA, nameB = properties[0].split("-")

                    if nameA not in hubs.keys():
                        self._error('Connection: Hub '
                                    f'{nameA} deosnt exist.')
                    if nameB not in hubs.keys():
                        self._error('Connection: Hub '
                                    f'{nameB} doesnt exist.')
                    if hubs[nameA].has_connection(nameB):
                        self._error('Connection duplicate found.')
                    if nameA == nameB:
                        self._error('Connecting a hub to itself is forbidden')

                    # META Parsing
                    l_capacity = 1
                    if nb_properties == 2:
                        meta_dict = self._meta(properties[1])

                    for prop, val in meta_dict.items():
                        if prop == 'max_link_capacity':
                            l_capacity = int(val)
                        else:
                            self._error(f'Unknown property provided: {prop}')
                    if l_capacity < 1:
                        self._error('Connection capacity has to be >= 1')

                    if hubs[nameA].hub_type != HubType.BLOCKED:
                        if hubs[nameB].hub_type != HubType.BLOCKED:
                            hubs[nameA].connect(hubs[nameB], l_capacity)

                case _:
                    if not obj_type.startswith('#') and obj_type != '':
                        self._error('Unknown object '
                                    f'\'{obj_type}\' found.')

        if start_hub is None:
            self._error("start_hub is missing in the file.")
        if end_hub is None:
            self._error("end_hub is missing in the file.")
        if nb_drones is None:
            self._error("nb_drones is missing in the file.")

        assert nb_drones is not None
        assert start_hub is not None
        assert end_hub is not None

        graph = Graph(
            nb_drones=nb_drones, hubs=hubs,
            start=start_hub, end=end_hub
        )

        return graph

    def _hub(self, data: str) -> Hub:
        """Parses string to Hub object"""

        values = re.findall(r'\[.*?\]|\S+', data)
        nb_values = len(values)
        if nb_values not in [3, 4]:
            self._error(
                f"Wrong number of properties: {nb_values}. "
                "(should be <name> <x> <y> [metadate]).")

        # MAIN Parsing
        hub = Hub(name=values[0], x=int(values[1]), y=int(values[2]))

        # META Parsing
        if nb_values == 4:
            meta_dict = self._meta(values[3])

        for prop, val in meta_dict.items():
            match prop:
                case 'max_drones':
                    cap = int(val)
                    if cap < 1:
                        self._error('max_drones has to be >= 1')
                    hub.capacity = cap
                case 'color':
                    hub.color = val
                case 'zone':
                    if val == 'restricted':
                        hub.hub_type = HubType.RESTRICTED
                    elif val == 'normal':
                        hub.hub_type = HubType.NORMAL
                    elif val == 'priority':
                        hub.hub_type = HubType.PRIORITY
                    elif val == 'blocked':
                        hub.hub_type = HubType.BLOCKED
                    else:
                        self._error(
                            f'Wrong HubType provided: {val}. '
                            'Hub type should be one of the '
                            'following: priority/normal/'
                            'restricted/blocked'
                        )
                case _:
                    self._error(f'Unknown property provided: {prop}')
        return hub

    def _meta(self, meta: str) -> dict[str, str]:
        if not re.fullmatch(r'\[.*\]', meta):
            self._error('Meta is not within []')
        meta_dict = {}
        metas = meta[1:-1].strip(' ').split(' ')
        for m in metas:
            if not re.fullmatch(r'\S+=\S+', m):
                self._error(f'Property is in wrong format: {m} '
                            'should be [property=value]')
            prop, value = m.split('=')
            meta_dict[prop] = value
        return meta_dict

    def _nb_drones(self, data: str) -> int:
        nb_drones = int(data)
        if nb_drones < 1:
            self._error('nb_drones has to be >= 1')
        return nb_drones
