"""Bracketology scoring for the Ready, set, BrAcKEt league.

The app pays correct *advancers*, not the boot name. Same formula in both
games: ceremony t is worth t points per baker you kept who actually advanced.

Week to Week: lineup resets to whoever is still in. Minus the required
number. UK air locks the next TWO ceremonies; unused second ceremony reopens.

First Impression: one nested survivor path, locked at the start of Episode 2.
Do not lock it before Cake Week.

Elim 2 showing “12/10 drop 2” is the cumulative quota from the original 12
when earlier tabs are still fully selected — not a scheduled Cake Week double.
Channel 4 week 1 has been a single boot in 8/9 series (S15 was a non-elim).
"""

from __future__ import annotations

from typing import Any

from gbbo.s17 import S17

N_START = 12
N_FINALISTS = 3
N_BOOT_CEREMONIES = N_START - N_FINALISTS  # 9
WINNER_CEREMONY = N_BOOT_CEREMONIES + 1  # 10


def ceremony_specs(n_start: int = N_START, n_finalists: int = N_FINALISTS) -> list[dict[str, Any]]:
    specs = []
    remaining = n_start
    for t in range(1, n_start - n_finalists + 1):
        remaining -= 1
        specs.append(
            {
                "elim_index": t,
                "n_advance": remaining,
                "n_drop": 1,
                "kind": "boot",
            }
        )
    specs.append(
        {
            "elim_index": n_start - n_finalists + 1,
            "n_advance": 1,
            "n_drop": n_finalists - 1,
            "kind": "winner",
        }
    )
    return specs


def expected_w2w_correct(p_elim: list[float], drop: int) -> float:
    """Expected correct advancers when exactly one baker goes home and you minus `drop`.

    Equals (n-2) + p_elim[drop]. Maximised by dropping the highest p_elim.
    """
    n = len(p_elim)
    if n < 2:
        return 0.0
    return (n - 2) + p_elim[drop]


def expected_w2w_points(p_elim: list[float], drop: int, elim_index: int) -> float:
    return elim_index * expected_w2w_correct(p_elim, drop)


def survival_value(p_survive: list[float]) -> float:
    """Expected FI points if this baker is kept at every ceremony they actually survive."""
    return sum((t + 1) * p for t, p in enumerate(p_survive))


def _names(rows: list[dict[str, Any]]) -> list[str]:
    return [r["baker_short"] for r in rows]


def attach_card(payload: dict[str, Any]) -> dict[str, Any]:
    rows = list(payload.get("rows") or [])
    specs = ceremony_specs()
    w2w_order = sorted(rows, key=lambda r: -r.get("p_elim", 0))
    fi_order = sorted(rows, key=lambda r: (-survival_value(r.get("p_survive") or []), -r.get("p_win", 0)))

    w2w_ceremonies = []
    remaining = list(w2w_order)
    for spec in specs[:2]:
        n_drop = min(spec["n_drop"], max(0, len(remaining) - spec["n_advance"]))
        if spec["kind"] == "winner":
            n_drop = max(0, len(remaining) - 1)
        drops = _names(remaining[:n_drop]) if n_drop else []
        remaining = remaining[n_drop:]
        w2w_ceremonies.append(
            {
                "elim_index": spec["elim_index"],
                "kind": spec["kind"],
                "n_advance": spec["n_advance"],
                "minus": drops,
                "keep": _names(remaining),
            }
        )

    fi_tabs = []
    for spec in specs:
        keep = fi_order[: spec["n_advance"]]
        minus_this = fi_order[spec["n_advance"] :]
        # People who leave exactly at this ceremony (nested prefix).
        prev_n = spec["n_advance"] + spec["n_drop"]
        just_out = fi_order[spec["n_advance"] : prev_n]
        fi_tabs.append(
            {
                "elim_index": spec["elim_index"],
                "kind": spec["kind"],
                "n_advance": spec["n_advance"],
                "minus_this_tab": _names(just_out),
                "minus_if_still_on_all_12": _names(minus_this),
                "keep": _names(keep),
            }
        )

    p_elim = [r["p_elim"] for r in w2w_order]
    e1_drop = 0
    e2_drop = 1 if len(w2w_order) > 1 else 0
    bakers = []
    for r in rows:
        surv = r.get("p_survive") or []
        bakers.append(
            {
                "baker_id": r["baker_id"],
                "baker_short": r["baker_short"],
                "p_win": round(float(r["p_win"]), 4),
                "p_elim": round(float(r["p_elim"]), 4),
                "elim_rank": r.get("elim_rank"),
                "win_rank": r.get("win_rank"),
                "fi_value": round(survival_value(surv), 3),
                "p_finalist": round(surv[N_BOOT_CEREMONIES - 1], 4) if len(surv) >= N_BOOT_CEREMONIES else None,
            }
        )

    return {
        "app": S17["league_app"],
        "league": S17["league_name"],
        "commissioner": S17["league_commissioner"],
        "scoring": "t points per baker you kept who advanced at elimination t",
        "clock": {
            "w2w_locks_at": S17["w2w_first_lock"],
            "w2w_locks": "next two elimination ceremonies when the episode starts on Channel 4",
            "fi_locks_at": S17["fi_lock"],
            "fi_status": "DRAFT — do not lock before Cake Week",
            "if_second_ceremony_unused": "picks reopen after scores publish",
        },
        "week_to_week": {
            "do_now": True,
            "ceremonies": w2w_ceremonies,
            "expected_points_elim1_if_minus_top": round(expected_w2w_points(p_elim, e1_drop, 1), 3),
            "expected_points_elim1_if_minus_second": round(expected_w2w_points(p_elim, e2_drop, 1), 3),
        },
        "first_impression": {
            "lock_now": False,
            "winner": fi_order[0]["baker_short"] if fi_order else "",
            "final_three": _names(fi_order[:3]),
            "drop_order": _names(list(reversed(fi_order[3:]))),
            "tabs": fi_tabs,
        },
        "bakers": bakers,
    }
