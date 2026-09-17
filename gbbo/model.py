"""Explainable dual ranking: this-week elimination hazard, remaining P(win).

n=16 historical winners. Do not treat these numbers as a market edge.
They exist to beat a casual friend pool, and even that edge is thin
before episode 1.
"""

from __future__ import annotations

import math
import random
from typing import Any

from gbbo.features import occupation_group, technical_percentile
from gbbo.s17 import BAKERS as S17_BAKERS

# Historical winner ages series 1-16, used as a weak density prior.
WINNER_AGES = [20, 22, 23, 24, 28, 30, 30, 31, 31, 32, 33, 34, 36, 41, 45, 60]


def _age_multiplier(age: int | None) -> float:
    if age is None:
        return 1.0
    # inverted-U around the historical cluster 22-36
    if 22 <= age <= 36:
        return 1.12
    if 37 <= age <= 50:
        return 0.95
    if age <= 21:
        return 0.82
    if 51 <= age <= 59:
        return 0.72
    return 0.45  # 60+


def _gauss_age_density(age: int | None, h: float = 8.0) -> float:
    if age is None:
        return 1.0
    dens = 0.0
    for a in WINNER_AGES:
        dens += math.exp(-((age - a) ** 2) / (2 * h * h))
    return dens / len(WINNER_AGES)


