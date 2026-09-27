# Allocation planner — how the supply is shared out

**Status: the method is finished and tested; the numbers it runs on are not.**
`config/allocation.yaml` is marked `provisional: true`, no relief centre has been
verified yet (QUESTIONS.md Q2), and the litres-per-person figure is `UNVERIFIED`
until P4-02 checks it against the Sphere Handbook. Everything below is the
*machinery*. The worked examples use made-up numbers, clearly labelled, so you can
check the arithmetic by hand without needing any real data.

**D21 binds this whole document:** the site and the report give **shares and relative
priorities only, never absolute litre or supply totals.** The population layer
undercounts by about 2.3×, so a ratio cancels that bias and a total does not.

---

## 1. The question

> We have this much supply sitting at these centres. Which cells should get how much,
> and from which centre?

The planner does **not** decide how much supply exists, and it does not invent
centres. It takes both as given and answers only the sharing-out question.

---

## 2. The model

**Given**

| Symbol | Meaning | Where it comes from |
| --- | --- | --- |
| $p_i$ | Priority of cell $i$, between 0 and 1 | `data/processed/scores.csv` |
| $n_i$ | Need of cell $i$, in units per day | vulnerable people × units per person (D8) |
| $s_j$ | Stock at centre $j$, in units | entered by the planner |
| $d_{ij}$ | Distance from centre $j$ to cell $i$, in metres | straight line in UTM 42N × circuity factor |
| $D$ | Service distance, 5,000 m | `config/allocation.yaml` |
| $T$ | The top 20% of cells by priority, among those with need | computed |
| $\alpha$ | Minimum share owed to $T$, 0.25 | `config/allocation.yaml` |

**Decide** $x_{ij} \ge 0$, the units sent from centre $j$ to cell $i$ — defined only
for pairs with $d_{ij} \le D$.

**Maximise**

$$\sum_{ij} p_i\,x_{ij} \;-\; \varepsilon \sum_{ij} \frac{d_{ij}}{D}\,x_{ij} \;-\; \lambda u$$

**Subject to**

$$\sum_i x_{ij} \le s_j \quad \text{(no centre sends more than it has)}$$
$$\sum_j x_{ij} \le n_i \quad \text{(no cell receives more than it needs)}$$
$$\sum_{i \in T, j} x_{ij} \;\ge\; F \;-\; u \quad \text{(equity, soft)}$$
$$x_{ij} \ge 0,\qquad u \ge 0$$

where $F = \alpha \cdot \min\!\left(\sum_j s_j,\ \sum_i n_i\right)$ is a **constant**
worked out before the solve — not a share of $\sum x$. That distinction matters a great
deal, and §2 below explains why.

Solved with `scipy.optimize.linprog(method="highs")`.

### Why need is not defined from Priority

Need comes from the count of vulnerable residents — people aged 60+ and children
under 5 — and deliberately **not** from Priority. Priority is already the objective
the solver is maximising. If it also defined need, the model's own judgement would
sit on both sides of the optimisation, and the resulting allocation would look
beautifully targeted no matter how wrong the priorities were. Age counts are measured
independently of the model, so they can disagree with it. (D8.)

### Why the tiebreak is divided by $D$

$\varepsilon = 0.001$ is meant to be a *tiebreak*: when two plans deliver the same
priority-weighted total, prefer the one with shorter journeys. Written with raw
metres, $\varepsilon d_{ij}$ reaches $0.001 \times 5000 = 5.0$, while $p_i$ never
exceeds $1.0$. The "small" term would be five times larger than the thing it is
breaking ties in, and the solver would quietly be minimising travel with priority as
the afterthought — while every line of the code still said the opposite.

Dividing by $D$ makes the term dimensionless and bounded by $\varepsilon$ itself, so
it can only ever decide between plans that are otherwise equal. **A consequence worth
knowing:** a cell with priority below $\varepsilon$ is not worth serving at all, and
the solver will leave it empty even with unlimited stock. With real data no such cell
has any need, because priority is zero exactly where the population is zero — but if
that ever stops being true, this is where it would show up.

### Why the floor is a fixed quantity, not a share (D27)

