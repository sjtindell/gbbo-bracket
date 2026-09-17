"""Wikitext helpers for GBBO series pages."""

from __future__ import annotations

import re
from collections.abc import Iterable

LINK_RE = re.compile(r"\[\[(?:[^|\]]+\|)?([^\]]+)\]\]")
HTML_RE = re.compile(r"<[^>]+>")
BOLD_RE = re.compile(r"'{2,}")
REF_TAG_RE = re.compile(r"<ref[^>]*>.*?</ref>", re.I | re.S)
NAMED_REF_RE = re.compile(r"\{\{efn\|.*?\}\}", re.I | re.S)
NOWIKI_RE = re.compile(r"<nowiki>.*?</nowiki>", re.I | re.S)


def strip_templates(text: str) -> str:
    """Unwrap or drop innermost {{templates}}, keeping visible text."""

    def split_args(inner: str) -> list[str]:
        parts: list[str] = []
        buf: list[str] = []
        link_depth = 0
        i = 0
        while i < len(inner):
            two = inner[i : i + 2]
            if two == "[[":
                link_depth += 1
                buf.append(two)
                i += 2
                continue
            if two == "]]" and link_depth:
                link_depth -= 1
                buf.append(two)
                i += 2
                continue
            if inner[i] == "|" and link_depth == 0:
                parts.append("".join(buf))
                buf = []
                i += 1
                continue
            buf.append(inner[i])
            i += 1
        parts.append("".join(buf))
        return [p.strip() for p in parts]

    def repl(match: re.Match[str]) -> str:
        inner = match.group(1)
        parts = split_args(inner)
        name = (parts[0] if parts else "").lower()
        args = parts[1:]
        if name in {"nowrap", "nobold", "nobr", "small"} or name.startswith("sort"):
            return args[-1] if args else ""
        if name.startswith("cite") or name in {"efn", "frac", "notelist", "clear", "abbr"}:
            return ""
        if name in {"safe", "gbbo safe"}:
            return "SAFE"
        if name in {"eliminated", "elim"}:
            return "OUT"
        if name in {"good"} and args and "star" in args[0].lower():
            return "SB"
        if name in {"won", "winner"} or "winner" in name:
            return "WINNER"
        if "runner" in name:
            return "RUNNER_UP"
        if name.startswith("gbbo result") and args:
            return args[0]
        return args[-1] if args else parts[0]

    prev = None
    out = text
    while prev != out:
        prev = out
        out = re.sub(r"\{\{([^{}]*)\}\}", repl, out)
    return out


def strip_markup(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = REF_TAG_RE.sub("", text)
    text = NAMED_REF_RE.sub("", text)
    text = NOWIKI_RE.sub("", text)
    text = strip_templates(text)
    text = LINK_RE.sub(r"\1", text)
    text = HTML_RE.sub(" ", text)
    text = BOLD_RE.sub("", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    text = re.sub(r"\bnowrap\|", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def slugify(name: str) -> str:
    cleaned = strip_markup(name).lower()
    cleaned = re.sub(r"[^a-z0-9]+", "-", cleaned).strip("-")
    return cleaned or "unknown"


def split_sections(wikitext: str) -> list[tuple[int, str, str]]:
    """Return (level, heading, body) for each heading including lead as level 0."""
    pattern = re.compile(r"^(={2,})(.+?)\1\s*$", re.M)
    parts: list[tuple[int, str, str]] = []
    last = 0
    last_level = 0
    last_title = "lead"
    for match in pattern.finditer(wikitext):
        body = wikitext[last : match.start()]
        parts.append((last_level, last_title.strip(), body))
        last_level = len(match.group(1))
        last_title = match.group(2).strip()
        last = match.end()
    parts.append((last_level, last_title.strip(), wikitext[last:]))
    return parts


def extract_tables(body: str) -> list[str]:
    """Extract `{| ... |}` tables, ignoring `|}` that lives inside `{{templates}}`."""
    tables = []
    start = None
    table_depth = 0
    tmpl_depth = 0
    i = 0
    n = len(body)
    while i < n - 1:
        two = body[i : i + 2]
        if two == "{{":
            tmpl_depth += 1
            i += 2
            continue
        if two == "}}" and tmpl_depth:
            tmpl_depth -= 1
            i += 2
            continue
        if tmpl_depth == 0 and two == "{|":
            if table_depth == 0:
                start = i
            table_depth += 1
            i += 2
            continue
        if tmpl_depth == 0 and two == "|}" and table_depth:
            table_depth -= 1
            if table_depth == 0 and start is not None:
                tables.append(body[start : i + 2])
                start = None
            i += 2
            continue
        i += 1
    return tables


def _split_row_cells(row: str) -> list[str]:
    """Split a wikitable row (without leading |-) into cell strings."""
    row = row.strip("\n")
    if not row.strip():
        return []
    # Header cells use ! and body cells use |. Wikipedia mixes both.
    # First, split on newline cells that start with | or !
    chunks: list[str] = []
    current: list[str] = []
    for line in row.split("\n"):
        raw = line.strip()
        if not raw:
            continue
        if raw.startswith("|+") or raw.startswith("|{"):
            continue
        if raw.startswith("|") or raw.startswith("!"):
            if current:
                chunks.append("\n".join(current))
            current = [raw.lstrip("|!").lstrip()]
        else:
            if current:
                current.append(raw)
            else:
                current = [raw]
    if current:
        chunks.append("\n".join(current))

    cells: list[str] = []
    for chunk in chunks:
        # || inline splits, but not inside templates
        pieces = _split_untemplated(chunk, "||")
        expanded: list[str] = []
        for piece in pieces:
            if "!!" in piece and "{{" not in piece:
                expanded.extend(_split_untemplated(piece, "!!"))
            else:
                expanded.append(piece)
        cells.extend(expanded)
    return [c.strip() for c in cells if c.strip() != ""]


def _split_untemplated(text: str, sep: str) -> list[str]:
    parts: list[str] = []
    buf: list[str] = []
    depth = 0
    i = 0
    n = len(sep)
    while i < len(text):
        if text[i : i + 2] == "{{":
            depth += 1
            buf.append(text[i : i + 2])
            i += 2
            continue
        if text[i : i + 2] == "}}" and depth:
            depth -= 1
            buf.append(text[i : i + 2])
            i += 2
            continue
        if depth == 0 and text[i : i + n] == sep:
            parts.append("".join(buf))
            buf = []
            i += n
            continue
        buf.append(text[i])
        i += 1
    parts.append("".join(buf))
    return parts


def iter_table_rows(table: str) -> Iterable[list[str]]:
    inner = table.strip()
    if inner.startswith("{|"):
        inner = inner[2:]
    if inner.endswith("|}"):
        inner = inner[:-2]
    # Some older GBBO tables omit the first `|-` after `{|`. Insert one
    # before the first header/data marker so split still yields rows.
    if not re.search(r"\n\|-", inner):
        inner = re.sub(r"\n(?=[!|])", "\n|-\n", inner, count=1)
    rows = re.split(r"\n\|-[^\n]*\n", "\n" + inner)
    for row in rows:
        cells = _split_row_cells(row)
        if cells:
            yield cells


def cell_attr_and_value(cell: str) -> tuple[str, str]:
    """Split optional `style=...|value` attributes from the visible value."""
    depth = 0
    for i, ch in enumerate(cell):
        if cell[i : i + 2] == "{{":
            depth += 1
        elif cell[i : i + 2] == "}}" and depth:
            depth -= 1
        elif ch == "|" and depth == 0 and "=" in cell[:i]:
            return cell[:i].strip(), cell[i + 1 :].strip()
    return "", cell.strip()
