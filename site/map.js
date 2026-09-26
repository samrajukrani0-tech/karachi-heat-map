/* Map and legend. No framework, no build step. */
(function () {
  "use strict";

  var RAMP = ["#F6E3D0", "#D4B5A4", "#B18678", "#8E584B", "#6C2A1F"];
  var LABELS = ["Lower priority", "", "", "", "Highest priority"];

  function quintile(rank, maxRank) {
    // Rank 1 is the highest priority, so quintile 1 is the top fifth.
    var q = Math.ceil((rank / maxRank) * 5);
    return Math.min(Math.max(q, 1), 5);
  }

  function fillFor(props, maxRank) {
    return RAMP[5 - quintile(props.rank, maxRank)];
  }

  function announce(text) {
    var live = document.getElementById("live");
    if (live) live.textContent = text;
  }

  function buildLegend(container, meta) {
    var box = document.createElement("div");
    box.className = "legend";
    box.setAttribute("aria-hidden", "true");
    var swatches = document.createElement("div");
    swatches.className = "legend-swatches";
    RAMP.forEach(function (colour, i) {
      var s = document.createElement("span");
      s.className = "legend-swatch";
      s.style.background = colour;
      s.title = LABELS[i] || "";
      swatches.appendChild(s);
    });
    box.appendChild(swatches);
    var ends = document.createElement("div");
    ends.className = "legend-ends";
    ends.innerHTML = "<span>Lower priority</span><span>Highest priority</span>";
    box.appendChild(ends);
    container.appendChild(box);
  }

  function init() {
    var host = document.getElementById("map");
    if (!host || typeof L === "undefined") return;

    var map = L.map(host, {
      zoomControl: true,
      attributionControl: true,
      scrollWheelZoom: false
    });
    map.attributionControl.setPrefix("");

    // Esri World Light Gray Canvas: free, no API key, and light enough that the
    // priority ramp sits on top of it rather than competing with it. CARTO's light_all
    // was the first choice and silently began returning "API KEY REQUIRED" watermark
    // tiles -- HTTP 200, so nothing failed, it just stopped being a map.
    L.tileLayer(
      "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/" +
      "World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}",
      {
        attribution:
          'Tiles &copy; <a href="https://www.esri.com/">Esri</a> &mdash; Esri, HERE, ' +
          'Garmin, &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap' +
          '</a> contributors, and the GIS user community',
        maxZoom: 16,
        crossOrigin: true
      }
    ).addTo(map);

    fetch("data/cells.geojson")
      .then(function (r) {
        if (!r.ok) throw new Error("cells.geojson returned " + r.status);
        return r.json();
      })
      .then(function (doc) {
        var maxRank = doc.metadata.distinguishable_ranks;

        var layer = L.geoJSON(doc, {
          style: function (feature) {
            return {
              fillColor: fillFor(feature.properties, maxRank),
              fillOpacity: 0.82,
              color: "#FFFFFF",
              weight: 0.6
            };
          },
          onEachFeature: function (feature, lyr) {
            var p = feature.properties;
            lyr.getElement && lyr.on("add", function () {
              var el = lyr.getElement();
              if (el) {
                el.setAttribute("tabindex", "0");
                el.setAttribute("role", "button");
                el.setAttribute(
                  "aria-label",
                  "Cell ranked " + p.rank + " of " + maxRank +
                  ". " + (p.reasons[0] || "")
                );
              }
            });
            lyr.on("click keypress", function (e) {
              if (e.type === "keypress" && e.originalEvent.key !== "Enter" &&
                  e.originalEvent.key !== " ") return;
              window.dispatchEvent(new CustomEvent("cell:select", { detail: p }));
              announce("Selected cell ranked " + p.rank + " of " + maxRank);
            });
          }
        }).addTo(map);

        map.fitBounds(layer.getBounds(), { padding: [8, 8] });
        buildLegend(host.parentNode, doc.metadata);

        var note = document.getElementById("provisional-note");
        if (note && (doc.metadata.weights_provisional || doc.metadata.model_incomplete)) {
          note.hidden = false;
        }
        var count = document.getElementById("cell-count");
        if (count) count.textContent = String(doc.metadata.cells);
        window.__mapReady = { cells: doc.features.length, maxRank: maxRank };
        announce(doc.metadata.cells + " cells loaded.");
      })
      .catch(function (err) {
        var fallback = document.getElementById("map-error");
        if (fallback) {
          fallback.hidden = false;
          fallback.textContent =
            "The map data could not be loaded (" + err.message +
            "). The figures on the other pages are unaffected.";
        }
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
