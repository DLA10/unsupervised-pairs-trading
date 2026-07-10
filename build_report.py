"""
Build a single self-contained interactive HTML report for Phases 1-5.

High-level progress report: for each phase it explains what the phase does, what we
achieved, any problem we hit and how we fixed it, and the relevant outputs (with every
chart captioned, including what the X- and Y-axes mean). Re-run any time:
    python build_report.py
"""
import json, html as html_lib
from pathlib import Path

import markdown as md_lib

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "dissertation_report.html"


# ---------- helpers ----------------------------------------------------------
def esc(s):
    return html_lib.escape(str(s))

def md(src):
    return md_lib.markdown(src, extensions=["tables", "sane_lists"])

def outputs_of(name):
    """Return (figures, tables) from a notebook, each in cell order."""
    nb = json.load(open(ROOT / f"{name}.ipynb", encoding="utf-8"))
    figs, tbls = [], []
    for c in nb["cells"]:
        for o in c.get("outputs", []):
            data = o.get("data", {})
            if "image/png" in data:
                b = data["image/png"]
                figs.append(("".join(b) if isinstance(b, list) else b).replace("\n", ""))
            elif "text/html" in data:
                h = data["text/html"]
                tbls.append("".join(h) if isinstance(h, list) else h)
    return figs, tbls

def figure(b64, title, what, x, y, takeaway):
    cap = (f"<b>{title}</b> {what}"
           f'<span class="axes"><b>X-axis</b> — {x}<br><b>Y-axis</b> — {y}</span>'
           f'<span class="take"><b>What we learn:</b> {takeaway}</span>')
    return (f'<figure><img class="zoom" loading="lazy" '
            f'src="data:image/png;base64,{b64}"><figcaption>{cap}</figcaption></figure>')

def figure_panels(b64, title, what, panels, takeaway):
    """panels: list of (panel_name, x, y)."""
    rows = "".join(f"<li><b>{esc(n)}</b> — X: {x}; Y: {y}</li>" for n, x, y in panels)
    cap = (f"<b>{title}</b> {what}<div class='axes'><ul>{rows}</ul></div>"
           f'<span class="take"><b>What we learn:</b> {takeaway}</span>')
    return (f'<figure><img class="zoom" loading="lazy" '
            f'src="data:image/png;base64,{b64}"><figcaption>{cap}</figcaption></figure>')

def table(html, caption):
    return f'<div class="tbl">{html}</div><p class="tcap">{caption}</p>'

def H(heading, body):
    return f"<h3>{heading}</h3>{body}"

def P(*paras):
    return '<div class="md">' + "".join(f"<p>{p}</p>" for p in paras) + "</div>"

def UL(*items):
    return '<div class="md"><ul>' + "".join(f"<li>{i}</li>" for i in items) + "</ul></div>"


# ---------- pull the real figures / tables -----------------------------------
vae, _ = outputs_of("vae_training")
lat, _ = outputs_of("latent_inspection")
hdb, hdb_t = outputs_of("hdbscan_clustering")
coint, coint_t = outputs_of("cointegration")
strat, _ = outputs_of("strategy")

def g(lst, i):
    return lst[i] if i < len(lst) else ""


# ---------- curated, plain-English content -----------------------------------
def term(t, d):
    return f'<span class="term" tabindex="0" data-def="{esc(d)}">{t}</span>'

OVERVIEW = f"""
<p class="lead">This report walks through the first five phases of the project in plain language, kept at
a high level: what each phase does, what we achieved, and the key results. The goal is a
<b>{term("pairs-trading", "Buy one stock and short another that normally moves with it; profit when the gap between them returns to normal.")}</b>
strategy — find two stocks that normally move together and, when they temporarily drift apart, bet the
gap will close again.</p>

<p>The novel part is <b>how</b> we find the pairs. Instead of just eyeballing price charts, we teach a
small neural network to read each stock's recent behaviour and boil it down to a short
<b>{term("fingerprint", "A short list of numbers summarising how a stock has been behaving; look-alike stocks get similar fingerprints.")}</b>.
Stocks with similar fingerprints are grouped, and we look for tradeable pairs only inside those groups:</p>

<div class="pipe">
  <span>1 · Data</span><i>→</i><span>2 · Fingerprints</span><i>→</i><span>3 · Behaviour groups</span>
  <i>→</i><span>4 · Tradeable pairs</span><i>→</i><span>5 · Strategy</span>
</div>

<p>Hover any underlined term for a plain definition, click any chart to enlarge it, and use the menu at
the top to jump between phases.</p>
"""

