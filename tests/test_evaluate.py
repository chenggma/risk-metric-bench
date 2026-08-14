import math
import unittest

from bench.evaluate import auroc, lead_times, median, percentile


class TestAuroc(unittest.TestCase):
    def test_perfect_separation(self):
        labels = [0, 0, 0, 1, 1]
        scores = [0.1, 0.2, 0.3, 0.8, 0.9]
        self.assertAlmostEqual(auroc(labels, scores), 1.0, places=12)

    def test_perfect_inversion(self):
        labels = [1, 1, 0, 0]
        scores = [0.1, 0.2, 0.8, 0.9]
        self.assertAlmostEqual(auroc(labels, scores), 0.0, places=12)

    def test_all_ties_is_half(self):
        labels = [0, 1, 0, 1]
        scores = [0.5, 0.5, 0.5, 0.5]
        self.assertAlmostEqual(auroc(labels, scores), 0.5, places=12)

    def test_known_mixed_case(self):
        # pairs: (0.1,0) (0.4,1) (0.35,0) (0.8,1) -> concordant 3/4 + ...
        labels = [0, 1, 0, 1]
        scores = [0.1, 0.4, 0.35, 0.8]
        # positive scores 0.4, 0.8 vs negatives 0.1, 0.35: all 4 pairs won
        self.assertAlmostEqual(auroc(labels, scores), 1.0, places=12)

    def test_single_class_nan(self):
        self.assertTrue(math.isnan(auroc([0, 0], [0.1, 0.2])))


class TestPercentileMedian(unittest.TestCase):
    def test_nearest_rank(self):
        vals = list(range(1, 101))  # 1..100
        self.assertEqual(percentile(vals, 95.0), 95)
        self.assertEqual(percentile(vals, 100.0), 100)

    def test_median_odd_even(self):
        self.assertEqual(median([3, 1, 2]), 2)
        self.assertEqual(median([4, 1, 2, 3]), 2.5)
        self.assertTrue(math.isnan(median([])))


class TestLeadTimes(unittest.TestCase):
    def _rows(self):
        # One vehicle: samples at t=0..4, collision-bound (label 1 at t=3,4).
        rows = []
        scores = {0: 0.1, 1: 0.2, 2: 0.9, 3: 0.95, 4: 0.99}
        for t in range(5):
            rows.append(
                {
                    "seed": 1,
                    "veh": "a",
                    "t": float(t),
                    "label": 1 if t >= 3 else 0,
                    "m": scores[t],
                }
            )
        return rows

    def test_first_alarm_defines_lead(self):
        rows = self._rows()
        leads = lead_times(rows, "m", threshold=0.85)
        # alarm at t=2, last positive sample at t=4 -> lead 2.0
        self.assertEqual(leads, [2.0])

    def test_threshold_never_crossed_no_lead(self):
        rows = self._rows()
        self.assertEqual(lead_times(rows, "m", threshold=2.0), [])

    def test_non_collision_vehicle_ignored(self):
        rows = [
            {"seed": 1, "veh": "b", "t": 0.0, "label": 0, "m": 5.0},
        ]
        self.assertEqual(lead_times(rows, "m", threshold=0.1), [])


if __name__ == "__main__":
    unittest.main()
