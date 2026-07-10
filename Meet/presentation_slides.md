---
marp: true
title: Unsupervised Learning for Adaptive Market-Neutral Pairs Trading
paginate: true
---

# An Unsupervised-Learning Approach to Adaptive Market-Neutral Pairs Trading

Lalith Aditya Devaraj · KU ID 2551111
MSc Data Science · Supervisor: Dr. Gordon Hunter
Progress Presentation — 10 July 2026

---

## What Is "Pairs Trading"?

- Some pairs of companies tend to move up and down **together** — e.g. two big banks, or two oil companies.
- Sometimes the two drift apart for a while, then come back together.
- The trade: **buy** the one that has fallen behind, **short** (bet against) the one that has run ahead.
- I profit when the gap **closes again** — I don't care whether the overall market goes up or down. This is why it's called **market-neutral**.

---

## A Quick Example — Coca-Cola & Pepsi

- Coca-Cola (KO) and Pepsi (PEP) sell a very similar product to a very similar customer — their stock prices normally drift up and down **together**.
- Suppose a new **sugar tax law** is announced. It raises costs for *any* sugary-drinks maker, so **both** stocks dip by a similar amount — the relationship between them stays intact.
- Now suppose Pepsi has a one-off *good* earnings surprise from its snacks business (nothing to do with soda or the law) — Pepsi's price jumps a bit more than Coke's. A **temporary gap** opens up between them.
- My strategy: **buy Coke, short Pepsi**, betting that once the one-off news fades, the two settle back into their normal relationship — the gap closes and I profit from that, regardless of whether the whole market went up or down that week.
- (This exact pair, KO–PEP, is one my model independently re-discovered — see Step 2.)

---

## What My Project Does

- I built a pipeline that finds and trades stock pairs **automatically**, instead of a person picking them by eye.
- The key new step: a **Variational Autoencoder (VAE)** — a type of neural network — reads three months of a stock's price behaviour and compresses it into a short list of numbers, called a **latent representation**.
- **Plain English:** the VAE learns a compressed numerical summary of "how this stock behaves." Two stocks with similar summaries have behaved similarly.
- Stocks with similar latent representations are grouped together, and I only search for tradeable pairs **inside** those groups.

---

## Why This Is Interesting

Two research questions:

1. Can a learned representation (VAE) find **better** stock pairs than the traditional approach of comparing price correlation directly?
2. Is the VAE's extra complexity actually needed — or would **GARCH**, a much simpler, classical statistical model, do just as well on the same data?

**Plain English:** GARCH is an "old, standard" statistical model of how a stock's volatility (its riskiness) rises and falls over time, worked out with a handful of numbers rather than a trained neural network. I run both, side by side, and compare — on my supervisor's suggestion, since it's a fairer, simpler like-for-like comparison than my original plan.

Either answer — VAE wins, or GARCH is just as good — is a useful, honest result.

---

## What Others Have Done Before

- **Gatev, Goetzmann & Rouwenhorst (2006)** — the classic pairs-trading study; picked pairs by comparing price charts directly. Worked, but has weakened over time as more people copied it (Do & Faff, 2010).
- **Vidyamurthy (2004) / Engle & Granger (1987)** — introduced **cointegration testing**, a statistical test that checks whether two prices have a genuinely stable, mean-reverting relationship, rather than just "looking" similar.
- **Kingma & Welling (2014)** — introduced the VAE, the neural network I use to build latent representations.
- **McInnes et al. (2017)** — introduced **HDBSCAN**, the clustering algorithm I use to group similar stocks.
- **Sarmento & Horta (2020)** — closest precedent: used a linear dimensionality-reduction technique + a different clustering method (OPTICS) to pick pairs. My project takes a different comparison route: **VAE vs GARCH** (a classical volatility model) as the "does the AI earn its keep" test, using **HDBSCAN** for clustering and a plain correlation baseline for reference.
- **Engle (1982) / Bollerslev (1986)** — introduced ARCH and GARCH, the classical statistical models used here as the simple, well-understood comparison against the VAE.

---

## The Pipeline, End to End

