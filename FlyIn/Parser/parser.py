from __future__ import annotations
from FlyIn import Map, Zone, ZoneType, Connection
import re
 
 
 
class ParseError(Exception):
    pass
 
 
class Parser:
 
    @staticmethod
    def parse_file(path: str) -> Map:
        try:
            with open(path, "r") as f:
                return Parser.parse(f.read())
        except FileNotFoundError:
            raise ParseError(f"File not found: {path}")
 
    @staticmethod
    def parse(data: str) -> Map:
        nb_drones: int | None = None
        zones: dict[str, Zone] = {}
        connections: list[Connection] = []
        zone_colors: dict[str, str] = {}
        start: Zone | None = None
        end: Zone | None = None
 
        for line_num, raw_line in enumerate(data.strip().splitlines(), start=1):
            line = raw_line.strip()
 
            if not line or line.startswith("#"):
                continue
 
            if ":" not in line:
                raise ParseError(f"Line {line_num}: missing ':' in '{line}'")
 
            kind, _, rest = line.partition(":")
            kind = kind.strip()
            rest = rest.strip()
 
            if kind == "nb_drones":
                nb_drones = Parser._parse_nb_drones(rest, line_num)
 
            elif kind == "start_hub":
                zone = Parser._parse_zone(rest, line_num)
                zone.is_start = True
                zone.max_drones = 999
                zones[zone.name] = zone
                zone_colors[zone.name] = Parser._extract_color(rest)
                start = zone
 
            elif kind == "end_hub":
                zone = Parser._parse_zone(rest, line_num)
                zone.is_end = True
                zone.max_drones = 999
                zones[zone.name] = zone
                zone_colors[zone.name] = Parser._extract_color(rest)
                end = zone
 
            elif kind == "hub":
                zone = Parser._parse_zone(rest, line_num)
                zones[zone.name] = zone
                color = Parser._extract_color(rest)
                if color:
                    zone_colors[zone.name] = color
 
            elif kind == "connection":
                connections.append(Parser._parse_connection_raw(rest, line_num))
 
            else:
                raise ParseError(f"Line {line_num}: unknown type '{kind}'")
 
        if nb_drones is None:
            raise ParseError("Missing 'nb_drones'")
        if start is None:
            raise ParseError("Missing 'start_hub'")
        if end is None:
            raise ParseError("Missing 'end_hub'")
 
        built_connections = Parser._build_connections(connections, zones)
 
        return Map(
            nb_drones=nb_drones,
            zones=zones,
            connections=built_connections,
            start=start,
            end=end,
            zone_colors=zone_colors,
        )
 
    # ─────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────
 
    @staticmethod
    def _parse_nb_drones(rest: str, line_num: int) -> int:
        try:
            return int(rest.strip())
        except ValueError:
            raise ParseError(f"Line {line_num}: nb_drones must be an integer, got '{rest}'")
 
    @staticmethod
    def _parse_zone(rest: str, line_num: int) -> Zone:
        """Парсит 'name x y [zone=... color=... max_drones=...]'."""
        meta_match = re.search(r"\[(.+?)\]", rest)
        meta_str = meta_match.group(1) if meta_match else ""
        base = re.sub(r"\[.+?\]", "", rest).strip()
 
        parts = base.split()
        if len(parts) != 3:
            raise ParseError(f"Line {line_num}: expected 'name x y', got '{base}'")
 
        name = parts[0]
        try:
            x, y = int(parts[1]), int(parts[2])
        except ValueError:
            raise ParseError(f"Line {line_num}: x and y must be integers in '{base}'")
 
        meta = Parser._parse_meta(meta_str, line_num)
 
        zone_type = ZoneType.NORMAL
        if "zone" in meta:
            try:
                zone_type = ZoneType(meta["zone"])
            except ValueError:
                raise ParseError(f"Line {line_num}: unknown zone type '{meta['zone']}'")
 
        max_drones = int(meta.get("max_drones", 1))
 
        return Zone(name=name, x=x, y=y, zone_type=zone_type, max_drones=max_drones)
 
    @staticmethod
    def _parse_connection_raw(rest: str, line_num: int) -> tuple[str, str, int]:
        """Возвращает (name_a, name_b, max_link_capacity) — без объектов Zone."""
        meta_match = re.search(r"\[(.+?)\]", rest)
        meta_str = meta_match.group(1) if meta_match else ""
        base = re.sub(r"\[.+?\]", "", rest).strip()
 
        if "-" not in base:
            raise ParseError(f"Line {line_num}: connection must be 'name_a-name_b', got '{base}'")
 
        name_a, _, name_b = base.partition("-")
        name_a = name_a.strip()
        name_b = name_b.strip()
 
        meta = Parser._parse_meta(meta_str, line_num)
        max_link_capacity = int(meta.get("max_link_capacity", 1))
 
        return name_a, name_b, max_link_capacity
 
    @staticmethod
    def _build_connections(
        raw: list[tuple[str, str, int]],
        zones: dict[str, Zone],
    ) -> list[Connection]:
        """Строит Connection объекты и добавляет соседей в зоны."""
        connections = []
        for name_a, name_b, capacity in raw:
            if name_a not in zones:
                raise ParseError(f"Connection references unknown zone '{name_a}'")
            if name_b not in zones:
                raise ParseError(f"Connection references unknown zone '{name_b}'")
 
            zone_a = zones[name_a]
            zone_b = zones[name_b]
 
            conn = Connection(
                zone_a=zone_a,
                zone_b=zone_b,
                max_link_capacity=capacity,
            )
            zone_a.neighbors.append(conn)
            zone_b.neighbors.append(conn)
 
            connections.append(conn)
 
        return connections
 
    @staticmethod
    def _parse_meta(meta_str: str, line_num: int) -> dict[str, str]:
        """Парсит 'zone=restricted color=red max_drones=2' -> dict."""
        result: dict[str, str] = {}
        if not meta_str.strip():
            return result
        for pair in meta_str.split():
            if "=" not in pair:
                raise ParseError(f"Line {line_num}: invalid metadata '{pair}'")
            key, _, value = pair.partition("=")
            result[key.strip()] = value.strip()
        return result
 
    @staticmethod
    def _extract_color(rest: str) -> str:
        """Достаёт color из metadata строки."""
        meta_match = re.search(r"\[(.+?)\]", rest)
        if not meta_match:
            return ""
        meta = Parser._parse_meta(meta_match.group(1), 0)
        return meta.get("color", "")