SCORECARD = [
    ("Fingerprints are meaningful", "+0.48", "Close fingerprints really do mean stocks that move together (and not by luck: p = 0.001)."),
    ("Groups are stable", "0.86 / 1.0", "Re-doing the grouping on 90% of the stocks, 100 times, gives almost the same groups every time."),
    ("Tradeable pairs found", "112", "Pairs whose price gap reliably springs back, drawn from 8 stable behaviour groups."),
    ("Single-pair result", "Sharpe 0.58", "Reward-for-risk of the strongest pair, traded on unseen 2020+ data (before costs)."),
    ("Market-neutral", "beta ≈ 0.09", "The basket barely moves with the market — profit comes from the pairs, not market direction."),
]


def phase1():
    facts = ("<table><tr><th>Companies</th><td>462 (from the S&amp;P 500)</td></tr>"
             "<tr><th>History</th><td>2015–2026 · 2,839 trading days</td></tr>"
             "<tr><th>Gaps after cleaning</th><td>0</td></tr>"
             "<tr><th>Snippets per company</th><td>47 windows of 60 days each</td></tr></table>")
    return (
        '<div class="lead-box">We collected 11+ years of daily prices for the whole S&amp;P 500, cleaned '
        'them into one gap-free table, and cut each company\'s history into comparable 60-day snippets — '
        'the raw material every later phase uses.</div>'
        + H("What this phase does", P(
            "Download daily prices for every S&amp;P 500 company, tidy them into a single aligned table "
            "with no missing days, and reshape each company's returns into a stack of 60-day (~3-month) "
            "snippets, all put on the same scale so later steps compare the <i>shape</i> of behaviour "
            "rather than how big or pricey a stock is."))
        + H("What we achieved", UL(
            "A clean, gap-free dataset of <b>462 companies over 2,839 trading days</b>.",
            "<b>47 comparable 60-day snippets</b> per company, ready for the model.",
            "A documented, reproducible starting point for everything that follows."))
        + H("A problem we hit and how we fixed it", P(
            "Fourteen single-day price moves were larger than 50%. Rather than assume they were data "
            "errors, we checked each one — they were <b>genuine market events</b> (for example PG&amp;E's "
            "2019 wildfire-liability crash), so we kept them. Nothing was silently thrown away."))
        + H("Key facts", f'<div class="tbl">{facts}</div>'))


def phase2():
    return (
        '<div class="lead-box">A small neural network learned to turn each stock\'s 60-day behaviour into '
        'a compact <b>latent representation</b> (the "fingerprint" referred to throughout this report), '
        'trained only on the early years and then frozen. We then checked, hard, that these '
        'representations actually capture how stocks move.</div>'
        + H("What this phase does", P(
            "Train a " + term("VAE", "A small neural network that compresses each 60-day pattern to 12 numbers and rebuilds it, arranging the numbers so 'close together' means 'behaves alike'.") +
            " (a type of neural network) on 2015–2017 data so it can summarise any stock's 60-day pattern "
            "as a short fingerprint. The model is then <b>frozen</b> — never changed again — so that when "
            "we later apply it to 2020+ data, it has genuinely never seen those years. Finally we inspect "
            "the fingerprints to confirm they are meaningful."))
        + H("What we achieved", UL(
            "A trained, frozen fingerprint-maker that rebuilds unseen patterns well.",
            "The make-or-break check passed strongly: stocks with <b>close fingerprints really do move "
            "together</b> (agreement +0.48), and it is not luck (p = 0.001).",
            "Textbook look-alikes land as near-neighbours — JPMorgan &amp; Bank of America, Coca-Cola &amp; "
            "Pepsi, Visa &amp; Mastercard."))
        + H("A problem we hit and how we fixed it", P(
            "Two of the twelve fingerprint numbers came out essentially blank — the same value for every "
            "stock, carrying no information. The fix is simple: we leave those two out in the next phase "
            "so they cannot add noise to the grouping."))
        + H("Key outputs",
            figure_panels(g(vae, 0), "Training progress.",
                "The model's score improving as it learns, in three panels. <b>Total ELBO</b> is the "
                "overall training score (the other two added together); <b>Reconstruction (MSE)</b> is how "
                "far the rebuilt snippet is from the original (the average squared miss); <b>KL divergence</b> "
                "is the 'tidiness' pressure that keeps the representations in a neat, well-organised space. "
                "Healthy training falls then flattens.",
                [("all panels", "training pass (one sweep through the data)",
                  "the score (lower Total ELBO &amp; Reconstruction is better; KL rising then settling is healthy)")],
                "Training went smoothly and the model genuinely used its representations — the rebuild "
                "error fell and levelled off, and the tidiness term rose then settled. So it neither "
                "ignored the representations nor merely memorised noise.")
            + figure(g(vae, 1), "Rebuilding unseen patterns.",
                "For four snippets the model never trained on, the original pattern (one line) vs the "
                "model's rebuilt version (the other). They should share the same overall shape.",
                "day within the 60-day snippet", "the rescaled daily move on that day",
                "The model recreates the broad shape of patterns it has never seen, so the representations "
                "capture each stock's essential behaviour rather than random noise.")
            + figure(g(lat, 0), "The representation map.",
                "Every stock placed on a 2-D map so look-alikes sit close together, coloured by industry. "
                "<b>t-SNE</b> and <b>UMAP</b> are two standard ways of flattening the 12 numbers down to a "
                "2-D picture while keeping near-neighbours near; we show both to check the story holds "
                "either way.",
                "a layout coordinate — no units; only how close two dots are matters",
                "a layout coordinate — likewise, position is meaningless, closeness is everything",
                "Stocks bunch together by industry, so the representation captures real structure — but "
                "not rigidly: some look-alikes sit together across industry lines, which is exactly the "
                "kind of non-obvious pairing this approach is meant to find.")))


