"""Tiny agent entry points. Humans should not need this — the weekly skill runs it."""

from __future__ import annotations

import json
import sys

from gbbo.ingest import ingest_history
from gbbo.paths import ensure_dirs
from gbbo.report import run_preseason, write_weekly_report

USAGE = """python3 -m gbbo ingest [force]
python3 -m gbbo report [week]

ingest         rebuild CSVs from cached Wikipedia (series 1–17)
ingest force   refetch Wikipedia, then rebuild
report         week-0 rankings + preseason report
report N       week-N report file (then edit the markdown)
"""


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in {"-h", "--help", "help"}:
        sys.stderr.write(USAGE)
        return 0 if args else 2

    cmd, *rest = args
    ensure_dirs()

    if cmd == "ingest":
        force = bool(rest) and rest[0] == "force"
        summary = ingest_history(through=17, force=force)
        out = {k: v for k, v in summary.items() if k != "history"}
        hist = summary.get("history") or {}
        out["bread_week_sb_to_final"] = hist.get("bread_week_sb_to_final")
        out["winners_with_zero_sb"] = hist.get("winners_with_zero_sb")
        print(json.dumps(out, indent=2, default=str))
        return 0

    if cmd == "report":
        week = int(rest[0]) if rest else 0
        if week == 0:
            pred, report = run_preseason()
            print(f"wrote {pred}")
            print(f"wrote {report}")
            return 0
        from gbbo.model import predict_week0

        path = write_weekly_report(week, predict_week0())
        print(f"wrote {path} — fill after episode ingest")
        return 0

    sys.stderr.write(USAGE)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
