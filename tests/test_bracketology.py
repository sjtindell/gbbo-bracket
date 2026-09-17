import unittest

from gbbo.bracketology import (
    ceremony_specs,
    expected_w2w_correct,
    expected_w2w_points,
    survival_value,
)
from gbbo.model import predict_week0


class ScoringMath(unittest.TestCase):
    def test_ceremony_ladder(self):
        specs = ceremony_specs()
        self.assertEqual(len(specs), 10)
        self.assertEqual([s["n_advance"] for s in specs], [11, 10, 9, 8, 7, 6, 5, 4, 3, 1])
        self.assertEqual(specs[-1]["kind"], "winner")
        self.assertEqual(specs[-1]["n_drop"], 2)

    def test_w2w_ev_prefers_highest_hazard(self):
        p = [0.20, 0.15, 0.10, 0.08, 0.08, 0.07, 0.07, 0.07, 0.06, 0.05, 0.04, 0.03]
        self.assertAlmostEqual(sum(p), 1.0)
        best = expected_w2w_correct(p, 0)
        second = expected_w2w_correct(p, 1)
        worst = expected_w2w_correct(p, 11)
        self.assertGreater(best, second)
        self.assertGreater(second, worst)
        self.assertAlmostEqual(best, 10 + 0.20)
        self.assertEqual(expected_w2w_points(p, 0, 1), best)
        self.assertEqual(expected_w2w_points(p, 0, 2), 2 * best)

    def test_survival_value_weights_late_rounds(self):
        early = [1.0] + [0.0] * 9  # survives only ceremony 1
        late = [0.0] * 8 + [1.0, 1.0]  # finalist + winner
        self.assertEqual(survival_value(early), 1.0)
        self.assertEqual(survival_value(late), 9 + 10)


class PreseasonCard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = predict_week0()
        cls.card = cls.payload["bracketology"]

    def test_w2w_two_minuses(self):
        w2w = self.card["week_to_week"]["ceremonies"]
        self.assertEqual(len(w2w), 2)
        self.assertEqual(w2w[0]["minus"], ["Gary"])
        self.assertEqual(w2w[1]["minus"], ["Connie"])
        self.assertEqual(len(w2w[0]["keep"]), 11)
        self.assertEqual(len(w2w[1]["keep"]), 10)
        self.assertNotIn("Gary", w2w[1]["keep"])

    def test_fi_nested_and_unlocked(self):
        fi = self.card["first_impression"]
        self.assertFalse(fi["lock_now"])
        self.assertEqual(fi["starts_at_elim"], 2)
        tabs = fi["tabs"]
        self.assertEqual(tabs[0]["elim_index"], 2)
        self.assertEqual(len(tabs[0]["keep"]), 10)
        self.assertEqual(len(tabs[0]["minus_this_tab"]), 2)
        keeps = [set(t["keep"]) for t in tabs]
        for earlier, later in zip(keeps, keeps[1:]):
            self.assertTrue(later.issubset(earlier))
        self.assertEqual(len(tabs[-1]["keep"]), 1)
        self.assertEqual(fi["winner"], tabs[-1]["keep"][0])
        self.assertEqual(sorted(fi["first_minus"]), ["Connie", "Gary"])

    def test_fi_elim2_is_the_first_pane(self):
        tab = self.card["first_impression"]["tabs"][0]
        self.assertEqual(tab["elim_index"], 2)
        self.assertEqual(len(tab["minus_if_still_on_all_12"]), 2)


if __name__ == "__main__":
    unittest.main()
