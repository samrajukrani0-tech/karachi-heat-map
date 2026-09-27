# Entering the expert rankings (P6-01)

When completed copies of [the ranking form](expert-ranking-form.md) come back from
Edhi, Saylani or any other relief team, this is how they get into the analysis. Nothing
else needs building: the script is written and tested, and it is waiting for this file.

## 1. Before handing out the form

- Ask people to fill it in **before they see the map**, and write down whether they did.
  Someone who has seen the map will tend to agree with it, which proves nothing.
- Do **not** write anyone's name anywhere in the project. Give each person a code:
  R01, R02, R03 … Keep the list of who is who on paper, not in the repository (§2.5).

## 2. Typing each form in

Open `data/manual/expert_rankings.csv`. It has a header row and nothing else. Add **one
row per place ranked** on each form:

| Column | What to put | Example |
|---|---|---|
| `respondent` | the person's code | `R01` |
| `organisation` | who they work for | `Edhi Foundation` |
| `role` | their job, in a few words | `ambulance coordinator` |
| `years_in_landhi` | as they wrote it, or blank | `6` |
| `date` | the day they filled it in | `2026-11-14` |
| `ranked_before_seeing_map` | `yes` or `no` | `yes` |
| `place` | exactly as printed on the form | `Ilyas Goth` |
| `rank` | the number they wrote, 1 = needs support first | `1` |
| `lat`, `lon` | only for a place they **wrote in**; blank otherwise | `24.8401`, `67.2003` |
| `notes` | anything they said about that place | `water tanker stops here` |

Ranks for one person must be 1, 2, 3 … with no gaps or repeats. A place written in by
hand is scored only if you add its location, which you can read off any map app.
Without a location it is listed in the report, not guessed.

## 3. Running it

```sh
uv run python -m pipeline.expert --check   # checks the file, names any bad line
uv run python -m pipeline.expert           # runs the comparison
```

This writes `data/processed/expert_agreement.json` and `docs/expert-agreement.md`.
The report gives each person's agreement with the model (Spearman ρ with a 95%
confidence interval and a permutation p-value). It also shows how far the blind
respondents agree with **each other** (Kendall's W) and how their average ranking
compares with the model.

## 4. Then

Read the notes before the numbers. Decide whether anything in the model should change;
that decision is yours (P6-01), and it goes in DECISIONS.md like every other.
