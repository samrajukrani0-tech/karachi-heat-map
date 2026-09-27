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

---

## P1-03 — Why a download cache needs a hash, not just a filename

**What and why.** Everything this project downloads now lands in `data/raw/` with an
entry in `manifest.json` giving its URL, size, date, licence and sha256. A repeated run
uses the cached copy and touches the network zero times. That is partly politeness —
Overpass and the satellite archives are free services — and partly reproducibility: a
year from now the model should rebuild from exactly the bytes it was built from.

**The key idea in A Level terms.** The cache's rule is that a file is reused only if it
still hashes to the value in the manifest. A hash function like SHA-256 takes any input
and produces a fixed 256-bit output, designed so that changing a single bit anywhere
changes the output unrecognisably. Hashing is a mapping from an infinite set to a finite
one, so collisions must exist by the pigeonhole principle — but with 2²⁵⁶ possible
outputs, finding one is not something that happens by accident. This is what makes the
check meaningful: if the recomputed hash matches, the file is the one we downloaded.

There is a subtlety the project ran into immediately, and it is a nice lesson in what a
measurement actually measures. Re-running the same Overpass query returned a *different*
sha256 while producing a geometrically identical boundary, because Overpass stamps each
response with a timestamp. So the hash proves "these bytes are unchanged"; it does not
prove "this query returns the same answer". Reproducibility of the *result* is checked a
different way: the area came out at 25.370 km² both times.

The retry logic contains a second idea. Failures are split into those worth repeating
(503 "busy", 429 "too many requests") and those that never will be (404 "not there").
Retrying a 404 is just asking the same wrong question more politely. Waits between
retries grow exponentially — 4 s, 8 s, 16 s — so a struggling server is not hammered by
a client convinced it is special.

**Questions.**

1. Why does the cache verify the hash instead of just checking the file exists?
<details><summary>Answer</summary>
Existence proves nothing about contents. A download interrupted halfway leaves a file
that looks fine to `ls` but is truncated; an edited file looks identical too. Verifying
the hash means the pipeline either uses the exact bytes it recorded or fetches them
again — it never half-trusts.
</details>

2. Given that hash collisions must exist, why is a hash check still convincing?
<details><summary>Answer</summary>
By the pigeonhole principle an infinite input set mapped to 2²⁵⁶ outputs guarantees
collisions. But SHA-256 is built so that finding one takes work on the order of 2¹²⁸
operations, far beyond anything feasible. The guarantee is computational, not
mathematical impossibility — which is enough for detecting a truncated download.
</details>

3. The Overpass response hash changes on every download. What does that tell you about
   using hashes as evidence of reproducibility?
<details><summary>Answer</summary>
A hash certifies bytes, not meaning. Any content with a timestamp, ordering that is not
guaranteed, or compression metadata will hash differently while being equivalent. To
show a *result* reproduces you must re-derive the result itself — here, re-measuring the
area — and say plainly which of the two you have checked.
</details>

---

## P1-04 — Reading heat from orbit, and why the median beats the mean

**What and why.** Landhi's 265 cells now each carry a hot-season daytime surface
temperature: a mean and a 90th percentile, in °C. They come from 48 Landsat passes over
April–June across five years. Each pass is cloud-masked, converted from raw counts to
temperature, and then the 48 values at each 30 m pixel are reduced to one number by
taking the **median**. Cells range from 39.19 °C to 46.28 °C — a 7 °C spread inside one
town.

**The key idea in A Level terms.** Two ideas meet here, one from Physics and one from
Statistics.

*How a satellite measures temperature at all.* Every object above absolute zero radiates
electromagnetic energy, and the hotter it is the more it radiates and the shorter the
peak wavelength — Wien's law, λ_max ∝ 1/T. At the temperatures of ground in Karachi
(around 315 K) that peak sits in the thermal infrared, near 9–10 µm. Landsat's TIRS
instrument measures brightness in a band at about 11 µm, and the Stefan–Boltzmann
relationship between radiated power and T⁴ lets that brightness be inverted into a
temperature. The satellite is not "seeing heat"; it is measuring radiated power at a
chosen wavelength and solving backwards. The raw file stores integers, and USGS
publishes the linear conversion the pipeline applies: K = 0.00341802 × DN + 149.0.