```
Daily Prices (S&P 500)
        │
        ▼
Log Returns → 60-day windows
        │
        ▼
VAE (Variational Autoencoder)
  compresses each 60-day window into a
  12-number latent representation
        │
        ▼
HDBSCAN
  groups stocks with similar latent
  representations into clusters
        │
        ▼
Engle-Granger Cointegration Test
  within each cluster, tests every pair for a
  reliable, mean-reverting relationship
        │
        ▼
Trading Strategy
  buy the laggard / short the leader,
  market-neutral, volatility-based thresholds
        │
        ▼
Walk-Forward Backtest (2020 onward)
  rolling out-of-sample test, chained into
  one continuous equity curve
        │
        ▼
Benchmark
  VAE  vs  GARCH  vs  Correlation  vs  Buy & Hold
```

---

## My Plan, In 10 Steps

| # | Step | Status |
|---|------|--------|
| 1 | Data collection & cleaning | ✅ Done |
| 2 | Train the VAE, validate the latent representation | ✅ Done |
| 3 | HDBSCAN clustering + stability check | ✅ Done |
| 4 | Engle-Granger cointegration & pair selection | ✅ Done |
| 5 | Trading strategy (single pair + portfolio) | ✅ Done |
| 6 | Walk-forward backtest (rolling, frozen VAE) | ⏳ Next |
| 7 | Pair persistence & turnover | ⏳ Upcoming |
| 8 | Transaction costs | ⏳ Upcoming |
| 9 | Benchmark: VAE vs GARCH vs Correlation vs Buy & Hold | ⏳ Upcoming |
| 10 | Results compilation & write-up | ⏳ Upcoming |

---

## Step 1 (Done) — Getting Clean Data

- Collected 11 years of daily prices (2015–2026) for the S&P 500: **462 companies** kept (from 503 scraped — 40 removed for insufficient history, 1 for too much missing data).
- Converted prices into **log returns**, then cut each company's history into 3-month (60-day) windows so behaviour is compared fairly, on the same scale.
- Found **14 single-day price jumps over 50%**. Checked each one by hand instead of assuming they were data errors — they were real events (e.g. the PG&E wildfire crash) — so I **kept** them rather than deleting them.

---

## Step 2 (Done) — VAE & the Latent Representation

- Trained a **VAE** (Variational Autoencoder) on the earliest data only (2015–2017), then **froze it** — it's never retrained, so later results can't "leak" future information.
- **Plain English:** the VAE learns to squeeze 3 months of a stock's behaviour down into 12 numbers (the latent representation), and back out again, as accurately as possible.
- Validated that the latent representation is *meaningful*, three ways:
  - Rebuilds a stock's pattern accurately, even for data it never trained on.
  - Similar stocks land close together in latent space (checked with a permutation test and t-SNE/UMAP visualisations).
  - Well-known real pairs (e.g. JPMorgan–Bank of America) end up close together — without ever being told they're related.

---

## Step 3 (Done) — HDBSCAN Clustering

- **HDBSCAN** (Hierarchical Density-Based Spatial Clustering) automatically groups stocks with similar latent representations — and, importantly, is allowed to leave a stock **unlabelled** rather than force it into a group it doesn't belong to.
- Result: **10 clusters** found (e.g. a clean banks group, a utilities group, a REITs group).
- Checked the clusters aren't a fluke by re-running HDBSCAN 100 times on random 90% samples of the data — clusters agreed **86% of the time** (Adjusted Rand Index).
- Kept the **8 most stable clusters → 80 stocks** carried forward.

---

## Step 4 (Done) — Cointegration & Pair Selection

- Inside each stable cluster, tested **every possible pair** — 670 in total — with the **Engle-Granger cointegration test**, which checks whether the gap between two prices reliably snaps back to normal rather than drifting apart forever.
- **114 pairs** passed the statistical test. Applied quality filters (how fast the gap reverts, how big the gap typically is) to reach a clean shortlist of **112 tradeable pairs**.
- Cross-checked the top pairs with a second test (**Johansen**) as a robustness check.

---

## Step 5 (Done) — Trading Results

- **Single pair** (Northern Trust – Regions Financial): **+42.8%** cumulative return, Sharpe ratio 0.58, 69% of trades profitable.
- **Diversified portfolio** (10 pairs, no overlapping stocks): **+12.3%** cumulative return, smaller swings (max drawdown −8%), and confirmed close to **zero exposure to the overall market** (beta ≈ +0.09) — i.e. genuinely market-neutral.
- **Caveat:** these results are **before trading costs** — realistic fees are added in Step 8.

---

## Problems Encountered & How I Fixed Them

