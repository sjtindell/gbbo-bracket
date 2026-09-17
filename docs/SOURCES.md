# Sources

Provenance also lives in `data/processed/sources.csv` after ingest.

## Canonical structured data

| Source | Coverage | Use | License / risk |
| --- | --- | --- | --- |
| Wikipedia series pages 1–17 | Bakers, results chart, episode tables, technical ranks | Primary scrape via Parse API | CC BY-SA 4.0 / low |
| Official class of 2026 | Series 17 bios | Extracted facts only | Copyright prose / medium |
| Channel 4 press, 8 Sep 2026 | Ages, jobs, hometowns | Confirm official first names | Press facts / low |
| TVmaze show 2950 | Airdates, episode titles | Calendar | CC BY-SA / low |
| CRAN `bakeoff` 0.2.0 | Series 1–10 | Optional seed. **HIGH/LOW collapsed to IN** — do not trust `results_raw` for favourites | MIT packaging of wiki facts |
| monica-m-kim/Great-British-Bake-Off | S3–S16 weekly + handshakes | Cross-check technicals / HS | MIT |
| nathangiusti/BakeOff | Netflix numbering, human valence scores | Feature ideas, not canonical | No license stated / medium |

## Do not ingest

- IMDb (ToS, bad airdates)
- Fandom wiki (incomplete, 403 to bots)
- Tableau Public “My Rating” (fake)
- Junior / Celebrity Bake Off as winner priors
- Full Guardian / Telegraph / Vulture / GBC article text

## Weekly recap map (UK Tuesday night)

| # | Source | Why |
| --- | --- | --- |
| 1 | Wikipedia series 17 | Technical order + HIGH/LOW |
| 2 | r/bakeoff watchalong | Handshakes, doom-edit, “should have gone” |
| 3 | Digital Spy or Metro | Same-night SB + exit |
| 4 | Radio Times | Who left + next week’s challenges |
| 5 | Channel 4 press | Official quotes |
| 6 | Second Helpings | Why they went (same night, slot TBA) |
| 7 | X `#GBBO` | Handshake catch-up |
| 8 | User notes | Primary if they watched |

US recaps (Vulture, Decider, Telly Visions) are Friday insurance after Netflix.

## Markets

Checked 17 Sep 2026: no Series 17 winner contract on Polymarket, Kalshi, Metaculus, PredictIt. Oddschecker / Paddy Power / Sky Bet specials pages had no GBBO event. betting.co.uk: markets not open. OLBG 16 Sep table is labelled theoretical.

Historical leak risk is why books often suspend late GBBO markets (Frances 2013, 2015 Ladbrokes halt, Prue’s 2017 tweet).

## Method papers / blogs (priors, not databases)

- Nick Ahamed, Analyzing the Great British Bake Off
- DeepBake (dantaki)
- Giusti BakeOff repo
- Times / @GBBOData 2025 “recipe for success”
- Lenti & Sanna Passino, reversed Plackett–Luce / endure-Elo (JQAS 2023)
- Glickman Glicko; Weng & Lin Bayesian ranking
