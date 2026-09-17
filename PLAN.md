# GBBO Series 17 friend bracket — locked v1

**Locked:** 17 September 2026 (Pacific), after research + critic.  
**Status:** spec only; implement next.  
**Product:** entertainment for a friend pool. Not a book.

Council: [S17 intel](fe4e0478-948a-46cd-a0f5-739b29f8e20d), [data sources](61c2d01d-1303-4414-981b-9679b9b3f140), [recap map](3ab16a4b-9e29-4710-a0b5-787948fced32), [markets/methods](af522ab3-a1e9-48ed-a839-77b774a37dbb), [skill file](4926179e-7e90-4d74-a730-2fb18d34a5f4).  
Critic: [Critic review GBBO plan](dcb939b0-247a-4e68-ade9-210106bf1099) — **reject the draft as a research platform.** This file is the fold.

## What we ship

One Wikipedia-backed simulator. Two queries from the **same** Monte Carlo:

1. `P(boot this week)` among remaining
2. `P(win | remaining)`
3. Friend **bracket** = rank by expected finishing place from those sims (one internally consistent order, not 10 independent boot calls)

Weekly: user picks top 1–2 from the boot board. After the episode, ingest structured results, re-run remaining field.

**Even-out:** softmax temperature `T` so pre-season max `P(win) ∈ [0.12, 0.20]`. Do not edit probabilities after the fact. Marginal `P(win)` is allowed to disagree with a single path (high-variance bakers).

## Clock (Pacific user)

| Event | When |
| --- | --- |
| UK premiere | Tue 22 Sep 2026, 20:00 BST = **12:00 PDT** |
| Netflix US (Collection 14) | Fri 25 Sep 2026 (~3:01 a.m. ET historically) |
| *Second Helpings* | **same Tuesday night** (Extra Slice is gone) |
| Spoiler window | Tue noon PDT → Friday Netflix. Wikipedia/social are spoilers. |

Reports need a `SPOILER STATUS` banner. Skill must not open wiki/reddit/X if the user is waiting for Friday.

## Cuts (do not build)

Recap NLP / 0–10 recap scores · sub-agents · series 1–7 warehouse · CRAN `bakeoff` · Monica Kim · TVmaze client · C4/Radio Times/Digital Spy/Metro/Guardian scrapers · Reddit/X/Netflix · IMDb/Fandom · OLBG/Polymarket/Kalshi · theme-match matrix · age/occupation/chaos priors · Prue-taste switch · post-air elim softmax on this week’s score · “drop lowest skill” · hardcoded “36% favourite finalist” · invented surnames · SQLite · Junior/Celebrity.

Live source of truth is **user YAML**, not Wikipedia (wiki lags Tuesday night).

## Data

### Historical

Wikipedia **series 8–16 only** (C4 / Paul+Prue / ~12 bakers / 10 episodes). Closest era **except the new judge**. Nigella replacing Prue is unmeasured extra variance → **higher T**, not a feature switch.

Parse: results summary + per-episode technical ranks. Accept `HIGH|LOW|SAFE|SB|OUT|WD|N/A|WINNER|RUNNER_UP` and `n_eliminated` per episode (S13 ep3 no elim then double; S15 Jeff N/A/WD; S16 ep9 three-on-the-bottom). Resolve titles via API redirects (`The_Great_British_Bake_Off_(series_14)` vs `..._series_16`). Cache HTML. UA: `gbbo-bracket/0.1 (personal; USER_EMAIL) python-requests/x`. ~1 req/s. Commit S15 + S16 HTML fixtures.

If technical tables fail: keep HIGH/LOW/SB/OUT, skip ranks. If a series results table fails: skip that series, continue.

### Live S17

`data/weekly/s17eNN.yml` is canonical. `--from-wiki` only fills empty YAML fields; **YAML wins on conflict**. If wiki is blank and YAML is empty, fail closed.

```yaml
series: 17
episode: 1
theme: Cake
star_baker: null   # display_name
eliminated: []
high: []
low: []
technical: {}      # display_name: rank
n_eliminated: 1
notes: ""          # user-written bullets only
spoiler_ok: false
```

Hardcode ep1 theme `Cake`. Leave 2–10 empty until ingested. TVmaze already lists 17x01 Cake Week; do not scrape listings.

### S17 seed (facts)

Official first names only: **Clara, Connie, Danni, Gabe, Gary, Mo, Molly, Moyin, Nikki, Shannon, Tom, Yannis**.  
https://thegreatbritishbakeoff.co.uk/meet-the-class-of-2026/

Surnames **only if Wikipedia or official said them**: Clara Satchell-Silva, Gabe Capes, Gary Harding, Molly Chauhan, Moyin Odeniran, Tom Whittaker. Leave Connie, Danni, Mo, Nikki, Shannon, Yannis surname-blank. Fan/OLBG names (Connie Lewis, Mo Mahirr, Shannon Amy) are **not facts**.

