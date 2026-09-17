"""Occupation bins, era labels, and historical feature tables."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from statistics import mean, median
from typing import Any

STEM_RE = re.compile(
    r"scientist|engineer|doctor|nurse|surgeon|dentist|pharmacist|physicist|"
    r"chemist|software|programmer|analyst|architect|technician|paramedic|"
    r"radiographer|anaesthet|anesthet|medical|surgeon|gp\b|physician|"
    r"researcher|mathematic|statistic|developer",
    re.I,
)
CREATIVE_RE = re.compile(
    r"artist|design|actor|actress|musician|photographer|illustrat|stylist|"
    r"hairdress|drag|theatre|theater|writer|author|film|advertis|graphic|"
    r"fashion|costume",
    re.I,
)
STUDENT_RE = re.compile(r"student|graduate|undergrad|phd|doctoral", re.I)
RETIRED_RE = re.compile(r"retired|pension", re.I)
FOOD_RE = re.compile(
    r"chef|baker|cater|butcher|food|cook|patiss|restaur|hospitality|barista",
    re.I,
)
HEALTH_RE = re.compile(
    r"nhs|nurse|carer|care assistant|midwife|occupational therap|physio|"
    r"social work|discharge",
    re.I,
)


def occupation_group(occupation: str) -> str:
    text = occupation or ""
    if RETIRED_RE.search(text):
        return "retired"
    if FOOD_RE.search(text):
        return "food_adjacent"
    if STEM_RE.search(text):
        return "stem_medical"
    if STUDENT_RE.search(text):
        return "student"
    if CREATIVE_RE.search(text):
        return "creative"
    if HEALTH_RE.search(text):
        return "healthcare"
    if not text.strip():
        return "unknown"
    return "other"


def judge_era(series: int) -> str:
    if series <= 7:
        return "berry_hollywood"
    if series <= 16:
        return "leith_hollywood"
    return "lawson_hollywood"


def network_era(series: int) -> str:
    if series <= 4:
        return "bbc2"
    if series <= 7:
        return "bbc1"
    return "channel4"


def technical_percentile(rank: int | None, n: int | None) -> float | None:
    if not rank or not n or n <= 1:
        return None
    return 1.0 - (rank - 1) / (n - 1)


def summarize_history(bakers: list[dict], baker_episodes: list[dict], episodes: list[dict]) -> dict[str, Any]:
    winners = [b for b in bakers if str(b.get("is_winner")) in {"1", "True", True} or b.get("place") in {1, "1"}]
    # coerce
    def flag(row: dict, key: str) -> bool:
        v = row.get(key)
        return v in {1, "1", True, "True"}

    winners = [b for b in bakers if flag(b, "is_winner") or str(b.get("place")) == "1"]
    ages = [int(b["age"]) for b in winners if b.get("age") not in (None, "")]
    occ = Counter(occupation_group(b.get("occupation") or "") for b in winners)
    sb = []
    for b in winners:
        n = b.get("n_star_baker")
        if n not in (None, ""):
            sb.append(int(n))

    # technical stats for winners vs all
    by_id = defaultdict(list)
    for row in baker_episodes:
        by_id[row["baker_id"]].append(row)

    def median_tech_pct(baker_id: str) -> float | None:
        pcts = []
        for row in by_id.get(baker_id, []):
            pct = technical_percentile(
                int(row["technical_rank"]) if row.get("technical_rank") not in (None, "") else None,
                int(row["n_in_technical"]) if row.get("n_in_technical") not in (None, "") else None,
            )
            if pct is not None:
                pcts.append(pct)
        return median(pcts) if pcts else None

    winner_tech = [median_tech_pct(b["baker_id"]) for b in winners]
    winner_tech = [x for x in winner_tech if x is not None]
    field_tech = []
    for b in bakers:
        v = median_tech_pct(b["baker_id"])
        if v is not None:
            field_tech.append(v)

    zero_sb_winners = sum(1 for n in sb if n == 0)
    # week-1 last in technical who still won
    week1_last_winners = []
    for b in winners:
        w1 = [r for r in by_id.get(b["baker_id"], []) if str(r.get("episode")) == "1"]
        if not w1:
            continue
        rank = w1[0].get("technical_rank")
        n = w1[0].get("n_in_technical")
        if rank not in (None, "") and n not in (None, "") and int(rank) == int(n):
            week1_last_winners.append(b.get("baker_short") or b["baker_id"])

    # HIGH/LOW in week 1 vs made final
    week1 = [r for r in baker_episodes if str(r.get("episode")) == "1"]
    made_final = {b["baker_id"] for b in bakers if flag(b, "is_winner") or flag(b, "is_runner_up") or str(b.get("place")) in {"1", "2"}}
    def rate(code: str) -> tuple[int, int, float]:
        rows = [r for r in week1 if r.get("result") == code]
        n = len(rows)
        k = sum(1 for r in rows if r["baker_id"] in made_final)
        return n, k, (k / n if n else 0.0)

    # bread week star baker -> final
    bread_sb_final = {"n": 0, "final": 0}
    theme_by = {(int(e["series"]), int(e["episode"])): (e.get("theme") or "").lower() for e in episodes}
    for row in baker_episodes:
        if row.get("result") != "SB":
            continue
        theme = theme_by.get((int(row["series"]), int(row["episode"])), "")
        if "bread" in theme:
            bread_sb_final["n"] += 1
            bread_sb_final["final"] += int(row["baker_id"] in made_final)

    return {
        "n_bakers": len(bakers),
        "n_winners": len(winners),
        "winner_ages": ages,
        "winner_age_mean": round(mean(ages), 1) if ages else None,
        "winner_age_median": median(ages) if ages else None,
        "winner_age_min": min(ages) if ages else None,
        "winner_age_max": max(ages) if ages else None,
        "winner_occupation_groups": dict(occ),
        "winner_star_baker_counts": sb,
        "winner_star_baker_mean": round(mean(sb), 2) if sb else None,
        "winners_with_zero_sb": zero_sb_winners,
        "winner_median_technical_percentile_mean": round(mean(winner_tech), 3) if winner_tech else None,
        "field_median_technical_percentile_mean": round(mean(field_tech), 3) if field_tech else None,
        "week1_last_technical_winners": week1_last_winners,
        "week1_HIGH_to_final": rate("HIGH"),
        "week1_LOW_to_final": rate("LOW"),
        "week1_SB_to_final": rate("SB"),
        "week1_SAFE_to_final": rate("SAFE"),
        "bread_week_sb_to_final": bread_sb_final,
        "winners": [
            {
                "series": b.get("series"),
                "name": b.get("baker_full") or b.get("baker_short"),
                "age": b.get("age"),
                "occupation": b.get("occupation"),
                "occupation_group": occupation_group(b.get("occupation") or ""),
                "n_star_baker": b.get("n_star_baker"),
                "era": judge_era(int(b["series"])) if b.get("series") not in (None, "") else "",
            }
            for b in winners
        ],
    }
