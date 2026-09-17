# GBBO Series 17 bracket

Friend-pool toolkit for **The Great British Bake Off series 17** (UK) / **The Great British Baking Show Collection 14** (Netflix US).

Not a betting shop. Not affiliated with Love Productions, Channel 4, or Netflix. As of 17 September 2026 there is **no** live Polymarket or Kalshi contract for this series.

Weekly work is done by the Cursor skill at `.cursor/skills/gbbo-weekly/SKILL.md`. Agents run the two commands below; there is no product CLI for humans.

## Agent commands

Python 3.11+, stdlib only.

```bash
python3 -m gbbo ingest         # Wikipedia cache → CSVs
python3 -m gbbo ingest force   # refetch Wikipedia, then rebuild
python3 -m gbbo report         # week-0 rankings + preseason report
python3 -m gbbo report N       # write reports/weekly/s17eNN-….md, then edit it
```

After an episode: notes in `data/weekly/s17eNN.md` (from `_template.md`), `ingest force`, `report N`, **commit and push**. Bugbot only sees pushed commits.

## Layout

```
data/processed/     canonical CSVs
data/raw/wiki/      cached Wikipedia wikitext (CC BY-SA)
data/weekly/        episode notes (URLs + original bullets, not recap dumps)
reports/weekly/     human reports, one new file per run
gbbo/               ingest, parser, model, report
.cursor/skills/     weekly agent skill
```

## Model, in one paragraph

Pre-season is a nearly flat 1/12 with tiny knobs (age curve, precision-job analog, self-described chaos, Shannon’s 2025 reserve stint) then a Monte Carlo of nine boots and a noisy final of three so the field stays evened out. After episodes exist, the boot is scored from **this week’s** package. Season-win odds are an EWMA of those scores simulated forward. Star Baker count is a feature, not the answer — David Atherton won with zero.

We do **not** observe which judge wanted whom to leave. Hollywood handshake is the only regular Paul-specific observable.

## Data license

Historical results are parsed from Wikipedia and cached here. Wikipedia text is [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Official baker bios are copyrighted; we store extracted facts and URLs, not copied prose.

## Calendar

- UK: Tuesday 22 September 2026, 8pm, Channel 4, Cake Week first. **Week to Week Elim 1+2 lock at that start.**
- US: Friday 25 September 2026, Netflix.
- First Impression locks at the **start of Episode 2** (Tuesday 29 September 2026, 8pm BST). Do not submit it preseason.
- Pool: Bracketology league **Ready, set, BrAcKEt**. Minus advancers; points = elimination number × people you correctly kept.
- 10 episodes, 12 bakers, finale of 3 unless a non-elim week forces a double later.
