# Dissertation Project Phases (Revised)
## An Unsupervised Learning Approach for Adaptive Market-Neutral Pairs Trading
### Variational Autoencoders and Clustering for Asset Relationship Discovery

---

### Scope Note

This plan is scoped to exactly what the approved MSc project form commits to: one VAE, HDBSCAN clustering, Engle–Granger cointegration, a market-neutral pairs trading strategy with adaptive volatility-based thresholds, walk-forward validation, and benchmarking against traditional pairs trading. Depth at each step is prioritised over breadth across extensions. Deferred ideas (β-VAE, temporal convolutional VAE, HMM regime conditioning, risk-parity allocation, exposure management, full turnover-cost sensitivity, component ablation) are preserved in a separate `future_work.md` for the Discussion and Future Work chapter.

The original seventeen-step plan has been re-grouped into ten higher-level phases. No committed work has been removed; sub-steps that were previously stand-alone phases now sit beneath the consolidated phase that owns them. The collapse is purely organisational and is reflected in the proposal's Gantt chart and method narrative.

---

## Phase 1 — Data Foundation: Universe, Cleaning, and Feature Engineering

**Purpose.** Produce a clean, model-ready tensor of fixed-length log-return windows for every viable S&P 500 constituent over the 2015–2026 study period.

**Sub-steps.**

- *Universe selection and data acquisition.* Define the investment universe (S&P 500 constituents) and download daily adjusted-close, open, high, low, and volume across the full study window. The date range covers multiple market regimes (bull, bear, crisis, sideways) — at least 5–7 years. Record the data source, retrieval date, and known limitations (survivorship bias from current-membership tickers, corporate actions, delisted names). The universe-choice justification is a viva target.
- *Cleaning and alignment.* Resolve missing values caused by trading halts, cross-exchange holidays, or new listings. Apply split, reverse-split, and dividend adjustments via `auto_adjust=True`. Document survivorship bias explicitly and its expected directional effect. Align all tickers to a common trading calendar; remove tickers with insufficient history (e.g. < 80% coverage). Maintain a written audit logging every decision and threshold.
- *Feature engineering.* Convert prices to log returns for stationarity and scale-invariance. Apply per-window z-score normalisation. Choose a 60-day lookback window (the headline value, justified with reference to typical pair-spread half-lives and prior literature; an optional sensitivity check at 30/60/90/120 days is permitted in Phase 9 if scope allows). Structure the data as a 3-D tensor of (assets × windows × window length).

**Outcome.** A cleaned, aligned price matrix with a documented data-quality audit; a 3-D tensor of normalised 60-day log-return windows ready for VAE ingestion; a defensible written rationale for the universe choice and the window length.

---

## Phase 2 — VAE Training and Latent Space Inspection

**Purpose.** Train a single Variational Autoencoder once on the initial training window, freeze its weights, and verify quantitatively that the resulting 12-D latent space encodes economically meaningful behaviour before any downstream clustering is attempted.

**Sub-steps.**

- *Architecture and training.* Build a dense VAE with a low-dimensional latent space (8–16 dimensions; 12 is the headline value), with the encoder parameterising a Gaussian posterior (mean, variance) and the decoder reconstructing the input return window. Train using the standard ELBO objective (reconstruction + KL divergence) on the initial training window only (e.g., 2015 to end of 2017). Apply early stopping; tune latent dimension, hidden-layer width, learning rate, and batch size. Save weights, training logs, and loss curves. Maintain a short design note explaining each hyperparameter choice — examiners will ask.
- *Freeze.* On reaching stable convergence, **freeze the VAE weights**. They will not be updated again at any later stage of the project. This is a deliberate methodological choice (see Phase 6); it makes the latent space a fixed coordinate system across all walk-forward windows so cluster identity, pair persistence, and turnover analysis are coherent.
- *Latent inspection.* Extract latent vectors (mean of the variational posterior) for every asset. Visualise in 2-D using both t-SNE and UMAP, colour-coded by sector and market-cap. Confirm that known related assets (KO–PEP, JPM–BAC, V–MA) appear proximate. Compute silhouette score by sector, t-SNE/UMAP trustworthiness, and a permutation test of latent-distance vs. return-correlation alignment. Inspect per-dimension KL divergence to detect posterior collapse.

