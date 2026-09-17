"""Build canonical CSVs from Wikipedia series pages + S17 seed."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from gbbo.csvutil import write_csv
from gbbo.features import judge_era, network_era, occupation_group, summarize_history
from gbbo.parse import parse_series_page
from gbbo.paths import PROCESSED, ensure_dirs
from gbbo.s17 import BAKERS as S17_BAKERS
from gbbo.s17 import S17
from gbbo.wiki import fetch_wikitext, series_title

SERIES_FIELDS = [
    "series",
    "year",
    "n_episodes",
    "n_bakers",
    "network",
    "channel_era",
    "judge_era",
    "hosts",
    "judges",
    "winner_name",
    "runner_up_names",
    "source_url",
]
BAKER_FIELDS = [
    "baker_id",
    "series",
    "baker_full",
    "baker_short",
    "age",
    "occupation",
    "occupation_group",
    "hometown",
    "place",
    "elimination_episode",
    "is_winner",
    "is_runner_up",
    "n_star_baker",
    "n_technical_win",
    "pronouns",
    "years_baking_est",
    "precision_job",
    "chaos_self_describe",
    "heritage_flavours",
    "visual_showstopper",
    "backup_baker",
    "savoury_bias",
    "started_late",
    "bio_url",
    "name_source",
    "notes",
]
EPISODE_FIELDS = [
    "series",
    "episode",
    "title",
    "theme",
    "technical_set_by",
    "n_bakers_start",
    "n_eliminated",
    "n_star_baker",
    "no_elimination_flag",
    "double_elimination_flag",
]
BE_FIELDS = [
    "series",
    "episode",
    "baker_id",
    "baker_short",
    "result",
    "technical_rank",
    "n_in_technical",
    "signature_name",
    "showstopper_name",
    "handshake_signature",
    "handshake_showstopper",
    "appeared",
]
SOURCE_FIELDS = [
    "source_id",
    "name",
    "url",
    "retrieved_at",
    "series_from",
    "series_to",
    "fields",
    "method",
    "license",
    "tos_risk",
    "notes",
]


def ingest_history(through: int = 17, *, force: bool = False) -> dict[str, Any]:
    ensure_dirs()
    series_rows = []
    baker_rows = []
    episode_rows = []
    be_rows = []
    sources = []
    warnings: list[str] = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for n in range(1, through + 1):
        title = series_title(n)
        url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
        try:
            wt = fetch_wikitext(title, force=force)
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"series {n} fetch failed: {exc}")
            continue
        parsed = parse_series_page(wt, n)
        meta = parsed["series_meta"]
        series_rows.append(
            {
                "series": n,
                "year": meta.get("year") or (2009 + n),
                "n_episodes": meta.get("n_episodes") or "",
                "n_bakers": meta.get("n_bakers") or len(parsed["bakers"]),
                "network": meta.get("network") or "",
                "channel_era": network_era(n),
                "judge_era": judge_era(n),
                "hosts": meta.get("hosts") or "",
                "judges": meta.get("judges") or "",
                "winner_name": meta.get("winner_name") or "",
                "runner_up_names": meta.get("runner_up_names") or "",
                "source_url": url,
            }
        )
        for b in parsed["bakers"]:
            baker_rows.append(
                {
                    **b,
                    "occupation_group": occupation_group(b.get("occupation") or ""),
                    "pronouns": "",
                    "years_baking_est": "",
                    "precision_job": "",
                    "chaos_self_describe": "",
                    "heritage_flavours": "",
                    "visual_showstopper": "",
                    "backup_baker": "",
                    "savoury_bias": "",
                    "started_late": "",
                    "bio_url": url,
                    "name_source": "wikipedia-series-page",
                    "notes": "",
                }
            )
        episode_rows.extend(parsed["episodes"])
        for row in parsed["baker_episodes"]:
            be_rows.append(
                {
                    **row,
                    "handshake_signature": "",
                    "handshake_showstopper": "",
                    "appeared": 1,
                }
            )
        sources.append(
            {
                "source_id": f"wiki-series-{n}",
                "name": title,
                "url": url,
                "retrieved_at": now,
                "series_from": n,
                "series_to": n,
                "fields": "bakers,episodes,baker_episode,results_chart",
                "method": "wikipedia-parse-api-wikitext",
                "license": "CC BY-SA 4.0",
                "tos_risk": "low",
                "notes": "Cached under data/raw/wiki/. Reuse requires attribution.",
            }
        )
        n_b = len(parsed["bakers"])
        n_ep = len(parsed["episodes"])
        n_be = len(parsed["baker_episodes"])
        tech = sum(1 for r in parsed["baker_episodes"] if r.get("technical_rank") is not None)
        if n_b < 8:
            warnings.append(f"series {n}: only {n_b} bakers parsed")
        if n > 2 and n_ep < 6:
            warnings.append(f"series {n}: only {n_ep} episode sections parsed")
        if n > 2 and tech < 10:
            warnings.append(f"series {n}: only {tech} technical ranks")

    # Overlay S17 official structured facts.
    by_id = {b["baker_id"]: b for b in baker_rows if str(b.get("series")) == "17"}
    if not by_id:
        # wiki page may have been empty-ish; seed from s17.py
        for b in S17_BAKERS:
            baker_rows.append(
                {
                    **b,
                    "series": 17,
                    "place": "",
                    "elimination_episode": "",
                    "is_winner": 0,
                    "is_runner_up": 0,
                    "n_star_baker": 0,
                    "n_technical_win": 0,
                    "occupation_group": occupation_group(b.get("occupation") or ""),
                }
            )
    else:
        for seed in S17_BAKERS:
            current = by_id.get(seed["baker_id"])
            if not current:
                # try match on short name
                current = next((b for b in baker_rows if str(b.get("series")) == "17" and b.get("baker_short") == seed["baker_short"]), None)
            if current:
                for key in (
                    "baker_full",
                    "age",
                    "occupation",
                    "hometown",
                    "pronouns",
                    "years_baking_est",
                    "precision_job",
                    "chaos_self_describe",
                    "heritage_flavours",
                    "visual_showstopper",
                    "backup_baker",
                    "savoury_bias",
                    "started_late",
                    "bio_url",
                    "name_source",
                    "notes",
                ):
                    if seed.get(key) not in (None, ""):
                        current[key] = seed[key]
                current["occupation_group"] = occupation_group(current.get("occupation") or "")
            else:
                baker_rows.append(
                    {
                        **seed,
                        "series": 17,
                        "place": "",
                        "elimination_episode": "",
                        "is_winner": 0,
                        "is_runner_up": 0,
                        "n_star_baker": 0,
                        "n_technical_win": 0,
                        "occupation_group": occupation_group(seed.get("occupation") or ""),
                    }
                )

    official_ids = {b["baker_id"] for b in S17_BAKERS}
    baker_rows = [
        b for b in baker_rows if str(b.get("series")) != "17" or b.get("baker_id") in official_ids
    ]

    # Ensure series 17 metadata row is complete.
    s17_row = next((r for r in series_rows if r["series"] == 17), None)
    if s17_row:
        s17_row.update(
            {
                "year": S17["year"],
                "n_episodes": S17["n_episodes"],
                "n_bakers": S17["n_bakers"],
                "network": S17["network"],
                "hosts": S17["hosts"],
                "judges": f"{S17['judge_1']}, {S17['judge_2']}",
            }
        )
    else:
        series_rows.append(
            {
                "series": 17,
                "year": S17["year"],
                "n_episodes": S17["n_episodes"],
                "n_bakers": S17["n_bakers"],
                "network": S17["network"],
                "channel_era": network_era(17),
                "judge_era": judge_era(17),
                "hosts": S17["hosts"],
                "judges": f"{S17['judge_1']}, {S17['judge_2']}",
                "winner_name": "",
                "runner_up_names": "",
                "source_url": "https://en.wikipedia.org/wiki/The_Great_British_Bake_Off_series_17",
            }
        )

    sources.append(
        {
            "source_id": "official-s17-bios",
            "name": "Meet the Class of 2026",
            "url": "https://thegreatbritishbakeoff.co.uk/meet-the-class-of-2026/",
            "retrieved_at": now,
            "series_from": 17,
            "series_to": 17,
            "fields": "structured bio facts only, not copied prose",
            "method": "manual extraction",
            "license": "facts; prose remains Love Productions copyright",
            "tos_risk": "medium",
            "notes": "Do not dump full bios into the repo.",
        }
    )
    sources.append(
        {
            "source_id": "c4-press-s17",
            "name": "Channel 4 Meet the Bakers",
            "url": "https://www.channel4.com/press/news/great-british-bake-2026-meet-bakers",
            "retrieved_at": now,
            "series_from": 17,
            "series_to": 17,
            "fields": "age, occupation, hometown",
            "method": "manual",
            "license": "press facts",
            "tos_risk": "low",
            "notes": "",
        }
    )

    write_csv(PROCESSED / "series.csv", series_rows, SERIES_FIELDS)
    write_csv(PROCESSED / "bakers.csv", baker_rows, BAKER_FIELDS)
    write_csv(PROCESSED / "episodes.csv", episode_rows, EPISODE_FIELDS)
    write_csv(PROCESSED / "baker_episode.csv", be_rows, BE_FIELDS)
    write_csv(PROCESSED / "sources.csv", sources, SOURCE_FIELDS)

    hist = summarize_history(baker_rows, be_rows, episode_rows)
    (PROCESSED / "history_stats.json").write_text(json.dumps(hist, indent=2, default=str), encoding="utf-8")

    summary = {
        "n_series": len(series_rows),
        "n_bakers": len(baker_rows),
        "n_episodes": len(episode_rows),
        "n_baker_episode": len(be_rows),
        "n_technical_ranks": sum(1 for r in be_rows if r.get("technical_rank") not in (None, "")),
        "warnings": warnings,
        "history": {k: hist[k] for k in hist if k != "winners"},
    }
    (PROCESSED / "ingest_summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    return summary
