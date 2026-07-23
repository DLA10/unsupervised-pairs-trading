# Future Work — deferred ideas for the Discussion chapter

Each idea below was considered during planning, deliberately deferred to keep the project inside the
approved scope, and is preserved here as write-up material. Format per item: what it is, why it was
considered, why it was deferred, and what it would add.

## 1. β-VAE variant
A VAE trained with the "tidiness" pressure turned up (β > 1), which encourages each fingerprint number
to capture one independent aspect of behaviour. Considered because cleaner, more interpretable
fingerprint dimensions could make clusters easier to explain economically. Deferred because the
standard β = 1 VAE already passed every latent-space quality gate, and tuning β adds a hyperparameter
search with no guarantee of better *pairs*. Would add: interpretability of individual latent
dimensions and possibly crisper clusters.

## 2. Temporal Convolutional VAE
Replacing the dense encoder with one that reads the 60-day window as an ordered sequence rather than
a flat list of numbers. Considered because return windows have temporal structure (trends, volatility
clustering) a dense network can only partially exploit. Deferred because the dense VAE already
produced a latent space that recovers known pairs, and a sequence architecture roughly doubles
training cost and design choices to defend. Would add: sensitivity to the *ordering* of moves within
a window, potentially sharper behavioural fingerprints.

## 3. Multi-architecture VAE ablation
Training several encoder architectures side by side and comparing downstream pair quality. Considered
as the thorough way to show the chosen architecture is not a lucky pick. Deferred for compute budget
and because Phase 9 already isolates the encoder's contribution against GARCH and correlation
baselines. Would add: evidence that results are robust to architecture choice.

## 4. Inverse-volatility / risk-parity allocation
Sizing each pair position by the inverse of its spread volatility instead of equal weight, so every
pair contributes similar risk. Considered because equal-weight lets the jumpiest pair dominate
portfolio risk. Deferred because equal weight is the transparent baseline the examiner can verify at
a glance, and allocation tweaks are orthogonal to the dissertation's question (does the VAE find
better pairs?). Would add: a smoother portfolio and a fairer risk comparison across pairs.

## 5. Sector-exposure management and shared-leg constraints
Explicit caps on how much of the portfolio can sit in one sector, beyond the current no-shared-legs
rule. Considered because the Phase 5 portfolio concentrates in financials and utilities. Deferred
because the concentration is honestly diagnosed and reported, and adding constraints introduces new
free parameters. Would add: protection against a sector-wide shock hitting several pairs at once.

## 6. HMM-based market regime detection
A hidden Markov model that labels each period calm/stressed and switches thresholds accordingly.
Considered because pair behaviour plausibly differs across regimes. Deferred because the rolling
z-score already adapts thresholds to local volatility implicitly, and Phase 7's turnover-vs-volatility
analysis answers the "do relationships change under stress?" question quantitatively without a regime
model. Would add: explicit regime-conditional behaviour and possibly earlier exits in crises.

## 7. Full turnover-cost sensitivity analysis
Sweeping the cost model over a fine grid of commission and slippage assumptions and re-optimising the
strategy under each. Considered because cost assumptions drive net profitability. Deferred in favour
of Phase 8's single calibrated cost model plus a coarse sensitivity check, which answers the viability
question without an optimisation loop that risks overfitting to cost assumptions. Would add: a full
map of the strategy's break-even cost frontier.

## 8. Component-wise ablation (e.g. HDBSCAN vs k-means)
Swapping each pipeline component in turn to attribute performance to individual choices. Considered as
the academically complete decomposition. Deferred because Phase 9's encoder swap is the ablation that
answers the headline research question; clusterer and test swaps multiply run count without touching
the core claim. Would add: finer-grained attribution of where the pipeline's edge comes from.

## 9. VAE retraining on a rolling schedule (drift check)
Periodically re-training the VAE on recent data and comparing latent spaces to detect drift.
Considered because a 2015–2017 encoder could in principle go stale. Deferred because freezing the VAE
is what makes the walk-forward defensibly look-ahead-free and keeps latent dimensions comparable
across time (a prerequisite for the Phase 7 persistence analysis); the frozen encoder's continued
usefulness is itself evidenced by the out-of-sample results. Would add: an empirical answer to "how
fast does a return-shape encoder age?", and a documented re-training protocol if drift were found.