*Why the median.* Each pixel has up to 48 readings, and some are wrong — a thin cloud
edge the quality mask missed reads far too cold, because the cloud top is cold. The
arithmetic mean is pulled by every outlier in proportion to how extreme it is. The
median is the middle value once sorted, so it is unmoved by how far out an outlier lies;
it only matters that it is on one side. Formally the median minimises the sum of
*absolute* deviations while the mean minimises the sum of *squared* deviations, and
squaring is exactly what makes a single bad reading dominate. With 33–47 clear looks per
pixel, a handful of contaminated readings cannot shift the median at all.

**Questions.**

1. A thin cloud the mask misses makes one reading 15 °C too cold. With 40 readings, how
   much does that shift the mean, and how much the median?
<details><summary>Answer</summary>
The mean shifts by 15/40 ≈ 0.375 °C. The median shifts by roughly one position in the
sorted order — typically a few hundredths of a degree, and nothing at all if the bad
value was already below the middle. This is why the composite uses the median.
</details>

2. Why does the 90th percentile of a cell sit above its mean for all 265 cells, and what
   would it mean if one cell broke that?
<details><summary>Answer</summary>
Within a cell, LST values are roughly symmetric with a tail towards hot surfaces such as
roofs and tarmac, so the 90th percentile sits above the centre while the mean sits near
it. A cell where p90 fell below the mean would be strong evidence the two statistics had
been computed over different pixel sets — a bug, not a property of Karachi.
</details>

3. The cells range over 7 °C within one town. Why is that spread the thing that matters,
   rather than the absolute values?
<details><summary>Answer</summary>
The index ranks places within the pilot area, so only relative differences drive the
result; normalisation maps the range onto 0–1 regardless of the absolute level. If every
cell read 43 °C the hazard layer would be constant and would contribute nothing. The
absolute values still matter for plausibility checks and for saying honestly that this is
surface, not air, temperature.
</details>

---

## P1-06 — Two models agreeing is not the same as two models being right

**What and why.** Every cell now carries a modelled population. Two independent sources
were computed and compared: Meta's 31 m layer gives Landhi 295,132 people, WorldPop's
93 m layer gives 308,105 — a 4.4% difference, and they agree on the spatial pattern with
a Spearman rank correlation of 0.834. Meta was chosen because at 0.105 km² per cell it
supplies about 119 pixels per cell against WorldPop's 13.

Then the independent check: the **2023 census records 681,293** people in Landhi Town.
Both models are at roughly **44%** of that.

**The key idea in A Level terms.** The instinct on seeing two independent sources agree
is to trust them. That instinct is wrong here, and understanding why is the lesson.

Two measurements agreeing tells you they have small *random* error relative to each
other. It says nothing about *systematic* error — bias shared by both. Meta and WorldPop
are built the same way: detect buildings from satellite imagery, then distribute census
population across them in proportion to built area. Both inherit the same two problems:
a pre-2023 census baseline, and the assumption that people scale with building
*footprint*. In Landhi, where housing is dense and often multi-storey, footprint area
understates how many people live on it. Both models are wrong in the same direction for
the same reason, so their agreement is close to meaningless as a check on accuracy.

This is why the project insisted on an *independent* figure rather than a second model.
The census counts people directly; it does not share the building-footprint assumption.

**Why the diagnosis mattered more than the discrepancy.** A gap could mean the models are
wrong, or that our boundary is wrong. These have opposite fixes. Summing both rasters
over the whole of Korangi District settled it: models 1.81M and 1.93M against a census
3.13M. The same shortfall appears at a scale where our boundary plays no part, so the
boundary is fine and the models undercount.

**What follows, mathematically.** Priority ranks cells *within* Landhi and normalisation
is relative, so multiplying every cell by the same factor k leaves the ranking
completely unchanged — a uniform bias is invisible to a relative index. But the bias is
*not* uniform: Landhi is at 0.44 of census while the district is at 0.58, which suggests
denser areas are undercounted more. A bias that varies with the very quantity being
measured does change the ranking, and in the worst possible direction: under-ranking the
most crowded places.

**Questions.**

1. Two independent sources agree to within 4.4% and correlate at ρ = 0.834. Why is that
   weak evidence that either is accurate?
<details><summary>Answer</summary>
Agreement bounds their *relative* random error, not their shared *systematic* error. Both
use building footprints and a pre-2023 census baseline, so both understate dense
multi-storey housing in the same way. Two thermometers with the same manufacturing fault
agree beautifully and are both wrong.
</details>