def preseason_weights(bakers: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    bakers = bakers or S17_BAKERS
    scored = []
    for b in bakers:
        w = 1.0
        reasons: list[str] = []
        age = b.get("age")
        am = _age_multiplier(age)
        w *= am
        if am != 1.0:
            reasons.append(f"age {age} ×{am:.2f}")
        w *= 0.7 + 0.6 * _gauss_age_density(age)  # mild density, not a hammer
        if b.get("precision_job"):
            w *= 1.10
            reasons.append("precision-job analog ×1.10")
        if b.get("chaos_self_describe"):
            w *= 0.88
            reasons.append("self-described chaos ×0.88")
        if b.get("started_late") and (age or 0) >= 60:
            w *= 0.85
            reasons.append("late starter at 60+ ×0.85")
        if b.get("years_baking_est") is not None and b["years_baking_est"] <= 3:
            w *= 0.84
            reasons.append(f"short tenure ({b['years_baking_est']}y) ×0.84")
        if b.get("backup_baker"):
            w *= 1.08
            reasons.append("2025 reserve baker ×1.08")
        if b.get("heritage_flavours"):
            w *= 1.04
            reasons.append("heritage/flavour lane vs Nigella ×1.04")
        occ = occupation_group(b.get("occupation") or "")
        if occ == "stem_medical":
            w *= 1.06
            reasons.append("stem/medical occupation group ×1.06")
        if occ == "retired":
            w *= 0.80
            reasons.append("retired occupation group ×0.80")
        scored.append({**b, "prior_weight": w, "prior_reasons": reasons, "occupation_group": occ})
    total = sum(s["prior_weight"] for s in scored)
    for s in scored:
        s["p_win"] = s["prior_weight"] / total if total else 1 / len(scored)
        # preseason elim risk ≈ inverse skill, flattened
        s["skill_mu"] = 5.0 + 4.0 * (s["p_win"] * len(scored) - 1.0)
    # elim probs from inverse prior, not identical ranking to win
    inv = [1.0 / max(s["prior_weight"], 1e-6) for s in scored]
    z = _softmax(inv, temp=2.4)
    for s, p in zip(scored, z, strict=True):
        s["p_elim"] = p
    scored.sort(key=lambda r: -r["p_win"])
    for i, s in enumerate(scored, start=1):
        s["win_rank"] = i
    elim_order = sorted(scored, key=lambda r: -r["p_elim"])
    for i, s in enumerate(elim_order, start=1):
        s["elim_rank"] = i
    return scored


def weekly_score_from_row(row: dict[str, Any]) -> float:
    """0-10ish package score. Used post-air or when notes exist."""
    n = row.get("n_in_technical")
    rank = row.get("technical_rank")
    pct = technical_percentile(
        int(rank) if rank not in (None, "") else None,
        int(n) if n not in (None, "") else None,
    )
    tech = 3.5 * pct if pct is not None else 1.75
    sig_map = {"disaster": 0.3, "poor": 0.6, "mixed": 1.0, "fine": 1.5, "good": 1.8, "rave": 2.0}
    show_map = {"disaster": 0.4, "poor": 0.9, "mixed": 1.8, "fine": 2.6, "good": 3.1, "rave": 3.5}
    sig = sig_map.get((row.get("signature_valence") or "fine").lower(), 1.5)
    show = show_map.get((row.get("showstopper_valence") or "fine").lower(), 2.6)
    hs = 1.0 if str(row.get("handshake") or "") in {"1", "True", "true"} else 0.0
    fav = 0.0
    if str(row.get("result") or "") == "HIGH":
        fav = 1.0
    elif str(row.get("result") or "") == "LOW":
        fav = -1.0
    elif str(row.get("result") or "") == "SB":
        fav = 1.2
        show = max(show, 3.0)
    elif str(row.get("result") or "") == "OUT":
        fav = -1.2
    return tech + sig + show + hs + fav


def update_skill(mu: float, sigma: float, score: float, alpha: float = 0.45) -> tuple[float, float]:
    mu2 = (1 - alpha) * mu + alpha * score
    # variance shrinks slowly as we see weeks
    sigma2 = max(0.7, math.sqrt((1 - alpha) * sigma * sigma + alpha * (score - mu) ** 2))
    return mu2, sigma2


def softmax_elim(scores: list[float], temp: float = 1.8) -> list[float]:
    # lower score = more likely to go
    inv = [-s for s in scores]
    return _softmax(inv, temp=temp)


def _softmax(xs: list[float], temp: float) -> list[float]:
    if not xs:
        return []
    m = max(xs)
    exps = [math.exp((x - m) / temp) for x in xs]
    z = sum(exps) or 1.0
    return [e / z for e in exps]


def monte_carlo_win(
    mus: list[float],
    sigmas: list[float],
    *,
    weeks_left: int,
    n_elim_this_week: int = 1,
    draws: int = 6000,
    seed: int = 17,
    final_noise: float = 1.35,
) -> list[float]:
    """Simulate remaining weeks: drop the lowest (or two) each week, then noisy final of 3."""
    rng = random.Random(seed)
    n = len(mus)
    wins = [0] * n
    if n == 0:
        return []
    if n == 1:
        return [1.0]
    for _ in range(draws):
        alive = list(range(n))
        remaining_weeks = weeks_left
        first = True
        while len(alive) > 3 and remaining_weeks > 0:
            drop = n_elim_this_week if first else 1
            first = False
            drop = min(drop, max(0, len(alive) - 3))
            if drop <= 0:
                break
            scored = []
            for i in alive:
                scored.append((rng.gauss(mus[i], sigmas[i]), i))
            scored.sort()  # lowest first
            victims = {idx for _, idx in scored[:drop]}
            alive = [i for i in alive if i not in victims]
            remaining_weeks -= 1
        # if still more than 3, keep cutting on skill
        while len(alive) > 3:
            scored = [(rng.gauss(mus[i], sigmas[i]), i) for i in alive]
            scored.sort()
            alive = [idx for _, idx in scored[1:]]
        # final: extra noise, highest wins
        if not alive:
            continue
        final = [(rng.gauss(mus[i], sigmas[i] * final_noise), i) for i in alive]
        winner = max(final)[1]
        wins[winner] += 1
    tot = sum(wins) or 1
    return [w / tot for w in wins]


def most_likely_boot_order(
    rows: list[dict[str, Any]], weeks_left: int
) -> tuple[list[str], list[str]]:
    """Greedy path: boot current highest elim-prob baker each remaining non-final week."""
    remaining = [dict(r) for r in rows]
    order: list[str] = []
    boots_needed = min(max(0, len(remaining) - 3), weeks_left)
    for _ in range(boots_needed):
        remaining.sort(key=lambda r: -r["p_elim"])
        boot = remaining.pop(0)
        order.append(boot["baker_short"])
        inv = [
            1.0 / max(r.get("prior_weight") or math.exp(r.get("skill_mu", 5) / 2), 1e-6)
            for r in remaining
        ]
        probs = _softmax(inv, temp=2.4)
        for r, p in zip(remaining, probs, strict=True):
            r["p_elim"] = p
    remaining.sort(key=lambda r: -r.get("p_win", 0))
    return order, [r["baker_short"] for r in remaining]


def _mix_uniform(probs: list[float], cap: float = 0.20) -> list[float]:
    """Blend toward 1/n until nobody is over `cap`. That is the evened-out board."""
    n = len(probs) or 1
    uniform = 1.0 / n
    mixed = list(probs)
    alpha = 0.0
    while mixed and max(mixed) > cap and alpha < 0.95:
        alpha += 0.05
        mixed = [(1 - alpha) * p + alpha * uniform for p in probs]
        z = sum(mixed) or 1.0
        mixed = [p / z for p in mixed]
    return mixed


def predict_week0() -> dict[str, Any]:
    ranked = preseason_weights()
    mus = [r["skill_mu"] for r in ranked]
    sigmas = [2.8] * len(ranked)
    mc = monte_carlo_win(mus, sigmas, weeks_left=9, draws=8000, seed=2026, final_noise=1.6)
    mc = _mix_uniform(mc, cap=0.18)
    for r, p in zip(ranked, mc, strict=True):
        r["p_win_mc"] = p
        r["p_win"] = p
    # renormalize already 1
    ranked.sort(key=lambda r: -r["p_win"])
    for i, r in enumerate(ranked, start=1):
        r["win_rank"] = i
    # elim: inverse of current skill
    inv = [1 / max(math.exp(r["skill_mu"] / 3.0), 1e-6) for r in ranked]
    probs = _softmax(inv, temp=2.2)
    by_id = {r["baker_id"]: p for r, p in zip(ranked, probs, strict=True)}
    for r in ranked:
        r["p_elim"] = by_id[r["baker_id"]]
    elim_sorted = sorted(ranked, key=lambda r: -r["p_elim"])
    for i, r in enumerate(elim_sorted, start=1):
        r["elim_rank"] = i
    order, finalists = most_likely_boot_order(
        [{**r} for r in ranked],
        weeks_left=9,
    )
    return {
        "week": 0,
        "mode": "preseason",
        "rows": ranked,
        "boot_order": order,
        "projected_finalists": finalists,
    }
