import unittest
from pathlib import Path

from gbbo.parse import (
    _short_name,
    normalize_result,
    parse_series_page,
    parse_technical_rank,
)
from gbbo.wikitext import slugify

ROOT = Path(__file__).resolve().parents[1]
WIKI = ROOT / "data" / "raw" / "wiki"


class ParseHelpers(unittest.TestCase):
    def test_slugify(self):
        self.assertEqual(slugify("Pui Man"), "pui-man")

    def test_short_name_quoted_vs_first_token(self):
        self.assertEqual(_short_name("Carol 'Pui Man' Li"), "Pui Man")
        self.assertEqual(_short_name("Pui Man"), "Pui")
        self.assertEqual(_short_name("Hassan Islam"), "Hassan")
        self.assertEqual(_short_name("Shannon Amy"), "Shannon")

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
        parsed = parse_series_page(snippet.read_text(encoding="utf-8"), 16)
        shorts = {b["baker_short"] for b in parsed["bakers"]}
        self.assertIn("Jasmine", shorts)
        self.assertIn("Toby", shorts)
        self.assertTrue(any(b.get("is_winner") for b in parsed["bakers"]))
        chart = parsed["results_chart"]
        self.assertIn("Jasmine", chart)
        self.assertEqual(chart["Jasmine"][9], "WINNER")
        ep1 = [r for r in parsed["baker_episodes"] if r["episode"] == 1]
        self.assertGreaterEqual(len(ep1), 3)
        hassan = next(r for r in ep1 if r["baker_short"] == "Hassan")
        self.assertEqual(hassan["result"], "OUT")
        self.assertEqual(hassan["technical_rank"], 10)


class MasterclassAndAliases(unittest.TestCase):
    WIKI = """
== Bakers ==
{| class="wikitable"
|-
! Baker !! Age !! Hometown !! Occupation
|-
! {{nowrap|Jairzinho Parris}}
| 51 || London || Head of Finance
|-
! Carol 'Pui Man' Li
| 51 || Essex || Bridal designer
|}

== Results summary ==
{| class="wikitable"
|-
! Baker !! 1 !! 2
|-
! Jairzeno
| SAFE
| OUT
|-
! Pui
| SAFE
| OUT
|}

== Episodes ==
=== Episode 1: Cake ===
{| class="wikitable"
|-
! Baker !! Signature !! Technical !! Showstopper !! Result
|-
! Jairzinho
| Lime
| 1st
| Cake
| {{Safe}}
|-
! Pui Man
| Roll
| 2nd
| Lion
| {{Safe}}
|}
=== Episode 2: Bread ===
{| class="wikitable"
|-
! Baker !! Signature !! Technical !! Showstopper !! Result
|-
! Jairzinho
| Loaf
| 1st
| Ship
| {{Eliminated}}
|}
=== Masterclass ===
==== Episode 1 ====
Masterclass leftover table should not replace Cake week.
{| class="wikitable"
|-
! Baker !! Result
|-
! Jairzinho
| {{Safe}}
|}
=== Episode 1 ===
Unthemed duplicate heading, also skipped.
"""

    def test_skips_masterclass_and_maps_typos(self):
        parsed = parse_series_page(self.WIKI, 12)
        ids = {b["baker_id"] for b in parsed["bakers"]}
        self.assertIn("12-jairzinho", ids)
        self.assertIn("12-pui-man", ids)
        self.assertNotIn("12-jairzeno", ids)
        self.assertNotIn("12-pui", ids)
        themes = {e["episode"]: e["theme"] for e in parsed["episodes"]}
        self.assertEqual(themes[1], "Cake")
        self.assertEqual(themes[2], "Bread")
        self.assertEqual(len(parsed["episodes"]), 2)
        ep1 = [r for r in parsed["baker_episodes"] if r["episode"] == 1]
        names = {r["baker_short"] for r in ep1}
        self.assertEqual(names, {"Jairzinho", "Pui Man"})
        jz = next(r for r in ep1 if r["baker_id"] == "12-jairzinho")
        self.assertEqual(jz["technical_rank"], 1)


@unittest.skipUnless(WIKI.exists(), "wiki cache missing")
class CachedSeriesPages(unittest.TestCase):
    def _parse(self, n: int) -> dict:
        path = WIKI / f"The_Great_British_Bake_Off_series_{n}.wikitext"
        self.assertTrue(path.exists(), path)
        return parse_series_page(path.read_text(encoding="utf-8"), n)

    def test_series_17_official_first_names(self):
        parsed = self._parse(17)
        shorts = {b["baker_short"] for b in parsed["bakers"]}
        self.assertIn("Shannon", shorts)
        self.assertNotIn("Shannon Amy", shorts)
        ids = {b["baker_id"] for b in parsed["bakers"]}
        self.assertIn("17-shannon", ids)
        self.assertNotIn("17-shannon-amy", ids)

    def test_series_16_pui_man_not_truncated(self):
        parsed = self._parse(16)
        ids = {b["baker_id"] for b in parsed["bakers"]}
        self.assertIn("16-pui-man", ids)
        self.assertNotIn("16-pui", ids)
        ep_nums = [e["episode"] for e in parsed["episodes"]]
        self.assertEqual(sorted(ep_nums), list(range(1, 11)))
        self.assertEqual(ep_nums, sorted(set(ep_nums)))

    def test_series_12_jairzinho_not_split(self):
        parsed = self._parse(12)
        ids = {b["baker_id"] for b in parsed["bakers"]}
        self.assertIn("12-jairzinho", ids)
        self.assertNotIn("12-jairzeno", ids)

    def test_series_4_to_7_no_duplicate_episodes(self):
        for n in (4, 5, 6, 7):
            parsed = self._parse(n)
            ep_nums = [e["episode"] for e in parsed["episodes"]]
            self.assertEqual(ep_nums, sorted(set(ep_nums)), f"series {n} duplicates")
            bread = [e for e in parsed["episodes"] if "bread" in (e.get("theme") or "").lower()]
            self.assertTrue(bread, f"series {n} lost bread week")


if __name__ == "__main__":
    unittest.main()
