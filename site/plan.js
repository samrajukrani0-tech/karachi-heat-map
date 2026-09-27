/* Plan supplies: exact precomputed scenarios, plus a browser-side quick estimate.
   The arithmetic lives in planner-core.js; this file is only the page. */
(function () {
  "use strict";

  var SHARE_RAMP = ["#F6E3D0", "#D4B5A4", "#B18678", "#8E584B", "#6C2A1F"];
  var UNSERVED = "#FFFFFF";
  var MAX_POINTS = 5;

  var state = { cells: null, meta: null, config: null, points: [], markers: [],
                map: null, geo: null, fills: {} };

  function el(id) { return document.getElementById(id); }
  function pct(v) { return (v * 100).toFixed(v > 0 && v < 0.01 ? 1 : 0) + "%"; }
  function fmt(n) { return Math.round(n).toLocaleString("en-GB"); }
  function announce(t) { var l = el("live"); if (l) l.textContent = t; }
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  function shareFill(share, maxShare) {
    if (!(share > 0)) return UNSERVED;
    var band = Math.min(4, Math.floor((share / maxShare) * 5 - 1e-9));
    return SHARE_RAMP[Math.max(0, band)];
  }

  function paint(shares) {
    state.fills = {};
    var max = 0;
    Object.keys(shares).forEach(function (h) { max = Math.max(max, shares[h]); });
    state.geo.setStyle(function (f) {
      var fill = shareFill(shares[f.properties.h3] || 0, max || 1);
      state.fills[f.properties.h3] = fill;
      return { fillColor: fill, fillOpacity: 0.85, color: "#8E8A82", weight: 0.4 };
    });
  }

  /* --- exact scenarios ----------------------------------------------------- */
  function renderScenarios(doc) {
    var host = el("scenario-host");
    if (doc.status !== "ok" || !doc.scenarios.length) {
      host.innerHTML = '<p class="notice" id="scenario-empty">' + esc(doc.message) + "</p>";
      return;
    }
    var select = document.createElement("select");
    select.id = "scenario-select";
    doc.scenarios.forEach(function (s, i) {
      var o = document.createElement("option");
      o.value = String(i);
      o.textContent = s.commodity_name + ", stock " + pct(s.stock_fraction) +
        " of estimated need, " + s.max_distance_m / 1000 + " km";
      select.appendChild(o);
    });
    host.innerHTML = '<div class="field"><label for="scenario-select">Scenario</label></div>';
    host.firstChild.appendChild(select);
    var summary = document.createElement("p");
    summary.id = "scenario-summary";
    host.appendChild(summary);
    function show() {
      var s = doc.scenarios[Number(select.value)];
      summary.textContent = s.summary;
      var shares = {};
      s.lp.cells.forEach(function (c) { shares[c.h3] = c.share_of_stock; });
      paint(shares);
      el("result-kind").textContent = "Showing: exact plan for the selected scenario.";
      window.__planResult = { kind: "exact", id: s.id,
        shareTotal: s.lp.cells.reduce(function (a, c) { return a + c.share_of_stock; }, 0) };
      announce("Exact scenario shown.");
    }
    select.addEventListener("change", show);
    show();
  }

  /* --- quick estimate ------------------------------------------------------ */
  function renderPoints() {
    var list = el("point-list");
    list.innerHTML = "";
    state.points.forEach(function (p, i) {
      var li = document.createElement("li");
      li.className = "point";
      li.innerHTML =
        '<span class="point-name">Stock point ' + (i + 1) + "</span>" +
        '<label class="point-stock">Stock <input type="number" inputmode="numeric" min="0" ' +
        'step="1" value="' + p.stock + '" id="stock-' + i + '"> <span class="unit"></span></label>' +
        '<button type="button" class="linkish" id="remove-' + i + '">Remove</button>';
      list.appendChild(li);
      el("stock-" + i).addEventListener("input", function (e) {
        var v = Number(e.target.value);
        p.stock = isFinite(v) && v > 0 ? Math.floor(v) : 0;
      });
      el("remove-" + i).addEventListener("click", function () { removePoint(i); });
    });
    updateUnits();
    el("add-point").disabled = state.points.length >= MAX_POINTS;
    el("run").disabled = state.points.length === 0;
    el("points-empty").hidden = state.points.length > 0;
  }

  function addPoint(latlng) {
    if (state.points.length >= MAX_POINTS) {
      announce("At most " + MAX_POINTS + " stock points.");
      return;
    }
    state.points.push({ lat: latlng.lat, lon: latlng.lng, stock: 1000 });
    var marker = L.circleMarker(latlng, { radius: 8, color: "#1F5E6B", weight: 3,
      fillColor: "#FFFFFF", fillOpacity: 1 }).addTo(state.map);
    marker.bindTooltip("Stock point " + state.points.length, { permanent: true,
      direction: "right", className: "point-label" });
    state.markers.push(marker);
    renderPoints();
    announce("Stock point " + state.points.length + " added.");
  }

  function removePoint(i) {
    state.map.removeLayer(state.markers[i]);
    state.points.splice(i, 1);
    state.markers.splice(i, 1);
    state.markers.forEach(function (m, k) { m.setTooltipContent("Stock point " + (k + 1)); });
    renderPoints();
    announce("Stock point removed.");
  }

  function commodity() {
    var id = el("commodity").value;
    return state.config.commodities.filter(function (c) { return c.id === id; })[0];
  }

  function updateUnits() {
    var unit = commodity().unit.replace(" per day", "");
    document.querySelectorAll(".unit").forEach(function (u) { u.textContent = unit; });
  }

  function run() {
    var com = commodity();
    var maxD = Number(el("distance").value);
    var feats = state.cells.features;
    var priority = feats.map(function (f) { return f.properties.priority; });
    var need = feats.map(function (f) {
      return (f.properties.over60 + f.properties.under5) * com.units_per_person_per_day;
    });
    var stock = state.points.map(function (p) { return p.stock; });
    var dist = feats.map(function (f) {
      return state.points.map(function (p) {
        return PlannerCore.distanceM(f.properties.c[0], f.properties.c[1], p.lon, p.lat,
                                     state.config.circuity_factor);
      });
    });
    var plan = PlannerCore.greedy(priority, need, stock, dist, maxD);
    var stockTotal = stock.reduce(function (a, b) { return a + b; }, 0);
    var top = PlannerCore.topQuintile(priority, need);

    var shares = {}, rows = [];
    var order = feats.map(function (_, i) { return i; })
      .sort(function (a, b) { return priority[b] - priority[a] || a - b; });
    order.forEach(function (i) {
      if (plan.delivered[i] <= 0) return;
      var share = plan.delivered[i] / stockTotal;
      shares[feats[i].properties.h3] = share;
      rows.push({ i: i, share: share, units: plan.delivered[i],
                  met: plan.delivered[i] / need[i] });
    });
    paint(shares);

    var reachable = feats.filter(function (_, i) {
      return need[i] > 0 && dist[i].some(function (d) { return d <= maxD; });
    }).length;
    var withNeed = need.filter(function (n) { return n > 0; }).length;
    var topGot = plan.delivered.reduce(function (a, d, i) { return a + (top[i] ? d : 0); }, 0);
    var unit = com.unit.replace(" per day", "");

    var html = "<p><strong>Quick estimate (approximate).</strong> " +
      (stockTotal > 0
        ? fmt(plan.total) + " of the " + fmt(stockTotal) + " " + esc(unit) +
          " you entered are sent (" + pct(plan.total / stockTotal) + "), to " +
          rows.length + " of " + withNeed + " areas where people live. The " +
          "highest-priority fifth of areas receive " + pct(topGot / stockTotal) +
          " of your stock."
        : "No stock entered, so nothing is sent.") + "</p>";
    if (reachable < withNeed) {
      html += "<p class=\"small\">" + (withNeed - reachable) + " areas are further than " +
        maxD / 1000 + " km by road from every stock point and receive nothing.</p>";
    }
    if (stockTotal > 0 && plan.total < stockTotal) {
      html += "<p class=\"small\">" + fmt(stockTotal - plan.total) + " " + esc(unit) +
        " are left over because every area within reach already has its estimated need " +
        "met. Real need is higher than the estimate (see below), so do not read this " +
        "as a surplus.</p>";
    }
    el("result-summary").innerHTML = html;

    var body = rows.map(function (r, k) {
      var p = feats[r.i].properties;
      return "<tr><td class=\"num\">" + (k + 1) + "</td><td class=\"num\">" + p.rank +
        "</td><td class=\"num\">" + pct(r.share) + "</td><td class=\"num\">" + fmt(r.units) +
        "</td><td class=\"num\">" + pct(Math.min(1, r.met)) + "</td></tr>";
    }).join("");
    el("result-table").innerHTML = rows.length
      ? "<table><caption class=\"small muted\">Areas in the order they are served, " +
        "highest priority first</caption><thead><tr><th class=\"num\" scope=\"col\">Order" +
        "</th><th class=\"num\" scope=\"col\">Area rank</th><th class=\"num\" scope=\"col\">" +
        "Share of your stock</th><th class=\"num\" scope=\"col\">" + esc(unit) +
        "</th><th class=\"num\" scope=\"col\">Model's estimated need met</th></tr></thead><tbody>" +
        body + "</tbody></table>"
      : "";
    el("result-kind").textContent = "Showing: quick estimate for the stock points you placed.";
    window.__planResult = { kind: "greedy", stock: stock, total: plan.total,
      dispatched: plan.dispatched, delivered: plan.delivered, rows: rows.length,
      tableUnits: rows.reduce(function (a, r) { return a + r.units; }, 0) };
    announce("Quick estimate ready: " + rows.length + " areas served.");
  }

  function init() {
    if (typeof L === "undefined") return;
    var map = L.map(el("map"), { scrollWheelZoom: false });
    state.map = map;
    map.attributionControl.setPrefix("");
    L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/" +
      "World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}", {
        attribution: 'Tiles &copy; <a href="https://www.esri.com/">Esri</a> &mdash; Esri, ' +
          'HERE, Garmin, &copy; <a href="https://www.openstreetmap.org/copyright">' +
          'OpenStreetMap</a> contributors, and the GIS user community',
        maxZoom: 16, crossOrigin: true }).addTo(map);

    Promise.all([
      fetch("data/cells.geojson").then(function (r) { return r.json(); }),
      fetch("data/scenarios.json").then(function (r) { return r.json(); })
    ]).then(function (docs) {
      state.cells = docs[0];
      state.config = docs[1].planner;
      state.geo = L.geoJSON(state.cells, { interactive: false,
        style: { fillColor: UNSERVED, fillOpacity: 0.85, color: "#8E8A82", weight: 0.4 }
      }).addTo(map);
      map.fitBounds(state.geo.getBounds(), { padding: [8, 8] });

      var sel = el("commodity");
      state.config.commodities.forEach(function (c) {
        var o = document.createElement("option");
        o.value = c.id;
        o.textContent = c.name_en + ", " + c.units_per_person_per_day + " " +
          c.unit.replace(" per day", "") + " a person a day";
        sel.appendChild(o);
      });
      var dsel = el("distance");
      state.config.distances_m.forEach(function (d) {
        var o = document.createElement("option");
        o.value = String(d);
        o.textContent = d / 1000 + " km by road";
        if (d === state.config.max_distance_m) o.selected = true;
        dsel.appendChild(o);
      });
      sel.addEventListener("change", updateUnits);

      map.on("click", function (e) { addPoint(e.latlng); });
      el("add-point").addEventListener("click", function () { addPoint(map.getCenter()); });
      el("run").addEventListener("click", run);
      renderPoints();
      renderScenarios(docs[1]);
      window.__planReady = { cells: state.cells.features.length,
                             scenarios: docs[1].scenarios.length };
    }).catch(function (err) {
      var box = el("map-error");
      box.hidden = false;
      box.textContent = "The planner data could not be loaded (" + err.message + ").";
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
