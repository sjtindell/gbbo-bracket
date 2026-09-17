# Method

## Problem

A friend bracket needs three different answers that people keep collapsing into one ranking:

1. Who wins the series among bakers still in.
2. Who goes home **this week**.
3. A consistent finishing path (the bracket) that can be rebuilt after a surprise boot.

Star Baker leaders are decent at (1) mid-season and bad at (2). Flashy showstoppers are the opposite.

## What we can measure

| Signal | Where it lives | Notes |
| --- | --- | --- |
| Age, occupation, hometown | Wikipedia bakers table, official bios | Weak winner prior. Occupation is not destiny. |
| Weekly result HIGH/LOW/SAFE/SB/OUT | Wikipedia results chart | HIGH/LOW is the “favourite / least favourite” flag DeepBake used. The CRAN `bakeoff` package **drops** this by mapping HIGH→IN. |
| Technical rank 1…n | Per-episode Wikipedia tables | Public through series 16. Best fully ordered weekly signal. |
| Signature / showstopper names | Same tables | Names, not scores. |
| Hollywood handshake | Recaps, Reddit, Monica Kim CSV | Paul-only. Never in the technical. Missing from most wiki tables. |
| User / recap valence | `data/weekly/` | disaster→rave mapping. This is how text becomes a number. |
| Theme week | Episode headings | Bread / pastry / chocolate difficulty is a modifier, not a fate. |

## What we cannot measure (and will not fake)

- **Which judge cast which elimination vote.** It is not published. Recaps sometimes say “Paul wanted X to stay”. That is a weekly note (`judge_split`), not a column we can regress on for 16 series.
- **Live prediction-market prices** for Series 17. None found on Polymarket, Kalshi, Metaculus, PredictIt, Oddschecker as of 17 Sep 2026. UK books had not opened. OLBG’s Shannon 6/4 table is theoretical and badly overrounded.
- **True years of baking** except where a bio states it.
- **Edit time / confessionals** as a Survivor-style feature. Wrong show.

## Council, then one stack

Four seats, then a decision:

1. **Statistician.** n=16 winners, ~192 bakers. Discrete-time elim hazard and a Monte Carlo of remaining weeks. Leave-one-series-out if we claim skill. No neural net.
2. **Tent watcher.** This week’s three bakes decide the boot. Résumé decides who is *allowed* a bad week. The final is a new contest.
3. **Scout.** Bios are marketing. Shannon’s reserve year is real and small. Clara’s two-year tenure is real and small. Moyin’s macarons-at-14 is a technical tell, not a trophy.
4. **Critic.** If the winner probability on a pre-season favourite is 25 percent, we flattened it wrong or we are LARPing as a book.

**v1 stack**

- Pre-season: almost flat weights × tiny age / job / chaos / reserve multipliers → Monte Carlo so the board is evened out.
- Weekly score \(s\): technical percentile × 3.5 + signature valence (0–2) + showstopper valence (0–3.5) + handshake + HIGH/LOW.
- Elim: softmax of \(-s\) among remaining (temperature ~1.8). Double-elim: two draws.
- Skill: EWMA \(\mu \leftarrow 0.55\mu + 0.45 s\).
- Win: 6–8k simulated remaining weeks, drop lowest, noisy final of three.
- Bracket: greedy boot order from the elim ranking, then the three left. Rebuild after every OUT.

**Models to test against each other once the corpus is in**

| Name | Use |
| --- | --- |
| Uniform | Sanity. Mean P(actual winner) should be ~1/n_start. |
| Technical-only EWMA + MC | Does the public rank list already do most of the work? |
| Full weekly score + MC | v1 |
| Star-Baker-count softmax | The friend-pool folk model. We want to beat this, not become it. |
| Age-only | Should be weak. If it wins, we overfit something else. |

Metric: leave-one-series-out mean probability on the actual winner, plus Brier on weekly OUT. Report the numbers even when they are embarrassing.

## Judge eras

- Series 1–7: Mary Berry / Paul Hollywood
- Series 8–16: Prue Leith / Paul Hollywood
- Series 17: Nigella Lawson / Paul Hollywood

Paul is the constant. Fit technical features across eras. Do not pretend Prue-era “needs more flavour” quotes are Nigella data. After week 2 of Series 17, overweight this season’s own HIGH/LOW and quotes.

## Calibration honesty

Sixteen trophies. One new co-judge. Pre-recorded show, so late “markets” (when they exist) have leaked. Friend-pool edge is: don’t crown the first Star Baker, don’t zero someone after Cake Week, don’t treat handshake as destiny, do update after every boot.