def phase3():
    comp = g(hdb_t, 1) or g(hdb_t, 0)
    return (
        '<div class="lead-box">We let the computer sort the fingerprints into behaviour groups — a clean '
        'utilities group, a banks group, a property-firms group, and so on — and proved the groups are '
        'real by re-doing the grouping a hundred times.</div>'
        + H("What this phase does", P(
            "Automatically sort the 80-odd most distinctive stocks into " +
            term("behaviour groups", "Sets of stocks with similar fingerprints, found automatically rather than by industry label.") +
            ", without telling the computer how many groups to expect, and set aside any stock with no "
            "clear look-alike. Then test how dependable those groups are."))
        + H("What we achieved", UL(
            "Groups with an obvious, sensible story — e.g. a 23-stock <b>utilities</b> group, a 24-stock "
            "<b>banks</b> group, and a <b>property-firms</b> group.",
            "Very high stability: re-doing the grouping on 90% of the stocks 100 times gives an average "
            "<b>match score of 0.86</b> (1.0 would be identical every time).",
            "<b>8 solid groups covering 80 stocks</b> pass forward to the pair search."))
        + H("A problem we hit and how we fixed it", P(
            "A first, naive attempt lumped almost everything into one giant blob. We fixed it two ways: we "
            "gave each stock a <b>richer fingerprint</b> (its average behaviour <i>and</i> how much it "
            "varies), and we told the grouping tool to pick out <b>tight sub-groups</b> instead of one "
            "big lump. The groups then separated cleanly."))
        + H("Key outputs",
            figure(g(hdb, 0), "The groups on the map.",
                "The same 2-D map as before, now coloured by the behaviour groups the computer found "
                "(grey = stocks left ungrouped). Each colour sitting in its own patch means the groups "
                "are real.",
                "a layout coordinate — no units, closeness is what matters",
                "a layout coordinate — no units, closeness is what matters",
                "The groups occupy tight, separate patches rather than being scattered across the map, "
                "which confirms they are genuine clusters and not arbitrary cuts through one big blob.")
            + figure_panels(g(hdb, 1), "How reliable the groups are.",
                "Left: the spread of match-scores from the 100 re-runs. Right: each group's own stability.",
                [("left", "match score (0 = random, 1 = identical grouping)",
                  "how many of the 100 re-runs landed at that score"),
                 ("right", "each group", "stability 0–1 (green kept ≥ 0.5, red dropped)")],
                "Dropping a random tenth of the stocks barely changes the grouping (scores bunch high, "
                "around 0.86), so the groups are dependable; only the two weakest groups fell below the "
                "line and were set aside.")
            + (table(comp, "The groups we kept — size, how tightly they hold together, the main "
                     "industries, and the stability score.") if comp else "")))


