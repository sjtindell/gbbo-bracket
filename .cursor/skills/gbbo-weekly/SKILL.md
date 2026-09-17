---
name: gbbo-weekly
description: Run the weekly Great British Bake Off Series 17 friend-bracket update. Use when the user wants GBBO predictions, elimination ranks, the ideal bracket, a weekly report, Cake Week picks, or to ingest a new episode of Bake Off / Baking Show.
---

# GBBO weekly run

Work in this repo. Produce **two rankings** and a **separate human weekly report**. Do not overwrite previous reports.

## Models

This workspace cannot use “other models.” For any sub-agent, use **Grok 4.6 xhigh** (`cursor-grok-4.6-xhigh`). For cheap one-off chores (fetch a URL, parse a table, run a command) you may use Composer (`composer-2.5-fast`). Do not send GBBO planning or weekly synthesis to other model families.

## Modes

The pool is **Bracketology**, league **Ready, set, BrAcKEt**. Both games score **correct advancers** × elimination number, not the boot name. Minus in the app.

1. **Week to Week (before every UK air):** minus the required number from the current remaining lineup. The episode start on Channel 4 locks the **next two** ceremonies. If the second ceremony does not happen, those picks reopen after scores. Always print two minus-lists.
2. **First Impression:** one nested survivor path (12→11→…→3→winner). Locks at the **start of Episode 2**. Do not lock before Cake Week. Rebuild the path after episode 1.
3. **Post-episode:** ingest what happened, update CSVs, resimulate the remaining field, write a new report. After Ep 1, also freeze the FI card before Ep 2.

Today the user is usually on US Pacific time. UK air is Tuesday 20:00. Netflix Collection 14 drops Friday. *Second Helpings* is the same Tuesday night — spoilers land three days before Netflix.

## Do this, in order

### A. Absorb the week

If the user pasted episode notes, treat those as primary.

Otherwise search (use sub-agents in parallel):

1. Wikipedia `The Great British Bake Off series 17` — technical ranks, HIGH/LOW/SB/OUT.
2. Same-night recap: Digital Spy or Metro “who left Bake Off”.
3. Radio Times who-left tracker + **next week’s theme**.
4. Channel 4 press “baker leaves the tent”.
5. r/bakeoff watchalong thread for handshakes Wikipedia will miss.
6. Optional: Great British Chefs Howard Middleton recap (often several days late).

Store **URLs + original notes** in `data/weekly/s17eNN.md` from `data/weekly/_template.md`. Do **not** dump full articles (copyright). Do not scrape IMDb.

### B. Update data

```bash
python3 -m gbbo ingest force
```

That refetches Wikipedia series 1–17 and rebuilds `data/processed/`. Cached ingest (no network): `python3 -m gbbo ingest`. Merge user valences from the weekly notes into the prediction step. There is no separate status / seed / ingest-week command.

### C. Rank

- Week to Week minus-list = highest this-week elim hazard, count = expected boots this ceremony (usually 1). Always also emit the next ceremony’s minus, nested on the first (double-elim hedge).
- Win board = EWMA skill + Monte Carlo of leftover weeks. After a boot, drop that baker and rerun. Probabilities among remaining should sum to 1.
- First Impression = nested keep-sets from survival value \(\sum_t t\cdot P(\text{survive } t)\), not “pick a champion quote.” Prefix-consistent. Draft until Ep 2.
- Rank **everyone** for elimination. The tap is minus, not star.

Never use OLBG theoretical odds as a prior. No Polymarket/Kalshi GBBO market exists as of 2026-09-17. Do not copy Bracketology/OLBG surnames onto official first names.

### D. Agent council (short, then decide)

Before locking the report, argue these seats in a few bullets (do not pad):

- **Numbers:** what did technical ranks / HIGH-LOW / SB actually do.
- **Tent:** flavour vs bake-through; Nigella pleasure vs Paul technical; only record a judge split if a source said it.
- **History:** n=16, David won with 0 SB, first-week disasters recover, final is a new contest (~36% most-credentialed finalist).
- **Critic:** kill overfit, invented surnames, and “the data says they will win”.

Then pick one stack. Default v1: weekly 0–10 score → softmax elim; EWMA + Monte Carlo for P(win).

### E. Weekly report LAST

```bash
python3 -m gbbo report N
```

Then **edit** `reports/weekly/s17eNN-YYYY-MM-DD.md` so it reads like a person. Requirements:

- English, not LLM throat-clearing (“In the ever-evolving landscape…”).
- What happened, who to **minus** this ceremony and the next, FI status (draft vs locked).
- Tables: P(win), elim ranks, technical order, nested keep sizes.
- Links to the recaps you actually used.
- Per-baker paragraph or bullet.
- Explicit uncertainty. Small sample. New judge.
- Clock: W2W locks at Channel 4 start; FI locks at start of Episode 2.

This report is a **new file every week**. Keep the preseason report on disk.

### F. Commit and push before you stop

Do this **every weekly run**, and after any parser/model/report change. Do not leave outputs only on disk.

```bash
git add reports/weekly data/processed data/weekly outputs
git add -A   # if code or docs changed too
git status
git commit -m "Add S17 week N report and updated rankings."
git push origin HEAD
```

If there is nothing to commit, still check `git status -sb` so we know origin is current. Bugbot and GitHub reviews only see what is pushed.

## Facts that are easy to get wrong

- Official bios are first names. Do not treat Bracketology/OLBG surnames as official.
- The pool scores advancers × ceremony number. “Pick the boot” is the minus action, not the points formula.
- Week to Week always needs two ceremonies ahead. First Impression waits until after episode 1.
- Shannon said she was a 2025 reserve baker (Media Mole Q&A). Small prior, not a lock.
- Mo’s age is 21 (Good Housekeeping has had 32 — wrong).
- Danni: they/them in official copy. Gabe: he/they (Pink News).
- Cake Week ep 1: stout cake signature, Nigella coffee-and-walnut technical, self-portrait showstopper (Telegraph first look). That is challenge intel, not a result.
- We do **not** observe which judge cast which elimination vote. Handshake = Paul liked a bake.

## Legal

Wikipedia = CC BY-SA, attribute. No full recap text. Not affiliated with Love Productions / Channel 4 / Netflix.
