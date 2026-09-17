# Plan (critic-revised v1)

Researched 17 Sep 2026. Series 17 starts 22 Sep UK / 25 Sep Netflix US. This is the shipped architecture, not the research wishlist.

## Critic cuts

- **No SQLite.** CSVs. The table count is small.
- **No 12-team tournament tree.** Sequential boot path. “Evened out” = probabilities are not 40% on a pre-season favourite, and the path is internally consistent.
- **No OLBG / Guardian joke rankings as data.**
- **No secret judge-vote model.** We cannot see it.
- **No IMDb scrape, no recap dumps, no Junior/Celebrity priors.**
- **No GPU ranking model.** n=16 trophies.
- **Shannon-as-favourite because 6/4** is not a thing. Reserve baker ×1.08 only.
- **Surnames:** official first names; Wikipedia surnames stored with source flags.

## Product

CLI + Cursor skill + weekly markdown report.

Weekly report is generated **last**, as its own file, in human language, with tables and links.

## Implementation order (this session)

1. Repo layout, CLI, Wikipedia wikitext parser.
2. Ingest series 1–17, overlay S17 bio facts.
3. History stats (ages, SB, technicals, week-1 rates).
4. Pre-season model + week-0 CSV.
5. Pre-season weekly report.
6. Skill + docs.
7. Public GitHub repo `sjtindell/gbbo-bracket`.

## Later (not blocking v1)

- Merge Monica Kim handshake column.
- Leave-one-series-out scoreboard in `outputs/backtest.json`.
- `ingest-week` auto-merge of YAML in the notes file.
- Optional friend-consensus fade if the user pastes the group’s picks.
