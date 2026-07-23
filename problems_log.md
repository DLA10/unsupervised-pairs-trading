# Problems Log — every hurdle, and how it was fixed

Kept for the viva and for interviews ("tell me about a problem you faced"). One entry per problem:
what happened, why, the fix, and the one-line takeaway to say out loud. Newest problems at the
bottom; run-time findings from Phases 6–10 get appended as they surface.

---

## Phase 1 — Data

### 1. Fourteen single-day price moves larger than ±50%
**Problem.** Data cleaning flagged 14 one-day moves beyond ±50% — big enough to be either data
corruption or real history.
**Cause.** Both exist in free data: Yahoo Finance does occasionally glitch, but markets also produce
genuine crashes.
**Fix.** Checked every one individually against news history instead of applying a blanket filter —
all 14 were real events (e.g. PG&E's wildfire-liability crash in Jan-2019, the COVID oil-stock
collapse on 2020-03-09). All were kept.
**Takeaway.** *Never silently delete outliers — an outlier filter that deletes the COVID crash would
have quietly falsified every backtest that followed.*

### 2. Survivorship bias in the universe
**Problem.** The ticker list is *today's* S&P 500, so companies that failed or were delisted along
the way are missing — the past looks rosier than it was.
**Cause.** Free data sources don't provide historical index membership.
**Fix.** Couldn't be fixed with available data, so it is *disclosed* everywhere results appear, with
the expected direction of the bias (returns modestly inflated) stated up front.
**Takeaway.** *A bias you name, quantify the direction of, and disclose is a limitation; a bias you
hide is a flaw.*

---

## Phase 2 — VAE

### 3. Posterior collapse: 2 of 12 fingerprint numbers went blank
**Problem.** Two latent dimensions came out with near-zero spread across all stocks — the same value
for everyone, carrying no information (the standard VAE failure called *posterior collapse*).
**Cause.** The "keep the space tidy" pressure (KL term) can win completely on some dimensions, so the
encoder learns to ignore them.
**Fix.** Diagnosed by measuring per-dimension spread (flagged at < 0.3× the median spread). Rather
than retraining with a different loss weighting — which would restart Phase 2 for uncertain gain —
the two dead dimensions are simply **excluded** from the downstream clustering fingerprint, keeping
the 10 informative ones. Documented as an accepted limitation.
**Takeaway.** *Diagnose, quantify the impact, then choose the minimal intervention — excluding two
dead columns beats retraining a model that already passes its quality gates.*

---

## Phase 3 — Clustering

### 4. HDBSCAN collapsed everything into one giant blob
**Problem.** The first clustering attempt produced one huge cluster plus noise under every
hyperparameter setting — useless for finding peer groups.
**Cause.** Three stacked causes, found by inspecting layer by layer: (1) averaging each stock's
window fingerprints erased how *variable* each stock is (steady utility ≈ jumpy tech stock after
averaging); (2) one latent dimension had a much larger numeric scale and dominated every distance;
(3) HDBSCAN's default `eom` mode greedily re-merges small tight groups into their parent.
**Fix.** Three textbook fixes at the clustering layer, none touching the VAE: augment the fingerprint
to `[mean, std]` per dimension; z-score every column; switch to `cluster_selection_method='leaf'`.
Result: 10 clean, sector-coherent clusters.
**Takeaway.** *When a pipeline fails, localise the failing layer before touching anything — the VAE
was fine; the aggregation, scaling, and extraction above it were not.*

### 5. The standard cluster-quality metric returned NaN
**Problem.** DBCV — the usual HDBSCAN quality score — returned NaN, so configurations couldn't be
compared.
**Cause.** Leaf mode labels ~80% of stocks as noise, and DBCV breaks down at high noise ratios.
**Fix.** Scored configurations with the silhouette on the non-noise subset instead, with guardrails
fixed in advance (silhouette > 0, ≥ 5 clusters, largest cluster ≤ 40% of grouped stocks) so the
substitute metric couldn't be gamed.
**Takeaway.** *When the textbook metric breaks, substitute a defensible one and write the guardrails
down before looking at the results.*

---

## Phase 4 — Cointegration

### 6. The two cointegration tests only agreed 50% of the time
**Problem.** Johansen confirmed only half of the Engle–Granger significant pairs.
**Cause.** Inspection showed the disagreement concentrates at the p ≈ 0.05 margin — borderline pairs
flip between tests; the strong pairs (all of the eventual top selections) agree.
**Fix.** Used Johansen as a *robustness check reported alongside results* — exactly as planned — not
as a hard filter that would have discarded valid borderline pairs.
**Takeaway.** *Two tests disagreeing at the margin is expected behaviour; find WHERE they disagree
before deciding it's a problem.*

### 7. Multiple testing: could the 114 "significant" pairs be luck?
**Problem.** 670 tests at p < 0.05 hands you ~34 false positives even if nothing is real.
**Cause.** Any mass-testing procedure harvests flukes; pairs-trading research is notorious for it.
**Fix.** Three structural protections, now stated explicitly in the notebook: within-cluster testing
bounds the test count (vs ~107,000 exhaustive pairs); thresholds fixed in advance, not tuned; and the
Phase 6 walk-forward re-validates every pair quarterly, so a fluke stops being selected almost
immediately. Observed 114 vs ~34 expected under pure chance (3.3×).
**Takeaway.** *Quantify the fluke budget instead of hand-waving: "114 found vs 34 expected by chance"
is an answer; "we used p < 0.05" is not.*