def phase4():
    short = g(coint_t, len(coint_t) - 1)
    return (
        '<div class="lead-box">Inside each group we tested every possible pair to see whether its price '
        'gap reliably springs back, double-checked the strong ones with a second test, and trimmed down '
        'to a tradeable shortlist.</div>'
        + H("What this phase does", P(
            "For every pair of stocks within a group, measure whether their price gap is "
            + term("springy", "Statistically, the gap is 'cointegrated' — it reliably pulls back to a normal level instead of wandering off.") +
            " (it stretches, then reliably pulls back), how fast it springs back, and the "
            + term("balancing weight", "The hedge ratio — how much of one stock to short against the other so the pair ignores the overall market.") +
            " needed to make the pair market-neutral. Keep only the strong, fast-enough ones."))
        + H("What we achieved", UL(
            "Tested <b>670 within-group pairs</b> and trimmed them to a <b>112-pair shortlist</b> with "
            "reliable, tradeable spring-back speeds.",
            "The strongest pairs (e.g. Northern Trust &amp; Regions Financial) passed <b>both</b> "
            "independent tests we ran.",
            "Balancing weights locked in now, to be reused unchanged when we trade — so the test stays "
            "honest."))
        + H("Key outputs",
            figure(g(coint, 0), "Four example pairs.",
                "The price gap of the four strongest pairs over the formation years, shown as 'how "
                "unusual is it right now'. We want to see it swing across the middle and repeatedly cross "
                "the red lines — each crossing is a trading opportunity.",
                "trading day across 2015–2019",
                "the standardised gap (how many 'steps' from its average); red lines mark where we'd trade",
                "These gaps clearly oscillate around the middle and keep crossing the trade lines, so each "
                "pair should throw up repeated chances to trade rather than drifting away and never coming "
                "back.")
            + figure_panels(g(coint, 1), "Summaries across all tested pairs.",
                "Left: how statistically convincing each pair is. Middle: how fast pairs spring back. "
                "Right: how many pairs survived each quality rule.",
                [("left", "springiness score (lower = stronger; red line = our 0.05 cut-off)",
                  "number of pairs"),
                 ("middle", "spring-back speed in days (shaded 5–60 = our keep-zone)", "number of pairs"),
                 ("right", "each quality rule in turn", "pairs still remaining")],
                "Plenty of pairs are statistically convincing and spring back at a tradeable speed, and the "
                "funnel shows the screening is doing real work — 670 raw candidates trimmed to a clean "
                "112-pair shortlist.")
            + (table(short, "The final tradeable shortlist (strongest first): the two stocks, the "
                     "balancing weight, the springiness score, the speed, and whether the second test "
                     "agreed.") if short else "")))


