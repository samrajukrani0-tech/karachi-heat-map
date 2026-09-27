/* Offline support (P5-02). Precaches the app shell and the data, then serves
   same-origin requests network-first: online you always get the current files,
   offline you get the last good copy. Basemap tiles are Esri's and are deliberately
   NOT cached (data/SOURCES.md); offline, the map draws data/roads.geojson instead.
   tests/test_offline.py fails if a file in site/ is missing from SHELL. */
var VERSION = "khm-v1";
var SHELL = [
  "./",
  "index.html", "plan.html", "briefs.html", "how-it-works.html",
  "data-and-credits.html", "about.html",
  "style.css", "map.js", "plan.js", "planner-core.js", "offline.js", "sw-register.js",
  "favicon.svg",
  "vendor/leaflet.js", "vendor/leaflet.css",
  "vendor/images/layers.png", "vendor/images/layers-2x.png",
  "vendor/images/marker-icon.png", "vendor/images/marker-icon-2x.png",
  "vendor/images/marker-shadow.png",
  "data/cells.geojson", "data/scenarios.json", "data/roads.geojson",
  "i18n/en.json"
];

self.addEventListener("install", function (event) {
  event.waitUntil(caches.open(VERSION).then(function (cache) {
    return cache.addAll(SHELL);
  }).then(function () { return self.skipWaiting(); }));
});

self.addEventListener("activate", function (event) {
  event.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.filter(function (k) { return k !== VERSION; })
      .map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});

self.addEventListener("fetch", function (event) {
  var request = event.request;
  if (request.method !== "GET" || new URL(request.url).origin !== self.location.origin) {
    return;   // tiles and anything else third-party: straight to the network
  }
  event.respondWith(fetch(request).then(function (response) {
    if (response.ok) {
      var copy = response.clone();
      caches.open(VERSION).then(function (cache) { cache.put(request, copy); });
    }
    return response;
  }).catch(function () {
    return caches.match(request, { ignoreSearch: true }).then(function (hit) {
      return hit || caches.match("index.html");
    });
  }));
});