`baker_id = {series}-{slug}` from **display first name**, stable even if wiki later adds a surname (`17-tom` not `17-tom-whittaker`). S16 also has a Tom.

Pronouns: **Danni they/them**; **Gabe they/them** (Pink News: he/they — store they/them as default). Do not misgender in reports.

Ages/occupations/hometowns from Wikipedia S17 where present. `prior_notes` only for Shannon: 2025 backup baker (Media Mole Q&A) — `×1.15` max, then renormalize. Not a favourite lock.

Judges: Paul Hollywood + **Nigella Lawson**. Hosts: Alison Hammond + Noel Fielding.

Mo is **21** (official / Radio Times). Ignore Good Housekeeping listing 32.

## Model (dumb on purpose)

One loop: structured outcomes → EWMA skill → Monte Carlo remaining weeks.

**Weekly outcome score** (structured only):

| result | points |
| --- | --- |
| SB | +2.0 |
| HIGH | +1.0 |
| SAFE | +0.2 |
| LOW | −1.0 |
| OUT | −2.0 |
| WINNER | +2.5 |
| RUNNER_UP | +1.2 |
| WD / N/A / blank | skip |

Technical: `1.5 * (1 - (rank-1)/(n_tech-1))` if rank known (1 = best). Missing technical ≠ 0; skip that term.

**Skill:** `s ← 0.65 s + 0.35 score` after each appeared week. Init `s=0`. `low_streak` = consecutive LOW/OUT.

**Pre-season S17:** all `s=0`, Shannon prior mass `×1.15`, renormalize. No age/occupation/chaos. Higher `T` than a Prue-era in-progress season.

**Hazard this week:**  
`h_i = −s_i + 0.35 * low_streak_i`  
`P(elim_i) = softmax(h / T_elim)` over remaining, unless `n_eliminated=0` or episode is the final.

**MC (5000 paths):** remaining episodes until 3 left: each week sample 1 boot (or known `n_eliminated` if a future episode is already a double — v1 default: 1 until 3 remain). After each simulated week, add `N(0, σ)` to remaining skills (`σ≈0.35`). Final 3: draw winner `softmax(s / T_final)` with `T_final > T_elim`. Do not simulate WD/illness. Do not hardcode 36%.

If pre-season max `P(win) > 0.25`, **raise T and regenerate**.

**Fit:** hardcoded weights. No gradient search.

**Validate:** leave-one-series-out on S8–16:

- Week-k boot in model’s top-2 vs random `2/(n_remaining)`
- Pre-final favourite (highest skill entering ep10) win rate
- Pre-season “favourite” is near-chance — print that so the report cannot overclaim

If LOTO boot top-2 is not clearly above chance, **keep the model** and say so. Do not add features to chase 9 C4 winners.

Post-air: the boot is **known**. Do not predict week N’s elimination after ingesting week N. `phase=post` leaves `p_elim_this_week` empty; then run `phase=pre` for week N+1.

## CSVs

No `sources.csv`. No recap corpus. `source` column on fact rows + `ATTRIBUTION.md`.

**`data/processed/series.csv`**  
`series,era,network,n_bakers,n_episodes,premiere_uk,premiere_us,judges,hosts,winner_baker_id,wiki_title`

**`data/processed/bakers.csv`**  
`baker_id,series,slug,display_name,wiki_name,full_name_sourced,age,hometown,occupation,pronouns,status,placement,prior_notes`  
`status`: `remaining|eliminated|withdrawn|winner|runner_up`

**`data/processed/episodes.csv`**  
`series,episode,theme,uk_airdate,us_airdate,n_eliminated,star_baker_id,notes`

**`data/processed/baker_episode.csv`**  
`baker_id,series,episode,appeared,result,technical_rank,n_technical,source`  
`appeared` 0/1. `technical_rank` empty if unknown.

**`data/processed/skill_state.csv`** (not `ratings.csv`)  
`series,as_of_episode,baker_id,skill,low_streak,sb_count,weeks_appeared,last_result`

**`data/processed/forecasts.csv`**  
`generated_at_utc,series,as_of_episode,phase,baker_id,p_elim_this_week,p_win,expected_finish,bracket_place,model_version`  
`phase`: `pre` | `post`

**`data/processed/name_map.csv`**  
`raw,series,baker_id`

## CLI

Package `gbbo`, run from `gbbo-bracket/`:

```text
python -m gbbo scrape-wiki --series 8-16
python -m gbbo seed-s17
python -m gbbo build
python -m gbbo validate
python -m gbbo predict --series 17 --week 1 --phase pre
python -m gbbo ingest-week --series 17 --week N [--from-wiki] [--yaml data/weekly/s17eNN.yml]
python -m gbbo predict --series 17 --week N --phase post
python -m gbbo predict --series 17 --week N+1 --phase pre
```

`predict` writes `skill_state.csv`, appends `forecasts.csv`, writes `reports/s17-weekNN-{pre|post}.md`.  
`validate` prints LOTO stats and `reports/calibration.md`.

