# Sources and data

Inventory as of 17 September 2026. Provenance for Wikipedia ingest also lives in `data/processed/sources.csv`.

## What we actually scraped

Wikipedia **Parse API wikitext** (`action=parse&prop=wikitext`), one page per series, cached under `data/raw/wiki/`. User-Agent is set. About 0.6s between requests. Re-ingest uses the cache unless `python3 -m gbbo ingest force`.

Parsed into CSVs:

| File | Rows | What is in it |
| --- | ---: | --- |
| `data/processed/series.csv` | 17 | Year, network, hosts, judges, winner name, era labels |
| `data/processed/bakers.csv` | 204 | Age, job, hometown, place, SB count, technical wins. S17 overlay from official facts. |
| `data/processed/episodes.csv` | 155 | Theme, boot count, SB count, no-elim / double flags |
| `data/processed/baker_episode.csv` | 1,170 | HIGH/LOW/SAFE/SB/OUT/WINNER/RUNNER_UP, technical rank, bake names |
| `data/processed/history_stats.json` | 1 | Winner ages, week-1 rates, bread-week SB→final |

Handshake columns exist and are **empty** (0/1,170). `technical_set_by` is sparse (Paul 27, Prue 21, blank 107). S17 has Cake Week as a heading only: 12 baker rows, 0 technical ranks, `n_eliminated=0` because nothing has aired.

Technical ranks are good for S2–S7, S9, S12–S16. Weak where Wikipedia tables omit them: **S8 44%, S10 16%, S11 52%**. S1 69%. That is why winner vs field technical percentiles (0.575 vs 0.451) are directional, not a law.

S17 bios in `gbbo/s17.py` are **hand-extracted facts** (age, job, hometown, a few 0/1 flags). Official first names only. Not copied bio essays.

## In the CSVs, used by the model

- Age curve, occupation group, Shannon reserve flag, chaos / precision-job / heritage / late-starter knobs (S17 only).
- Historical HIGH/LOW/SB/SAFE → final rates, bread-week SB → final (8/15), winner SB counts (David is the real zero-SB winner; Edd’s zero is S1).
- Monte Carlo on those priors. No handshake. No recap valence yet. No Monica Kim merge.

## Cited, not ingested

| Source | Why it is cited | Why it is not in the CSVs |
| --- | --- | --- |
| TVmaze show 2950 / 17x01 | Calendar, Cake Week briefs | Calendar only so far |
| CRAN `bakeoff` 0.2.0 / apreshill | Teaching dataset S1–10 | HIGH/LOW collapsed to IN |
| monica-m-kim/Great-British-Bake-Off (MIT) | Handshake + ingredients S3–16 | Not merged yet |
| nathangiusti/BakeOff | Human −1/0/+1 valence, theme difficulty | No license; Netflix numbering; ideas only |
| dantaki/DeepBake | Wiki HIGH/LOW/SB/tech → NN | n=16; we are not training a net |
| Times / @GBBOData 2025 | Trifecta ~69% to final; most-credentialed finalist ~36% | Instagram, no public CSV |
| OLBG 16 Sep 2026 table | Theoretical 6/4 Shannon | Overround ~335%; unofficial surnames |
| Fantasy Bake Off | Different scoring | Not this league |
| Bracketology | The pool we play | Do not scrape picks or leaderboards |

## Weekly recap map (after air, facts + URLs only)

1. Wikipedia series 17 — technical order, HIGH/LOW, SB, OUT  
2. r/bakeoff watchalong — handshakes Wikipedia will miss  
3. Digital Spy or Metro — same-night exit + SB  
4. Radio Times — who left + **next week’s challenges**  
5. Channel 4 press “baker leaves the tent”  
6. *Second Helpings* — same Tuesday night  
7. User notes in `data/weekly/s17eNN.md`

Do not dump article text. US recaps (Vulture, Decider) are Friday insurance.

## Markets (rechecked 17 Sep 2026)

No Series 17 winner contract on Polymarket, Kalshi, Metaculus, or PredictIt. UK books not open. OLBG is labelled theoretical.

## Extra sources found this pass (not in the repo)

| Source | Extra fields | Risk | Verdict |
| --- | --- | --- | --- |
| Wikipedia **bake-table cell colours** already in our wikitext cache | Handshake (salmon) on signature/showstopper, S8+ | CC BY-SA | Parse it; we already downloaded it |
| monica-m-kim CSVs | `signature_handshake`, `showstopper_handshake` S3–16 | MIT | Merge into empty handshake columns |
| hollywoodhandshakes.com / sebzapata lists | Handshake through ~S14 | No license; stills are LP copyright | Cross-check names only, no images |
| TVmaze episode `summary` | Pre-air challenge briefs | CC BY-SA | Store facts (stout cake, coffee-walnut technical, self-portrait) |
| Radio Times listings | Next-week theme **before** wiki updates | Copyright; facts OK | Weekly notes, not a scrape |
| Powell 2023 JQAS, endure-Elo / reversed Plackett–Luce | Method (F1, not GBBO) | Paper | Fits “worst leaves”; do not cite as Lenti & Sanna Passino |
| erdavis 2019 technical-difficulty blog | Recipe familiarity S1–9 | Needs recipes | Skip; official recipe collections are ToS-blocked |
| Kaggle / shaunedwards gbbo-api | Wiki remixes | Unclear | Skip |
| Tableau Public GBBO sample | Handshake + fake “My Rating” | Educational; no redistribution | Already banned fake ratings |
| amyksu Netflix VTT sentiment | S1–4 subtitle NLP | Netflix copyright | Do not copy |
| Official bakeoff.co.uk recipes | Difficulty/time | Site forbids copying recipe collections | Do not scrape |
| BARB ratings | Viewers | Unrelated to who leaves | Ignore |

## Do not ingest

IMDb, Fandom, full recaps, Junior/Celebrity as winner priors, OLBG/Bracketology surnames as official names, subtitle files, recipe dumps, fantasy/Bracketology leaderboards.

## Add next (value vs hassle)

1. **Handshakes** into the columns we already have. Monica Kim + wiki cell colour + weekly notes after air. Helps Week to Week. Does not pick the trophy.  
2. **Pre-air briefs** (TVmaze summary, Radio Times listing, Telegraph first look) for the two locked ceremonies. Wiki is late.  
3. **Theme as a this-week modifier** (chocolate/pastry harder) from episode titles we already store.  
4. **Human valence in `data/weekly/`** after each episode. Do not train a recap classifier on 16 winners.  
5. Optional later: discrete-time elim / endure-Elo on technical + HIGH/LOW, leave-one-series-out. Not DeepBake.

## Method notes we already trust

Nick Ahamed: this week’s package (especially LOW + last in technical) drives the boot more than last week’s Star Baker. Times / GBBO Data: handshake + technical win + SB (“trifecta”) often reach the final; the most decorated finalist still wins about a third of the time. David Atherton won with zero Star Baker.