def phase5():
    mt = ("<table><tr><th></th><th>Single pair</th><th>Ten-pair basket</th></tr>"
          "<tr><th>Total return (2020+)</th><td>+42.8%</td><td>+12.3%</td></tr>"
          "<tr><th>Per-year return</th><td>+5.8%</td><td>+1.9%</td></tr>"
          "<tr><th>Reward-for-risk (Sharpe)</th><td>0.58</td><td>0.44</td></tr>"
          "<tr><th>Worst drop (drawdown)</th><td>−12.7%</td><td>−8.0%</td></tr>"
          "<tr><th>Market sensitivity (beta)</th><td>—</td><td>+0.09</td></tr></table>")
    return (
        '<div class="lead-box">Finally we traded the pairs on years the model had never seen (2020 '
        'onward): one pair to show the mechanics, then a diversified basket of ten. The basket is '
        'genuinely market-neutral.</div>'
        + H("What this phase does", P(
            "Trade the shortlisted pairs out-of-sample. For each pair we watch its gap and open a trade "
            "when it is unusually stretched (about 2 " + term("steps", "Standard deviations — how far today's gap is from its recent normal. The threshold automatically widens in turbulent markets and tightens in calm ones.") +
            " out), closing when it returns near normal. We do this for the single strongest pair, then "
            "for an evenly-weighted basket of ten pairs chosen so no stock is reused."))
        + H("What we achieved", UL(
            "The single pair grew about <b>43%</b> over the period with a decent reward-for-risk "
            "(" + term("Sharpe", "Reward for the bumpiness endured; higher is better, above ~1 is good.") + " 0.58).",
            "The ten-pair basket was <b>smoother</b> — a shallower worst-drop (−8% vs −12.7%) — because "
            "spreading across pairs cancels out individual rough patches.",
            "Crucially, the basket's " + term("beta", "How much it moves when the market moves 1%. Near zero = market-neutral.") +
            " to the market is about <b>0.09 (near zero)</b>, confirming it profits from the pairs "
            "themselves, not from the market's direction."))
        + H("Key outputs",
            figure_panels(g(strat, 0), "Trading the single strongest pair (2020+).",
                "Top: the gap over time with the open/close levels. Bottom: how £1 grew.",
                [("top", "date (2020 onward)",
                  "the standardised gap (red = open levels, grey = close levels)"),
                 ("bottom", "date", "value of £1 invested")],
                "The rule behaves sensibly — opening when the gap is stretched and closing as it returns — "
                "and the pair ended the unseen period clearly in profit.")
            + figure_panels(g(strat, 1), "The ten-pair basket.",
                "Left: basket vs single-pair growth. Middle: the basket's drops from its peak. Right: "
                "how much each pair contributed.",
                [("left", "date", "value of £1 invested (basket vs single pair)"),
                 ("middle", "date", "% below the previous peak (shallower is better)"),
                 ("right", "total return over the period", "each pair")],
                "The basket's ride is noticeably smoother than the single pair (shallower drops), and the "
                "gains come from several pairs rather than one lucky bet — the diversification is working.")
            + figure(g(strat, 2), "Is it really market-neutral?",
                "Each dot is one day: the market's move that day against the basket's move. A nearly flat "
                "red line means the basket barely follows the market.",
                "the market's daily return",
                "the basket's daily return (the red line's steepness is the 'beta'; near-flat = good)",
                "The dots form an almost-flat cloud, so the basket hardly moves with the market — its "
                "profits really do come from the pairs closing back up, not from market direction.")
            + table(mt, "Scorecard: the single pair vs the diversified basket (before trading costs).")))


NEXT = [
    ("Phase 6 — Walk-forward test", "Re-run the whole pipeline on a rolling schedule across 2020+: every "
     "few months, re-group the stocks, re-find the pairs and trade the next stretch, using the same frozen "
     "fingerprint-maker. This produces one continuous, realistic out-of-sample track record — the headline "
     "result of the dissertation."),
    ("Phase 7 — Pair persistence", "Track which pairs survive from one period to the next and which come "
     "and go, and see whether pairs change more during market stress."),
    ("Phase 8 — Trading costs", "Apply realistic commission and slippage to every trade and check whether "
     "the strategy still makes money after fees."),
    ("Phase 9 — Benchmark comparison", "Run the exact same pipeline with simpler engines — a basic linear "
     "version, a plain price-correlation version, and a buy-and-hold baseline — to prove the machine-"
     "learning approach actually adds value."),
    ("Phase 10 — Results &amp; write-up", "Compile the final figures, tables and summary statistics into "
     "the dissertation chapters."),
]


# ---------- assemble ---------------------------------------------------------
PHASES = [
    ("p1", "Phase 1 · Data", "Phase 1 — Data Foundation: Universe, Cleaning &amp; Feature Engineering", phase1),
    ("p2", "Phase 2 · VAE", "Phase 2 — VAE Training and Latent Space Inspection", phase2),
    ("p3", "Phase 3 · Groups", "Phase 3 — HDBSCAN Clustering and Stability", phase3),
    ("p4", "Phase 4 · Pairs", "Phase 4 — Cointegration and Pair Selection", phase4),
    ("p5", "Phase 5 · Strategy", "Phase 5 — Strategy: Single-Pair and Multi-Pair", phase5),
]


