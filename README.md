# GBBO Series 17 bracket

Friend-pool toolkit for **The Great British Bake Off series 17** (UK) / **The Great British Baking Show Collection 14** (Netflix US).

Not a betting shop. Not affiliated with Love Productions, Channel 4, or Netflix. The job is to beat a group chat, not Polymarket — and as of 17 September 2026 there is **no** live Polymarket or Kalshi contract for this series anyway.

## What you get each week

1. A remaining-season **win ranking** (probabilities sum to 1 among bakers still in).
2. A full **elimination ranking** for the upcoming episode. You pick the top one or two.
3. A **bracket** that is a finishing path (who is most likely to go, in order), not a 12-team knockout tree.
4. A **separate human weekly report** in `reports/weekly/`. New file every run. English first, tables and links included.

## Quick start

Python 3.11+. Stdlib only.

```bash
cd gbbo-bracket
python3 -m gbbo ingest-history --through 17
python3 -m gbbo status
python3 -m gbbo weekly-report --week 0
```

That fetches Wikipedia series pages (cached under `data/raw/wiki/`), writes CSVs to `data/processed/`, and writes:

- `outputs/predictions/s17-week00.csv`
- `reports/weekly/s17e00-YYYY-MM-DD-preseason.md`

After an episode:

1. Fill `data/weekly/s17eNN.md` from `data/weekly/_template.md` (your notes + URLs, not pasted recaps).
2. Re-run `ingest-history --through 17 --force` once Wikipedia has the new table.
3. Run `weekly-report --week N` and edit the markdown so it sounds like you.
4. **Commit and push** (`git add -A && git commit && git push`). Weekly reports are part of the project, not local scratch.

Cursor skill: `.cursor/skills/gbbo-weekly/SKILL.md` (invoke with `/gbbo-weekly`).

## Layout

```
data/processed/     canonical CSVs (series, bakers, episodes, baker_episode, sources)
data/raw/wiki/      cached Wikipedia wikitext
data/weekly/        your episode notes
reports/weekly/     human reports, one file per run
gbbo/               ingest, parser, model, report CLI
.cursor/skills/     weekly agent skill
```

## Model, in one paragraph

Pre-season is a nearly flat 1/12 with tiny knobs (age curve, precision-job analog, self-described chaos, Shannon’s 2025 reserve stint) then a Monte Carlo of nine boots and a noisy final of three so the field stays evened out. After episodes exist, the boot is scored from **this week’s** package (technical percentile, signature/showstopper valence, handshake, HIGH/LOW). Season-win odds are an EWMA of those scores simulated forward. Star Baker count is a feature, not the answer — David Atherton won with zero.

We do **not** observe which judge wanted whom to leave. Hollywood handshake is the only regular Paul-specific observable. Nigella replacing Prue is a flavour/pleasure shift, not a new dataset.

## Data license

Historical results are parsed from Wikipedia and cached here. Wikipedia text is [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). If you reuse `data/raw/wiki/` or the derived CSVs, attribute Wikipedia. Official baker bios are copyrighted; we store extracted facts and URLs, not copied prose.

## CLI

| Command | What it does |
| --- | --- |
| `python3 -m gbbo ingest-history` | Wikipedia series 1–17 → CSVs |
| `python3 -m gbbo seed-s17` | Same overlay of Series 17 bio facts |
| `python3 -m gbbo status` | Row counts |
| `python3 -m gbbo predict` | Week-0 ranking CSV |
| `python3 -m gbbo weekly-report --week 0` | Rankings **and** the human report |
| `python3 -m gbbo ingest-week --week N` | Checks that weekly notes exist |

## Calendar

- UK: Tuesday 22 September 2026, 8pm, Channel 4, Cake Week first.
- US: Friday 25 September 2026, Netflix.
- 10 episodes, 12 bakers, finale of 3 unless a non-elim week forces a double later.