**Outcome.** A trained, frozen VAE with documented convergence behaviour and reconstruction quality on held-out data; visual and quantitative confirmation that the latent space encodes meaningful asset relationships; per-dimension KL diagnostics showing no posterior collapse; a written design note covering all hyperparameter choices.

---

## Phase 3 — HDBSCAN Clustering and Stability Analysis

**Purpose.** Group assets in the latent space into behaviourally coherent clusters and quantify how stable those clusters are under perturbation, before committing them to downstream cointegration testing.

**Sub-steps.**

- *Clustering.* Apply HDBSCAN to per-asset behavioural fingerprints derived from the latent vectors. Configure `min_cluster_size`, `min_samples`, and the distance metric (Euclidean or cosine). Record cluster labels, membership probabilities, persistence scores, and outlier scores. Tune hyperparameters by jointly evaluating DBCV index and economic interpretability — 50 micro-clusters is too fragmented, 2 mega-clusters is too coarse.
- *Composition profile.* For each cluster, report size, sector/industry distribution, average intra-cluster return correlation, and average pairwise latent distance. Compare cluster composition against GICS sector classifications to quantify how much the ML-discovered structure aligns with or diverges from human-defined categories.
- *Stability analysis.* Bootstrap-resample the latent profile tensor (≈100 iterations), re-run HDBSCAN on each resample, and compute the Adjusted Rand Index (ARI) between original and resampled cluster assignments. Report mean and standard deviation of ARI. Clusters with low individual stability are flagged for exclusion from pair search downstream.

**Outcome.** A documented set of dense, well-separated asset clusters with noise-labelled outliers excluded; a composition report covering sector alignment, intra-cluster cohesion, and bootstrap stability; a viva-defensible answer to "how do you know your clusters are real?"

---

## Phase 4 — Cointegration Testing and Pair Selection

**Purpose.** Reduce the candidate pool produced by clustering to a high-quality, statistically validated, economically sensible shortlist of tradeable pairs.

**Sub-steps.**

- *Intra-cluster cointegration.* Within each stable cluster, run pairwise Engle–Granger cointegration tests. For each pair record the test statistic, p-value, OLS hedge ratio, and the residual spread's half-life of mean reversion (from an AR(1) coefficient or OU fit). Long half-lives (> 60 days) make pairs untradeable even when statistically cointegrated.
- *Johansen robustness check.* Run the Johansen test on the top-N pairs identified by Engle–Granger and document the agreement rate. Johansen is more robust in finite samples and handles multivariate relationships; the comparison directly addresses the standard viva challenge.
- *Pair filtering.* Apply quality gates: Engle–Granger p-value below threshold (e.g., 0.05); half-life inside a tradeable range (e.g., 5–60 days); spread variance large enough to generate returns above transaction costs; and a plausible economic story. Document the number of pairs removed at each gate and the rationale for each threshold so the choice is transparent rather than fitted.

**Outcome.** A ranked master list of all candidate pairs across all clusters scored by cointegration strength and mean-reversion speed, with a Johansen robustness check on the top pairs; a final filtered shortlist of high-quality pairs forming the tradeable universe for all subsequent strategy phases.

---

## Phase 5 — Strategy Implementation: Single-Pair Baseline and Multi-Pair Portfolio

**Purpose.** Implement the trading logic on one pair to isolate mechanics, then scale to a multi-pair portfolio to demonstrate diversification and verify aggregate market-neutrality.

**Sub-steps.**

- *Single-pair mechanics.* Construct the spread as a linear combination of the two assets using the cointegration hedge ratio from Phase 4. The hedge ratio is what makes each trade market-neutral by design: long and short leg sizes are calibrated so that the combined pair has approximately zero net exposure to the broad market, and P&L comes from spread reversion rather than directional moves. Standardise the spread using a rolling z-score over a 60-day window. Use fixed z-score levels for entry (e.g., ±2.0) and exit (e.g., ±0.5); because the rolling standard deviation in the denominator scales with local spread volatility, the equivalent threshold in absolute price space adapts to the current market regime — wider in volatile periods, tighter in calm periods. This is the "dynamic spread modelling with adaptive volatility-based thresholds" specified in the project summary.
- *Single-pair backtest.* Run the strategy on a held-out window not used in VAE training or pair selection. Record cumulative return, annualised return, Sharpe ratio, maximum drawdown, average trade duration, win rate, and profit factor.
- *Multi-pair portfolio.* Select the top N pairs (8–12) from the shortlist and trade simultaneously with equal-weight capital allocation (1/N per pair). Because each pair is individually market-neutral, the aggregate portfolio is also market-neutral at entry. Aggregate individual P&L curves into a portfolio equity curve and record portfolio-level metrics (cumulative return, Sharpe, drawdown, diversification ratio).
- *Exposure diagnostic.* Flag any stock appearing in more than one pair, report sector concentration, and verify empirically that the aggregate portfolio beta to the broad market is close to zero. No structural correction is applied at this stage; the diagnostic itself is a viva-ready answer on whether the portfolio is genuinely market-neutral and diversified.

