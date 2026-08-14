"""Parsers for SUMO FCD and collision outputs (xml.etree, streaming)."""

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Dict, Iterator, List, Tuple


@dataclass(frozen=True)
class ActorState:
    veh_id: str
    x: float
    y: float
    speed: float
    angle_deg: float  # SUMO: degrees, 0 = north, clockwise
    length: float = 4.5
    width: float = 2.0

    @property
    def heading_rad(self):
        """Math convention: radians, 0 = +x (east), counter-clockwise."""
        import math

        return math.radians(90.0 - self.angle_deg)

    @property
    def vx(self):
        import math

        return self.speed * math.cos(self.heading_rad)

    @property
    def vy(self):
        import math

        return self.speed * math.sin(self.heading_rad)


def iter_fcd(path) -> Iterator[Tuple[float, List[ActorState]]]:
    """Yield (time, [ActorState...]) per timestep, streaming."""
    for _, elem in ET.iterparse(path, events=("end",)):
        if elem.tag == "timestep":
            t = float(elem.get("time"))
            actors = [
                ActorState(
                    veh_id=v.get("id"),
                    x=float(v.get("x")),
                    y=float(v.get("y")),
                    speed=float(v.get("speed")),
                    angle_deg=float(v.get("angle")),
                )
                for v in elem.findall("vehicle")
            ]
            yield t, actors
            elem.clear()


def read_collisions(path) -> List[Dict]:
    """[{time, collider, victim}] from a SUMO collision-output file."""
    out = []
    try:
        tree = ET.parse(path)
    except ET.ParseError:
        return out
    for c in tree.getroot().findall("collision"):
        out.append(
            {
                "time": float(c.get("time")),
                "collider": c.get("collider"),
                "victim": c.get("victim"),
            }
        )
    return out