2. If every cell's population were multiplied by 2.3, which outputs of the model would
   change and which would not?
<details><summary>Answer</summary>
Nothing that depends only on ranking changes: normalised Exposure, Priority order,
quintile classes and the map all stay identical, because robust min–max rescales to the
observed range. What changes is anything absolute — the need calculation in the
allocation planner, and therefore litres of water and numbers of ORS sachets.
</details>

3. Why is summing over Korangi District the right test to separate "our boundary is
   wrong" from "the models are wrong"?
<details><summary>Answer</summary>
It is a controlled comparison: the district total does not depend on our boundary at all,
since it uses the official district outline. If the models matched the census there, the
error would have to lie in how we defined Landhi. They do not match, so the error lives
in the models — the boundary is exonerated by evidence rather than by assumption.
</details>

---

## P1-11 — What a table of numbers has to admit about itself

**What and why.** Every layer built in Phase 1 is now one table: 265 rows, one per cell,
14 columns. Alongside it sits a generated data dictionary that says what each column is,
where it came from, and — the part that matters — what it is not. Four of the five
configured indicators are complete. The fifth, distance to a verified relief centre, is an
empty column, because no centre has been verified in person and OpenStreetMap covers only
about 11% of Landhi.

**The key idea in A Level terms.** The interesting part of this feature was reading the
distributions rather than producing them, because the shape of a distribution decides what
statistics are allowed to mean.

*Skew and why `log1p`.* The population column is heavily right-skewed: most cells hold a
few hundred people, a few hold thousands, and some hold none. For such data the mean sits
well above the median and is dragged around by the largest cells. Taking log(1+x)
compresses the long right tail, so differences become multiplicative rather than additive
— the gap between 100 and 1,000 people becomes the same as between 1,000 and 10,000. That
matches how the quantity behaves: a cell with ten times more people is meaningfully
different, whereas a hundred extra people in a crowded cell is not. `log1p` rather than
`log` because log(0) is undefined and empty cells are real.

*Bimodality, and why it is a warning.* The `lack_green` column is not skewed; it is
**bimodal** — one mass near 0 and another near 1, with little in between. That is a
different problem. Robust min–max normalisation clips at the 5th and 95th percentile and
stretches what remains onto 0–1, which assumes the values in between are informative. When
a variable is really two clusters, that stretch mostly separates the two groups and says
little about differences within them. It is not wrong, but it means the indicator is
closer to a yes/no than a gradient, and the model report should say so rather than imply a
smooth measure of greenness.

**Questions.**

1. Why does a right-skewed variable pull the mean away from the median, and why does a
   logarithm help?
<details><summary>Answer</summary>
The mean weights every value by its size, so a handful of very large values shift it
upwards; the median only counts positions, so it stays near the bulk of the data. A
logarithm converts ratios into differences, so the long multiplicative tail becomes a
short additive one and the transformed distribution is far closer to symmetric.
</details>

2. Both `population` and `lack_green` have awkward distributions. Why does one get a
   transform and the other only a warning?
<details><summary>Answer</summary>
Skew is a property of the scale, and changing scale fixes it — log turns a multiplicative
quantity into an additive one. Bimodality is a property of the underlying reality: Landhi
genuinely has green areas and built areas with little in between. No transform removes
that, and one that appeared to would be hiding the structure rather than modelling it. The
honest response is to describe it.
</details>

3. Why keep an entirely empty column in the table at all, rather than leaving it out until
   the data exists?
<details><summary>Answer</summary>
An absent column is invisible; an empty one is a question. Keeping `dist_centre_m` present
and reported as 100% missing means the gap appears in the missing-value summary, in the
data dictionary, and in a test that fails if it is ever quietly filled without the
documentation being updated. Omitting it would let the model be read as complete when it
is not.
</details>

---

## P2-02 — Turning opinions into numbers, and checking they hold together

**What and why.** The AHP tool asks you to compare indicators two at a time — "for heat
harm in Landhi, does lack of greenery matter more than distance to a clinic, and by how
much?" — and turns those answers into weights. It also tells you whether your answers
agree with each other, and if they do not, it says so instead of quietly averaging them.