**Outcome.** A single-pair backtest that establishes the baseline mechanics (with the market-neutrality and adaptive-threshold properties explicitly documented), and a multi-pair portfolio backtest demonstrating diversification benefits with an empirical aggregate-market-neutrality check.

---

## Phase 6 — Walk-Forward Pipeline (frozen VAE)

**Purpose.** Run the full pipeline on a rolling-window schedule across the entire out-of-sample period using the frozen VAE from Phase 2, producing a single continuous out-of-sample equity curve.

**Sub-steps.**

- *Walk-forward design.* Specify the training window length (initial 2015–2017 used to train the VAE), the rebalancing frequency (every 3 months), and the test window length (3 months of forward trading per rebalance, non-overlapping on the test side to prevent look-ahead). Map the full dated train/test schedule across the dataset.
- *Frozen-VAE execution.* This is the methodological centrepiece. **The VAE is trained once in Phase 2 and frozen for the rest of the project; its weights do not update in any walk-forward step.** At each rebalance, only the downstream stages re-fit:
    - Push the latest 60-day return windows for every asset through the *frozen* VAE → fresh latent codes;
    - Re-run HDBSCAN on the fresh latent codes → fresh clusters;
    - Re-run intra-cluster Engle–Granger cointegration → fresh ranked pairs;
    - Re-apply the pair filters → fresh tradeable shortlist;
    - Trade the new pair set across the next 3-month window with the strategy from Phase 5.
- *Why frozen.* (i) Latent identity stability across windows — dimension *k* of the latent code means the same thing in every rebalance, which is a prerequisite for the persistence and turnover analysis in Phase 7. (ii) The VAE encodes generic, slow-moving return-shape patterns that are not expected to drift quarter-to-quarter; the regime adaptivity required by the project aim is delivered by the re-clustering and re-cointegration in fresh data, not by re-training the encoder. (iii) Lower compute cost and a cleaner, more defensible viva story regarding look-ahead bias.
- *Continuous equity curve.* Chain the per-window P&L into one continuous out-of-sample equity curve spanning the entire test period. Produce per-window performance attribution so it is possible to discuss which market conditions the system handles well.

**Outcome.** A complete walk-forward backtest with a frozen VAE and quarterly re-clustering, producing a continuous out-of-sample equity curve, full aggregate performance metrics, and per-window performance attribution. This is the headline result of the dissertation.

---

## Phase 7 — Pair Persistence and Turnover Analysis

**Purpose.** Analyse how the pair portfolio evolves across rebalances, validate (or challenge) the need for re-clustering, and substitute a quantitative turnover-vs-volatility link for an explicit regime model.

**Sub-steps.**

- Track which pairs survive from Window N to Window N+1, which are dropped, and which are newly discovered. Compute pair persistence rates and identify long-lived pairs (4+ consecutive windows) versus transient ones (one window only).
- Compute portfolio turnover at each rebalance and visualise pair lifetimes as a heatmap or Gantt-style chart.
- Overlay turnover against a market volatility proxy (VIX, rolling realised vol of the broad index, or cross-sectional correlation dispersion) and test for correlation. This gives a defensible quantitative answer to "do pair relationships change during market stress?" without building a regime model.

**Outcome.** A pair-stability report with persistence rates, turnover metrics, lifetime distributions, visual timelines, and a quantitative link between turnover and market-state proxies.

---

## Phase 8 — Transaction Cost Model and Net-of-Costs Backtest

