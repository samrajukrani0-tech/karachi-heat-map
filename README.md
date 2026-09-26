# Karachi Heat Priority Map

A free, mobile-first map to help a Karachi relief team decide where heat-relief
support should go first during a heatwave, and why. Pilot area: **Landhi Town**.

**Status: in development.** Phase 0 (setup and decisions) is complete. Nothing here
should be used for real planning yet.

## What it is

For each small area (H3 resolution 9 cells, about 0.105 km² each) the model combines
three things:

- **Hazard** — how hot the ground gets on summer afternoons, from Landsat surface
  temperature.
- **Exposure** — how many people live there.
- **Vulnerability** — age, how densely built it is, how little greenery there is, and
  how far it is from care and from a relief centre.

Priority is the geometric mean of the three, so all three have to be present for an
area to rank highly. Every area also shows the three reasons that push its own score
up, in plain words.

## What it is not

- Not an official warning system. Follow the Pakistan Meteorological Department and
  PDMA Sindh for warnings.
- Not a mortality model. It never estimates deaths or assigns causes.
- Not a verdict on any neighbourhood.

## Reproduce

Requires [uv](https://docs.astral.sh/uv/). Python 3.12 is installed by uv itself.

```sh
uv sync
uv run python scripts/check.py --quick
uv run python scripts/features.py
```

Note: `h3` is pinned below 4.4 because 4.4+ publishes no x86_64 macOS wheel.

## Reading the repo

| File | What it holds |
|---|---|
| `PROMPT.md` | the full brief this project is built against |
| `CLAUDE.md` | condensed working rules |
| `DECISIONS.md` | every judgement call, with options, reasoning and the decision |
| `QUESTIONS.md` | open questions only Samraj can answer |
| `PROGRESS.md` | append-only log of what was built and the evidence for it |
| `LEARNING_LOG.md` | the modelling ideas in plain language, with practice questions |
| `features.json` | the backlog and the source of truth for progress |
| `config/` | the decisions as machine-readable configuration |

## Credits and licences

- Code: MIT (`LICENSE`)
- Documentation and site text: CC BY 4.0 (`LICENSE-docs`)
- `data/processed/`: ODbL 1.0 (`LICENSE-data`) — it contains data derived from
  OpenStreetMap, © OpenStreetMap contributors
- Every dataset keeps its own licence; see `data/SOURCES.md`

## AI assistance

Built with Claude Code as a coding assistant. Research question, modelling decisions,
weights and fieldwork by Samraj Lal Ukrani.
