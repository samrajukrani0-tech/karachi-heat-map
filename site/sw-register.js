/* Register the offline service worker from pages that have no map (P5-02). */
if ("serviceWorker" in navigator && /^https?:$/.test(location.protocol)) {
  window.addEventListener("load", function () {
    navigator.serviceWorker.register("sw.js").catch(function () { /* optional */ });
  });
}