def build():
    nav = "".join(f'<a href="#{pid}">{lbl}</a>' for pid, lbl, *_ in PHASES)
    parts = [f"""<header><div class="wrap"><h1>Unsupervised-Learning Pairs Trading</h1>
      <p class="sub">Progress report &mdash; Phases 1 to 5</p></div></header>
      <nav id="nav"><div class="wrap"><a href="#overview">Overview</a>{nav}
      <a href="#next">What's next</a><a href="#glossary">Glossary</a></div></nav><main class="wrap">"""]

    cards = "".join(f'<div class="card"><div class="big">{v}</div>'
                    f'<div class="lbl">{term(l, d)}</div></div>' for l, v, d in SCORECARD)
    tracker = ("".join(f'<span class="done">{n} ✓</span>' for n in
               ["1 Data", "2 VAE", "3 Groups", "4 Pairs", "5 Strategy"]) +
               "".join(f'<span class="todo">{n}</span>' for n in
               ["6 Walk-forward", "7 Persistence", "8 Costs", "9 Benchmark", "10 Write-up"]))
    parts.append(f'<section id="overview"><h2>Overview</h2>{OVERVIEW}'
                 f'<h3>Headline results</h3><div class="cards">{cards}</div>'
                 f'<h3>Progress</h3><div class="tracker">{tracker}</div></section>')

    for pid, _lbl, title, fn in PHASES:
        parts.append(f'<section id="{pid}"><h2>{title}</h2>{fn()}</section>')

    nx = "".join(f"<h3>{t}</h3>{P(d)}" for t, d in NEXT)
    parts.append(f'<section id="next"><h2>What\'s next (Phases 6–10)</h2>'
                 f'{P("The first five phases above build and validate the engine. The remaining phases put it through its paces and write it up. Here is what each one will do.")}{nx}</section>')

    gl = "".join(f"<dt>{t}</dt><dd>{esc(d)}</dd>" for t, d in GLOSSARY)
    parts.append(f'<section id="glossary"><h2>Glossary</h2><dl class="gloss">{gl}</dl></section>')
    parts.append('</main><div id="lightbox"><img></div>'
                 '<footer class="wrap">Click charts to zoom · hover underlined terms for definitions.</footer>')

    doc = ("<!doctype html><html lang='en'><head><meta charset='utf-8'>"
           "<meta name='viewport' content='width=device-width, initial-scale=1'>"
           "<title>Pairs Trading — Progress Report</title><style>" + CSS + "</style></head><body>"
           + "\n".join(parts) + "<script>" + JS + "</script></body></html>")
    OUT.write_text(doc, encoding="utf-8")
    print(f"Wrote {OUT}  ({OUT.stat().st_size/1024:.0f} KB)")


GLOSSARY = [
    ("Pairs trading", "Buy one stock and short another that normally moves with it; you profit when the gap between them returns to its usual level, regardless of which way the market goes."),
    ("Fingerprint / latent code", "A short list of numbers (here, 12) summarising how a stock has recently behaved. Look-alike stocks get similar fingerprints."),
    ("VAE (variational autoencoder)", "The small neural network that produces the fingerprints. It learns to squeeze a 60-day pattern down to 12 numbers and rebuild it, arranging the numbers so 'close together' means 'behaves alike'."),
    ("Behaviour group / cluster", "A set of stocks with similar fingerprints, found automatically rather than by industry label."),
    ("Cointegration ('springy' gap)", "Two stocks' price gap reliably springs back to a normal level instead of wandering off -- exactly what makes a pair tradeable."),
    ("Hedge ratio / balancing weight", "How much of stock B to short against one unit of stock A so the pair ignores the overall market's direction."),
    ("Half-life (spring-back speed)", "Roughly how many days the gap takes to close half of a stretch."),
    ("Z-score / 'steps'", "How unusual today's gap is versus its recent normal, in standard deviations. We open past 2 and close near half a step; this automatically widens in turbulent markets and tightens in calm ones."),
    ("Sharpe ratio", "Reward for the bumpiness endured -- higher is better; above about 1 is considered good."),
    ("Drawdown", "The worst drop from a high point to a later low along the way."),
    ("Beta", "How much something moves when the whole market moves 1%. Near zero means market-neutral."),
    ("Match score (ARI)", "How closely two groupings agree: 1 = identical, 0 = no better than chance. Used to check the groups are stable."),
    ("Out-of-sample", "Data the model never saw while being built (here, 2020 onward) -- the fair test of whether it really works."),
]

