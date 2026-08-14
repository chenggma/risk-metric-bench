import unittest

from bench.label import collision_times_by_vehicle, label_sample


COLLISIONS = [
    {"time": 100.0, "collider": "a", "victim": "b"},
    {"time": 150.0, "collider": "a", "victim": "c"},
]


class TestFirstCollision(unittest.TestCase):
    def test_first_time_wins(self):
        first = collision_times_by_vehicle(COLLISIONS)
        self.assertEqual(first["a"], 100.0)
        self.assertEqual(first["b"], 100.0)
        self.assertEqual(first["c"], 150.0)

    def test_none_victim_ignored(self):
        first = collision_times_by_vehicle(
            [{"time": 5.0, "collider": "x", "victim": None}]
        )
        self.assertEqual(first, {"x": 5.0})


class TestLabelSample(unittest.TestCase):
    def setUp(self):
        self.first = collision_times_by_vehicle(COLLISIONS)

    def test_inside_window_positive(self):
        self.assertEqual(label_sample("a", 96.0, self.first, 5.0), 1)

    def test_window_edge_positive(self):
        self.assertEqual(label_sample("a", 95.0, self.first, 5.0), 1)

    def test_before_window_negative(self):
        self.assertEqual(label_sample("a", 94.9, self.first, 5.0), 0)

    def test_at_or_after_collision_dropped(self):
        self.assertIsNone(label_sample("a", 100.0, self.first, 5.0))
        self.assertIsNone(label_sample("a", 120.0, self.first, 5.0))

    def test_uninvolved_vehicle_negative(self):
        self.assertEqual(label_sample("z", 99.0, self.first, 5.0), 0)


if __name__ == "__main__":
    unittest.main()
