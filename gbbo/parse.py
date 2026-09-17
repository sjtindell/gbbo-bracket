"""Parse GBBO series wikitext into structured rows."""

from __future__ import annotations

import difflib
import re
from typing import Any

from gbbo.wikitext import (
    cell_attr_and_value,
    extract_tables,
    iter_table_rows,
    slugify,
    split_sections,
    strip_markup,
)

RESULT_ALIASES = {
    "SAFE": "SAFE",
    "IN": "SAFE",
    "HIGH": "HIGH",
    "FAV": "HIGH",
    "FAVOURITE": "HIGH",
    "FAVORITE": "HIGH",
    "LOW": "LOW",
    "UNFAV": "LOW",
    "UNFAVOURITE": "LOW",
    "SB": "SB",
    "STAR BAKER": "SB",
    "STARBAKER": "SB",
    "OUT": "OUT",
    "ELIM": "OUT",
    "ELIMINATED": "OUT",
    "WINNER": "WINNER",
    "WIN": "WINNER",
    "RUNNER-UP": "RUNNER_UP",
    "RUNNER UP": "RUNNER_UP",
    "RUNNER_UP": "RUNNER_UP",
    "SICK": "SICK",
    "WD": "WD",
    "WITHDREW": "WD",
    "QUIT": "QUIT",
    "LEFT": "WD",
}

COLOR_RESULT = {
    "lemonchiffon": "SB",
    "gold": "SB",
    "khaki": "SB",
    "cornflowerblue": "HIGH",
    "lightblue": "HIGH",
    "dodgerblue": "HIGH",
    "plum": "LOW",
    "pink": "LOW",
    "thistle": "LOW",
    "tomato": "OUT",
    "red": "OUT",
    "darkred": "OUT",
    "salmon": "OUT",
    "yellow": "WINNER",
    "limegreen": "RUNNER_UP",
    "lightgreen": "RUNNER_UP",
    "palegreen": "RUNNER_UP",
    "silver": None,  # already eliminated / empty
    "lightgrey": None,
    "lightgray": None,
    "gainsboro": None,
}

ORDINAL_RE = re.compile(r"(\d+)\s*(?:st|nd|rd|th)", re.I)
FINISH_EP_RE = re.compile(r"episode\s+(\d+)", re.I)
PLACE_RE = re.compile(r"(\d+)")
YEAR_RE = re.compile(r"first_aired\s*=\s*\{\{Start date\|[^\|]*\|(\d{4})", re.I)
YEAR_RE2 = re.compile(r"first_aired\s*=\s*.*?(\d{4})", re.I)
WINNER_RE = re.compile(r"winner\s*=\s*(.+)", re.I)
RUNNER_RE = re.compile(r"runner_up\s*=\s*(.+)", re.I)
JUDGES_RE = re.compile(r"judges\s*=\s*(.+)", re.I)
PRESENTER_RE = re.compile(r"presenter\s*=\s*(.+)", re.I)
NETWORK_RE = re.compile(r"network\s*=\s*(.+)", re.I)
EPISODES_RE = re.compile(r"num_episodes\s*=\s*(\d+)", re.I)
CONTESTANTS_RE = re.compile(r"num_contestants\s*=\s*(\d+)", re.I)

# Wikipedia results-chart typos / truncations that must map to the bakers table.
CHART_NAME_ALIASES = {
    "jairzeno": "jairzinho",
    "pui": "pui man",
}


def _template_name_and_args(text: str) -> list[tuple[str, list[str]]]:
    found = []
    for match in re.finditer(r"\{\{([^{}]+)\}\}", text):
        inner = match.group(1)
        bits = [b.strip() for b in inner.split("|")]
        found.append((bits[0].strip(), bits[1:]))
    return found


