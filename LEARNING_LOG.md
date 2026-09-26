# Learning log

One entry per feature, in plain language, with the A Level connection where the link
is genuine, and two or three questions to check understanding.

---

## Phase 0 — the decisions, and why the maths choices are not arbitrary

**What and why.** Before writing any pipeline code we settled twelve decisions. Three
of them are really mathematical choices in disguise, and they interact in a way worth
understanding, because a mentor or interviewer is most likely to push on exactly this.

**The key idea in A Level terms.**

*Normalisation (D5).* Each indicator arrives in its own units — degrees Celsius,
metres, a fraction, a count of people. You cannot add or multiply those, so each is
mapped to 0–1. Robust min–max clips at the 5th and 95th percentile and then scales
linearly, so it keeps the *spacing* between cells. Percentile rank keeps only the
*order*. Choosing between them is choosing how much information you keep: rank is
immune to outliers but throws away magnitude, so forty cells within a tenth of a
degree of each other get spread across the whole scale.

*Aggregation (D6).* Priority is a **geometric** mean of Hazard, Exposure and
Vulnerability, not an arithmetic one. The reason is substitutability. An arithmetic
mean lets a high value in one dimension compensate for a near-zero value in another,
so a scorching empty factory yard (H ≈ 1, V ≈ 0.8, E ≈ 0) scores 0.6 and ranks near
the top. The geometric mean gives it (1 × 0 × 0.8)^⅓ = 0. For risk, all three have to
be present for harm to happen, so multiplication is the honest model. The AM–GM
inequality also tells you the geometric mean is never larger than the arithmetic one,
so this is always the more cautious choice.

