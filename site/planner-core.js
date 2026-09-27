/* The planner's arithmetic, with no page code in it, so the tests can check it
   against the Python solver directly (tests/e2e/planner.spec.js).

   greedy() is a line-for-line port of pipeline/allocate.py solve_greedy with
   round_units=True: highest priority first (ties by cell index), each cell served from
   the nearest stock point that still has stock (ties by point index), whole units only.
   It is the "quick estimate". It is NOT the exact solver, which can do better. */
(function (root) {
  "use strict";

  // WGS84. Local radii of curvature at the mean latitude; over a few kilometres this
  // agrees with the UTM 42N distances the Python pipeline uses to about 0.01%.
  var A = 6378137.0, E2 = 0.00669437999014;

  function distanceM(lon1, lat1, lon2, lat2, circuity) {
    var phi = ((lat1 + lat2) / 2) * Math.PI / 180;
    var w = 1 - E2 * Math.sin(phi) * Math.sin(phi);
    var n = A / Math.sqrt(w);                    // prime vertical
    var m = A * (1 - E2) / Math.pow(w, 1.5);     // meridian
    var dx = (lon2 - lon1) * Math.PI / 180 * n * Math.cos(phi);
    var dy = (lat2 - lat1) * Math.PI / 180 * m;
    return Math.sqrt(dx * dx + dy * dy) * (circuity || 1);
  }

  function stableOrder(n, key) {
    var idx = [];
    for (var i = 0; i < n; i++) idx.push(i);
    return idx.sort(function (a, b) { return key(a) - key(b) || a - b; });
  }

  /* priority[i], need[i], stock[j], dist[i][j] in metres, maxDistance in metres.
     Returns x[i][j] (units from point j to cell i) plus per-cell and per-point totals. */
  function greedy(priority, need, stock, dist, maxDistance) {
    var nCells = priority.length, nPoints = stock.length;
    if (need.length !== nCells || dist.length !== nCells) {
      throw new Error("priority, need and dist must have one entry per cell");
    }
    var left = stock.slice(), still = need.slice(), x = [];
    for (var i = 0; i < nCells; i++) {
      if (!(priority[i] >= 0 && priority[i] <= 1)) throw new Error("priority must be in [0, 1]");
      if (!(need[i] >= 0)) throw new Error("need must be non-negative");
      x.push(new Array(nPoints).fill(0));
    }
    for (var j = 0; j < nPoints; j++) {
      if (!(stock[j] >= 0) || !isFinite(stock[j])) throw new Error("stock must be a non-negative number");
    }
    var order = stableOrder(nCells, function (k) { return -priority[k]; });
    order.forEach(function (c) {
      if (!(still[c] > 0)) return;
      var near = stableOrder(nPoints, function (k) { return dist[c][k]; });
      for (var t = 0; t < near.length; t++) {
        var p = near[t];
        if (still[c] <= 0) break;
        if (dist[c][p] > maxDistance || left[p] <= 0) continue;
        var send = Math.floor(Math.min(still[c], left[p]));
        if (send <= 0) continue;
        x[c][p] += send;
        still[c] -= send;
        left[p] -= send;
      }
    });
    var delivered = x.map(function (row) { return row.reduce(function (a, b) { return a + b; }, 0); });
    var dispatched = stock.map(function (_, p) {
      return x.reduce(function (a, row) { return a + row[p]; }, 0);
    });
    return { x: x, delivered: delivered, dispatched: dispatched,
             total: delivered.reduce(function (a, b) { return a + b; }, 0) };
  }

  /* Top 20% of cells by priority among those with need -- allocate.top_quintile. */
  function topQuintile(priority, need) {
    var eligible = [];
    for (var i = 0; i < priority.length; i++) if (need[i] > 0) eligible.push(i);
    var mask = priority.map(function () { return false; });
    if (!eligible.length) return mask;
    var k = Math.max(1, Math.ceil(0.2 * eligible.length));
    eligible.sort(function (a, b) { return priority[b] - priority[a] || a - b; });
    eligible.slice(0, k).forEach(function (i) { mask[i] = true; });
    return mask;
  }

  root.PlannerCore = { distanceM: distanceM, greedy: greedy, topQuintile: topQuintile };
})(typeof window !== "undefined" ? window : this);