def normalize_result(raw: str, attrs: str = "") -> str | None:
    blob = (raw or "") + " " + (attrs or "")
    templates = _template_name_and_args(raw)
    for name, args in templates:
        key = name.strip().lower()
        if key in {"safe", "gbbo safe"}:
            return "SAFE"
        if key in {"eliminated", "elim", "gbbo eliminated"}:
            return "OUT"
        if key in {"good"} and args and "star" in args[0].lower():
            return "SB"
        if "winner" in key:
            return "WINNER"
        if "runner" in key:
            return "RUNNER_UP"
        if key.startswith("gbbo result") or key == "gbbo result":
            if args:
                mapped = RESULT_ALIASES.get(args[0].upper().replace("_", " "))
                if mapped:
                    return mapped
        if key in RESULT_ALIASES:
            return RESULT_ALIASES[key.upper()]

    text = strip_markup(raw).upper()
    text = re.sub(r"\[.*?\]", "", text)
    text = text.replace("STAR BAKER", "SB")
    for token in (
        "RUNNER-UP",
        "RUNNER UP",
        "WINNER",
        "STAR BAKER",
        "SB",
        "ELIMINATED",
        "OUT",
        "HIGH",
        "LOW",
        "SAFE",
        "SICK",
        "QUIT",
        "WITHDREW",
        "WD",
    ):
        if re.search(rf"\b{re.escape(token)}\b", text):
            return RESULT_ALIASES.get(token.replace(" ", " "), RESULT_ALIASES.get(token, token))

    # color fallback
    attr_l = attrs.lower().replace(" ", "")
    for color, result in COLOR_RESULT.items():
        if color in attr_l:
            return result
    if not text.strip():
        return None
    # leftover words like "N/A"
    if text.strip() in RESULT_ALIASES:
        return RESULT_ALIASES[text.strip()]
    return None


def parse_technical_rank(raw: str) -> int | None:
    text = strip_markup(raw)
    match = ORDINAL_RE.search(text)
    if match:
        return int(match.group(1))
    if re.fullmatch(r"\d+", text.strip()):
        return int(text.strip())
    return None


def parse_infobox(wikitext: str) -> dict[str, Any]:
    info: dict[str, Any] = {}
    m = YEAR_RE.search(wikitext) or YEAR_RE2.search(wikitext)
    if m:
        info["year"] = int(m.group(1))
    m = EPISODES_RE.search(wikitext)
    if m:
        info["n_episodes"] = int(m.group(1))
    m = CONTESTANTS_RE.search(wikitext)
    if m:
        info["n_bakers"] = int(m.group(1))
    m = WINNER_RE.search(wikitext)
    if m:
        info["winner_name"] = strip_markup(m.group(1).split("\n")[0])
    m = RUNNER_RE.search(wikitext)
    if m:
        info["runner_up_names"] = strip_markup(m.group(1).split("\n")[0])
    m = JUDGES_RE.search(wikitext)
    if m:
        info["judges"] = strip_markup(m.group(1).split("\n")[0])
    m = PRESENTER_RE.search(wikitext)
    if m:
        info["hosts"] = strip_markup(m.group(1).split("\n")[0])
    m = NETWORK_RE.search(wikitext)
    if m:
        info["network"] = strip_markup(m.group(1).split("\n")[0])
    return info


def _looks_like_header(cells: list[str]) -> bool:
    joined = " ".join(strip_markup(c).lower() for c in cells)
    return "baker" in joined and ("age" in joined or "occupation" in joined or "episode" in joined)