---

## Phase 5 — Strategy

### 8. The one-day-lag traps in backtest accounting
**Problem.** Two classic places a daily backtest quietly lies: trading on the same day's signal
(look-ahead), and attributing P&L to the wrong trade when computing per-trade statistics.
**Cause.** A position opened on day *t*'s signal earns returns from day *t+1*; naive bookkeeping
misses the shift on one side or the other.
**Fix.** Positions are shifted one day before P&L (`pos.shift(1) × return`), and trade statistics are
segmented on the *shifted* (effective) position so each trade lines up with the P&L it actually
earned. Both are commented in the code as deliberate.
**Takeaway.** *In daily backtests, the one-day lag is where credibility lives — get it right in the
P&L AND in the trade attribution.*

---

## Project management

### 9. The 17-phase plan was unmanageable
**Problem.** The original plan had 17 stand-alone phases; progress was hard to communicate and
notebook numbering drifted out of sync.
**Cause.** Planning granularity finer than the natural units of work.
**Fix.** Re-grouped into 10 phases (no scope removed — sub-steps preserved under their owning phase),
with a traceability section mapping every phase to the approved project form. Stale "Phase 2/3
Summary" fossil cells from the old numbering were removed from the notebooks in the July-2026 audit.
**Takeaway.** *Renumbering a plan leaves fossils — after any reorganisation, grep everything for the
old numbering.*