**The key idea in A Level terms.** Suppose the true importances are w₁, w₂, w₃. If you
judged perfectly, your answer comparing indicator i with indicator j would be exactly
aᵢⱼ = wᵢ/wⱼ. Written as a matrix, that means **A·w = 3w** — the weight vector is an
eigenvector of your own comparison matrix, with eigenvalue equal to the number of items.

Real answers are never perfect, so A·w = λw with λ slightly larger than n, and the weights
are the **principal eigenvector**: the direction that A stretches most. The tool finds it
by power iteration — start with any positive vector, multiply by A over and over, and
renormalise. Each multiplication amplifies the dominant direction relative to the others
by the ratio of their eigenvalues, so the vector converges to the one that matters. That
is the same eigenvector algebra as in Further Maths, used here on a matrix of opinions.

How far λ exceeds n measures how much you contradicted yourself. That gap is scaled into
the **consistency ratio**, which compares your inconsistency against what randomly-filled
answers would produce.

**The part worth understanding for three indicators specifically.** With three items there
is exactly *one* way to be inconsistent. Multiply your three answers around the loop:
κ = a₁₂ × a₂₃ ÷ a₁₃. If you said greenery is 3× clinics, clinics are 3× centres, then
consistency demands greenery is 9× centres. Say 5 instead and κ = 9/5 = 1.8. Everything —
λmax, CI, CR — is a function of κ alone.

That has a consequence the tool now states out loud: because the contradiction is a single
loop, it is shared **equally** among all three answers. In logarithms the three errors come
out as exactly +d/3, +d/3, −d/3. So there is no "bad answer" to correct; the tool asks all
three again rather than pretending it can identify a culprit.

**Questions.**

1. You say greenery is 3× more important than clinic distance, and clinic distance is 2×
   more important than centre distance. What must you say about greenery versus centre
   distance to be perfectly consistent, and what is κ if you say 4 instead?
<details><summary>Answer</summary>
Consistency requires 3 × 2 = 6. Saying 4 gives κ = (3 × 2)/4 = 1.5 — your answers multiply
out to 1.5 where perfect agreement would be 1.
</details>

2. Why is a *perfectly consistent* set of answers not necessarily a *good* set?
<details><summary>Answer</summary>
Consistency measures only whether your judgements agree with each other, not whether they
are right. You could believe something entirely wrong and believe it coherently: a matrix
built as aᵢⱼ = wᵢ/wⱼ from any weights at all has CR = 0. The consistency ratio bounds
internal coherence, never validity.
</details>

3. The tool reports weights to four decimal places from answers picked off a 1–9 scale.
   What is wrong with reading them that precisely?
<details><summary>Answer</summary>
The input is coarse — whole numbers attached to verbal descriptions — so the output cannot
be finer than the input. Four decimals are useful for reproducing the computation exactly,
but interpreting 0.6370 as distinguishable from 0.63 reads precision into a judgement that
never had it. One scale point of change in a single answer moves the weights by several
percentage points.
</details>

## P3-09 — Deploy

**What and why.** The site is live on GitHub Pages, deployed by CI rather than by hand,
so what the public sees is always something that passed the gates. The last acceptance
criterion was that the Playwright smoke suite passes *against the live URL*, not just
against a local dev server — because the two can differ, and this time they did. Running
the suite against the deployed site failed almost entirely, and the reason was that a
path written as `/index.html` means "the root of this domain", not "next to the page I am
on". On a local dev server those are the same place. On GitHub Pages, where the project
lives at `/karachi-heat-map/`, they are not.

**The key idea in A Level terms.** This is the difference between an **absolute** and a
**relative** reference, and it is the same idea as a position vector versus a displacement
vector. `/index.html` is absolute: it is measured from a fixed origin (the domain root),
so it means the same place no matter where you are standing. `index.html` is relative: it
is measured from where you currently are, so the same expression resolves to different
places in different contexts. The bug was writing an absolute reference while assuming it
was relative — which works perfectly as long as you happen to be standing at the origin,
and silently breaks the moment you move. A local dev server puts you at the origin; a
project page on a shared domain does not.

**Questions to check you have it.**

1. The site works locally and the paths are all `/index.html`. Why does this keep working
   right up until the moment it is deployed?
