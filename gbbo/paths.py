from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
WIKI_RAW = RAW / "wiki"
PROCESSED = DATA / "processed"
WEEKLY = DATA / "weekly"
CORPUS = DATA / "corpus"
REPORTS = ROOT / "reports"
WEEKLY_REPORTS = REPORTS / "weekly"
OUTPUTS = ROOT / "outputs"
PREDICTIONS = OUTPUTS / "predictions"
DOCS = ROOT / "docs"

USER_AGENT = (
    "GBBOBracket/0.1 (https://github.com/sjtindell/gbbo-bracket; "
    "research project for a friend pool; not affiliated with Love Productions)"
)


def ensure_dirs() -> None:
    for path in (
        RAW,
        WIKI_RAW,
        PROCESSED,
        WEEKLY,
        CORPUS,
        WEEKLY_REPORTS,
        PREDICTIONS,
        DOCS,
    ):
        path.mkdir(parents=True, exist_ok=True)
