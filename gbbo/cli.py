from __future__ import annotations

import argparse
import json
import sys

from gbbo.ingest import ingest_history
from gbbo.paths import PROCESSED, WEEKLY, ensure_dirs
from gbbo.report import run_preseason, write_weekly_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gbbo", description="GBBO Series 17 friend-bracket toolkit")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ing = sub.add_parser("ingest-history", help="Fetch Wikipedia series 1–17 and write CSVs")
    p_ing.add_argument("--through", type=int, default=17)
    p_ing.add_argument("--force", action="store_true")

    sub.add_parser("seed-s17", help="Alias: ingest-history already overlays S17 bios")
    sub.add_parser("predict", help="Write ranking CSVs (week 0 = preseason)")
    p_pred = sub.add_parser("weekly-report", help="Write the human weekly report (run this last)")
    p_pred.add_argument("--week", type=int, default=0)

    p_status = sub.add_parser("status", help="Show processed data counts")
    _ = p_status

    p_week = sub.add_parser("ingest-week", help="Placeholder: merge a weekly notes file after an episode")
    p_week.add_argument("--week", type=int, required=True)

    args = parser.parse_args(argv)
    ensure_dirs()

    if args.cmd == "ingest-history":
        summary = ingest_history(through=args.through, force=args.force)
        print(json.dumps({k: v for k, v in summary.items() if k != "history"}, indent=2, default=str))
        print("history_stats keys:", sorted((summary.get("history") or {}).keys()))
        return 0
    if args.cmd == "seed-s17":
        summary = ingest_history(through=17, force=False)
        print("S17 overlay complete. bakers:", summary["n_bakers"])
        return 0
    if args.cmd == "predict":
        pred, _rep = run_preseason()
        print(f"wrote {pred}")
        return 0
    if args.cmd == "weekly-report":
        if args.week == 0:
            pred, report = run_preseason()
            print(f"wrote {pred}")
            print(f"wrote {report}")
            return 0
        from gbbo.model import predict_week0 as _pw

        payload = _pw()
        path = write_weekly_report(args.week, payload)
        print(f"wrote stub {path} — fill after episode ingest")
        return 0
    if args.cmd == "ingest-week":
        notes = WEEKLY / f"s17e{args.week:02d}.md"
        if not notes.exists():
            print(f"Create {notes} from data/weekly/_template.md first.", file=sys.stderr)
            return 2
        print(f"Notes found at {notes}. Merge into baker_episode.csv is week-1+ work.")
        print("For now: update Wikipedia cache with --force after the episode, then ingest-history --through 17 --force.")
        return 0
    if args.cmd == "status":
        for name in ("series.csv", "bakers.csv", "episodes.csv", "baker_episode.csv", "sources.csv"):
            path = PROCESSED / name
            n = sum(1 for _ in path.open()) - 1 if path.exists() else 0
            print(f"{name}: {n} rows ({path})")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
