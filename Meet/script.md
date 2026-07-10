# Pairs-trading progress

---

## Opening (set the scene)

"The project is a pairs-trading strategy on the S&P 500. Pairs trading is a simple idea: I look for
two stocks that normally move together, and when they temporarily drift apart, I bet the gap will
close again, I buy the one that's fallen behind and short the one that's run ahead. It doesn't really
matter which way the whole market goes; I just need that gap between the two to come back to normal.

The new part in my version is *how* I find the pairs. Instead of eyeballing price charts, I train a
small neural network to read each stock's recent behaviour and squeeze it down to a short
latent representation, just 12 numbers. Stocks with similar latent representations get grouped together, and I only go
looking for tradeable pairs inside those groups.

I've finished the first five phases, so what I'll walk you through is: getting the data, building the
latent representations, grouping the stocks, picking the pairs, and then actually trading them."

---

## Phase 1, the data

**Message:** clean, solid foundation, 462 companies, 11 years, no gaps.

Tickers must have data starting on or before 2015-06-01


|                        |                                                                                        |
| ---------------------- | -------------------------------------------------------------------------------------- |
| **Final Ticker Count** | 462 (from 503 scraped, 40 removed for insufficient history, 1 dropped for >2% missing) |


"First I pulled daily prices for the whole S&P 500, that's about 462 companies once I drop the ones
without enough history, over roughly eleven years. I cleaned it all into one aligned table with no
missing days, and then cut each company's history into comparable 60-day snippets, about three months
each. Everything's put on the same scale so I'm comparing the *shape* of how a stock behaves, not
whether it's a cheap stock or an expensive one.

One thing worth mentioning: I found fourteen single-day moves bigger than 50%. Instead of assuming they
were errors and deleting them, I checked each one, they were real events, like the PG&E wildfire
crash, so I kept them. I didn't quietly throw anything away."

---

## Phase 2, the latent representations

**Message:** the encoder trained cleanly, and the latent representations genuinely group look-alike stocks.

### Graph: training progress (three curves)

"This first chart is just the model learning. The left curve is its overall score, it drops quickly
and then flattens out, which is exactly the healthy shape I want to see. The middle one shows it can
rebuild a stock's three-month pattern accurately, and the right one shows it's keeping the latent representations
tidy and organised rather than ignoring them. So the engine that makes my latent representations is working
properly."

### Graph: rebuilding unseen patterns (four little plots)

"These four are stocks the model never saw while training. The faint line is what the stock actually
did; the bold line is what the model rebuilds from only those 12 numbers. They track each other
closely, and that's the whole point. If 12 numbers can rebuild a stock I never showed it, then two
stocks with similar numbers really do behave similarly. That's what makes them candidate pairs."

### Graph: the map (t-SNE and UMAP)

"Here every stock is a dot, placed so that similar latent representations sit close together. The colours are
industries, and I want to stress, I never told the model the industry, it's just a sanity check.
Banks land near banks, utilities near utilities, in both layouts. But notice there are some
cross-industry neighbours too, those are exactly the non-obvious pairs a human flicking through
sector lists would never spot. That's the kind of edge this method is meant to give me."

---

## Phase 3, grouping the stocks

**Message:** 10 groups found, 8 are rock-solid, leaving 80 stocks to build pairs from.

### Graph: groups on the map

"This is the same map, but now I've coloured it by the groups the algorithm found on its own. Each
colour keeps to its own little patch instead of being scattered everywhere, that tells me these are
real clusters, not arbitrary slices through one big blob. The grey dots are stocks that didn't fit any
confident group; I just leave those out. From here on, I only hunt for pairs *inside* a single colour,
where the stocks genuinely move alike."

### Graph: how reliable the groups are

"I wanted to be sure the groups aren't just a fluke of this exact set of stocks, so I re-ran the whole
grouping 100 times, each time on a random 90% of the data. The left chart shows the results agree with
each other almost every time, a score of about 0.86 out of 1. The right chart scores each group on
its own: eight came out solid, the two weakest I dropped. That leaves 80 stocks in dependable groups."

# `mean_intra_dist` (Mean Intra-cluster Distance)

This measures:

> **How far apart points are inside the same cluster (on average)**

### In simple terms:

- Low value → points in the cluster are **very close together**
- High value → cluster is **spread out / loose**

# `persistence` (Cluster Stability Score)

This one usually comes from **hierarchical clustering / HDBSCAN-style methods**.

> It measures **how long a cluster survives as you “zoom” through density levels or linkage thresholds**

### In simple terms:

- High persistence → cluster is **stable and strongly defined**
- Low persistence → cluster **falls apart easily** when conditions change

---

## Phase 4, picking the pairs

**Message:** tested 670 candidate pairs, screened down to a clean 112-pair shortlist.

### Graph: four example pairs

"Inside those groups I test every possible pair. Each of these four panels is the *gap* between one
pair of stocks, drawn as 'how unusual is it right now'. The red lines are where I'd open a trade. See
how each line keeps stretching out and then snapping back through the middle? That spring-back is the
whole thing I profit from, and these four do it cleanly and over and over."

### Graph: the summaries and the funnel

"This zooms out to all 670 candidate pairs. The left chart is how statistically convincing each pair
is; the middle is how fast the gap springs back, I want the ones in the shaded, tradeable band, not
too slow and not just noise. The right chart is my filter in action: each bar is a quality rule, and
you can see it trimming 670 pairs all the way down to a clean shortlist of 112. That shortlist is what
I actually go on to trade."

---

## Where it's going (phases 6–10)

One line on each remaining phase:

- **Phase 6, walk-forward test.** I re-run the whole pipeline on a rolling schedule across 2020+, so the result is one continuous, realistic out-of-sample track record, the headline number of the dissertation.
- **Phase 7, pair persistence.** I check which pairs survive from one period to the next and which fade, and whether they break down more during market stress.
- **Phase 8, trading costs.** I add realistic commissions and slippage to every trade and check it still makes money after fees.
- **Phase 9, benchmark comparison.** I run the exact same pipeline with simpler engines instead of my neural network, a PCA version, a plain price-correlation version, and a buy-and-hold baseline, to prove the machine-learning part is actually pulling its weight.
- **Phase 10, results and write-up.** I pull all the final figures and tables together into the dissertation chapters.

### Explaining the PCA comparison (this is phase 9)

"My latent representations come from a neural network, which is the clever but complicated part of the project. PCA is the old, standard, textbook way of doing the same compression job. In plain terms: instead of *learning* a latent representation, PCA just looks at all the stocks and finds the handful of directions in which they vary the most, then describes each stock by where it sits along those few directions. It's simpler, faster, and has been around for decades.

The reason I include it is fairness. In phase 9 I run my whole pipeline twice, identical in every single step except the latent representation: once with the neural-network latent representation, once with the PCA one. Everything downstream, the grouping, the pair-finding, the trading rules, stays exactly the same. Then I put the out-of-sample results side by side, the returns, the reward-for-risk, the market-neutrality.

That comparison answers the question I expect you to ask: did the neural network actually earn its keep, or would plain old PCA have found just as good pairs? If my approach beats PCA, beats a simple price-correlation version, and beats just buying and holding the market, then the extra machine-learning step is justified. If it doesn't, that's an honest and still-interesting result in itself."

---

## If asked about weaknesses (be honest)

- "Everything so far is before trading costs, that's exactly what phase 8 checks."
- "My stock list is today's S&P 500, so there's some survivorship bias; I expect it to modestly
flatter the returns, and I've flagged it."
- "The single-pair result is one pair, so I don't lean on it, the basket and the upcoming
walk-forward test are the fairer picture."