- **HDBSCAN first attempt failed** — everything collapsed into one giant cluster, no matter the settings. Root cause: I was only feeding it each stock's *average* latent representation across time, which erased how *variable* a stock's behaviour was. **Fix:** also feed in the *variability* (standard deviation) of each latent dimension, and use a different clustering setting (`leaf` mode) that keeps small, tight groups instead of merging them back together.
- **2 of the 12 VAE latent dimensions collapsed** (they stopped carrying any information — a known VAE failure mode). **Fix:** simply excluded those 2 dimensions from clustering and kept the other 10, rather than shrinking or retraining the whole VAE.
- **Engle-Granger and Johansen only agreed 50% of the time.** Resolved by treating Johansen as a *robustness check* on the top pairs only, not a hard requirement — exactly as originally planned.

---

## What Is GARCH? (The Simple Comparison Model)

- **GARCH** = **G**eneralized **A**uto**R**egressive **C**onditional **H**eteroskedasticity — despite the long name, the idea is simple.
- **Plain English:** calm periods in a stock's price tend to stay calm, and turbulent periods tend to stay turbulent. GARCH is a classical statistical formula (from the 1980s, no neural network involved) that captures this "riskiness comes in waves" pattern using just a handful of numbers per stock.
- **Pairs-trading angle:** instead of the VAE's *learned*, 12-number description of a stock's behaviour, GARCH gives a simple, transparent, few-number description based purely on its volatility pattern. I cluster and pair stocks using this simple description too, and compare the results to the VAE — this tells me whether the VAE's complexity is actually earning its keep, or whether classical statistics does just as well.

---

## What's Left To Do (Steps 6–10)

- **Step 6 — Walk-forward backtest:** re-run the whole pipeline on a rolling schedule across 2020 onward (frozen VAE, but clusters and pairs refreshed every quarter), chained into one continuous, realistic result. This is the **headline result** of the dissertation.
- **Step 7 — Pair persistence & turnover:** check how long pairs stay reliable before they stop working, and whether that relates to overall market volatility.
- **Step 8 — Transaction costs:** add realistic commissions and slippage to every trade, and check the strategy still makes money after fees.
- **Step 9 — Benchmark comparison:** re-run the exact same pipeline with **GARCH** instead of the VAE, and with a simple **rolling-correlation** pair selector instead of VAE+HDBSCAN, plus a **buy-and-hold** baseline — to see whether the AI step actually earns its keep.
- **Step 10 — Results & write-up:** compile final figures, tables, and the dissertation chapters.

---

## Time Plan

| Period | Milestone | Status |
|---|---|---|
| April 2026 | Data collection, VAE training & validation | ✅ Done |
| May 2026 | Clustering, cointegration, pair selection | ✅ Done |
| June 2026 | Single-pair & portfolio strategy | ✅ Done |
| **July–August 2026** | **Walk-forward backtest, turnover, transaction costs** | ⏳ In progress (today: 10 July) |
| August–September 2026 | Benchmark vs GARCH / Correlation / Buy & Hold | ⏳ Upcoming |
| September 2026 | Final write-up | ⏳ Upcoming |

---

## Is This Ethical?

- All data is **public, already-published stock prices** — nothing private, no personal data, no human participants involved.
- No real money is traded and no advice is given to any real investor — this is a **research simulation**.
- The dissertation will state clearly that results are a **research output**, not financial advice, and that a good backtest does not guarantee live-trading success.

---

## Legal & Professional Issues

- Stock price data (Yahoo Finance / `yfinance`) and all software used (PyTorch, HDBSCAN, statsmodels, etc.) are free, open-source, and licensed for research use.
- No personally identifiable information is processed at any point, so **GDPR / UK Data Protection Act** do not apply.
- Professional integrity: I'm reporting results **transparently**, including a known limitation — my stock list is *today's* S&P 500, which can slightly flatter historical returns (survivorship bias) — and I've disclosed this rather than hiding it. Negative or null results (e.g. if GARCH matches the VAE) will be reported honestly, not suppressed.

---

## Where Things Stand

- **5 of 10 steps complete** — the full pipeline (VAE → HDBSCAN → cointegration → trading) works end-to-end and produces a market-neutral strategy.
- What's left: making the result realistic over time (rolling backtest, trading fees) and proving the AI step was actually worth using (benchmark comparison).
- On track to finish by **September 2026**.

---

# Thank You

Questions?