def parse_bakers_table(table: str, series: int) -> list[dict[str, Any]]:
    rows = list(iter_table_rows(table))
    if not rows:
        return []
    header_idx = 0
    for i, cells in enumerate(rows[:4]):
        if _looks_like_header(cells):
            header_idx = i
            break
    headers = [slugify(strip_markup(cell_attr_and_value(c)[1] or c)) for c in rows[header_idx]]
    # normalize header names
    mapped = []
    for h in headers:
        if "baker" in h:
            mapped.append("baker")
        elif h == "age":
            mapped.append("age")
        elif "hometown" in h or "from" == h:
            mapped.append("hometown")
        elif "occupation" in h or "job" in h:
            mapped.append("occupation")
        elif "finish" in h:
            mapped.append("finish")
        elif h == "place" or "position" in h:
            mapped.append("place")
        else:
            mapped.append(h)
    if mapped and (mapped[0].startswith("class") or "wikitable" in mapped[0]):
        mapped = mapped[1:]
    headers = mapped
    bakers = []
    for cells in rows[header_idx + 1 :]:
        values = []
        for cell in cells:
            _, val = cell_attr_and_value(cell)
            values.append(strip_markup(val))
        if not values:
            continue
        record = {headers[i]: values[i] if i < len(values) else "" for i in range(len(headers))}
        name = record.get("baker") or values[0]
        if not name or name.lower() in {"baker", "contestant", "bakers"}:
            continue
        if name.lower().startswith("class=") or "wikitable" in name.lower():
            continue
        age = None
        if record.get("age") and re.search(r"\d+", record["age"]):
            age = int(re.search(r"\d+", record["age"]).group(0))
        elim_ep = None
        finish = record.get("finish") or ""
        fm = FINISH_EP_RE.search(finish)
        if fm:
            elim_ep = int(fm.group(1))
        place = None
        place_raw = record.get("place") or ""
        if "winner" in place_raw.lower() or place_raw.strip() in {"1", "1st", "1st place"}:
            place = 1
        elif "runner" in place_raw.lower():
            place = 2
        else:
            pm = PLACE_RE.search(place_raw)
            if pm:
                place = int(pm.group(1))
        short = _short_name(name)
        occupation = record.get("occupation") or ""
        if occupation and re.match(r"^(1st|2nd|3rd|\d+th|winner|runner)", occupation, re.I):
            if place is None:
                if "winner" in occupation.lower():
                    place = 1
                else:
                    pm = PLACE_RE.search(occupation)
                    if pm:
                        place = int(pm.group(1))
            occupation = ""
        if short.isdigit() or short in {"-", "Elimination"}:
            continue
        bakers.append(
            {
                "series": series,
                "baker_full": name,
                "baker_short": short,
                "baker_id": f"{series}-{slugify(short)}",
                "age": age,
                "occupation": occupation,
                "hometown": record.get("hometown") or "",
                "finish_text": finish,
                "elimination_episode": elim_ep,
                "place": place,
            }
        )
    return bakers


def _short_name(full: str) -> str:
    """Tent name: quoted nickname if present, otherwise the first given name."""
    full = strip_markup(full)
    nick = re.search(r"[\"']([^\"']+)[\"']", full)
    if nick:
        alias = nick.group(1).strip()
        if alias and alias.lower() not in {"jr", "jnr"}:
            return alias
    parts = [p.strip(",") for p in full.split() if p.strip(",")]
    return parts[0] if parts else full


def _resolve_baker_id(name: str, bakers: list[dict[str, Any]]) -> str | None:
    key = name.lower().strip()
    key = CHART_NAME_ALIASES.get(key, key)
    if not key or key.isdigit() or key in {"-", "elimination"}:
        return None
    by_short = {b["baker_short"].lower(): b["baker_id"] for b in bakers}
    if key in by_short:
        return by_short[key]
    slug = slugify(key)
    for b in bakers:
        if slugify(b["baker_short"]) == slug:
            return b["baker_id"]
        short = b["baker_short"].lower()
        if short.startswith(key + " ") or key.startswith(short + " "):
            return b["baker_id"]
    best_id = None
    best = 0.0
    for b in bakers:
        ratio = difflib.SequenceMatcher(None, key, b["baker_short"].lower()).ratio()
        if ratio > best:
            best = ratio
            best_id = b["baker_id"]
    if best >= 0.84:
        return best_id
    return None


def _canonical_short(name: str, bakers: list[dict[str, Any]]) -> str:
    baker_id = _resolve_baker_id(name, bakers)
    if baker_id:
        for b in bakers:
            if b["baker_id"] == baker_id:
                return b["baker_short"]
    return name


