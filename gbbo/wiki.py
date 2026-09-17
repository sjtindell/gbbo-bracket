"""Polite Wikipedia Parse API client with on-disk wikitext cache."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from gbbo.paths import USER_AGENT, WIKI_RAW, ensure_dirs

API = "https://en.wikipedia.org/w/api.php"


def _request(params: dict[str, str], pause: float = 0.6) -> dict:
    query = urllib.parse.urlencode(params)
    req = urllib.request.Request(
        f"{API}?{query}",
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Wikipedia HTTP {exc.code} for {params}") from exc
    time.sleep(pause)
    return payload


def fetch_wikitext(title: str, *, force: bool = False) -> str:
    """Return wikitext for a page. Cached under data/raw/wiki/."""
    ensure_dirs()
    slug = title.replace(" ", "_").replace("/", "_")
    cache: Path = WIKI_RAW / f"{slug}.wikitext"
    if cache.exists() and not force:
        return cache.read_text(encoding="utf-8")
    data = _request(
        {
            "action": "parse",
            "page": title,
            "prop": "wikitext",
            "format": "json",
            "formatversion": "2",
            "redirects": "1",
        }
    )
    parse = data.get("parse") or {}
    text = parse.get("wikitext") or ""
    if isinstance(text, dict):
        text = text.get("*", "")
    if not text:
        raise RuntimeError(f"No wikitext for {title}: {data.get('error')}")
    cache.write_text(text, encoding="utf-8")
    meta = {
        "title": title,
        "resolved": parse.get("title"),
        "pageid": parse.get("pageid"),
        "url": f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}",
    }
    cache.with_suffix(".json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return text


def series_title(n: int) -> str:
    return f"The Great British Bake Off series {n}"