Deps: `requests`, `beautifulsoup4`, `lxml`, `pandas`, `numpy`. Fixture tests are the scrape (S15 + S16 HTML). Sequential GETs, 1.0s sleep, cache `data/raw/wiki/series_{n}.html`. Action API `parse&prop=text` **or** wikitext; HTML `wikitable` with cell text `HIGH/LOW/SAFE/SB/OUT/...` is enough.

## Skill

`.cursor/skills/gbbo-weekly/SKILL.md`  
Frontmatter: `name: gbbo-weekly` (must match folder) + `description` (friend-bracket GBBO S17, weekly boots, winner probs).

Body: exact CLI, YAML schema, spoiler clock, **do not spawn sub-agents / do not scrape recaps / YAML wins / never invent surnames**. Skill **runs CLIs**. User may paste 5 lines they wrote into `notes`. Skill may say “you may skim r/bakeoff” — the agent must not.

## First pre-season report (`reports/s17-week01-pre.md`)

1. Banner: entertainment / friend bracket; not a book; Nigella era n=0; C4 winners n=9.
2. Clock: UK Tue 22 Sep 20:00 BST = 12:00 PDT; Netflix Fri 25 Sep; Second Helpings same Tuesday night.
3. Champion pick (highest `p_win`) + table of 12: `p_win`, `p_elim_week1`, `bracket_place`, expected finish.
4. Week 1 boot board ranked (user picks top 1–2). Cake Week only; no fake theme-fit.
5. Illustrative finishing order (`bracket_place` 1–12), labeled *one path from expected finish, not 10 separate boot calls*.
6. Per baker (templated, no LLM lore): name, age, job, hometown, pronouns if known, prior_notes, `p_win`, `p_elim_week1`, one line “near-flat prior; Shannon backup ×1.15 if applicable.”
7. Calibration appendix: LOTO vs 1/n; “pre-season ranking is barely informed.”
8. Data vintage: wiki titles, scrape time, model_version, temperature.
9. Out of scope: odds, social, recaps, handshakes, Prue-taste, OLBG surnames.

## Legal / ToS (README)

- **Wikipedia:** CC BY-SA 4.0. Attribution in README + every report footer (article titles + retrieval timestamp). Structured facts in CSV; **do not dump recap prose**. Contactable UA; sequential; generic `python-requests` alone is blocked.
- **Official GBBO / C4 press:** transcribe 12 fact rows by hand. **Do not** copy bio essays. No photos.
- **Radio Times, Digital Spy, Metro, Guardian recaps:** no scrape, no stored article text, no “summarise this URL into baker_episode.” User-authored notes only.
- **Reddit / X:** no scrapers. **Netflix:** no. **Fan sites / OLBG:** no.

## Implementation order (one coding agent)

Kill criteria in parentheses. Do not “just add Monica” if behind.

0. Scaffold: `gbbo/` package, `requirements.txt`, README, ATTRIBUTION, empty processed CSVs, skill stub.
1. Hand-seed S17: bakers / series / 10 episode slots, ep1 Cake, UK/US dates. **No HTTP to C4.**
2. Wiki scraper (the hard part): title resolve → cache HTML → bakers + results + technical ranks for **8–16**. Tests on S15 and S16 fixtures. **Do not start series 1–7.**
3. `build`: canonical IDs, `name_map.csv`, sanity (one winner/series, OUT counts vs `n_eliminated`, no duplicate `baker_id`).
4. `validate`: hardcoded EWMA + MC LOTO → `reports/calibration.md`. No parameter search.
5. `predict` week 1 pre: forecasts + **full pre-season report**.
6. `ingest-week`: YAML required-capable; `--from-wiki` optional. Recompute skill; `phase post` then next week `pre`.
7. Skill + README ToS, how to rerun, calibration humility.

## Weekly workflow (after v1 ships)

| When (PDT) | Action |
| --- | --- |
| Now → Mon 21 Sep | v1 repo, historical scrape, week 1 pre report |
| Tue 22 Sep 12:00 | UK ep1 live. Do **not** open wiki/reddit/X if unspoiled for Friday |
| Tue night / Wed | If using UK clock: fill YAML or `--from-wiki`; ingest; post week 1; pre week 2 |
| Fri 25 Sep | Netflix. Same CSVs; do not re-scrape recaps |
| Each later week | Pre: data through N−1 + theme if known. Post: YAML/wiki structured fields only |

## Calibration humility (print this)

Pre-season this is a **tempered prior**, not a forecast. **9 Channel 4 winners**, **0 Nigella episodes**. Printing `P(win)=0.18` as if it were a market is the product lying to the group. No GBBO S17 contract on Polymarket/Kalshi; UK books not open; OLBG Shannon 6/4 is theoretical (overround ~335%). Historical pre-season favourites fail (Josh 2023, Dylan 2024). Star Baker count ≠ winner (David 0 SB).
