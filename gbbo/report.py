"""Machine tables + the human weekly report."""

from __future__ import annotations

import json
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
    card = payload.get("bracketology")
    if card:
        (PREDICTIONS / f"s17-week{week:02d}-bracketology.json").write_text(
            json.dumps(card, indent=2), encoding="utf-8"
        )
    return path


def _pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def render_preseason_report(payload: dict, *, extra_history: dict | None = None) -> str:
    rows = sorted(payload["rows"], key=lambda r: r["win_rank"])
    elim = sorted(payload["rows"], key=lambda r: r["elim_rank"])
    pick = rows[0]
    today = date.today().isoformat()
    hist = extra_history or {}
    card = payload.get("bracketology") or {}
    w2w = (card.get("week_to_week") or {}).get("ceremonies") or []
    fi = card.get("first_impression") or {}
    e1 = w2w[0] if w2w else {}
    e2 = w2w[1] if len(w2w) > 1 else {}
    minus1 = ", ".join(e1.get("minus") or []) or "n/a"
    minus2 = ", ".join(e2.get("minus") or []) or "n/a"
    fi_first = ", ".join(fi.get("first_minus") or []) or f"{minus1}, {minus2}"

    lines = [
        f"# GBBO Series 17 weekly report — pre-season ({today})",
        "",
        "Week before Cake Week. Nobody has baked on air yet. The numbers are a soft prior "
        "plus a simulation of a 12-to-3 season, not a betting line. There is no Polymarket "
        "or Kalshi contract for this series. The OLBG 6/4 table going around is theoretical "
        "(the implied probabilities add up to about 335%). We ignored it.",
        "",
        "## The setup",
        "",
        f"- UK premiere: **Tuesday {S17['premiere']}, {S17['uk_slot']}** (Channel 4).",
        f"- US: Netflix Collection 14, **Friday {S17['us_premiere']}**, about three days later.",
        "- Judges: Paul Hollywood and Nigella Lawson. Hosts: Alison Hammond and Noel Fielding.",
        "- Companion show: *Second Helpings* (Jon Richardson and Judi Love), same Tuesday night. Extra Slice is gone, so UK recaps land three days before Netflix.",
        f"- Pool: **{S17['league_app']}**, league **{S17['league_name']}** (commissioner {S17['league_commissioner']}). About eight people so far.",
        "",
        "## How Bracketology scores",
        "",
        "Both games score the people you **kept** who actually survived, not the person who went home. "
        "Elimination 1 is 1 point per correct keep, Elimination 2 is 2 points, and so on. "
        "You minus the people you think are leaving.",
        "",
        f"- **Week to Week** is the weekly game. It locks when Cake Week *starts* on Channel 4 "
        f"({S17['w2w_first_lock']}), and it locks the next two ceremonies in case that episode has a double. "
        "If only one person goes, the unused second pick comes back after scores. "
        "Cake Week has never been a Channel 4 double.",
        f"- **First Impression** is the season-long card. In the app it starts at **Elimination 2** "
        "(10 of 12 advance, drop 2). There is no Elimination 1 pane on that card. Cake Week is the "
        "episode you get to watch. The card does not lock until Episode 2 starts "
        f"({S17['fi_lock']}). Filling it now costs nothing. Watch Cake Week, change whatever you want, then leave it.",
        "",
        "## Week to Week (the other tab, before Tuesday)",
        "",
        f"- **Elim 1** (locks {S17['w2w_first_lock']}): minus **{minus1}**. Keep the other eleven.",
        f"- **Elim 2** (locked at the same time, as a hedge): minus **{minus2}** from whoever is left. "
        "If episode 1 is a normal single boot, this pick comes back.",
        "",
        "The Cake Week board is almost flat (about 9.5% vs 7.9%). Gary is first because the prior "
        "says he is the most exposed, not because we know Cake Week. Nadiya came last in her first "
        "technical and still won. You score the eleven you kept, at 1 point each.",
        "",
        "## First Impression (open until Episode 2)",
        "",
        f"You can enter a full card now and rewrite it after Cake Week. Nothing is scored until it locks "
        f"at **{S17['fi_lock']}**. The first screen you see is Elimination 2: minus **{fi_first}** so 10 remain. "
        f"Starter winner **{fi.get('winner') or pick['baker_short']}** at {_pct(pick['p_win'])} is only a nudge "
        "over a flat 8.3%. Pre-season favourites are a bad habit (Josh 2023, Dylan 2024, Jürgen as the season-long favourite in 2021). Later rounds pay more: dropping a finalist at Elim 7 costs 7+8+9.",
        "",
        "If everyone else goes Shannon because she was a 2025 reserve and plans for a living, "
        "Shannon or Yannis is still the play, with Moyin for technical upside and Molly for "
        "consistency. Do not pick Gary or Connie to win. They can last. They almost certainly "
        "do not lift the trophy.",
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
        "These come from 8,000 simulated seasons (nine boots, then a noisy final of three). "
        "They are flatter than the bio multipliers on purpose. After each elimination we drop "
        "that baker and run it again.",
        "",
        "## Cake Week elimination order",
        "",
        "Week to Week minus order. Elim 1 is the first row, Elim 2 hedge is the second. Cake Week is noisy.",
        "",
        "| Elim rank | Baker | P(this week) |",
        "| ---: | --- | ---: |",
    ]
    for r in elim:
        lines.append(f"| {r['elim_rank']} | {r['baker_short']} | {_pct(r['p_elim'])} |")

    order = payload.get("boot_order") or []
    finalists = payload.get("projected_finalists") or fi.get("final_three") or []
    fi_drops = fi.get("drop_order") or order
    lines += [
        "",
        "## First Impression starter card",
        "",
        "The first pane is Elimination 2. Minus two names so 10 remain. Enter this now if you want, then change it after Cake Week.",
        "",
        f"- First pane (Elim 2): minus **{fi_first}**",
        f"- Then minus, in order: {' → '.join((fi_drops or [])[2:]) if fi_drops else '(n/a)'}",
        f"- Final three: {', '.join(finalists) if finalists else '(n/a)'}",
        f"- Winner (keep 1, minus 2): {fi.get('winner') or pick['baker_short']}",
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
        occ = hist.get("winner_occupation_groups") or {}
        if isinstance(occ, dict) and occ:
            occ_txt = ", ".join(f"{k} {v}" for k, v in occ.items())
            lines.append(f"- Occupation groups among winners: {occ_txt}.")
        else:
            lines.append(f"- Occupation groups among winners: {occ}")
        lines.append(
            f"- Star Baker counts among winners: {hist.get('winner_star_baker_counts')} "
            f"(mean {hist.get('winner_star_baker_mean')}; zeros in the file: {hist.get('winners_with_zero_sb')}). "
            "David Atherton (S10) is the real zero-SB winner. Edd’s zero is not comparable — the award started in series 2. "
            "Richard Burr had five and lost."
        )
        lines.append(
            f"- Mean of winners’ median technical percentile: {hist.get('winner_median_technical_percentile_mean')} "
            f"vs field {hist.get('field_median_technical_percentile_mean')} (1.0 = always first). "
            "Directionally winners are a bit more consistent on technicals; Wikipedia ranks are missing for chunks of S8/S10/S11, so do not treat the decimal as a law."
        )
        w1 = hist.get("week1_last_technical_winners") or []
        if isinstance(w1, list):
            w1_txt = ", ".join(str(x) for x in w1) if w1 else "none parsed"
        else:
            w1_txt = str(w1)
        lines.append(f"- Winners who came last in the week-1 technical: {w1_txt}.")
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
        "- **Paul and Prue/Nigella publish a split vote.** They do not. We almost never know which judge wanted whom to leave. Recaps sometimes flag an on-camera disagreement; that is a weekly note, not a historical feature.",
        "- **Bread week is a slaughterhouse.** Theme difficulty from Giusti’s scores: chocolate and pastry are harder relative to a baker’s own average; bread is only slightly hard. Bread-week *Star Baker* is the interesting bit (they tend not to go home early).",
        "- **First week decides the season.** It decides the first boot. It does not crown the champion.",
        "",
        "## Judges this year",
        "",
        "Paul is still Mr Technical. Nigella has said she looks for pleasure, not fault, and that she is about the eating. "
        "That is not a 180 from Prue (Prue was already the flavour judge). Heritage flavour, salt, goo, and eating quality "
        "probably get a bit more love. Rustic finish is still a risk when Paul is scoring bake-through. Noel already "
        "joked about the tent over-salting after Nigella praised salt. We do not see which judge wanted whom to leave. "
        "A handshake is still just Paul liking one bake.",
        "",
        "## What we are doing with the numbers",
        "",
        "Sixteen winners is a small sample, and Nigella has judged zero episodes, so this stays almost flat on purpose. "
        "After episodes exist we will use that week’s bakes for who goes home, and a running skill score for who wins. "
        "No neural nets, no IMDb, no dumped recaps, no fake judge-vote model. If the history tests look embarrassing we will print that too.",
        "",
        "## What to do in the app",
        "",
        f"- **Week to Week:** minus **{minus1}** for Elim 1 and **{minus2}** for Elim 2 before Cake Week starts on Channel 4.",
        f"- **First Impression:** starts at Elim 2. Minus **{fi_first}** so 10 remain. Fill it now if you like. Change it after episode 1. It locks when episode 2 starts.",
        "- Netflix watchers: mute `#GBBO` and *Second Helpings* from Tuesday 8pm UK until Friday. Last year Extra Slice was Friday, which matched Netflix. This year the recap is the same night.",
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
        "- Fantasy Bake Off scoring (different pool, not Bracketology): https://fantasybakeoff.co.uk/how-to-play/",
        "- Bracketology: https://bracketology.tv/great-british-baking-show",
        "- TVmaze series 17 episode 1: https://www.tvmaze.com/episodes/3744890/the-great-british-bake-off-17x01-cake-week",
        "",
        "Wikipedia material is CC BY-SA 4.0. Recap URLs are cited; full article text is not stored.",
        "",
        "## Caveats",
        "",
        "Sixteen winners. New co-judge. Bios are marketing. Cake Week has already been press-screened as messy "
        "(stout cakes, a falling hat cake in the trailer) without naming who leaves. If the first boot is a "
        "showstopper collapse from someone we like, that is Bake Off, not a model failure.",
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
        "## Bracketology",
        "",
        "- Week to Week: minus who this ceremony, minus who next (two-ceremony lock at the next UK air).",
        "- First Impression: locked at Episode 2 start. If this is the week-1 report, freeze the nested path here.",
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