The obvious way to write "the top 20% of cells should get at least a quarter of the
supply" is $\sum_{i \in T} x \ge \alpha \sum x$. **That version is a trap, and the
first draft of this solver fell into it.**

The floor is a share of *what the solver decides to allocate*, so the solver can meet
it by allocating less — shrinking the denominator instead of raising the numerator.
Work out what a unit sent to an ordinary cell is worth: it raises $\alpha \sum x$ by
$\alpha$, so the shortfall $u$ grows by $\alpha$ and the penalty by $\lambda\alpha$.
The unit nets

$$p_i - \lambda\alpha = p_i - 0.25$$

at the configured settings. **Every cell with Priority below 0.25 becomes actively
worth not serving.** Priority is a geometric mean on $[0,1]$, so sub-0.25 cells are
perfectly ordinary — in one test case the solver shipped 20 units and left **280 in the
warehouse**, and reported no shortfall while doing it, because by its own definition
there wasn't one.

Anchoring $F$ to $\min(\text{total stock}, \text{total need})$ — the most that could
ever be delivered, which the solver has no way to influence — removes the incentive
entirely. Sending a unit to an ordinary cell leaves $F$ untouched, so it is still worth
sending; sending one to a top-quintile cell reduces $u$ and earns $\lambda$ on top of
$p_i$, until the floor is met. That is what the rule was meant to say.

**This is a judgement call on Samraj's rule, not just on its algebra** — see QUESTIONS.md
Q15 for the alternatives and what each would change.

### Why the equity rule is soft

A hard floor of $\alpha$ can make the problem **infeasible** — for instance when the
highest-priority cells simply lie more than $D$ from every centre holding stock. An
infeasible LP returns nothing at all, which is the least useful possible answer to a
coordinator with a van. The slack variable $u$ lets the solver miss the floor when it
must, at a price of $\lambda$ per unit, and the plan then *reports* the shortfall
rather than hiding it. A shortfall is a finding, so the plan also says **which of three
things caused it**: the top cells' own need is already met and the floor asks for more
than they can use; some of them have no centre within $D$; or there is simply not
enough stock within reach. The first draft asserted the second cause every time, which
is usually wrong — a field brief repeating that would send someone to fix a distance
problem that does not exist.

### Rounding

The LP works in real numbers; a van carries whole units. `largest_remainder` floors
every $x_{ij}$, then hands back the discarded units in order of the largest fractional
part — **checking, as each unit is placed, that the centre still has stock and the
cell still has unmet need.** Rounding per centre alone would respect stock and quietly
break the need constraint.

Two limits worth stating. It hands back only as many units as flooring discarded, so a
plan of 7.7 units rounds to 7 and never to 8. And it can only preserve a cap the plan
already respects: flooring 9.7 against a stock of 2 gives 9, which is still over, so an
infeasible plan is refused rather than silently passed through.

---

## 3. The greedy baseline

What a person would do with a paper map: take the highest-priority cell, serve it from
the nearest centre that still has stock, move on to the next cell.

It is here for two reasons. It is the honest comparison — if the LP cannot beat the
obvious method, the LP is not earning its complexity. And it is fast enough to run in
a browser, which is why the site offers it as a clearly-labelled **"quick estimate"**
while the precomputed scenarios use the exact solver.

**The LP can never score worse than greedy**, because greedy's answer is itself a
feasible point of the LP: it respects stock, need and the distance limit. The LP
searches every feasible point, so the best one it finds is at least as good.

---

## 4. Worked example A — scarce stock (SYNTHETIC)

Two centres, three cells. All numbers invented.

| Centre | Stock |
| --- | --- |
| C1 | 100 |
| C2 | 60 |

| Cell | Priority | Need | to C1 | to C2 |
| --- | --- | --- | --- | --- |
| A | 0.9 | 80 | 1,000 m | 4,000 m |
| B | 0.6 | 90 | 2,000 m | 1,000 m |
| C | 0.3 | 50 | **6,000 m** — beyond $D$ | 2,000 m |

Total stock is 160; total need is 220. Supply is scarce, so the question is who
misses out.

**By hand.** Every unit is worth $p_i$ minus at most 0.001, so the priority ordering
decides the quantities outright: fill A, then B, then C.

