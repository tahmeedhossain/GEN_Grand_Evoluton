# GEN-Grand: the Grand Epistemic Network of physics

Six released instances of the Great Epistemic Network (GEN) — the electromagnetism history reader, the lattice energy-flow network, the University Physics reader, the Standard Model history, the nonclassicality network and the quantum resource theory network — normalised into one state / model / observable schema, glued on shared concepts, and analysed by an engine that detects the update rules from structure, replays the Standard Model history, verifies the readers as filtrations, reproduces the census of the quantum networks and measures pedagogical against historical order.

Version 2 (14 November 2026) adds **Part II: the evolution of the network** — a calendar-year index for the two quantum networks computed from their references, the derivation of their growth node by node and route by route, the four-branch evolutionary network (electromagnetism, the Standard Model history as the union of its steps with removals, nonclassicality, resource theories) with a year slider, the growth rules and counting identities, and the method phases read against the philosophy of science. Version 1 (Part I only) is kept as `GEN_grand_thesis_v1.pdf`.

- **Thesis:** `thesis/main.pdf` = `GEN_grand_thesis.pdf` (XeLaTeX source `thesis/main.tex` + `thesis/part2.tex`; every number is a macro in `thesis/numbers.tex` / `thesis/numbers_evo.tex` written by the build).
- **Merged network (Part I):** `data/gen_grand_network.json` (883 nodes, 1011 routes, 105 concepts).
- **Evolutionary network (Part II):** `data/gen_evolution_network.json` (406 nodes, 564 routes, 57 shared concepts, every item dated with provenance; HEP items carry removal step and year).
- **Explorer pages:** `gen_grand_explorer.html` (Part I) and `gen_evolution_explorer.html` (Part II, year slider; self-contained; open in a browser).
- **Engine:** `gen_engine/` — Part I: `schema.py`, `load.py`, `glue.py`, `atlas.py`, `ops.py`, `replay_hep.py`, `filtration.py`, `census.py`, `figures.py`, `tables.py`, `page.py`; Part II: `chrono.py` (the year index), `evolution.py` (growth analyses), `figures_evo.py`, `tables_evo.py`, `page_evo.py`.
- **Sources:** `data/sources/` — the released data files of the six repositories at the commits in `data/sources/PROVENANCE.txt`.

## Rebuild everything

```sh
python3 build.py                 # Part I: out/*.json, data/gen_grand_network.json, thesis/numbers.tex, figures, tables, page;
                                 # then Part II (build_evolution.py): out/evolution.json, data/gen_evolution_network.json,
                                 # thesis/numbers_evo.tex, figures/fig_evo_*.pdf, thesis/tables/tab_evo_*.tex, gen_evolution_explorer.html
python3 build_evolution.py       # Part II analyses alone (needs out/hep_replay.json from build.py)
python3 -m gen_engine.figures_evo; python3 -m gen_engine.tables_evo; python3 -m gen_engine.page_evo
cd thesis && xelatex main && bibtex main && xelatex main && xelatex main
```

Requirements: Python 3.11+, networkx, matplotlib, numpy; XeLaTeX with the DejaVu fonts (TeX Live).

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

The thesis is generated with Claude (Anthropic) for Tahmeed Hossain (Department of Theoretical Physics, University of Dhaka); see its disclosure chapter. Code: MIT. Text, data and figures: CC BY-NC-SA 4.0 where they derive from the University Physics reader (which carries that licence), CC BY 4.0 otherwise.