### 10. The supervisor-approved PCA→GARCH swap missed two files
**Problem.** When the Phase 9 comparator changed from PCA to GARCH (supervisor's guidance), the
commit updated the planning docs — but a July-2026 audit found `build_report.py` and the generated
`dissertation_report.html` still described the old "basic linear version" comparator.
**Cause.** The change was applied to the files being *looked at*, not to every file that mentioned
the decision.
**Fix.** Grep-audited the whole repository for the stale wording, fixed the builder, regenerated the
report, and verified "GARCH" present / "linear version" absent programmatically.
**Takeaway.** *When a decision changes, search the repo for every trace of the old decision — the
file you forgot is always the one you show someone.*

### 11. Setup instructions referenced a file that didn't exist
**Problem.** README and the working notes both said `pip install -r requirements.txt` — but no
`requirements.txt` existed anywhere in the repository.
**Cause.** Dependencies were installed ad-hoc during development; the file was assumed rather than
created.
**Fix.** Wrote `requirements.txt` from the *actual* imports across all notebooks (plus `arch` for
Phase 9 and `markdown` for the report builder), with PyTorch's CUDA install line documented
separately.
**Takeaway.** *Every command in a README must be executable on a fresh machine — test the
instructions, not just the code.*

### 12. Docs claimed a CUDA build that wasn't installed
**Problem.** README/notes said "PyTorch cu126 wheels", but the installed build is `2.5.1+cu121`.
**Cause.** The install command was written from the download page, the environment from an earlier
install; nobody re-checked.
**Fix.** Verified the live environment (`torch.__version__`) and aligned every doc to the installed
cu121 build (fully compatible with the CUDA 12.7 driver).
**Takeaway.** *Environment claims are testable — one `python -c "import torch"` beats any memory of
what was installed.*

---

## Phases 6–9 — walk-forward design and scaffolding (July-2026)

### 13. "Quarterly" rebalancing needed a calendar that couldn't leak
**Problem.** A rolling quarterly schedule invites subtle look-ahead bugs at every boundary (formation
windows overlapping trading windows, partial quarters, misaligned dates).
**Cause.** Calendar quarters don't line up with anything else in the pipeline.
**Fix.** Reused the existing non-overlapping 60-trading-day window grid from Phase 1 as the rebalance
calendar (windows 20–46 = 27 "quarters"): formation = windows *w−20…w−1*, trading = window *w*, so
formation and trading can never overlap *by construction*. Documented the honest consequence: the
walk-forward actually starts 2019-10-10 (window 20), not the "2020-01" shorthand used earlier, and
the final 18 days beyond window 46 go untraded.
**Takeaway.** *Reuse structures that already guarantee your invariants — the window grid was built
non-overlapping in Phase 1, so the walk-forward inherits look-ahead-freeness instead of proving it.*

### 14. Fair benchmarking vs "everything lives in notebooks"
**Problem.** Phase 9's apples-to-apples claim ("only the encoder differs") is only credible if the
GARCH and correlation variants run the *identical* backtest code — but copy-pasting the engine into
each notebook guarantees drift, and the project rule says deliverables are notebooks, not modules.
**Cause.** Genuine tension between reproducibility-by-isolation and fairness-by-sharing.
**Fix.** The Phase 6 notebook *writes* the engine to `walkforward.py` via `%%writefile` — the code
remains fully visible inside the notebook (satisfying the notebooks-only spirit), while Phase 9
imports the byte-identical machinery (satisfying the fairness requirement).
**Takeaway.** *"Identical pipeline" must be literal — share the code object, don't re-type it.*

### 15. What to do with capital in thin quarters
**Problem.** If a quarter yields only 4 tradeable pairs, splitting all capital across them doubles
the bet on each pair exactly when the selector is least confident.
**Cause.** Equal-weight 1/n allocation couples position size to selector supply.
**Fix.** Fixed 10% sleeves: each pair gets 1/10 of capital; unfilled sleeves sit in cash. Risk per
pair is constant through time; thin quarters de-lever automatically.
**Takeaway.** *Don't let a portfolio's risk per position depend on how many ideas you happened to
find that quarter.*

### 16. Open positions at rebalance boundaries
**Problem.** A pair can still be mid-trade when the quarter ends and the pair list changes — carrying
it forward tangles accounting; closing it costs money.
**Cause.** Quarterly re-selection and multi-week trades inevitably collide.
**Fix.** Force-close everything on the quarter's last day, and *count that exit in the turnover
series* so Phase 8 charges real money for the realism. Simple accounting, honestly costed.
**Takeaway.** *Choose the simple rule and pay its true cost visibly, rather than the clever rule
whose cost hides in the seams.*

### 17. The dead-dimension decision could flicker across rebalances
**Problem.** Recomputing "which fingerprint numbers are blank" at every rebalance could flip a
borderline dimension in and out, silently changing the feature space mid-backtest.
**Cause.** The exclusion rule (spread < 0.3× median) sits near a boundary for one dimension.
**Fix.** The decision is made once, on the pre-2020 formation windows — collapse is a property of the
*frozen* VAE, not of the passing data — and frozen thereafter, exactly like the VAE weights.
**Takeaway.** *Anything that defines the feature space must be frozen with the model, or the
"fixed ruler" argument falls apart.*

### 18. GARCH fits fail on real data
**Problem.** Fitting GARCH(1,1) to 462 stocks × 27 windows ≈ 12,500 fits guarantees some
non-convergence and boundary (α+β≈1) cases; unhandled, one bad stock crashes the whole run — or
worse, poisons the feature matrix with NaN/infinities that z-scoring spreads everywhere.
**Cause.** Maximum-likelihood optimisers on short, quiet, or pathological return series.
**Fix.** Each failed or boundary fit gets that window's cross-sectional median features, the count is
logged and printed per window (nothing hidden), returns are scaled ×100 for optimiser health (the
standard trick), and a zero-spread guard protects the z-scoring. The `arch` API usage was verified on
synthetic GARCH data before shipping.
**Takeaway.** *At thousands of fits, failures are a certainty, not an edge case — design the failure
path and make its frequency visible.*

### 19. How many pairs may the correlation baseline test?
**Problem.** Letting the classical baseline test all ~107,000 pairs would hand it hundreds of lucky
p < 0.05 pairs — an advantage that is multiple-testing luck, not selection skill.
**Cause.** Unequal test counts = unequal fluke budgets.
**Fix.** The correlation baseline shortlists its top-200 pairs before testing — the same order of
magnitude as the cluster chains' per-quarter test count — so all selectors face a comparable fluke
budget.
**Takeaway.** *When comparing selectors, equalise the number of statistical bets each is allowed to
place.*

### 20. Shipping code I'm not allowed to run
**Problem.** The working contract says the user executes all notebooks (GPU, cost); but handing over
five untested notebooks risks wasting the user's time on a crash 10 minutes into a run.
**Cause.** Deliberate division of labour in the project workflow.
**Fix.** Three-layer verification without touching the real pipeline: (1) AST syntax check of every
code cell; (2) the walk-forward engine smoke-tested on *synthetic* data with planted cointegrated
pairs — recovered the planted pairs, exercised the correlation and empty-selection paths, verified
turnover accounting; (3) an automated IO-chain audit proving every notebook's inputs are produced
upstream and nothing overwrites a Phase 1–5 artifact.
**Takeaway.** *If you can't run the real thing, build a harness that exercises every code path on
data you control — "it parses" is not verification.*

### 21. The worktree had no data
**Problem.** This session ran in a git worktree, and `data/` is gitignored — so none of the artifacts
the new notebooks depend on existed where the code was written.
**Cause.** Git worktrees carry tracked files only; ignored directories stay with the main checkout.
**Fix.** All interface checks (file existence, window dates, artifact names) were run against the
main checkout's `data/` directory explicitly, and the run-order instructions tell the user to merge
the branch into the main checkout — where the data lives — before running.
**Takeaway.** *Know what your isolation mechanism does and doesn't copy, and validate against the
environment the code will actually run in.*

---

## Pending — to be filled in after the Phase 6–10 runs

- Phase 6: any starving quarters (< 3 pairs)? cluster-count degeneration? Johansen agreement drift?
- Phase 9: how many degenerate GARCH fits per window in practice?
- Phase 8: does the strategy survive 7 bp — and 14 bp?
- Anything that crashes, surprises, or contradicts the Phase 5 baseline.
