# DESIGN.md — Karachi Heat Priority Map

Written before any styling, per PROMPT.md §9. Reviewed against the brief and the
avoid-list at the end; the revisions that review forced are recorded there.

## Who this is for, and where they are standing

A field coordinator, outdoors, in sun, on a mid-range Android phone, deciding where a
van goes next. Possibly one-handed. Possibly on 3G. They are not browsing — they have a
question and about ten seconds.

Second audience: an NGO manager or a mentor on a laptop, deciding whether to trust any of
this. They will look for the caveats, and they should find them without hunting.

Those two needs pull in opposite directions — speed versus honesty — and the resolution
runs through the whole design: **the map answers fast, the caveats are one tap away and
never more than one tap away.**

## Three principles, specific to this project

**1. The uncertainty is part of the answer, not a disclaimer.**
Only 28 of 53 top-priority cells survive the sensitivity analysis. A design that renders
all 53 in identical confident colour would be lying by omission. Cells the model is unsure
about must *look* unsure — this is a visual requirement, not a footnote. Hatching, not a
tooltip.

**2. Readable in sun beats pretty on a desk.**
Text contrast ≥ 4.5:1 and key map labels ≥ 7:1 because of glare. No thin grey-on-white.
No colour whose meaning collapses under a bright screen at low brightness. Tap targets
≥ 44 px because this is used standing up, not sitting down.

**3. Nothing may imply a verdict on a neighbourhood.**
The legend says "Highest priority for support", never "worst" or "most dangerous"
(§2.5). Colour runs from pale to deep — a *quantity* ramp, not a traffic light. Red-to-
green would read as good-versus-bad places and is explicitly rejected.

## Colour

Karachi's hot season is dust, haze and hard light — bleached, not vivid. The palette is
drawn from that, and from the plain practicality of relief work: painted metal, tarpaulin,
printed forms.

| Token | Hex | Role |
|---|---|---|
| `--ink` | `#1A1C1E` | All body text. Near-black, never pure black. 16.12:1 on `--paper`. |
| `--paper` | `#FAF8F5` | Page background. Warm off-white, like sun on plaster. |
| `--rule` | `#D8D2C9` | Hairlines, table rules, panel edges. |
| `--deep` | `#6C2A1F` | The top of every sequential ramp; also the focus ring. 9.96:1 on `--paper`. |
| `--signal` | `#1F5E6B` | Interactive elements, links, the selected cell outline. 6.90:1 — above the 4.5:1 body requirement; not used for map labels. |
| `--muted` | `#58554E` | Secondary text. Contrast **7.01:1** on `--paper` (measured). |

The **priority ramp** is a five-step sequential scale:

`#F6E3D0` → `#D4B5A4` → `#B18678` → `#8E584B` → `#6C2A1F`

Measured, not assumed (`tests/test_design.py` re-checks all of it):
- **lightness decreases monotonically**, so the order survives greyscale — which matters,
  because field briefs get photocopied;
- the order is **preserved under simulated deuteranopia, protanopia and tritanopia**;
- adjacent steps differ by 1.54–1.83:1 in contrast, enough to separate by eye at the
  hexagon sizes used.

**No text is ever drawn on a ramp colour.** Ink on the deepest step is only 1.62:1, so
cell labels would be unreadable — which is why cells carry no text at all. The ≥ 7:1
requirement for key labels applies to the legend and panel, which sit on `--paper`, where
`--ink` measures 16.12:1 and `--deep` 9.96:1.

Cells the model is unsure about carry a **diagonal hatch** over their fill. Hatch, not a
lighter tint: a tint would read as "lower priority", which is a different claim.

## Type

One Latin typeface, system stack — no webfont, because a webfont is a network round-trip
on 3G for no legibility gain at these sizes:

```
system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif
```

| Role | Size / weight |
|---|---|
| Page title | 1.35 rem / 600 |
| Section heading | 1.05 rem / 600 |
| Body | 1 rem / 400, line-height 1.55 |
| Panel label | 0.8 rem / 600, letter-spacing 0.01em |
| Number readout | 1.6 rem / 600, tabular figures |

Numbers use `font-variant-numeric: tabular-nums` so values don't jitter as the panel
updates.

## Layout

Alignment rule: **one text column, left-aligned to a single edge, everywhere.** No centred
body text. The map is the exception — it goes full-bleed, because it is the content.

### 375 px (phone)

