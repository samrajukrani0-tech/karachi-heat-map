/* Map, layers and cell panel. No framework, no build step. */
(function () {
  "use strict";

  var RAMP = ["#F6E3D0", "#D4B5A4", "#B18678", "#8E584B", "#6C2A1F"];
  var STABILITY_FILL = {
    "confidently in": "#6C2A1F",
    "uncertain": "#D4B5A4",
    "confidently out": "#F6E3D0"
  };

  var LAYERS = [
    { id: "priority", label: "Priority", kind: "rank",
      low: "Lower priority", high: "Highest priority" },
    { id: "hazard", label: "Heat", kind: "value",
      low: "Cooler ground", high: "Hotter ground" },
    { id: "exposure", label: "People", kind: "value",
      low: "Fewer people", high: "More people" },
    { id: "vulnerability", label: "Vulnerability", kind: "value",
      low: "Fewer risk factors", high: "More risk factors" },
    { id: "stability", label: "Confidence", kind: "category",
      low: "Confidently not a priority", high: "Confidently a priority",
      note: "The middle band is the one to look at: those areas move a lot when the " +
            "assumptions are varied." }
  ];

  var state = { layer: "priority", selected: null, data: null, breaks: {} };

  function quantileBreaks(values) {
    var sorted = values.slice().sort(function (a, b) { return a - b; });
    return [0.2, 0.4, 0.6, 0.8].map(function (q) {
      return sorted[Math.floor(q * (sorted.length - 1))];
    });
  }

  function bandFor(value, breaks) {
    for (var i = 0; i < breaks.length; i++) { if (value <= breaks[i]) return i; }
    return 4;
  }

  function fillFor(props) {
    var layer = LAYERS.filter(function (l) { return l.id === state.layer; })[0];
    if (layer.kind === "category") return STABILITY_FILL[props.stability] || RAMP[0];
    if (layer.kind === "rank") {
      var q = Math.ceil((props.rank / state.data.metadata.distinguishable_ranks) * 5);
      return RAMP[5 - Math.min(Math.max(q, 1), 5)];
    }
    return RAMP[bandFor(props[state.layer], state.breaks[state.layer])];
  }

  /* DESIGN.md principle 1: a cell the model is unsure about must LOOK unsure. Hatching,
     not a lighter tint -- a tint would read as "lower priority", a different claim. */
  function isUncertain(props) { return props.stability === "uncertain"; }

  function announce(text) {
    var live = document.getElementById("live");
    if (live) live.textContent = text;
  }

  function num(value, unit) {
    if (value === null || value === undefined) return "not available";
    return value.toLocaleString("en-GB") + (unit ? " " + unit : "");
  }

  function renderPanel(props) {
    var panel = document.getElementById("panel");
    var max = state.data.metadata.distinguishable_ranks;
    if (!props) {
      panel.innerHTML = '<p class="small muted">Select an area on the map to see why it ' +
                        'is ranked where it is.</p>';
      return;
    }
    var band = props.rank <= max * 0.2 ? "Higher priority for support"
             : props.rank <= max * 0.6 ? "Middle of the range"
             : "Lower priority for support";
    var reasons = (props.reasons || []).map(function (r) {
      return "<li>" + r + "</li>";
    }).join("");
    var stability = {
      "confidently in": "The model is confident this area is among the highest priority.",
      "uncertain": "This area moves a lot when the assumptions are varied. Treat its " +
                   "exact position with caution.",
      "confidently out": "The model is confident this area is not among the highest " +
                         "priority."
    }[props.stability] || "";

    panel.innerHTML =
      '<h3 class="panel-rank">Rank ' + props.rank + ' of ' + max + '</h3>' +
      '<p class="panel-band">' + band + '</p>' +
      '<h4>Why here</h4><ul class="reasons">' + reasons + '</ul>' +
      '<h4>Confidence</h4>' +
      '<p class="small"><span class="chip chip-' +
        props.stability.replace(/ /g, "-") + '">' + props.stability + '</span></p>' +
      '<p class="small">' + stability + ' Across 1,000 runs with the assumptions varied, ' +
      'it ranked between ' + props.rank_low + ' and ' + props.rank_high + '.</p>' +
      '<h4>Values</h4>' +
      '<table><tbody>' +
      '<tr><th scope="row">Surface temperature</th><td class="num">' +
        num(props.lst, "°C") + '</td></tr>' +
      '<tr><th scope="row">Hottest tenth of days</th><td class="num">' +
        num(props.lst_p90, "°C") + '</td></tr>' +
      '<tr><th scope="row">People (modelled)</th><td class="num">' +
        num(props.people) + '</td></tr>' +
      '<tr><th scope="row">Aged 60+</th><td class="num">' + num(props.over60) + '</td></tr>' +
      '<tr><th scope="row">Under 5</th><td class="num">' + num(props.under5) + '</td></tr>' +
      '<tr><th scope="row">Green cover</th><td class="num">' +
        Math.round(props.green * 100) + '%</td></tr>' +
      '<tr><th scope="row">To nearest clinic</th><td class="num">' +
        num(props.dist_health, "m") + '</td></tr>' +
      '<tr><th scope="row">To nearest relief centre</th><td class="num">not available</td></tr>' +
      '</tbody></table>' +
      '<details class="cannot"><summary>What this cannot tell you</summary>' +
      '<ul class="small">' +
      '<li>The people count is modelled and is roughly <strong>half</strong> the 2023 ' +
      'census figure for Landhi. Use it to compare areas, never as a headcount.</li>' +
      '<li>Distance to a relief centre is missing entirely: no centre has been verified ' +
      'on the ground yet.</li>' +
      '<li>Surface temperature is the temperature of the ground, not the air, and says ' +
      'nothing about humidity.</li>' +
      '<li>Power cuts are not included, although they are a large part of why heat ' +
      'harms people here.</li>' +
      '<li>This describes an area, not the people in it, and is never a verdict on a ' +
      'neighbourhood.</li>' +
      '</ul></details>';
  }

  function buildLayerPicker(host) {
    var wrap = document.createElement("div");
    wrap.className = "layer-picker";
    var label = document.createElement("label");
    label.setAttribute("for", "layer-select");
    label.textContent = "Show";
    var select = document.createElement("select");
    select.id = "layer-select";
    LAYERS.forEach(function (l) {
      var o = document.createElement("option");
      o.value = l.id; o.textContent = l.label;
      select.appendChild(o);
    });
    select.addEventListener("change", function () {
      state.layer = select.value;
      window.dispatchEvent(new CustomEvent("layer:change", { detail: state.layer }));
      announce(select.options[select.selectedIndex].text + " layer shown.");
    });
    wrap.appendChild(label);
    wrap.appendChild(select);
    host.appendChild(wrap);
  }

  function buildLegend(host) {
    if (document.querySelector(".legend")) return;
    var box = document.createElement("div");
    box.className = "legend";
    box.setAttribute("aria-hidden", "true");
    var swatches = document.createElement("div");
    swatches.className = "legend-swatches";
    RAMP.forEach(function (colour) {
      var s = document.createElement("span");
      s.className = "legend-swatch";
      s.style.background = colour;
      swatches.appendChild(s);
    });
    box.appendChild(swatches);
    var ends = document.createElement("div");
    ends.className = "legend-ends";
    var lo = document.createElement("span");
    var hi = document.createElement("span");
    ends.appendChild(lo);
    ends.appendChild(hi);
    box.appendChild(ends);
    host.appendChild(box);
  }

  function updateLegend() {
    var layer = LAYERS.filter(function (l) { return l.id === state.layer; })[0];
    var note = document.getElementById("layer-note");
    if (note) {
      note.textContent = layer.note || "";
      note.hidden = !layer.note;
    }
    var ends = document.querySelector(".legend-ends");
    if (ends) {
      ends.firstElementChild.textContent = layer.low;
      ends.lastElementChild.textContent = layer.high;
    }
    var swatches = document.querySelectorAll(".legend-swatch");
    var colours = layer.kind === "category"
      ? [STABILITY_FILL["confidently out"], RAMP[1], STABILITY_FILL.uncertain,
         RAMP[3], STABILITY_FILL["confidently in"]]
      : RAMP;
    swatches.forEach(function (s, i) { s.style.background = colours[i]; });
  }

  function init() {
    var host = document.getElementById("map");
    if (!host || typeof L === "undefined") return;

    var map = L.map(host, { zoomControl: true, scrollWheelZoom: false });
    map.attributionControl.setPrefix("");
    L.tileLayer(
      "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/" +
      "World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}",
      {
        attribution:
          'Tiles &copy; <a href="https://www.esri.com/">Esri</a> &mdash; Esri, HERE, ' +
          'Garmin, &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap' +
          '</a> contributors, and the GIS user community',
        maxZoom: 16, crossOrigin: true
      }
    ).addTo(map);

    fetch("data/cells.geojson")
      .then(function (r) {
        if (!r.ok) throw new Error("cells.geojson returned " + r.status);
        return r.json();
      })
      .then(function (doc) {
        state.data = doc;
        ["hazard", "exposure", "vulnerability"].forEach(function (key) {
          state.breaks[key] = quantileBreaks(doc.features.map(function (f) {
            return f.properties[key];
          }));
        });

        var geo = L.geoJSON(doc, {
          style: function (feature) {
            return {
              fillColor: fillFor(feature.properties),
              fillOpacity: 0.82, color: "#FFFFFF", weight: 0.6
            };
          },
          onEachFeature: function (feature, lyr) {
            var p = feature.properties;
            lyr.on("add", function () {
              var el = lyr.getElement && lyr.getElement();
              if (!el) return;
              el.setAttribute("tabindex", "0");
              el.setAttribute("role", "button");
              el.setAttribute("aria-label",
                "Cell ranked " + p.rank + " of " + doc.metadata.distinguishable_ranks +
                ". " + (p.reasons[0] || ""));
              if (isUncertain(p)) el.classList.add("cell-uncertain");
            });
            function select() {
              state.selected = p;
              renderPanel(p);
              document.getElementById("panel-wrap").classList.add("is-open");
              announce("Selected cell ranked " + p.rank);
            }
            lyr.on("click", select);
            lyr.on("keypress", function (e) {
              var k = e.originalEvent.key;
              if (k === "Enter" || k === " ") { e.originalEvent.preventDefault(); select(); }
            });
          }
        }).addTo(map);

        map.fitBounds(geo.getBounds(), { padding: [8, 8] });
        window.addEventListener("layer:change", function () {
          geo.setStyle(function (feature) {
            return { fillColor: fillFor(feature.properties) };
          });
          updateLegend();
        });

        var note = document.getElementById("provisional-note");
        if (note && (doc.metadata.weights_provisional || doc.metadata.model_incomplete)) {
          note.hidden = false;
        }
        var count = document.getElementById("cell-count");
        if (count) count.textContent = String(doc.metadata.cells);
        renderPanel(null);
        buildLegend(document.getElementById("legend-host"));
        updateLegend();
        window.__mapReady = { cells: doc.features.length,
                              maxRank: doc.metadata.distinguishable_ranks };
        announce(doc.metadata.cells + " cells loaded.");
      })
      .catch(function (err) {
        var fallback = document.getElementById("map-error");
        if (fallback) {
          fallback.hidden = false;
          fallback.textContent = "The map data could not be loaded (" + err.message +
            "). The figures on the other pages are unaffected.";
        }
      });

    buildLayerPicker(document.getElementById("controls"));
    var close = document.getElementById("panel-close");
    if (close) {
      close.addEventListener("click", function () {
        document.getElementById("panel-wrap").classList.remove("is-open");
        renderPanel(null);
        state.selected = null;
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else { init(); }
})();
