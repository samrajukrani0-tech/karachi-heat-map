/* Offline view (P5-02): register the service worker, and when there is no network,
   draw a simplified outline of the main roads in place of the basemap tiles. */
(function () {
  "use strict";

  if ("serviceWorker" in navigator && /^https?:$/.test(location.protocol)) {
    window.addEventListener("load", function () {
      navigator.serviceWorker.register("sw.js").catch(function () { /* optional */ });
    });
  }

  function attach(map) {
    var roads = null, shown = false, loads = 0, errors = 0, tiles = [];
    var frame = map.getContainer().parentNode;
    var note = document.createElement("p");
    note.className = "notice small";
    note.id = "offline-note";
    note.hidden = true;
    note.textContent = "Offline: showing the main roads from OpenStreetMap instead of " +
      "the map background. The priorities are the same.";
    // Inside the page column, so it shares the one left edge (DESIGN.md).
    var column = document.createElement("div");
    column.className = "wrap";
    column.appendChild(note);
    frame.parentNode.insertBefore(column, frame);

    function show() {
      if (shown) return;
      shown = true;
      note.hidden = false;
      // Instead of the tiles, not on top of them: a patchwork of whatever tiles the
      // browser happened to keep would look like a map and be missing most of it.
      tiles.forEach(function (t) { map.removeLayer(t); });
      fetch("data/roads.geojson").then(function (r) { return r.json(); }).then(function (doc) {
        if (!shown) return;
        roads = L.geoJSON(doc, {
          interactive: false,
          attribution: "Roads &copy; OpenStreetMap contributors",
          style: function (f) {
            var major = /motorway|trunk|primary/.test(f.properties["class"]);
            return { color: "#8E8A82", weight: major ? 2.4 : 1.1, opacity: 0.9,
                     className: "offline-road" };
          }
        }).addTo(map);
        roads.bringToBack();
        window.__offlineRoads = doc.features.length;
      }).catch(function () { /* nothing cached either: the cells still draw */ });
    }
    function hide() {
      shown = false;
      note.hidden = true;
      if (roads) { map.removeLayer(roads); roads = null; }
      tiles.forEach(function (t) { if (!map.hasLayer(t)) t.addTo(map); });
    }

    // Connected to Wi-Fi with no internet looks "online", so failing tiles count too.
    map.eachLayer(function (layer) {
      if (!(layer instanceof L.TileLayer)) return;
      tiles.push(layer);
      layer.on("tileload", function () { loads++; if (shown && navigator.onLine) hide(); });
      layer.on("tileerror", function () { errors++; if (errors >= 4 && loads === 0) show(); });
    });
    window.addEventListener("offline", show);
    window.addEventListener("online", hide);
    if (!navigator.onLine) show();
  }

  window.OfflineView = { attach: attach };
})();