def _merge_baker_episodes(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One row per (baker_id, episode); keep the more complete copy."""

    def score(r: dict[str, Any]) -> tuple[int, int, int, int]:
        return (
            int(r.get("technical_rank") not in (None, "")),
            int(bool(r.get("signature_name"))),
            int(bool(r.get("showstopper_name"))),
            int(r.get("result") not in {None, "", "SAFE"}),
        )

    by_key: dict[tuple[str, int], dict[str, Any]] = {}
    for row in rows:
        baker_id = row.get("baker_id")
        if not baker_id:
            continue
        key = (baker_id, int(row["episode"]))
        prev = by_key.get(key)
        if prev is None:
            by_key[key] = row
            continue
        keep, other = (row, prev) if score(row) >= score(prev) else (prev, row)
        if keep.get("result") in {None, "", "SAFE"} and other.get("result"):
            keep["result"] = other["result"]
        for field in ("signature_name", "showstopper_name", "technical_rank", "n_in_technical"):
            if keep.get(field) in (None, "") and other.get(field) not in (None, ""):
                keep[field] = other[field]
        by_key[key] = keep
    return list(by_key.values())


def parse_results_summary(table: str) -> dict[str, list[str | None]]:
    """Map baker short name -> list of weekly result codes (index 0 = episode 1)."""
    rows = list(iter_table_rows(table))
    if not rows:
        return {}
    # Find the row that is episode numbers, then baker rows.
    start = 0
    for i, cells in enumerate(rows[:6]):
        joined = " ".join(strip_markup(cell_attr_and_value(c)[1]).lower() for c in cells)
        if "baker" in joined or re.fullmatch(r"\d+", strip_markup(cell_attr_and_value(cells[-1])[1] or "")):
            # header-ish
            start = i
    # The last header row often has 1..10
    header_rows = []
    data_start = 0
    for i, cells in enumerate(rows):
        texts = [strip_markup(cell_attr_and_value(c)[1]) for c in cells]
        if texts and texts[0].lower() in {"baker", "bakers", "elimination chart"}:
            header_rows.append(i)
            continue
        if texts and all(re.fullmatch(r"\d+", t or "") for t in texts if t):
            header_rows.append(i)
            continue
        if i > 0 and not header_rows:
            continue
        data_start = i
        break
    if header_rows:
        data_start = max(header_rows) + 1
    out: dict[str, list[str | None]] = {}
    for cells in rows[data_start:]:
        if not cells:
            continue
        name = strip_markup(cell_attr_and_value(cells[0])[1])
        if not name or name.lower() in {"baker", "colour key", "color key", "wikitable"}:
            continue
        if name.lower().startswith("class=") or "wikitable" in name.lower():
            continue
        weekly: list[str | None] = []
        for cell in cells[1:]:
            attrs, val = cell_attr_and_value(cell)
            weekly.append(normalize_result(val, attrs))
        out[_short_name(name)] = weekly
    return out


def parse_episode_table(table: str, series: int, episode: int) -> list[dict[str, Any]]:
    rows = list(iter_table_rows(table))
    if not rows:
        return []
    header_i = 0
    for i, cells in enumerate(rows[:3]):
        labels = " ".join(strip_markup(cell_attr_and_value(c)[1]).lower() for c in cells)
        if "baker" in labels:
            header_i = i
            break
    headers = [strip_markup(cell_attr_and_value(c)[1]).lower() for c in rows[header_i]]
    col = {"baker": 0, "signature": None, "technical": None, "showstopper": None, "result": None}
    for i, h in enumerate(headers):
        if "baker" in h:
            col["baker"] = i
        elif "signature" in h:
            col["signature"] = i
        elif "technical" in h:
            col["technical"] = i
        elif "showstopper" in h or "show stopper" in h:
            col["showstopper"] = i
        elif "result" in h:
            col["result"] = i
    people = []
    for cells in rows[header_i + 1 :]:
        if len(cells) <= col["baker"]:
            continue
        name = strip_markup(cell_attr_and_value(cells[col["baker"]])[1])
        if not name or name.lower() == "baker":
            continue
        def grab(idx: int | None) -> str:
            if idx is None or idx >= len(cells):
                return ""
            return cell_attr_and_value(cells[idx])[1]

        sig = strip_markup(grab(col["signature"]))
        tech_raw = grab(col["technical"])
        show = strip_markup(grab(col["showstopper"]))
        result_raw = grab(col["result"])
        result_attrs = ""
        if col["result"] is not None and col["result"] < len(cells):
            result_attrs, result_raw = cell_attr_and_value(cells[col["result"]])
        people.append(
            {
                "series": series,
                "episode": episode,
                "baker_short": _short_name(name),
                "signature_name": sig,
                "technical_rank": parse_technical_rank(tech_raw),
                "showstopper_name": show,
                "result": normalize_result(result_raw, result_attrs) or "SAFE",
            }
        )
    n_tech = sum(1 for p in people if p["technical_rank"] is not None)
    for p in people:
        p["n_in_technical"] = n_tech
    return people


def parse_episode_meta(heading: str, body: str) -> dict[str, Any]:
    m = re.search(r"Episode\s+(\d+)\s*:?\s*(.*)$", heading, re.I)
    episode = int(m.group(1)) if m else None
    theme = (m.group(2).strip() if m else heading)
    theme = re.sub(r"\s*\(.*?\)\s*$", "", theme).strip()
    set_by = None
    if re.search(r"set by Paul", body, re.I):
        set_by = "Paul Hollywood"
    elif re.search(r"set by Prue", body, re.I):
        set_by = "Prue Leith"
    elif re.search(r"set by Mary", body, re.I):
        set_by = "Mary Berry"
    elif re.search(r"set by Nigella", body, re.I):
        set_by = "Nigella Lawson"
    return {"episode": episode, "theme": theme, "technical_set_by": set_by, "body": body}


def parse_series_page(wikitext: str, series: int) -> dict[str, Any]:
    info = parse_infobox(wikitext)
    sections = split_sections(wikitext)
    bakers: list[dict[str, Any]] = []
    results: dict[str, list[str | None]] = {}
    episodes: list[dict[str, Any]] = []
    baker_episodes: list[dict[str, Any]] = []

    for level, title, body in sections:
        title_l = title.lower()
        tables = extract_tables(body)
        if title_l == "bakers" and tables:
            bakers = parse_bakers_table(tables[0], series)
        elif "result" in title_l and tables:
            results = parse_results_summary(tables[0])
        elif re.match(r"episode\s+\d+", title_l):
            # Masterclass subsections are ==== Episode 1 ==== with no theme.
            if level >= 4:
                continue
            meta = parse_episode_meta(title, body)
            if meta["episode"] is None:
                continue
            if not meta["theme"]:
                continue
            if any(e["episode"] == meta["episode"] for e in episodes):
                continue
            ep_rows = []
            if tables:
                ep_rows = parse_episode_table(tables[0], series, meta["episode"])
            episodes.append(
                {
                    "series": series,
                    "episode": meta["episode"],
                    "title": title,
                    "theme": meta["theme"],
                    "technical_set_by": meta["technical_set_by"],
                    "n_bakers_start": len(ep_rows) if ep_rows else None,
                }
            )
            baker_episodes.extend(ep_rows)

    # Overlay HIGH/LOW from results chart onto baker_episode rows.
    by_key = {(r["baker_short"].lower(), r["episode"]): r for r in baker_episodes}
    junk_names = {
        "wikitable",
        "baker",
        "bakers",
        "contestant",
        "colour key",
        "color key",
        "elimination",
        "elimination chart",
    }
    for short, weekly in results.items():
        if short.lower() in junk_names or short.lower().startswith("class="):
            continue
        canon = _canonical_short(short, bakers) if bakers else short
        for i, code in enumerate(weekly, start=1):
            if not code:
                continue
            rec = by_key.get((canon.lower(), i)) or by_key.get((short.lower(), i))
            if rec:
                if code in {"HIGH", "LOW"} and rec["result"] in {"SAFE", "HIGH", "LOW", None}:
                    rec["result"] = code
                if code == "SB":
                    rec["result"] = "SB"
                if code in {"OUT", "WINNER", "RUNNER_UP"}:
                    rec["result"] = code
            else:
                baker_episodes.append(
                    {
                        "series": series,
                        "episode": i,
                        "baker_short": canon,
                        "signature_name": "",
                        "technical_rank": None,
                        "showstopper_name": "",
                        "result": code,
                        "n_in_technical": None,
                    }
                )
                by_key[(canon.lower(), i)] = baker_episodes[-1]

    junk_names = {
        "wikitable",
        "baker",
        "bakers",
        "contestant",
        "colour key",
        "color key",
        "elimination",
        "elimination chart",
    }
    known = {b["baker_short"].lower() for b in bakers}
    known.update(_short_name(b["baker_full"]).lower() for b in bakers)
    for short in results:
        if short.lower() in junk_names or short.lower().startswith("class="):
            continue
        if short.isdigit() or short in {"-", "Elimination"}:
            continue
        if short.lower() in known:
            continue
        if _resolve_baker_id(short, bakers):
            continue
        bakers.append(
            {
                "series": series,
                "baker_full": short,
                "baker_short": short,
                "baker_id": f"{series}-{slugify(short)}",
                "age": None,
                "occupation": "",
                "hometown": "",
                "finish_text": "",
                "elimination_episode": None,
                "place": None,
            }
        )
        known.add(short.lower())

    aliases: dict[str, str] = {}
    for b in bakers:
        aliases[b["baker_short"].lower()] = b["baker_id"]
        aliases[_short_name(b["baker_full"]).lower()] = b["baker_id"]
        aliases[slugify(b["baker_short"])] = b["baker_id"]

    cleaned_be = []
    for row in baker_episodes:
        key = row["baker_short"].lower()
        baker_id = (
            aliases.get(key)
            or aliases.get(slugify(row["baker_short"]))
            or _resolve_baker_id(row["baker_short"], bakers)
        )
        if not baker_id:
            continue
        row["baker_id"] = baker_id
        row["baker_short"] = _canonical_short(row["baker_short"], bakers)
        cleaned_be.append(row)
    baker_episodes = _merge_baker_episodes(cleaned_be)
    # drop duplicate baker_ids keeping the row with more demographic fields
    by_id: dict[str, dict[str, Any]] = {}
    for b in bakers:
        current = by_id.get(b["baker_id"])
        if current is None or (b.get("age") and not current.get("age")):
            by_id[b["baker_id"]] = b
    bakers = list(by_id.values())

    # Derive elimination episode / place if missing.
    by_baker: dict[str, list[dict[str, Any]]] = {}
    for row in baker_episodes:
        by_baker.setdefault(row["baker_id"], []).append(row)
    for baker in bakers:
        rows = sorted(by_baker.get(baker["baker_id"], []), key=lambda r: r["episode"])
        if baker["place"] is None:
            if any(r["result"] == "WINNER" for r in rows):
                baker["place"] = 1
                baker["is_winner"] = 1
            elif any(r["result"] == "RUNNER_UP" for r in rows):
                baker["place"] = 2
                baker["is_runner_up"] = 1
        baker["is_winner"] = 1 if baker.get("place") == 1 else 0
        baker["is_runner_up"] = 1 if baker.get("place") == 2 else 0
        if baker["elimination_episode"] is None:
            outs = [r["episode"] for r in rows if r["result"] == "OUT"]
            if outs:
                baker["elimination_episode"] = min(outs)
            elif baker["place"] in {1, 2} and rows:
                baker["elimination_episode"] = max(r["episode"] for r in rows)
        baker["n_star_baker"] = sum(1 for r in rows if r["result"] == "SB")
        baker["n_technical_win"] = sum(1 for r in rows if r.get("technical_rank") == 1)

    for ep in episodes:
        rows = [r for r in baker_episodes if r["episode"] == ep["episode"]]
        ep["n_eliminated"] = sum(1 for r in rows if r["result"] == "OUT")
        ep["n_star_baker"] = sum(1 for r in rows if r["result"] == "SB")
        ep["no_elimination_flag"] = int(ep["n_eliminated"] == 0 and ep["episode"] < (info.get("n_episodes") or 10))
        ep["double_elimination_flag"] = int(ep["n_eliminated"] >= 2)
        if ep.get("n_bakers_start") is None:
            ep["n_bakers_start"] = len(rows)

    info.setdefault("n_episodes", max((e["episode"] for e in episodes), default=None))
    info.setdefault("n_bakers", len(bakers))
    return {
        "series_meta": info,
        "bakers": bakers,
        "episodes": episodes,
        "baker_episodes": baker_episodes,
        "results_chart": results,
    }
