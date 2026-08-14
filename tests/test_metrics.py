import unittest

from bench.metrics import TTS_FLOOR, inv_ttc, neg_tts_margin, pora_score
from bench.xmlio import ActorState


def actor(veh_id, x, y, speed, angle_deg):
    return ActorState(veh_id, x, y, speed, angle_deg)


EGO_EAST = actor("ego", 0.0, 0.0, 10.0, 90.0)  # driving east


class TestInvTtc(unittest.TestCase):
    def test_no_foes_zero(self):
        self.assertEqual(inv_ttc(EGO_EAST, []), 0.0)

    def test_closer_foe_scores_higher(self):
        near = actor("n", 30.0, 0.0, 0.0, 90.0)
        far = actor("f", 90.0, 0.0, 0.0, 90.0)
        self.assertGreater(inv_ttc(EGO_EAST, [near]), inv_ttc(EGO_EAST, [far]))

    def test_diverging_zero(self):
        behind = actor("b", -50.0, 0.0, 0.0, 90.0)
        self.assertEqual(inv_ttc(EGO_EAST, [behind]), 0.0)

    def test_capped(self):
        touching = actor("t", 3.5, 0.0, 0.0, 90.0)
        self.assertLessEqual(inv_ttc(EGO_EAST, [touching]), 10.0)


class TestNegTts(unittest.TestCase):
    def test_no_conflict_floor(self):
        self.assertEqual(neg_tts_margin(EGO_EAST, []), TTS_FLOOR)

    def test_imminent_beats_distant(self):
        near = actor("n", 20.0, 0.0, 0.0, 90.0)
        far = actor("f", 120.0, 0.0, 0.0, 90.0)
        self.assertGreater(
            neg_tts_margin(EGO_EAST, [near]), neg_tts_margin(EGO_EAST, [far])
        )


class TestPora(unittest.TestCase):
    def test_no_foes_zero(self):
        self.assertEqual(pora_score(EGO_EAST, []), 0.0)

    def test_bounded_unit_interval(self):
        crossing = actor("c", 15.0, -20.0, 12.0, 0.0)  # heading north
        s = pora_score(EGO_EAST, [crossing])
        self.assertGreaterEqual(s, 0.0)
        self.assertLessEqual(s, 1.0 + 1e-9)

    def test_conflict_scores_higher_than_clear(self):
        crossing = actor("c", 15.0, -15.0, 12.0, 0.0)  # will meet ego path
        parallel = actor("p", 0.0, 30.0, 10.0, 90.0)  # same direction, offset
        self.assertGreater(
            pora_score(EGO_EAST, [crossing]), pora_score(EGO_EAST, [parallel])
        )


if __name__ == "__main__":
    unittest.main()