1. **A** (0.9) needs 80. Both centres can reach it; C1 is nearer, so C1 sends **80**.
   C1 has 20 left.
2. **B** (0.6) needs 90. C2 is nearer (1,000 m vs 2,000 m), so C2 sends **60** — all
   it has. C1 sends its remaining **20**. B is still 10 short.
3. **C** (0.3) needs 50. C1 is out of range and C2 is empty. **C gets nothing.**

**Objective.**

$$0.9(80) + 0.6(60) + 0.6(20) = 72 + 36 + 12 = 120$$
$$\varepsilon\text{-term} = 0.001\left[\tfrac{1000}{5000}(80) + \tfrac{1000}{5000}(60) + \tfrac{2000}{5000}(20)\right] = 0.001[16 + 12 + 8] = 0.036$$
$$\textbf{objective} = 120 - 0.036 = \mathbf{119.964}$$

**Check the transport really is minimal.** With the quantities fixed at A = 80 and
B = 80, minimise $0.2a_1 + 0.8a_2 + 0.4b_1 + 0.2b_2$ subject to $a_1+a_2=80$,
$b_1+b_2=80$, $a_1+b_1\le 100$, $a_2+b_2\le 60$. The chosen plan gives
$16+0+8+12 = 36$. Shifting 10 units of A onto C2 gives $14+8+12+10 = 44$, which is
worse. So 36 is the minimum and the plan above is optimal.

**Equity.** Three cells have need, so $T$ is the top $\lceil 0.2 \times 3 \rceil = 1$
cell — that is A. A receives $80/160 = 50\%$, comfortably above the 25% floor, so
$u = 0$ and no penalty is paid.

**Greedy gets the same answer here**, and that is worth saying plainly: when stock is
simply scarce and every cell can be reached, serving the most important cell first is
already optimal. The LP earns its place in the next example.

---

## 5. Worked example B — where greedy goes wrong (SYNTHETIC)

| Centre | Stock |
| --- | --- |
| C1 | 10 |
| C2 | 10 |

| Cell | Priority | Need | to C1 | to C2 |
| --- | --- | --- | --- | --- |
| A | 0.9 | 10 | 1,000 m | 2,000 m |
| B | 0.8 | 10 | 1,000 m | **6,000 m** — beyond $D$ |

The trap: **B can only be reached from C1.** A can be reached from either.

**Greedy.** A has the higher priority, so it goes first and takes the nearest centre
with stock — C1, at 1,000 m — emptying it. B's only reachable centre is now empty, so
B gets nothing.

$$\text{greedy} = 0.9(10) - 0.001\left[\tfrac{1000}{5000}(10)\right] = 9 - 0.002 = \mathbf{8.998}$$

**The LP.** It can see that C1 is B's only option, so it serves A from C2 — slightly
further, slightly more costly — and keeps C1 for B.

$$\text{LP} = 0.9(10) + 0.8(10) - 0.001\left[\tfrac{2000}{5000}(10) + \tfrac{1000}{5000}(10)\right] = 17 - 0.006 = \mathbf{16.994}$$

**The LP delivers 20 units where greedy delivers 10 — nearly twice the value, from
exactly the same stock.** Greedy's mistake is that it is *myopic*: it makes the locally
best choice for A without knowing that C1 is a scarce resource someone else depends on.
This is the whole argument for solving the problem properly rather than by eye, and it
is the kind of situation a coordinator with several centres and a distance limit will
hit routinely.

---

## 6. What the planner does not know

- **Road distance.** Distances are straight-line × 1.3. A real route may be longer,
  and the Lyari Expressway or a railway line can put two nearby cells far apart in
  practice.
- **Time.** The model shares out one day's supply. It says nothing about refills,
  convoy scheduling or queueing at the centre.
- **Whether people come to the supply or the supply goes to them.** The model assumes
  delivery into the cell.
- **Load-shedding**, which Edhi named as the mechanism that turns a hot night into an
  emergency, and which the model cannot see at all (D20).
- **Anything a centre manager knows.** Every setting in `config/allocation.yaml` is a
  documented assumption waiting to be replaced by a field figure.