```
┌───────────────────────────────┐
│ Karachi Heat Priority Map     │  title, 44px tall
├───────────────────────────────┤
│ [Priority ▾]        [About]   │  layer picker + link, 44px targets
├───────────────────────────────┤
│                               │
│                               │
│          MAP                  │  full-bleed, fills remaining height
│        (265 hexes)            │
│                               │
│                               │
├───────────────────────────────┤
│ ▁▂▃▄▅  Highest → Lower        │  legend, always visible
└───────────────────────────────┘
        ↓ tap a cell
┌───────────────────────────────┐
│ ───                           │  drag handle
│ Rank 12 of 245                │
│ Higher priority for support   │
│                               │
│ Why here                      │
│ • Further from a clinic       │
│ • Hotter ground               │
│ • Little greenery or shade    │
│                               │
│ Confidence: uncertain ▨       │
│ This cell moves between rank  │
│ 8 and 47 when the assumptions │
│ are varied.                   │
│                               │
│ What this cannot tell you  ▸  │
└───────────────────────────────┘
   bottom sheet, ~60% height, swipe to dismiss
```

### 1280 px (laptop)

```
┌──────────────────────────────────────────────────────────────┐
│ Karachi Heat Priority Map            Map  Plan  Briefs  About│
├────────────────────────────────┬─────────────────────────────┤
│                                │ Rank 12 of 245              │
│                                │ Higher priority for support │
│                                │                             │
│            MAP                 │ Why here                    │
│         (265 hexes)            │ • Further from a clinic     │
│                                │ • Hotter ground             │
│                                │ • Little greenery or shade  │
│                                │                             │
│                                │ Values                      │
│                                │  Surface temp    44.7 °C    │
│  ▁▂▃▄▅ Highest → Lower         │  People            2,378    │
│                                │  To a clinic      1,540 m   │
└────────────────────────────────┴─────────────────────────────┘
     map ~62%                      panel ~38%, fixed, scrolls
```

The panel is **persistent on desktop** and a **bottom sheet on phone** — the same content
and the same DOM order, so keyboard and screen-reader users get one consistent reading
order at both widths.

## What the panel must always contain

In this order, because it is the order a coordinator asks in:

1. **Rank and class** — "Rank 12 of 245 · Higher priority for support"
2. **Why here** — up to three plain phrases, or "Below the Landhi average on every
   measure we track" when nothing is above the median
3. **Confidence** — the stability call, with the rank interval stated in words
4. **Values** — raw numbers with units, so a sceptical reader can check
5. **What this cannot tell you** — collapsed, always present, never removable

Item 5 is not decoration. It carries the population undercount and the missing
relief-centre indicator, and it is the thing that keeps the map honest when it is
screenshotted and forwarded on WhatsApp.

## Motion

None, beyond the bottom sheet's slide and a 120 ms fill transition on hover. Everything
respects `prefers-reduced-motion: reduce`, which disables both. No animated map
transitions — they cost frames on a mid-range phone and communicate nothing.

## Review against the brief's avoid-list

Checked honestly; two things had to change.

| To avoid | Status |
|---|---|
| Warm cream background, serif display, terracotta accent | **This was the first draft.** `--paper` is a warm off-white and `--deep` is close to terracotta. **Revised:** the serif display is gone entirely (system sans throughout), and `--deep` is justified as the top of a sequential data ramp rather than as a decorative accent — it appears in the map and the focus ring, nowhere else. |
| Near-black with one acid-bright accent | Avoided — the palette is muted throughout, `--signal` is a desaturated teal. |
| Broadsheet hairline columns | Avoided — one column. |
| Identical rounded cards, soft grey shadows, gradient washes | **The first draft had the panel as a rounded card with a shadow.** **Revised:** the panel is a plain surface separated by a 1px `--rule`. No shadows anywhere except the bottom sheet's edge, which is doing real work (signalling it is above the map). |
| All-caps eyebrow labels | Avoided. |
| Middle-dot metadata strings | Used exactly once — "Rank 12 of 245 · Higher priority for support" — where the dot separates two genuinely parallel facts. Not used as decoration elsewhere. |
| Arrows appended to button text | Avoided. "What this cannot tell you ▸" is a disclosure triangle indicating expansion state, not an arrow on a button. |
| One highlighted word in a headline | Avoided. |
| Numbered markers on non-sequences | Avoided — the "Why here" list is bulleted, because the three reasons are not ranked against each other in any way a reader could act on. |

## What would make this design wrong

Stated so it can be checked later: if field feedback says coordinators ignore the
confidence hatching, or read the colour ramp as a verdict on neighbourhoods despite the
wording, then principles 1 and 3 have failed and the design needs revisiting — not the
copy.