**Purpose.** Apply a credible but lightweight transaction cost model to the Phase 6 walk-forward equity curve and report whether the strategy survives realistic friction.

**Sub-steps.**

- Define a two-component cost model: a flat commission per trade (calibrated to typical institutional brokerage) and a proportional slippage cost in basis points (estimated from bid-ask spread literature, applied to the notional traded).
- Apply the cost model to every entry, exit, and rebalancing trade in the Phase 6 walk-forward backtest.
- Report net-of-costs metrics: net cumulative return, net Sharpe ratio, net maximum drawdown, total costs as a percentage of gross returns. Plot gross vs. net equity curves side by side and state plainly whether the strategy remains profitable under realistic friction.

**Outcome.** A documented transaction cost function, net-of-costs performance metrics for the headline VAE pipeline, and side-by-side gross vs. net equity curves. A clear written statement on practical viability.

---

## Phase 9 — Benchmark Comparison: VAE vs GARCH vs Correlation vs Buy-and-Hold

> **Change from the approved proposal.** The proposal originally specified PCA as the linear-encoder
> comparator. On the supervisor's guidance this was swapped for **GARCH**, a classical volatility model,
> as a simpler and fairer "does the ML complexity earn its keep" baseline. The structure of Phase 9
> (re-run the identical downstream chain with only the encoder swapped) is unchanged — only the
> comparator itself changed.

**Purpose.** Run a head-to-head comparison that isolates the contribution of the VAE encoder by running the *same* downstream pipeline with only the encoder swapped, plus a classical pairs-trading baseline and a market reference.

**Important — Phase 9 is heavier than the headline summary suggests.** It is not "compute four Sharpe ratios and tabulate them." For the GARCH variant, the entire Phase 1 → Phase 8 chain is re-run with the encoder swapped; for the correlation baseline and buy-and-hold, the strategy and cost model are re-applied with appropriately simplified earlier stages. The reason these variants do *not* become new top-level phases is methodological: the comparison only carries weight if the *identical codebase* is run with only the encoder swapped, so splitting them into parallel implementations would introduce differences other than the encoder and weaken the apples-to-apples claim. Renumbering this work from "Phase 16" in the previous plan to "Phase 9" here does not add scope; it makes the existing commitment legible.

**Chronology — when each variant is built.** Phases 1 → 8 build and run the VAE chain end-to-end. GARCH does not exist yet during these phases; the headline VAE walk-forward equity curve is finished by the end of Phase 8. Phase 9 is where the GARCH variant and the correlation baseline are built and run for the first time. Inside Phase 9, the entire Phase 1 → Phase 8 chain is re-instantiated three times: once with GARCH swapping in for the frozen VAE, once with rolling-correlation top-N replacing the encoder + HDBSCAN, and once for buy-and-hold. So inside Phase 9, GARCH does go through Phase 3 (HDBSCAN), Phase 4 (Engle–Granger + Johansen), Phase 6 (walk-forward), Phase 7 (persistence), Phase 8 (costs) — but only inside the Phase 9 re-runs, which happen August–September on the Gantt.

**Sub-steps.**

- *GARCH variant (the classical-statistics test).* Fit a univariate GARCH(1,1) model to each stock's return series on the same 2015–2017 training window used for the VAE. For each stock, extract a small feature vector describing its volatility dynamics — persistence (α + β), long-run unconditional variance (ω / (1 − α − β)), and the mean and standard deviation of the fitted conditional-volatility series over the window — in place of the VAE's 12-number latent representation. Re-fit GARCH at every walk-forward rebalance, exactly as the frozen VAE re-encodes fresh windows. Re-run Phase 3 HDBSCAN on the GARCH feature vectors, with its own hyperparameter pass and DBCV check, plus the bootstrap-ARI cluster stability. Re-run Phase 4 intra-cluster Engle–Granger and pair filters. Re-run the Phase 6 walk-forward pipeline. Re-run Phase 7 persistence/turnover. Re-apply the Phase 8 cost model. Output: a second equity curve directly comparable to the VAE one, because every step except the encoder is identical.
- *Correlation baseline (the classical pairs-trading reference).* Replace the encoder and clustering with rolling-Pearson pair selection: in each rebalance window, compute pairwise return correlations across the universe, take the top-N most correlated pairs, validate each with Engle–Granger, run the Johansen robustness check on the top pairs (mirroring Phase 4 of the VAE and GARCH chains so that all three active pipelines receive the same cointegration treatment), apply the same pair-quality filters, then trade with the same z-score rule and the same cost model. This is the baseline the dissertation's headline claim must beat to justify the ML pipeline. The correlation matrix is computed across the full 500-stock universe at each rebalance — this is one cheap matrix operation, not 124,750 separate computations, and matching the universe size across all three pipelines is what preserves the apples-to-apples comparison. The pre-filter exists specifically to bound the cointegration-test count and avoid the multiple-testing burden of exhaustive pairwise testing, mirroring the cluster-based pre-filter used by the VAE and GARCH pipelines.
- *Buy-and-hold (market reference).* Track the broad market index over the same out-of-sample window with the same cost model on entry and exit only. Contextualises absolute returns of all the active strategies.
- *Comparison.* Compare all four variants head-to-head on identical windows and identical costs across: net Sharpe, net cumulative return, max drawdown, win rate, average trade duration, turnover, and cost efficiency.

