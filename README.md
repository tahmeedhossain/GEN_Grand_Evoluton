# GEN-Grand: the Grand Epistemic Network of physics

Six released instances of the Great Epistemic Network (GEN) — the electromagnetism history reader, the lattice energy-flow network, the University Physics reader, the Standard Model history, the nonclassicality network and the quantum resource theory network — normalised into one state / model / observable schema, glued on shared concepts, and analysed by an engine that detects the update rules from structure, replays the Standard Model history, verifies the readers as filtrations, reproduces the census of the quantum networks and measures pedagogical against historical order.

The repository holds two versions of the network. The **two-tier network** (Part III, 20 November 2026) is the main network. The **tierless version** (Parts I and II, 13–14 November 2026) is kept as it was, and every page can switch to it.

Live site: https://tahmeedhossain.github.io/GEN_Grand_Evoluton/ (opens the main network).

## Main network: the two-tier network (Part III)

The same six graphs read at two levels of abstraction. Tier C holds the system-specific nodes (electromagnetism reader, Standard Model history, University Physics reader, lattice energy flow); tier A holds the generic nodes (nonclassicality network, resource-theory network). A state or observable node of tier A is a cluster of states or observables, and clustering is added as an operation of the method: rules R17 (state clustering), R18 (observable clustering: families, aggregates, effects), R19 (lift), R20 (descent), R21 (refinement), next to the eight phases of Part II.

- **Page:** `gen_two_tier_explorer.html`, opened by `index.html` (self-contained; open in a browser). Views: Evolution (year slider, the method cycle of the selected year in both tiers, a zoomable map of the network), Combined pipeline, Clusters, Checks, Method. Every node and line opens its statement, its references and, where they exist, the cells of the two-qubit kernel.
- **Text:** `TWO_TIER.md`: the claim and what the data says, abstraction edges, operations and rules, the combined pipeline, the closure of the memberships, the two-qubit kernel, proposals for the released graphs, limits. Every number in it is generated from the data by the build.
- **Data:** `data/gen_two_tier_network.json` (886 nodes, 1122 routes, 446 abstraction edges: 293 stated, 153 derived by closure), `out/two_tier_numbers.json` (every number quoted in the page and in `TWO_TIER.md`), `out/two_tier_context.json` (kernel table).
- **Engine:** `two_tier/` (`load.py`, `abstraction.py`, `kernel.py`, `pipeline.py`, `detail.py`, `export.py`, `notes.py`, `template.html`), run by `build_two_tier.py`. It reads `data/gen_grand_network.json`, `data/gen_evolution_network.json` and `data/sources/{gpt_v2.6,qrt_v1.2,hep_v1.2}.json`.

Main results (details and limits in `TWO_TIER.md`): no stated membership edge runs from a generic node into a system-specific cluster; 18 run from system-specific nodes into generic clusters, 15 of them curated for this network; the closure of the memberships derives 153 facts with no conflict, and the 112 facts that concern a state realised in the two-qubit kernel table agree with the computed cells in all 125 comparisons; ten proposals for the released graphs, none applied.

## Tierless version (Parts I and II)

Version 2 (14 November 2026) adds **Part II: the evolution of the network** — a calendar-year index for the two quantum networks computed from their references, the derivation of their growth node by node and route by route, the four-branch evolutionary network (electromagnetism, the Standard Model history as the union of its steps with removals, nonclassicality, resource theories) with a year slider, the growth rules and counting identities, and the method phases read against the philosophy of science. Version 1 (Part I only) is kept as `GEN_grand_thesis_v1.pdf`.

- **Thesis:** `thesis/main.pdf` = `GEN_grand_thesis.pdf` (XeLaTeX source `thesis/main.tex` + `thesis/part2.tex`; every number is a macro in `thesis/numbers.tex` / `thesis/numbers_evo.tex` written by the build).
- **Merged network (Part I):** `data/gen_grand_network.json` (883 nodes, 1011 routes, 105 concepts).
- **Evolutionary network (Part II):** `data/gen_evolution_network.json` (406 nodes, 578 routes, 57 shared concepts, every item dated with provenance; HEP items carry removal step and year).
- **Explorer pages:** `gen_grand_explorer.html` (Part I) and `gen_evolution_explorer.html` (Part II, year slider; self-contained; open in a browser).
- **Engine:** `gen_engine/` — Part I: `schema.py`, `load.py`, `glue.py`, `atlas.py`, `ops.py`, `replay_hep.py`, `filtration.py`, `census.py`, `figures.py`, `tables.py`, `page.py`; Part II: `chrono.py` (the year index), `evolution.py` (growth analyses), `figures_evo.py`, `tables_evo.py`, `page_evo.py`.
- **Sources:** `data/sources/` — the released data files of the six repositories at the commits in `data/sources/PROVENANCE.txt`.