<details><summary>Answer</summary>
Locally the site is served at `http://127.0.0.1:8765/`, so the domain root and the site
root are the same directory. An absolute path from the domain root therefore lands in the
right place by coincidence. On GitHub Pages the site is served from a subdirectory,
`/karachi-heat-map/`, so the two roots separate and every absolute path points one level
too high. The test never checked an assumption that only held in one environment.
</details>

2. After switching to relative paths, `baseURL` still had to be changed to end in a
   slash. Why does a trailing slash matter?
<details><summary>Answer</summary>
A relative path resolves against the *directory* of the current URL, which means
everything up to the last slash. With base `.../karachi-heat-map`, the last segment
`karachi-heat-map` is treated as a file name and discarded, so `index.html` resolves to
the domain root again — the same bug in a new disguise. With `.../karachi-heat-map/`, the
final segment is a directory and is kept.
</details>

3. The first live run printed "12 passed" and no failures. Why was that not good news?
<details><summary>Answer</summary>
Because the suite has 113 tests. A number that should have been 113 coming back as 12 is
information in itself: most tests never reported at all. The "passed" count only tells you
about tests that finished, so it is not a verdict on the run — it has to be read against
how many tests *should* have run. The 6.2-minute duration for twelve tests was the second
clue, since the same tests take seconds when they are actually loading a page.
</details>

## P4-01 — The allocation solver, and a rule that gamed itself

**What and why.** The planner answers "we have this much supply at these centres, which
cells get how much?" as a linear program: maximise the priority-weighted supply
delivered, subject to each centre's stock, each cell's need, and a 5 km service
distance. A greedy baseline — highest-priority cell first, nearest centre with stock —
is there so the LP has something to beat, and because it is fast enough to run in a
browser. Two things in the first version were wrong in ways that looked completely
normal from the outside, and both are worth understanding.

**The first was a units problem.** The spec says to subtract a "small" term
$\varepsilon \sum d_{ij} x_{ij}$ to break ties in favour of closer cells, with
$\varepsilon = 0.001$. But $d$ is in metres, so at the 5 km limit that term is
$0.001 \times 5000 = 5.0$, while priority never exceeds $1.0$. The "tiebreak" was five
times bigger than the thing it was breaking ties in: the solver would have been
minimising travel distance and treating priority as a rounding error, while every
comment in the code said the opposite. Dividing by $D$ makes the term dimensionless and
genuinely small.

**The second was worse, and an independent checker found it, not me.** The equity rule
— "the top 20% of cells should get at least 25% of the supply" — was written as
$\sum_T x \ge \alpha \sum x$, with a penalty $\lambda$ per unit of shortfall. That makes
the target a share of *what the solver decides to allocate*, so the solver can hit it by
allocating less. Work out what one unit sent to an ordinary cell is worth: it raises the
requirement by $\alpha$, so the penalty rises by $\lambda\alpha$, and the unit nets
$p_i - 0.25$. **Every cell below Priority 0.25 became worth not serving.** In one test
the solver shipped 20 units and left 280 in the warehouse — and reported no shortfall,
because by its own definition there wasn't one. A relief plan that withholds most of the
supply in order to look equitable, with a clean map and no warning, is about the worst
thing this project could ship.

**The key idea in A Level terms.** Both bugs are about what happens when you put two
quantities into the same expression without checking they are commensurable — the same
discipline as **dimensional analysis** in Physics. You cannot add 5 metres to 3 seconds,
and you should be equally suspicious of adding a normalised score to a raw distance.
The second bug is a case of an **endogenous constraint**: the quantity on the
right-hand side, $\alpha\sum x$, is not a fixed number but a function of the decision
variables. Optimisers exploit that ruthlessly, because a constraint you can move is not
really a constraint. The fix is to anchor the floor to something outside the solver's
control — $\alpha \cdot \min(\text{total stock}, \text{total need})$ — so that the
requirement is a constant and the only way to meet it is to actually serve those cells.
This is the same reason an economics or game-theory problem specifies which quantities
are exogenous: the answer depends entirely on what the agent is allowed to move.

**Questions to check you have it.**

1. In the broken version, why did the solver refuse to serve a cell with Priority 0.20
   but happily serve one at 0.30?
<details><summary>Answer</summary>
Serving an ordinary cell raised the requirement $\alpha \sum x$ by $\alpha = 0.25$, and
each unit of extra shortfall cost $\lambda = 1$. So the unit's net value was
$p_i - \lambda\alpha = p_i - 0.25$: positive at 0.30, negative at 0.20. The cutoff sat
exactly at $\lambda\alpha$, which is why 0.249 was dropped and 0.251 was kept. Note that
nothing in the code said "ignore cells below 0.25" — the threshold emerged from the
interaction of two settings that each looked reasonable alone.
</details>