**Outcome.** A definitive head-to-head comparison table proving (or disproving) the value added by the VAE-HDBSCAN framework over both the classical correlation baseline and the volatility-based (GARCH) variant of the same pipeline, with all comparisons on equal footing.

---

## Phase 10 — Results Compilation, Visualisation, and Write-Up

**Purpose.** Produce the complete set of publication-quality figures, tables, and summary statistics for the dissertation, consistently styled and ready for embedding.

**Sub-steps.**

- Latent space visualisation (t-SNE/UMAP with silhouette and trustworthiness metrics).
- Cluster composition and bootstrap-stability charts.
- Pair lifetime heatmap and per-window attribution from Phase 7.
- Portfolio equity curves (gross and net, overlaid with volatility proxy).
- Benchmark comparison table (VAE vs GARCH variant vs correlation baseline vs buy-and-hold).
- Turnover-vs-volatility scatter and the exposure diagnostic from Phase 5.
- Standardise visual style, axis labels, captions, and legends across all figures.
- Organise outputs into a logical structure mapping onto the dissertation chapter plan.

**Outcome.** A complete, organised set of figures, tables, and summary statistics ready to be embedded directly into the dissertation, with publication-quality formatting throughout.

---

## Phase-to-Form Traceability

Every phase above traces directly to language in the approved project form:

- Phase 1 — "Data Pre-processing and Transformation" objective.
- Phase 2 — "Neural Network Design", "Latent Feature Extraction", and the "hidden structural relationships and behavioural similarities" claim in the project summary.
- Phase 3 — "Density-Based Clustering" objective and the "improved pair stability" claim.
- Phase 4 — "Cointegration Testing" objective.
- Phase 5 — "Strategy Implementation" objective, the "market-neutral trading strategy" language in the aim, and the "dynamic spread modelling" and "adaptive volatility-based thresholds" language in the project summary; aggregate market-neutrality verification.
- Phase 6 — "Backtesting Simulation" objective and the "adaptive framework that adapts to changing market conditions" language in the aim.
- Phase 7 — supporting evidence for the "evolving relationships" claim in the summary.
- Phase 8 — standard practice expected of any backtest-based dissertation; supports the "practical viability" language in the summary.
- Phase 9 — "Performance Benchmarking" objective and the linear-encoder contrast raised in the project summary (comparator updated from PCA to GARCH per supervisor guidance).
- Phase 10 — standard write-up.

Nothing in this plan exceeds the form. Everything in the form is covered.

---

## Deferred to `future_work.md` (Discussion Chapter)

- β-VAE variant for disentangled latent representations
- Temporal Convolutional VAE variant
- Multi-architecture VAE ablation
- Inverse-volatility and risk-parity portfolio allocation
- Explicit sector-exposure management and shared-leg constraints
- HMM-based market regime detection and regime-conditional thresholds
- Full turnover-cost sensitivity analysis
- Component-wise ablation decomposition (HDBSCAN vs. k-means, etc.)
- VAE retraining on a rolling schedule (frozen-VAE drift check; if drift detected, document and re-train once)

Each should get a short paragraph in the Discussion / Future Work chapter explaining what it is, why it was considered, why it was deferred, and what it would add. This converts scoping judgment into a defensible narrative for the viva.