## Switching between the versions

Every page has a **Version** button at the bottom left (`assets/versions.js`). It lists the two-tier network (main), the tierless evolution (Part II) and the tierless merged network (Part I), with links to `TWO_TIER.md`, the thesis and this repository. The switch works on the live site and in a local clone (open the HTML files in a browser). The live site is served by GitHub Pages from the `gh-pages` branch, which `.github/workflows/publish-pages.yml` copies from `main` on every push.

## Rebuild everything

```sh
python3 build.py                 # Part I: out/*.json, data/gen_grand_network.json, thesis/numbers.tex, figures, tables, page;
                                 # then Part II (build_evolution.py): out/evolution.json, data/gen_evolution_network.json,
                                 # thesis/numbers_evo.tex, figures/fig_evo_*.pdf, thesis/tables/tab_evo_*.tex, gen_evolution_explorer.html
python3 build_evolution.py       # Part II analyses alone (needs out/hep_replay.json from build.py)
python3 -m gen_engine.figures_evo; python3 -m gen_engine.tables_evo; python3 -m gen_engine.page_evo
python3 build_two_tier.py        # Part III: data/gen_two_tier_network.json, out/two_tier_*.json, gen_two_tier_explorer.html, TWO_TIER.md
cd thesis && xelatex main && bibtex main && xelatex main && xelatex main
```

Requirements: Python 3.11+, networkx, matplotlib, numpy, scipy (the two-qubit kernel of Part III); XeLaTeX with the DejaVu fonts (TeX Live).

## What the engine computes

| Module | Output |
|---|---|
| `load.py` | the six instances in the universal schema (`out/branch_*.json`) |
| `atlas.py` + `glue.py` | the merged network with concepts, roles and role flips |
| `replay_hep.py` | per-step decomposition of the Standard Model history into primitive operations; automatic rule matrix vs the hand matrix (117/120) and the paper's table (114/120); cumulative view with observable families; predictive content per cluster |
| `filtration.py` | no-forward-link check (0/0/0 violations), growth curves, failed-route resolution, 2-section cycles and chains, chapter carry-in, historical vs pedagogical order (Kendall τ_b = 0.857 on 41 concepts) |
| `census.py` | witness-matrix census (469/3094), pair census (137/4186), QRT conversion census (14/156), sector × term census (24/60), agendas |
| `chrono.py` | calendar years for every node and route of EM, HEP (union of steps), GPT, QRT from references / step years / paragraph years, with provenance; filtration check (0 violations); robustness variant (latest cited source) |
| `evolution.py` | arrival/closure decomposition and the identity E = Σ d_arr − Σ(a(r)−1)⁺ + C (holds in all four branches); closure latency; preferential-closure ratio; densification α (1.40 / 1.55 / 1.47 / 1.30); witness–effect timing; explanation lags; layer half-years; shared-concept transfer lags; merged curve with glue and collapsed count; decade × phase tables; HEP rule firings by year |
| `two_tier/load.py` | nodes and routes of the six branches with tier (C system-specific, A generic) and year |
| `two_tier/abstraction.py` | abstraction edges (member, cut, subset, equal, complement, aggregate, criterion, test, …) from released edges, released statements, Part I cross-edges and glue, and the curation of 18 November 2026; closure of the memberships (rule R20) with domain and frame tags |
| `two_tier/kernel.py` | ten free-set predicates (purity, athermality, asymmetry, coherence, imaginarity, magic, discord, entanglement, steering, Bell nonlocality) on explicit two-qubit states; implications of the incidence table against the released inclusions; witnesses of the strictness claims |
| `two_tier/pipeline.py` | operations, rules R1 to R21, the stages of the combined cycle (phase × tier) and the attribution of every event to a stage |
| `two_tier/detail.py`, `export.py`, `notes.py` | the statement, references and check data behind every node and line; the page; `TWO_TIER.md` |

The thesis and the two-tier network are generated with Claude (Anthropic) for Tahmeed Hossain (Department of Theoretical Physics, University of Dhaka); see the thesis's disclosure chapter and the limits in `TWO_TIER.md`. Code: MIT. Text, data and figures: CC BY-NC-SA 4.0 where they derive from the University Physics reader (which carries that licence), CC BY 4.0 otherwise.
