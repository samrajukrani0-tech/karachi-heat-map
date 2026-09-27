/* Offline support (P5-02). Precaches the app shell and the data, then serves
   same-origin requests network-first: online you always get the current files,
   offline you get the last good copy. Basemap tiles are Esri's and are deliberately
   NOT cached (data/SOURCES.md); offline, the map draws data/roads.geojson instead.
   tests/test_offline.py fails if a file in site/ is missing from SHELL. */
var VERSION = "khm-v2";
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
  "i18n/en.json",
  "briefs/index.json",
  "briefs/allah-buksh-goth.html",
  "briefs/bagh-e-korangi.html",
  "briefs/future-colony.html",
  "briefs/ilyas-goth.html",
  "briefs/korangi-sector-29.html",
  "briefs/labour-colony.html",
  "briefs/landhi-89-chowk.html",
  "briefs/landhi-sector-21.html",
  "briefs/mansehra-colony.html",
  "briefs/muhammad-nagar.html",
  "briefs/sharafi-goth-landhi.html",
  "briefs/sherpao-colony.html"
];
// The briefs' PDF and PNG downloads (about 0.7 MB each pair) are deliberately NOT
// precached: 12 of them would cost a phone ~8 MB on its first visit. Each is cached
// the first time it is opened, by the network-first handler below.

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
