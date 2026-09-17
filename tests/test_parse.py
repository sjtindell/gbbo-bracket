import unittest
from pathlib import Path

from gbbo.parse import (
    normalize_result,
    parse_episode_table,
    parse_results_summary,
    parse_series_page,
    parse_technical_rank,
)
from gbbo.wikitext import extract_tables, slugify, strip_markup


class ParseHelpers(unittest.TestCase):
    def test_slugify(self):
        self.assertEqual(slugify("Pui Man"), "pui-man")

    def test_technical_rank(self):
        self.assertEqual(parse_technical_rank("4th"), 4)
        self.assertEqual(parse_technical_rank("align=center | 12th"), 12)

    def test_normalize_safe_and_sb(self):
        self.assertEqual(normalize_result("{{Safe}}"), "SAFE")
        self.assertEqual(normalize_result("{{Eliminated}}"), "OUT")
        self.assertEqual(normalize_result("{{Good|Star Baker}}"), "SB")
        self.assertEqual(
            normalize_result("HIGH", 'style="background:CornflowerBlue"'),
            "HIGH",
        )
        self.assertEqual(
            normalize_result("SB", 'style="background:LemonChiffon"'),
            "SB",
        )


class Series16Snippet(unittest.TestCase):
    def test_results_and_episode_from_snippet(self):
        snippet = Path(__file__).parent / "fixtures" / "series16_snippet.wiki"
        if not snippet.exists():
            self.skipTest("fixture missing")
        parsed = parse_series_page(snippet.read_text(encoding="utf-8"), 16)
        shorts = {b["baker_short"] for b in parsed["bakers"]}
        self.assertIn("Jasmine", shorts)
        self.assertTrue(any(b.get("is_winner") for b in parsed["bakers"]))
        chart = parsed["results_chart"]
        self.assertIn("Jasmine", chart)
        self.assertEqual(chart["Jasmine"][9], "WINNER")
        ep1 = [r for r in parsed["baker_episodes"] if r["episode"] == 1]
        self.assertGreaterEqual(len(ep1), 3)
        hassan = next(r for r in ep1 if r["baker_short"] == "Hassan")
        self.assertEqual(hassan["result"], "OUT")
        self.assertEqual(hassan["technical_rank"], 10)


if __name__ == "__main__":
    unittest.main()
