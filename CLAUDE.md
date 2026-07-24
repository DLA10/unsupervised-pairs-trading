# Dissertation — Working Contract for Claude

## What this project is

MSc dissertation: **Unsupervised-learning pairs trading** on the S&P 500.
Pipeline: log-returns → VAE latent space (trained once, frozen) → HDBSCAN clusters → Engle–Granger
cointegration → market-neutral pairs strategy with adaptive volatility-based thresholds → walk-forward
backtest → benchmarked against a correlation baseline and a GARCH variant.

The full plan lives in `dissertation_project_phases_v2.md` — **10 phases** (this replaced an earlier
17-phase plan; ignore any old phase numbers still embedded in notebook titles). Stay within that scope —
deferred ideas go to the Discussion / Future Work chapter.

---

## The working principles (non-negotiable)

### 1. Minimal code
Prefer 10 clear lines over 40 "robust" ones. No unnecessary abstractions, no defensive try/except for
impossible cases, no comments narrating what a well-named line already says. A dissertation notebook is
not production software — readability and defensibility matter more than configurability.

### 2. Explain every non-trivial choice — plain English first, tie to pairs trading, math last

Every hyperparameter, architecture choice, threshold, and methodology decision gets a short explanation.
The examiner grades the dissertation on its **pairs-trading contribution**, not on ML vocabulary — the
explanations have to survive that test.

**Write every explanation in this order:**

1. **Plain English — what is actually happening.** Everyday words a non-specialist could follow. Use
   concrete analogies ("fingerprint", "tidy space", "fuzzy cloud") rather than technical names.
2. **Pairs-trading angle — why this helps the strategy.** Say explicitly how the choice helps us identify
   better pairs, make clustering cleaner, produce more reliable cointegration, make the backtest more
   defensible. If you can't tie it back to pairs trading, the choice is probably out of scope.
3. **Math / technical detail — only if load-bearing.** Include it only when the reader needs it to follow
   what's going on. Put it **after** the intuition and label it "Technical note (safe to skip)".
   Otherwise cut it.

**Do not drop bare jargon.** Terms like *posterior collapse*, *KL divergence*, *ELBO*, *reparameterisation*
must be introduced in plain words first. If you can't say what it means and what it does for the strategy
cleanly, don't use the term.

**Self-check:** read the explanation out loud. If a student could pass the viva by repeating only your
words — without knowing any ML jargon — it's good. If it only makes sense to an ML researcher, rewrite it.

### 3. Claude never runs the code — the user runs every notebook

**Claude must never execute the notebooks — not a training loop, not a backtest, not even a single quick
cell.** The user runs every `.ipynb` on their local GPU (RTX 3060, 6 GB VRAM). This is both the handoff
protocol *and* a deliberate token-cost decision: running notebooks burns context for no benefit.

**Exception — dependency installs.** Claude *does* handle package installation itself, so the user never
has to. When a notebook needs a new library, Claude runs `python -m pip install <pkg>` into the notebook
environment (Python 3.11 at `C:\Users\lalit\AppData\Local\Programs\Python\Python311\python.exe` — the one
carrying torch cu121, hdbscan, sklearn, umap, statsmodels) and verifies the import resolves. Installing
and import-checking a package is *not* notebook execution and is allowed; running notebook cells is not.

**Handoff protocol, every phase:**
1. Claude finishes the code edits.
2. Claude stops and says in plain text: *"Scaffolding complete. Please run `<file>` and share the outputs."*
3. User executes, pastes/saves outputs.
4. Claude reviews outputs, flags red flags.
5. Claude updates the **Phase-completion log** below with what was learned.
6. Move to the next phase.

### 4. Every phase is a Jupyter notebook (`.ipynb`)
All phase deliverables are notebooks, never standalone `.py` scripts — so the workflow, explanations,
and outputs live together for the write-up.

### 5. Visualise wherever possible
Every notebook should include figures that make the result legible (loss curves, projections, spread
plots, equity curves, distributions). Figures double as dissertation material.

---

## Environment

Install once:

```
pip install -r requirements.txt
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

GPU: NVIDIA GeForce RTX 3060 Laptop (6 GB) · CUDA driver 12.7 · PyTorch cu121 wheels.

---

## Project snapshot

| Item | Value |
|---|---|
| Universe | S&P 500 — 462 tickers (after history & coverage filters) |
| Date range | 2015-01-02 → 2026-04-17 (2,839 trading days) |
| Data source | Yahoo Finance (`yfinance`, `auto_adjust=True`) |
| Window length / stride | 60 trading days (~3 months), non-overlapping → 47 windows per asset |
| Model-input tensor | `data/model_input/tensor_norm.npy` shape `(462, 47, 60)` |

**Windowing decision (the methodological backbone — keeps the walk-forward look-ahead-free):**

| Use | Period | Windows |
|---|---|---|
| **VAE training** (then frozen forever) | 2015-01 → Nov-2017 | windows **0–11** |
| **Pair-selection formation** (clustering fingerprint + cointegration) | 2015 → 2019 | windows **0–19** / prices 2015–2019 |
| **Held-out trading** (single-pair + multi-pair backtest) | 2020-01 → 2026 | windows 20+ |

The frozen VAE encoding *unseen* 2018–2026 windows is the intended design, not a leak: it is a fixed
feature extractor. Training on 2015–2017 only is what makes the out-of-sample walk-forward defensible.

### Key files
- `data/raw/<TICKER>.parquet` — OHLCV per ticker (503 files). **Input, kept.**
- `data/processed/adj_close.parquet`, `log_returns.parquet` — pre-cleaning download; **input to
  `data_cleaning.ipynb`, kept.**
- `data/processed/adj_close_clean.parquet`, `log_returns_clean.parquet` — cleaned, aligned. **Input.**
- `data/model_input/tensor_norm.npy` — z-scored windows, the VAE input. **Input.**
- `data/model_input/tensor_raw.npy`, `tickers.csv`, `window_dates.csv` — raw windows + metadata. **Input.**
- `data/model_input/latent_vectors.npy` `(462,47,12)` — VAE latents. **Regenerated by the VAE retrain.**
- `data/model_input/latent_profiles.npy`, `latent_profiles_aug.npy`, `sectors.csv`,
  `latent_projections.csv`, `cluster_labels.npy`, `cluster_assignments.csv`, `cluster_diagnostics.csv` —
  **all regenerated** when Phase 2/3 notebooks re-run on the corrected VAE.
- `models/vae/*` — frozen VAE weights + logs. **Regenerated by the VAE retrain.**
- `walkforward.py` — walk-forward engine, **written by `walk_forward.ipynb`** (`%%writefile`) and
  imported by `transaction_costs.ipynb` / `benchmark.ipynb` / `results_compilation.ipynb` so every
  variant runs byte-identical machinery.
- `data/model_input/wf_returns.csv`, `wf_turnover.csv`, `wf_pairs.csv`, `wf_summary.csv`,
  `wf_metrics.csv` — **produced by Phase 6**; `persistence_summary.csv`, `pair_lifetimes.csv` —
  **Phase 7**; `wf_net_returns.csv`, `cost_summary.csv` — **Phase 8**; `benchmark_returns.csv`,
  `benchmark_metrics.csv`, `garch_summary.csv`, `corr_summary.csv` — **Phase 9**.
- `results/figures/*.png`, `results/headline_numbers.csv` — **produced by Phase 10.**
- `problems_log.md` — every problem hit across the project + fix (viva/interview material).
- `future_work.md` — deferred ideas, one paragraph each, for the Discussion chapter.

Known limitation: **survivorship bias** — the ticker list is the *current* S&P 500, not historical
membership. Acknowledged in the cleaning notebook; expected to modestly inflate returns.

---

## Phase-completion log

Each row is filled in after the user runs a phase and shares the outputs. Numbering follows the v2 plan.

| Phase | Status | Notebook(s) | Key result |
|---|---|---|---|
| 1 — Data Foundation (universe, cleaning, features) | ✅ done | `data_download`, `data_cleaning`, `feature_engineering` | 462 tickers × 2839 days; 0 NaN, 14 extreme moves kept as real events; tensor `(462,47,60)` z-scored |
| 2 — VAE Train + Latent Inspection | ✅ done | `vae_training`, `latent_inspection` | Trained on windows 0–11 (2015–2017), 5,544 samples; early-stop ep 99, val ELBO 43.55; frozen, re-encoded all 47 windows → `latent_vectors.npy (462,47,12)`. Inspection (2015–2019 profile): permutation ρ=+0.479 p=0.001; t-SNE/UMAP trust 0.92/0.91; known pairs JPM–BAC #2, XOM–CVX #3, MA–V #4, KO–PEP #10; NN/all 0.368; silhouette-by-sector +0.010. **⚠️ 2/12 latent dims collapsed** (window-level std 0.05, 0.07) — accepted; to be excluded from the Phase 3 fingerprint. |
| 3 — HDBSCAN + Stability | ✅ done | `hdbscan_clustering` | Fingerprint `(462,20)` = `[mean,std]` over 10 active dims, 2015–2019 windows (0–19). Chosen mcs=3/ms=3/leaf → 10 clusters, 90 labelled / 372 noise. Clean stories: 23 utilities (stab 0.997), 24 banks (0.879), 16 REITs (0.816), + small industrials/cyclicals. **Bootstrap ARI 0.859 ± 0.059**. 8/10 clusters stable → **80 assets to Phase 4** (dropped clusters 4 & 5 at stability 0.36/0.48). |
| 4 — Cointegration + Pair Selection | ✅ done | `cointegration.ipynb` | Tested 670 within-cluster pairs (2015–2019). 114 EG-significant (p<0.05); Johansen agreement 50% (concentrated at the p≈0.05 margin — all top pairs agree). Gates → **112-pair shortlist** (half-life 5–60d, spread std≥0.01). Top pairs bank–bank (NTRS–RF p=0.0002 hl=19d, COF–HBAN, HBAN–BAC…), plus utilities & REITs. Saved `pairs_all.csv` (670), `pairs_shortlist.csv` (112). |
| 5 — Strategy: single-pair + multi-pair | ✅ done | `strategy.ipynb` | Traded shortlist on held-out 2020+ (1,581 days). **Single pair NTRS–RF**: +42.8% cum, ann 5.8%, Sharpe 0.58, max DD −12.7%, 32 trades, avg 22d, win 69%, PF 2.52. **Diversified portfolio** (10 pairs, 0 shared legs; legs Financials 13 / Utilities 6): +12.3% cum, Sharpe 0.44, max DD −8.0%, diversification ratio 2.29, market beta +0.088 (≈neutral). Gross of costs. Saved `portfolio_pairs.csv`, `strategy_metrics.csv`. |
| 6 — Walk-Forward Pipeline (frozen VAE) | 🔧 scaffolded | `walk_forward.ipynb` | Awaiting first run. 27 quarters (windows 20–46, 2019-10-10 → 2026-03-23), rolling 20-window formation, engine in `walkforward.py` (written by the notebook, shared with Phase 9). |
| 7 — Pair Persistence & Turnover | 🔧 scaffolded | `pair_persistence.ipynb` | Awaiting first run. Survival/lifetimes from `wf_pairs.csv`; turnover vs prior-quarter realised vol. |
| 8 — Transaction Costs | 🔧 scaffolded | `transaction_costs.ipynb` | Awaiting first run. 2 bp commission + 5 bp slippage per side on `wf_turnover`; half/double sensitivity. |
| 9 — Benchmark (VAE vs GARCH vs Correlation vs B&H) | 🔧 scaffolded | `benchmark.ipynb` | Awaiting first run. GARCH(1,1) 4-feature chain + corr top-200 + buy-and-hold through the identical `walkforward.py`; same cost toll from `cost_summary.csv`. Slow cell ~10–15 min (12.5k GARCH fits). |
| 10 — Results Compilation & Write-Up | 🔧 scaffolded | `results_compilation.ipynb` | Awaiting first run (needs 6–9 done). 7 styled figures + `results/headline_numbers.csv`. |

---

## Current phase

**Phases 1–5 complete and run. Phases 6–10 scaffolded (2026-07-23) — awaiting their first runs.**

Run order (each notebook reads the previous ones' saved artifacts):
1. `walk_forward.ipynb` — writes `walkforward.py` + `wf_*` artifacts (~5 min)
2. `pair_persistence.ipynb` — needs `wf_pairs.csv`
3. `transaction_costs.ipynb` — needs `wf_returns/wf_turnover`
4. `benchmark.ipynb` — needs `walkforward.py` + `cost_summary.csv` (slow cell ~10–15 min)
5. `results_compilation.ipynb` — needs everything above; writes `results/` (figures F1–F9 + tables T5–T10)

Also re-run once, to render the explanatory figures added 2026-07-24 (all deterministic, same
numbers): `data_cleaning`, `feature_engineering`, `latent_inspection`, `hdbscan_clustering`,
`cointegration`, `strategy`. **Never re-run** `data_download` (would refresh the dataset) or
`vae_training` (frozen weights; deliberately left untouched).

After each run: share the outputs, red flags get reviewed, the phase row above gets its Key result,
and any new problem goes into `problems_log.md` (the viva/interview log of every hurdle + fix).
Design decisions for Phases 6–9 (window-grid calendar, fixed 10% sleeves, quarter-end force-close,
frozen active dims, GARCH failure handling, corr top-200 fairness cap) are explained in the
notebooks' markdown and logged in `problems_log.md`.

---

## Methodological lessons (carry into the write-up)

**HDBSCAN first-attempt collapse → augmented fingerprint fix.** Clustering on the raw 12-D *mean-of-windows*
fingerprint collapsed to a 2-cluster split (one small utilities group + one ~all-market blob) under every
hyperparameter setting. Three stacked causes, three textbook fixes — all at the clustering layer, none
touching the VAE:

1. **Mean-aggregation destroyed information.** Averaging an asset's window-level latents shrinks per-dim
   spread by √N, erasing how *variable* an asset's behaviour is (stable IBM vs volatile NVDA look alike).
   *Fix:* augment the fingerprint with the per-dim **std** across windows → `[mean, std]` 24-D profile.
2. **Unequal per-dim scale skewed Euclidean distance** (one loud dim dominated). *Fix:* **z-score** every
   coordinate so all contribute equally.
3. **Default `cluster_selection_method='eom'` is too greedy** — it merges nested density peaks (banks,
   REITs, semis) back into the parent blob. *Fix:* `cluster_selection_method='leaf'` extracts the small
   tight peaks.

Leaf-mode raises the noise ratio (many assets have no confident peer group — fine; they just aren't
paired). At high noise HDBSCAN's DBCV returns `NaN`, so score configs with **silhouette on the non-noise
subset** instead. Guardrails: silhouette > 0, ≥5 clusters, largest cluster ≤ 40% of non-noise. *(The
specific cluster counts/tickers from earlier runs are omitted here — they change once the VAE is retrained
on the corrected window and the fingerprint is rebuilt on 2015–2019.)*
