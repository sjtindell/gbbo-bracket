"""Machine tables + the human weekly report."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from gbbo.csvutil import write_csv
from gbbo.model import predict_week0
from gbbo.paths import PREDICTIONS, WEEKLY_REPORTS, PROCESSED, ensure_dirs
from gbbo.s17 import S17

PRED_FIELDS = [
    "as_of_week",
    "mode",
    "baker_id",
    "baker_short",
    "win_rank",
    "p_win",
    "elim_rank",
    "p_elim",
    "skill_mu",
    "age",
    "occupation",
    "occupation_group",
    "reasons",
]


def write_predictions(payload: dict, week: int) -> Path:
    ensure_dirs()
    rows = []
    for r in payload["rows"]:
        rows.append(
            {
                "as_of_week": week,
                "mode": payload.get("mode", ""),
                "baker_id": r["baker_id"],
                "baker_short": r["baker_short"],
                "win_rank": r.get("win_rank"),
                "p_win": f"{r['p_win']:.4f}",
                "elim_rank": r.get("elim_rank"),
                "p_elim": f"{r['p_elim']:.4f}",
                "skill_mu": f"{r.get('skill_mu', 0):.3f}",
                "age": r.get("age"),
                "occupation": r.get("occupation"),
                "occupation_group": r.get("occupation_group"),
                "reasons": "; ".join(r.get("prior_reasons") or []),
            }
        )
    path = PREDICTIONS / f"s17-week{week:02d}.csv"
    write_csv(path, rows, PRED_FIELDS)
    return path


def _pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def render_preseason_report(payload: dict, *, extra_history: dict | None = None) -> str:
    rows = sorted(payload["rows"], key=lambda r: r["win_rank"])
    elim = sorted(payload["rows"], key=lambda r: r["elim_rank"])
    pick = rows[0]
    today = date.today().isoformat()
    hist = extra_history or {}

    lines = [
        f"# GBBO Series 17 weekly report — pre-season ({today})",
        "",
        "This is the write-up for the week before Cake Week, not a recap. "
        "Nothing has been baked on air yet. The numbers below are a weakly "
        "informed prior plus a Monte Carlo of a 12-to-3 sequential elimination, "
        "not a prediction market and not a claim that we can beat bookies. "
        "There is no live Polymarket or Kalshi contract for this series, and "
        "the OLBG 6/4 table circulating online is theoretical entertainment "
        "pricing whose implied probabilities sum to about 335 percent. We did "
        "not use it.",
        "",
        "## What this file is",
        "",
        "Every weekly run should leave a **separate** human-language report in "
        "`reports/weekly/`. Tables and CSVs live next to it. This document is "
        "the thing you can paste into a group chat after skimming. Later weeks "
        "will cover who actually went home, what recaps said, and how the "
        "rankings moved.",
        "",
        f"- UK premiere: **Tuesday {S17['premiere']}, {S17['uk_slot']}** (Channel 4).",
        f"- US: Netflix Collection 14, **Friday {S17['us_premiere']}**, about three days later.",
        "- Judges: Paul Hollywood and Nigella Lawson. Hosts: Alison Hammond and Noel Fielding.",
        "- Companion show: *Second Helpings* (Jon Richardson and Judi Love), same Tuesday night. Extra Slice is gone. That tightens the spoiler window for anyone watching on Netflix Friday.",
        "",
        "## The pick, in English",
        "",
        f"If you have to lock a champion before episode 1, the model’s top remaining-season probability is **{pick['baker_short']}** "
        f"at {_pct(pick['p_win'])}. That is a small bump over a flat 8.3 percent, not a mandate. "
        "Pre-season Bake Off favourites are historically shaky (Josh 2023, Dylan 2024, Jürgen as season-long favourite in 2021). "
        "The useful output this week is the **full ranking** and the **elimination ranking**, not a hot take.",
        "",
        "If your friends all pile onto Shannon because she was a 2025 reserve and her day job is planning, "
        "the evened-out play is still Shannon or Yannis, with Moyin as the technical-upside ticket and Molly as the consistency ticket. "
        "Do not use Gary or Connie as a winner pick. They can last; they almost certainly do not lift the trophy.",
        "",
        "## Remaining-season win probabilities",
        "",
        "| Rank | Baker | Age | Job | P(win) | Why the prior moved |",
        "| ---: | --- | ---: | --- | ---: | --- |",
    ]
    for r in rows:
        reasons = ", ".join(r.get("prior_reasons") or ["flat"])
        lines.append(
            f"| {r['win_rank']} | {r['baker_short']} | {r.get('age','')} | {r.get('occupation','')} | {_pct(r['p_win'])} | {reasons} |"
        )
    lines += [
        "",
        "These probabilities are Monte Carlo outcomes (8,000 paths, nine boots, noisy final of three). "
        "They are flatter than the raw bio multipliers on purpose — that is the “evened out” bracket. "
        "After each elimination we drop that baker and resimulate. We do not invent a 12-team knockout tree; "
        "Bake Off is sequential, not March Madness.",
        "",
        "## Ranked elimination risk for Cake Week",
        "",
        "Pick the top one, or two if you want a hedge. Cake Week is noisy. First-week disasters are recoverable "
        "(Nadiya came last in her first technical and still won). So this board is “who is most exposed if someone has to go”, "
        "not “this person cannot bake”.",
        "",
        "| Elim rank | Baker | P(this week) |",
        "| ---: | --- | ---: |",
    ]
    for r in elim:
        lines.append(f"| {r['elim_rank']} | {r['baker_short']} | {_pct(r['p_elim'])} |")

    order = payload.get("boot_order") or []
    finalists = payload.get("projected_finalists") or []
    lines += [
        "",
        "## Projected finishing path (the actual bracket)",
        "",
        "Most likely greedy boot order from the current elim ranking, then the three left standing. "
        "This will be wrong. It is internally consistent: nobody is both week-3 out and a finalist.",
        "",
        f"- Projected boots, weeks 1–9: {' → '.join(order) if order else '(n/a)'}",
        f"- Projected final three: {', '.join(finalists) if finalists else '(n/a)'}",
        f"- Projected winner: {rows[0]['baker_short']}",
        "",
        "## Baker cards",
        "",
    ]
    for r in rows:
        lines += [
            f"### {r['baker_short']} ({r.get('baker_full') or r['baker_short']})",
            "",
            f"- Age {r.get('age')}, {r.get('occupation')}, {r.get('hometown')}",
            f"- Win rank {r['win_rank']} ({_pct(r['p_win'])}); Cake Week elim rank {r['elim_rank']} ({_pct(r['p_elim'])})",
            f"- {r.get('notes') or 'No extra note.'}",
            "",
        ]

    lines += [
        "## What history actually says (series 1–16)",
        "",
        "Small sample. Sixteen winners. Treat every percentage as a description of the past, not a law.",
        "",
    ]
    if hist:
        ages = hist.get("winner_ages") or []
        lines.append(
            f"- Winner ages: {ages}. Mean {hist.get('winner_age_mean')}, median {hist.get('winner_age_median')}, "
            f"range {hist.get('winner_age_min')}–{hist.get('winner_age_max')}."
        )
        lines.append(f"- Occupation groups among winners: {hist.get('winner_occupation_groups')}")
        lines.append(
            f"- Star Baker counts among winners: {hist.get('winner_star_baker_counts')} "
            f"(mean {hist.get('winner_star_baker_mean')}; zero-SB winners: {hist.get('winners_with_zero_sb')}). "
            "David Atherton won with none. Richard Burr had five and lost."
        )
        lines.append(
            f"- Mean of winners’ median technical percentile: {hist.get('winner_median_technical_percentile_mean')} "
            f"vs field {hist.get('field_median_technical_percentile_mean')} (1.0 = always first)."
        )
        w1 = hist.get("week1_last_technical_winners") or []
        lines.append(f"- Winners who came last in the week-1 technical: {w1 or 'none parsed'}.")
        bread = hist.get("bread_week_sb_to_final") or {}
        if bread.get("n"):
            lines.append(
                f"- Bread-week Star Bakers who made the final: {bread.get('final')}/{bread.get('n')} "
                f"({100 * bread['final'] / bread['n']:.0f}%). Survival signal, not a winner lock."
            )
        for code in ("HIGH", "LOW", "SB", "SAFE"):
            trip = hist.get(f"week1_{code}_to_final")
            if trip:
                n, k, p = trip
                lines.append(f"- Week-1 {code} → final: {k}/{n} ({100 * p:.0f}%).")
        lines.append("")

    lines += [
        "### Things people think are true that are only half true",
        "",
        "- **Star Baker count picks the winner.** No. The Times / GBBO Data 2025: the most-credentialed finalist wins about 36 percent of the time, which is random among three.",
        "- **A Hollywood handshake means they will win.** It means Paul liked one bake. Never given in the technical. Nancy and Georgie won without one. Series 9 handed them out like sweets.",
        "- **Paul and Prue/Nigella publish a split vote.** They do not. We almost never know which judge wanted whom to leave. Recaps sometimes flag an on-camera disagreement; that goes in weekly notes as `judge_split`, not as a historical feature we can fit.",
        "- **Bread week is a slaughterhouse.** Theme difficulty from Giusti’s scores: chocolate and pastry are harder relative to a baker’s own average; bread is only slightly hard. Bread-week *Star Baker* is the interesting bit (they tend not to go home early).",
        "- **First week decides the season.** It decides the first boot. It does not crown the champion.",
        "",
        "## Judges this year",
        "",
        "Paul is still Mr Technical. Nigella has said she looks for pleasure, not fault, and that she is about the eating. "
        "That is not a 180 from Prue (Prue was already the flavour judge). Relative boost: heritage flavour, salt, goo, eating quality. "
        "Relative risk: rustic/homemade finish when Paul is scoring bake-through. Noel already noted the tent over-salting after Nigella praised salt. "
        "We do **not** have a dataset of “Nigella’s favourite vs Paul’s favourite” because that data is not public. "
        "Handshake remains a Paul-only observable.",
        "",
        "## Models we will actually run (and ones we will not)",
        "",
        "A small council of approaches, then one stack for v1:",
        "",
        "1. **Baseline:** 1/12 forever, then renormalise after boots. Beats swaggering bios.",
        "2. **This-week elim:** softmax on the week’s 0–10 package (technical percentile + signature/showstopper valence + handshake + HIGH/LOW). This is closer to how the show decides a boot.",
        "3. **Remaining P(win):** EWMA skill with shrinking variance, then Monte Carlo the rest of the season. Softmax-on-skill is the cheap fallback.",
        "4. **Validation:** leave-one-series-out on series 1–16 once the Wikipedia technicals are in. Report the mean probability assigned to the actual winner. If we cannot beat ~8–10 percent, we say so.",
        "5. **Not v1:** DeepBake-style neural nets, scraping IMDb, dumping full recap articles, treating OLBG as a market, modelling secret judge votes we cannot see.",
        "",
        "Text becomes numbers only where we can point at the mapping: technical rank → percentile; recap valence → {disaster, poor, mixed, fine, good, rave}; handshake → 0/1; HIGH/LOW/SB/OUT → result codes. "
        "Free-text bios stay as flags (chaos, precision job, years baking), not embeddings.",
        "",
        "## How to use this in the friend pool",
        "",
        "- Lock weekly elim picks **before** you watch, using the elim board from the previous report (this week: the Cake Week board above).",
        "- After you watch — or after the UK air, if you are ingesting recaps without watching — fill `data/weekly/s17eNN.md` from the template. Rank everyone. You still pick the top one or two.",
        "- Then rerun `python -m gbbo ingest-week --week N` and `python -m gbbo weekly-report --week N`. The new report is a new file. We do not overwrite this one.",
        "- US watchers: mute `#GBBO` and *Second Helpings* from Tuesday 8pm UK until Friday. Last year Extra Slice was Friday, which matched Netflix. This year the recap is the same night.",
        "",
        "## Sources used this week",
        "",
        "- Official class of 2026: https://thegreatbritishbakeoff.co.uk/meet-the-class-of-2026/",
        "- Channel 4 press: https://www.channel4.com/press/news/great-british-bake-2026-meet-bakers",
        "- Wikipedia series 17: https://en.wikipedia.org/wiki/The_Great_British_Bake_Off_series_17",
        "- Wikipedia contestant list: https://en.wikipedia.org/wiki/List_of_The_Great_British_Bake_Off_contestants",
        "- Shannon reserve Q&A: https://mediamole.co.uk/tv/the-great-british-bake-off-2026-shannon-age-job-qa/33820/",
        "- Nigella on judging: https://www.hellomagazine.com/film/880801/nigella-lawson-reveals-bake-off-judging-approach/",
        "- Telegraph Cake Week first look (challenges, not results): https://www.telegraph.co.uk/tv/2026/09/07/the-great-british-bake-off-first-look-review-channel-4/",
        "- OLBG theoretical odds (do not use): https://www.olbg.com/news/great-british-bake-series-17-meet-bakers-and-winner-odds",
        "- Betting.co.uk (markets not open): https://www.betting.co.uk/novelty-betting/great-british-bake-off/",
        "- CRAN bakeoff (series 1–10 seed, HIGH/LOW collapsed): https://cran.r-project.org/web/packages/bakeoff/",
        "- Monica Kim weekly files (series 3–16, includes handshakes): https://github.com/monica-m-kim/Great-British-Bake-Off",
        "- Giusti strength model: https://github.com/nathangiusti/BakeOff",
        "- DeepBake: https://github.com/dantaki/DeepBake",
        "- Nick Ahamed, Analytics Vidhya: https://medium.com/analytics-vidhya/analyzing-the-great-british-bake-off-part-1-ffcdf3791bf3",
        "- Times / GBBO Data 2025: https://www.thetimes.com/culture/tv-radio/article/bake-off-success-data-who-win-2025-q98wntjps",
        "- Fantasy Bake Off scoring (for pool design, not our model): https://fantasybakeoff.co.uk/how-to-play/",
        "- TVmaze series 17 episode 1: https://www.tvmaze.com/episodes/3744890/the-great-british-bake-off-17x01-cake-week",
        "",
        "Wikipedia material is CC BY-SA 4.0. Recap URLs are cited; full article text is not stored.",
        "",
        "## Caveats, again",
        "",
        "n=16. Nigella is a new co-judge. Bios are marketing. Cake Week has already been press-screened as messy (stout cakes, a falling hat cake in the trailer) without naming who leaves. "
        "If the first boot is a showstopper collapse from someone we like, that is Bake Off, not a model failure.",
        "",
    ]
    return "\n".join(lines) + "\n"


def write_weekly_report(week: int, payload: dict, history: dict | None = None) -> Path:
    ensure_dirs()
    if week == 0:
        body = render_preseason_report(payload, extra_history=history)
        path = WEEKLY_REPORTS / f"s17e00-{date.today().isoformat()}-preseason.md"
    else:
        body = render_inseason_stub(week, payload, history)
        path = WEEKLY_REPORTS / f"s17e{week:02d}-{date.today().isoformat()}.md"
    path.write_text(body, encoding="utf-8")
    return path


def render_inseason_stub(week: int, payload: dict, history: dict | None = None) -> str:
    rows = sorted(payload.get("rows") or [], key=lambda r: r.get("win_rank", 99))
    elim = sorted(payload.get("rows") or [], key=lambda r: r.get("elim_rank", 99))
    lines = [
        f"# GBBO Series 17 weekly report — week {week} ({date.today().isoformat()})",
        "",
        "Fill this after ingesting the episode. Keep it human. Cite URLs. Do not paste full recaps.",
        "",
        "## What happened",
        "",
        "- Theme:",
        "- Star Baker:",
        "- Eliminated:",
        "- Handshakes:",
        "- Technical ranking (1 = best):",
        "- Judge split (only if a recap actually said so; otherwise “not reported”):",
        "",
        "## Sources (URLs only)",
        "",
        "- Wikipedia:",
        "- Digital Spy / Metro:",
        "- Radio Times:",
        "- Channel 4 press:",
        "- r/bakeoff watchalong:",
        "- Your notes: `data/weekly/s17e{week:02d}.md`",
        "",
        "## Updated remaining-season P(win)",
        "",
        "| Rank | Baker | P(win) | P(elim next) |",
        "| ---: | --- | ---: | ---: |",
    ]
    for r in rows:
        lines.append(
            f"| {r.get('win_rank')} | {r.get('baker_short')} | {_pct(float(r['p_win']))} | {_pct(float(r['p_elim']))} |"
        )
    lines += [
        "",
        "## Next week elimination ranking",
        "",
        "| Rank | Baker | P(elim) |",
        "| ---: | --- | ---: |",
    ]
    for r in elim:
        lines.append(f"| {r.get('elim_rank')} | {r.get('baker_short')} | {_pct(float(r['p_elim']))} |")
    lines += [
        "",
        "## Projected path from here",
        "",
        f"- Boots: {' → '.join(payload.get('boot_order') or [])}",
        f"- Final three: {', '.join(payload.get('projected_finalists') or [])}",
        "",
        "## What changed our mind",
        "",
        "(One short paragraph. If nothing changed, say that.)",
        "",
        "## Caveats",
        "",
        "Small sample, new judge pairing, this week’s package is not a season résumé.",
        "",
    ]
    _ = history
    return "\n".join(lines).replace("{week:02d}", f"{week:02d}") + "\n"


def run_preseason() -> tuple[Path, Path]:
    payload = predict_week0()
    pred_path = write_predictions(payload, 0)
    hist = {}
    stats = PROCESSED / "history_stats.json"
    if stats.exists():
        import json

        hist = json.loads(stats.read_text(encoding="utf-8"))
    report_path = write_weekly_report(0, payload, hist)
    return pred_path, report_path
