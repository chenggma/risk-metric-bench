"""Ground-truth labeling: does this vehicle collide within the horizon?

A sample (veh, t) is positive iff the vehicle appears as collider or victim
in a logged collision at time tc with t < tc <= t + horizon. Samples at or
after the vehicle's first collision are dropped (post-crash kinematics are
not meaningful input for a warning metric).
"""

from typing import Dict, List, Set, Tuple


def collision_times_by_vehicle(collisions: List[Dict]) -> Dict[str, float]:
    """Vehicle id -> time of its FIRST collision."""
    first: Dict[str, float] = {}
    for c in collisions:
        for vid in (c["collider"], c["victim"]):
            if vid is None:
                continue
            if vid not in first or c["time"] < first[vid]:
                first[vid] = c["time"]
    return first


def label_sample(veh_id, t, first_collision: Dict[str, float], horizon):
    """Return 1 / 0, or None if the sample must be dropped (post-crash)."""
    tc = first_collision.get(veh_id)
    if tc is None:
        return 0
    if t >= tc:
        return None
    return 1 if (tc - t) <= horizon else 0
