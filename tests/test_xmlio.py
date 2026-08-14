import math
import os
import tempfile
import unittest

from bench.xmlio import ActorState, iter_fcd, read_collisions


FCD = """<fcd-export>
  <timestep time="0.00">
    <vehicle id="v1" x="10.0" y="0.0" speed="5.0" angle="90.0"/>
  </timestep>
  <timestep time="0.50">
    <vehicle id="v1" x="12.5" y="0.0" speed="5.0" angle="90.0"/>
    <vehicle id="v2" x="0.0" y="20.0" speed="8.0" angle="180.0"/>
  </timestep>
</fcd-export>
"""

COLLISIONS = """<collisions>
  <collision time="42.5" collider="v1" victim="v2" type="collision"/>
</collisions>
"""


def _tmp(content, suffix=".xml"):
    f = tempfile.NamedTemporaryFile(
        "w", suffix=suffix, delete=False, encoding="utf8"
    )
    f.write(content)
    f.close()
    return f.name


class TestActorState(unittest.TestCase):
    def test_sumo_angle_east_is_heading_zero(self):
        a = ActorState("v", 0, 0, 10.0, angle_deg=90.0)
        self.assertAlmostEqual(a.heading_rad, 0.0, places=12)
        self.assertAlmostEqual(a.vx, 10.0, places=9)
        self.assertAlmostEqual(a.vy, 0.0, places=9)

    def test_sumo_angle_north(self):
        a = ActorState("v", 0, 0, 10.0, angle_deg=0.0)
        self.assertAlmostEqual(a.heading_rad, math.pi / 2.0, places=12)
        self.assertAlmostEqual(a.vy, 10.0, places=9)

    def test_sumo_angle_south(self):
        a = ActorState("v", 0, 0, 6.0, angle_deg=180.0)
        self.assertAlmostEqual(a.vy, -6.0, places=9)


class TestIterFcd(unittest.TestCase):
    def test_stream(self):
        path = _tmp(FCD)
        try:
            steps = list(iter_fcd(path))
        finally:
            os.unlink(path)
        self.assertEqual(len(steps), 2)
        t0, actors0 = steps[0]
        self.assertEqual(t0, 0.0)
        self.assertEqual(len(actors0), 1)
        self.assertEqual(actors0[0].veh_id, "v1")
        t1, actors1 = steps[1]
        self.assertEqual(len(actors1), 2)
        self.assertEqual(actors1[1].y, 20.0)


class TestReadCollisions(unittest.TestCase):
    def test_parse(self):
        path = _tmp(COLLISIONS)
        try:
            out = read_collisions(path)
        finally:
            os.unlink(path)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["time"], 42.5)
        self.assertEqual(out[0]["collider"], "v1")
        self.assertEqual(out[0]["victim"], "v2")

    def test_malformed_returns_empty(self):
        path = _tmp("<collisions><collision")
        try:
            self.assertEqual(read_collisions(path), [])
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