2. Why does anchoring the floor to $\min(\text{total stock},\ \text{total need})$ remove
   the incentive, when anchoring it to $\sum x$ did not?
<details><summary>Answer</summary>
Because the new floor is a constant: total stock and total need are inputs, fixed before
the solve, and no choice of $x$ changes them. Sending a unit to an ordinary cell
therefore leaves the requirement — and the penalty — exactly where it was, so the unit
is worth its full $p_i$ and is still worth sending. Under the old version the
requirement moved every time the solver allocated anything, which is what let the
solver "satisfy" it by doing less.
</details>

3. The checker also found that the objective became `nan` when an out-of-range distance
   was written as `inf`, even though no supply was ever sent along that route. Why, and
   why was that dangerous rather than merely untidy?
<details><summary>Answer</summary>
The cost was summed over the whole distance matrix, and an unservable pair has $x = 0$,
so the term was $\infty \times 0$ — which is `nan` in IEEE arithmetic, not 0. The danger
is that **every comparison involving `nan` evaluates to False**, including
`lp.objective >= greedy.objective`. So the check "is the LP at least as good as greedy?"
would have silently answered "no" without anything raising an error. A crash is safe;
a wrong answer that looks like a normal answer is not.
</details>

## P4-01 (continued) — Round the problem, not the answer

**What and why.** The first round of fixes passed its own tests and was still wrong. A
second independent check found that the *rounding step* — turning the LP's real-numbered
answer into whole units a van can carry — had broken the module's headline claim. On the
265 real Landhi cells, the "clever" solver was delivering **fewer units than the greedy
paper-map baseline** in every scenario tried, and stranding 44 to 99 units in the
warehouse. In about 5% of random problems it also scored worse. The 346-test suite was
fully green throughout, because the guarantee had only ever been tested on the
*continuous* version of the problem, which was never the version the site would run.

The cause is worth understanding, because the rounding method was not careless. It hands
back units in order of the largest discarded fraction and stops at the first zero — and
it must, because it cannot see distances. A pair the fractional plan left at exactly zero
might be one the 5 km service limit forbids, so putting a unit there would break a
constraint the function has no way to check. The caution is correct. The mistake was
asking a rounding function to make an allocation decision at all.

The fix is to stop rounding and solve the integer problem directly. `scipy`'s `linprog`
takes an `integrality` mask, which switches HiGHS into mixed-integer mode; every shipment
is declared a whole number from the start. The full 265-cell problem solves in under a
tenth of a second, so there was never anything to trade away.

**The key idea in A Level terms.** An optimisation problem has a **feasible region** —
the set of allocations that satisfy every constraint — and the answer is the best point
*in* that region. Rounding takes the optimum of the continuous problem and moves it to a
nearby integer point. But "near the best point" and "the best nearby point" are different
things, and the gap between them is real: in Further Maths terms, the integer optimum of
a linear program is generally *not* the rounded LP optimum. This is exactly why integer
programming exists as its own subject rather than being a footnote to linear
programming. The slogan to remember is **round the problem, not the answer** — state up
front that the variables are whole numbers, and let the solver search the integer
feasible region, rather than solving an easier problem and patching the result.

**Questions to check you have it.**

1. Greedy hit the true integer optimum's total every time, while the rounded LP did not.
   Does that mean greedy is the better algorithm?