CSS = """
:root{--bg:#f6f7f9;--ink:#1f2733;--muted:#5b6675;--accent:#0d6e6e;--accent2:#10518f;--line:#e2e6ec;--card:#fff}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.65 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:980px;margin:0 auto;padding:0 20px}
header{background:linear-gradient(120deg,#0d6e6e,#10518f);color:#fff;padding:30px 0 24px}
header h1{margin:0;font-size:28px}header .sub{margin:6px 0 0;opacity:.9}
nav{position:sticky;top:0;z-index:50;background:#fff;border-bottom:1px solid var(--line);box-shadow:0 1px 6px rgba(0,0,0,.04)}
nav .wrap{display:flex;flex-wrap:wrap;gap:2px}
nav a{padding:12px 11px;color:var(--muted);text-decoration:none;font-size:14px;font-weight:600;border-bottom:3px solid transparent}
nav a:hover{color:var(--accent)}nav a.active{color:var(--accent);border-bottom-color:var(--accent)}
main{padding:10px 20px 60px}
section{padding:26px 0;border-top:1px solid var(--line)}
h2{font-size:24px;color:var(--accent2);margin:.2em 0 .6em}
h3{font-size:18px;margin:1.5em 0 .5em}
.lead{font-size:18px}
.lead-box{background:#eef6f6;border-left:4px solid var(--accent);padding:12px 16px;border-radius:6px;font-size:16.5px}
.md p{margin:.5em 0}.md ul{margin:.4em 0 .4em 1.1em}.md li{margin:.25em 0}
.pipe{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:14px 0}
.pipe span{background:var(--accent);color:#fff;padding:7px 12px;border-radius:20px;font-weight:600;font-size:14px}
.pipe i{color:var(--muted);font-style:normal}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px}
.card .big{font-size:22px;font-weight:700;color:var(--accent)}.card .lbl{font-size:13px;color:var(--muted);margin-top:4px}
.tracker{display:flex;flex-wrap:wrap;gap:6px}.tracker span{font-size:13px;padding:5px 10px;border-radius:6px}
.tracker .done{background:#dff3ea;color:#0a7048;border:1px solid #bfe6d4}
.tracker .todo{background:#f0f1f4;color:#8a93a0;border:1px solid var(--line)}
figure{margin:16px 0;text-align:center}
img.zoom{max-width:100%;border:1px solid var(--line);border-radius:8px;background:#fff;cursor:zoom-in}
figcaption{font-size:14px;color:var(--ink);margin-top:8px;text-align:left;background:#fafbfc;border:1px solid var(--line);border-radius:8px;padding:10px 12px}
.axes{display:block;color:var(--muted);font-size:13px;margin-top:6px}
.axes ul{margin:4px 0 0 1.1em}
.take{display:block;margin-top:8px;background:#eef6f6;border-radius:6px;padding:8px 11px;color:#0a5246;font-size:14px}
.tbl{overflow-x:auto;margin:12px 0}
.tbl table{border-collapse:collapse;font-size:13.5px;background:#fff;width:100%}
.tbl th,.tbl td{border:1px solid var(--line);padding:6px 10px;text-align:left}
.tbl th{background:#f0f3f6}
.tcap{font-size:13px;color:var(--muted);margin:2px 0 0}
.term{border-bottom:1px dotted var(--accent);cursor:help;position:relative}
.term:hover::after,.term:focus::after{content:attr(data-def);position:absolute;left:0;top:1.7em;width:280px;
  background:#1f2733;color:#fff;padding:9px 11px;border-radius:8px;font-size:13px;line-height:1.4;z-index:60;
  box-shadow:0 6px 20px rgba(0,0,0,.25);font-weight:400}
.gloss dt{font-weight:700;color:var(--accent2);margin-top:12px}.gloss dd{margin:2px 0 0}
footer{padding:24px 20px 50px;color:var(--muted);font-size:13px;text-align:center}
#lightbox{display:none;position:fixed;inset:0;background:rgba(10,15,25,.9);z-index:100;cursor:zoom-out;padding:30px}
#lightbox img{max-width:100%;max-height:100%;display:block;margin:auto;border-radius:6px}
"""

JS = """
var lb=document.getElementById('lightbox'),lbi=lb.querySelector('img');
document.querySelectorAll('img.zoom').forEach(function(im){im.addEventListener('click',function(){lbi.src=im.src;lb.style.display='block';});});
lb.addEventListener('click',function(){lb.style.display='none';lbi.src='';});
document.addEventListener('keydown',function(e){if(e.key==='Escape'){lb.style.display='none';}});
var links={};document.querySelectorAll('#nav a').forEach(function(a){links[a.getAttribute('href').slice(1)]=a;});
var obs=new IntersectionObserver(function(es){es.forEach(function(en){var a=links[en.target.id];if(!a)return;
if(en.isIntersecting){Object.values(links).forEach(function(x){x.classList.remove('active');});a.classList.add('active');}});},
{rootMargin:'-45% 0px -50% 0px'});
document.querySelectorAll('section[id]').forEach(function(s){obs.observe(s);});
"""

if __name__ == "__main__":
    build()
