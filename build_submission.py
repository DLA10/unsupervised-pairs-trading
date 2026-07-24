"""
Merge the 13 phase notebooks into the 1-2 consolidated notebooks the university
upload allows, in pipeline order, with all executed outputs preserved.

    python build_submission.py          -> submission/part1_foundation.ipynb (Phases 1-5)
                                           submission/part2_evaluation.ipynb (Phases 6-10)
    python build_submission.py --one    -> submission/full_pipeline.ipynb   (everything)

Run it AFTER executing the notebooks so the merged files embed the final outputs;
re-running it any time simply rebuilds them from the current notebooks.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "submission"

TITLE = "An Unsupervised-Learning Approach to Adaptive Market-Neutral Pairs Trading"
CANDIDATE = "Lalith Aditya Devaraj · KU ID 2551111 · MSc Data Science · Supervisor: Dr. Gordon Hunter"

SECTIONS = [
    ("data_download",       "Phase 1a — Data Download (S&P 500 universe, 2015-2026)"),
    ("data_cleaning",       "Phase 1b — Cleaning and Alignment"),
    ("feature_engineering", "Phase 1c — Feature Engineering (60-day normalised windows)"),
    ("vae_training",        "Phase 2a — VAE Training (2015-2017, then frozen)"),
    ("latent_inspection",   "Phase 2b — Latent Space Inspection (the quality gate)"),
    ("hdbscan_clustering",  "Phase 3 — HDBSCAN Clustering and Stability"),
    ("cointegration",       "Phase 4 — Cointegration Testing and Pair Selection"),
    ("strategy",            "Phase 5 — Strategy: Single Pair and Ten-Pair Portfolio"),
    ("walk_forward",        "Phase 6 — Walk-Forward Backtest (frozen VAE, 27 quarters)"),
    ("pair_persistence",    "Phase 7 — Pair Persistence and Turnover"),
    ("transaction_costs",   "Phase 8 — Transaction Costs"),
    ("benchmark",           "Phase 9 — Benchmark: VAE vs GARCH vs Correlation vs Buy-and-Hold"),
    ("results_compilation", "Phase 10 — Results Compilation (figures F1-F9, tables T5-T10)"),
]

PARTS = {
    "part1_foundation":  ("Part 1 of 2 — Data Foundation, VAE, Clustering, Pair Selection, Baseline Strategy (Phases 1-5)",  SECTIONS[:8]),
    "part2_evaluation":  ("Part 2 of 2 — Walk-Forward, Persistence, Costs, Benchmark, Results (Phases 6-10)",                SECTIONS[8:]),
}

NOTE = (
    "**About this consolidated notebook.** It is assembled, in pipeline order, from the project's "
    "individual phase notebooks with every executed output preserved, so code, explanations and "
    "results can be read together. Each section below is one phase; grey dividers mark the joins. "
    "The phases communicate through files saved in `data/` and `models/`, so any section can be "
    "re-executed on its own. **Caution if re-running end-to-end:** the Phase 1a section re-downloads "
    "prices as of the run date, and the Phase 2a section re-trains the VAE — both would regenerate "
    "the dataset and frozen weights rather than reproduce the archived results; every other section "
    "is deterministic given the saved artefacts."
)

def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}

def build(filename, part_title, sections):
    cells = [md(f"# {TITLE}\n\n## {part_title}\n\n{CANDIDATE}\n\n{NOTE}")]
    toc = "\n".join(f"{i}. **{label}**" for i, (_, label) in enumerate(sections, 1))
    cells.append(md(f"## Contents\n\n{toc}"))
    meta = None
    for i, (name, label) in enumerate(sections, 1):
        nb = json.loads((ROOT / f"{name}.ipynb").read_bytes())
        meta = meta or nb["metadata"]
        cells.append(md(f"---\n\n---\n\n# Section {i} · {label}\n\n*(from `{name}.ipynb`)*"))
        cells.extend(nb["cells"])
    n = 0
    for c in cells:                                   # clean sequential numbering
        if c["cell_type"] == "code":
            n += 1
            c["execution_count"] = n
            for o in c.get("outputs", []):
                if "execution_count" in o:
                    o["execution_count"] = n
    doc = {"cells": cells, "metadata": meta, "nbformat": 4, "nbformat_minor": 4}
    OUT.mkdir(exist_ok=True)
    path = OUT / f"{filename}.ipynb"
    path.write_bytes(json.dumps(doc, indent=1, ensure_ascii=False).replace("\n", "\r\n").encode("utf-8"))
    kb = path.stat().st_size // 1024
    print(f"wrote {path.relative_to(ROOT)}  ({len(cells)} cells, {n} code cells, {kb} KB)")

if __name__ == "__main__":
    if "--one" in sys.argv:
        build("full_pipeline", "Complete Pipeline (Phases 1-10)", SECTIONS)
    else:
        for fname, (part_title, sections) in PARTS.items():
            build(fname, part_title, sections)