*The interaction (D6b).* These two decisions collide. Robust min–max produces exact
zeros for the bottom 5% of each indicator, and anything multiplied by zero is zero —
so the coolest 5% of cells would get Priority 0 no matter how many vulnerable people
live there. The fix is to floor H and V at 0.01 but leave E alone, because a zero in H
is an artefact of clipping (Landhi's coolest cells are still around 40 °C in June)
while a zero in E is a fact: nobody lives there.

*Weights (D7).* AHP turns pairwise comparisons into weights by taking the principal
eigenvector of the comparison matrix — the same eigenvector algebra as in Further
Maths, found here by power iteration. It also gives a consistency ratio, which is a
numerical check on whether your own judgements contradict each other. We use it only
for the six vulnerability indicators, which combine as a weighted *arithmetic* mean.
We deliberately do **not** use it for the three dimensions, because in a multiplicative
model an exponent is an elasticity — a percentage response — not an importance, and
Saaty's 1–9 importance scale does not translate into one.

**Questions.**

1. Why would percentile-rank normalisation make the map look more decisive than the
   data justifies?
<details><summary>Answer</summary>
Because it forces a uniform spread. If most cells sit within a narrow real range,
rank stretches those tiny differences across the full 0–1 scale, so cells that are
physically almost identical appear far apart. Robust min–max keeps them close
together, which is the truthful picture.
</details>

2. A cell has H = 0.9, E = 0.9, V = 0.02. What do the arithmetic and geometric means
   give, and which better describes the situation?
<details><summary>Answer</summary>
Arithmetic (equal weights): (0.9 + 0.9 + 0.02)/3 ≈ 0.61. Geometric:
(0.9 × 0.9 × 0.02)^⅓ ≈ 0.26. The geometric answer is the better description: the
people there are hot and numerous but not especially vulnerable, so they should not
rank alongside a cell that is hot, crowded *and* vulnerable.
</details>

3. Why does flooring Exposure at 0.01 quietly break the model?
<details><summary>Answer</summary>
Because E = 0 is a real measurement, not an artefact — it means nobody lives in the
cell. Flooring it gives empty industrial land and creek a small positive Priority, so
the map shows supplies being needed where there is nobody to receive them, and the
allocation planner would send stock there.
</details>

---

## P1-01 — The pilot boundary, and why area is measured in a different coordinate system

**What and why.** The whole project needs one authoritative outline of Landhi Town. We
take it from OpenStreetMap relation 16350631, which is a *relation*: not a shape itself,
but a list of member ways that have to be joined end to end into closed rings. The code
merges those ways, closes them into a polygon, subtracts any inner rings (holes), and
writes the result as GeoJSON with its provenance attached. It measured 25.370 km²,
matching the figure computed independently during Phase 0.

**The key idea in A Level terms.** The boundary is *stored* in EPSG:4326 — plain
longitude and latitude in degrees — but its area is *measured* in EPSG:32642, a
projected system in metres. This is not bureaucracy; it is the reason the number means
anything.

Latitude and longitude are angles on a sphere, so a "square degree" is not a fixed
amount of ground. One degree of latitude is about 111 km everywhere, but one degree of
longitude is 111 km × cos(latitude). At Karachi's 24.84° N that factor is cos(24.84°) ≈
0.908, so a degree of longitude covers about 101 km, not 111. Computing an area directly
from degrees would multiply two quantities measured in different real units and give a
number in "square degrees", which corresponds to no fixed patch of ground at all.

A projection such as UTM zone 42N solves this by flattening a narrow north–south strip
of the Earth onto a plane in metres, accepting small distortions in exchange for being
able to do ordinary flat geometry. Every distance and area in this project is computed
after that transformation, which is why `config/area.yaml` records both systems
separately.

**Questions.**

1. Landhi's boundary spans about 0.071° of longitude and 0.055° of latitude. Roughly
   what ground distances are those, and why isn't the ratio the same as 0.071 : 0.055?
<details><summary>Answer</summary>
Latitude: 0.055° × 111 km ≈ 6.1 km. Longitude: 0.071° × 111 km × cos(24.84°) ≈ 0.071 ×
101 ≈ 7.2 km. The ratio in degrees is about 1.29 : 1, but on the ground it is about
1.18 : 1, because the degrees of longitude are "shorter" at this latitude. A map drawn
straight from degrees is stretched east–west.
</details>

2. Why does the build deliberately fail instead of overwriting the file when the
   measured area falls outside 25.37 ± 0.75 km²?
<details><summary>Answer</summary>
Because OpenStreetMap is edited by anyone. If someone redraws the relation, a build that
silently overwrites would quietly change what "the pilot area" means, and every figure
downstream — cell count, population, every indicator — would shift with no record of
why. Failing forces a human decision and a DECISIONS.md entry.
</details>

3. The inner-ring subtraction code never runs on Landhi's data. Why test it at all, and
   why must those fixtures be labelled SYNTHETIC?
<details><summary>Answer</summary>
Untested code is code you do not know works; if the project is ever pointed at a town
with an enclave, that branch runs for the first time in production. The fixtures are
hand-made squares, not measurements of anywhere, so they are labelled SYNTHETIC to
ensure nobody can mistake them for data or let them reach the live site (§2.1).
</details>

---

## P1-02 — Tiling a town with hexagons, and a contradiction worth finding

**What and why.** Landhi's outline is now covered by 265 hexagons, each about 0.105 km².
Choosing *which* hexagons count turned out to be the interesting part, because the edge
of the town cuts straight through cells: a hexagon might be 3% inside Landhi or 97%
inside. Two rules written during Phase 0 turned out to contradict each other, and
measuring them properly is what exposed it.

**The key idea in A Level terms.** The original rule said: include a cell if its centre
is inside the boundary, *or* if at least 50% of its area is inside. That "or" sounds
like it adds cells. It adds none — and the reason is a neat piece of geometry.

A hexagon is centrally symmetric: every point P has a partner P′ such that the centre is
the midpoint of PP′. Now let a straight line cut the hexagon. Reflecting the hexagon
through its own centre maps it onto itself, and maps the cut line to a parallel line on
the opposite side of the centre. If the centre lies on the *outside* of the cut, then the
inside piece maps into the outside piece, so the inside piece has the smaller area —
less than half. So for a straight boundary, "≥ 50% of area inside" and "centre inside"
are the same condition. The "or" can only ever matter where the boundary bends sharply
within a single cell, which for Landhi never happens.

That symmetry argument is why the measurement came back 248 cells under both rules, and
why coverage stalled at 96.55% against a 99% requirement.

The second idea is **clipping**. Once cells are admitted that stick out past the
boundary, the hexagons cover 27.08 km² while Landhi is only 25.37 km². If we measured
temperature or population over whole hexagons, edge cells would report figures partly
measured in Korangi. So every indicator is computed over the intersection of the cell
with the boundary — 1.935 km² of hexagon is simply excluded.

**Questions.**

1. Use the symmetry argument to explain why a hexagon whose centre is outside the
   boundary can never be more than half inside, when the boundary is a straight line.
<details><summary>Answer</summary>
Reflect the hexagon through its centre; the hexagon maps onto itself. The straight
boundary maps to a parallel line on the other side of the centre. If the centre is on the
outside of the boundary, the inside region reflects to a region strictly contained in the
outside region, so area(inside) &lt; area(outside), hence inside &lt; 50%.
</details>

2. Why not simply include every cell that touches the boundary at all, which would give
   100% coverage?
<details><summary>Answer</summary>
It would admit cells that are barely inside — as little as 0.3%. Even with clipping,
such a cell's analysis area is about 0.003 km², roughly three Meta population pixels, so
its indicator values would be noise rather than measurement. It would also add about 40
near-meaningless cells to the map and to the supply allocation. The 0.25 threshold is a
floor on how much real evidence a cell must contain.
</details>

3. The grid covers 99.115% of Landhi. Where is the missing 0.885%, and why does it
   matter that this is written down?
<details><summary>Answer</summary>
It is thin slivers along the boundary, where the edge clips corners of cells that did not
meet the threshold. It matters because a reader should know the map does not claim to
cover every square metre; an unstated gap is the kind of thing that quietly undermines
trust when someone notices it themselves.
</details>