<details><summary>Answer</summary>
No. Greedy is integral by construction — it only ever ships whole units — so it never
pays a rounding penalty, but it is still myopic and can strand a cell by spending its
only reachable centre (worked example B in docs/allocation.md, where greedy delivers 10
units against the LP's 20). The comparison was not "greedy beats LP"; it was "the
rounding step was costing the LP more than its advantage". Fix the rounding and the LP
wins again, by construction: greedy's plan is itself an integer feasible point, so the
integer optimum is at least as good.
</details>

2. Why did 346 passing tests fail to catch this?
<details><summary>Answer</summary>
Because the test asserting "the LP is never worse than greedy" ran with
`round_units=False`, on the continuous relaxation. That is the version where the claim is
provable, so the test could never fail — it was testing the mathematics, not the code
path the site would use. The lesson is to test the configuration you actually ship. The
regression test now runs at defaults, and a second one runs on all 265 real cells,
because the small synthetic problems also hid it.
</details>

3. The rounding function refuses to put a unit into a pair the plan left at zero, even
   when both the centre and the cell have room. Is that a bug?
<details><summary>Answer</summary>
No — it is the only safe behaviour for that function, and removing it would be a real
bug. `largest_remainder` receives only the plan, the stock and the need; it never sees
the distance matrix. A zero entry may be zero because the route is longer than the
service limit, so "filling it in" would ship supply further than the model allows and
nothing would catch it. The function is right to be conservative; the design was wrong to
put the decision there.
</details>

## P4-01 (third round) — A solver saying "success" is not proof of a right answer

**What and why.** The fix in the last round declared every shipment to be a whole
number and handed the problem to HiGHS in integer mode. That was the right idea and it
was still not enough. The *upper bounds* on those integer variables were left as
fractions — a cell needing 32.37 units got an upper bound of 32.37 — and given a
fractional bound the solver can return an answer that is not the best one **while
reporting `status = 0` and a MIP gap of 0.0**. Those two numbers are how a solver says
"I have proved this is optimal". Both were present, and both were wrong.

The symptom was tiny and would never have been noticed by eye: a two-cell,
one-centre problem delivering 50 units when 51 was both feasible and optimal. But 51 was
what the crude greedy baseline delivered, and what the older rounding code delivered, so
the "exact" solver was losing to the two things it had just been rewritten to beat. It
happened in about 0.7% of problems with fractional stocks and needs — which is to say,
all the realistic ones.

The fix is one line of reasoning: an integer that cannot exceed 32.37 cannot exceed 32,
so floor the bound. That is an *exact reformulation* — it removes no valid answer,
because no valid answer was fractional to begin with. The same argument applies to the
two constraint rows whose variables are all integers, but not to the equity row, which
carries the continuous slack variable and must be left alone.

**The key idea in A Level terms.** Two things are going on, and both are worth keeping.

The first is that **tightening a constraint without removing any feasible point is
free** — and sometimes necessary. This is the same manoeuvre as rewriting an inequality
into a sharper equivalent form before solving it: $2x < 9$ for integer $x$ means
$x \le 4$, and saying so costs nothing but tells you more. Solvers, like people, work
better when the constraints are stated in their sharpest true form.

The second is about **what counts as evidence**. `status = 0` means the algorithm
terminated as designed; `mip_gap = 0.0` means it believes the bound and the incumbent
have met. Neither is an independent check, because both are produced by the thing being
checked. The only tests that caught this were external: an entirely separate solver
written from the specification, and, on small cases, brute-force enumeration of every
possible integer allocation. That is the general shape of a real verification —
something that could disagree.

**Questions to check you have it.**

1. Why is flooring the upper bound of an integer variable not an approximation?
<details><summary>Answer</summary>
Because no feasible value is removed. The variable can only take whole-number values, so
the set of values satisfying $x \le 32.37$ and the set satisfying $x \le 32$ are the
same set: $\{0, 1, \ldots, 32\}$. The two formulations have identical feasible regions
and therefore identical optima. Only the solver's internal search changes — it is now
being told something true that it was previously having to discover.
</details>

2. The solver reported a MIP gap of zero and the answer was still suboptimal. What would
   you need in order to *know* an answer is optimal?
<details><summary>Answer</summary>
Something independent of the solver. Two things were used here: brute-force enumeration
of every integer allocation on problems small enough to make that feasible, which is a
proof rather than an argument; and a second solver written separately from the same
written specification, which can disagree. A check that shares code, assumptions or
authorship with the thing it is checking can only confirm internal consistency — which
is exactly what the zero gap was doing.
</details>

3. The equity row was deliberately *not* floored. Why would flooring it have been wrong?
<details><summary>Answer</summary>
Because that row contains the slack variable $u$, which is continuous. The argument for
flooring is "every variable in this row is an integer, so the left-hand side is an
integer, so the bound can be rounded to an integer without losing anything". That
argument fails the moment one term can take a fractional value: the left-hand side is
then not necessarily an integer, and flooring the right-hand side could cut off feasible
points. The reasoning has to be checked per row, not applied as a habit.
</details>
