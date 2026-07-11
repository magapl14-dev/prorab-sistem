const CACHE = "welldom-v20";
const STATIC = ["/", "/index.html", "/api.js", "/manifest.json"];

// Гарантированный fallback: если и сеть, и кэш пусты — отдаём реальный Response,
// а не undefined (иначе браузер валит fetch с TypeError и весь скрипт не грузится).
const _errorResponse = () =>
  new Response("", { status: 504, statusText: "Offline and not cached" });

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(STATIC)).catch(() => {}));
  self.skipWaiting();
});

self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(keys =>
    Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
  ));
  self.clients.claim();
});

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  if (req.url.includes("/api/")) return;

  // Network-first для HTML (чтобы обновления подтягивались), cache-fallback для offline
  if (req.mode === "navigate" || req.destination === "document") {
    e.respondWith((async () => {
      try {
        const r = await fetch(req);
        caches.open(CACHE).then(c => c.put(req, r.clone())).catch(() => {});
        return r;
      } catch (_) {
        return (await caches.match(req))
            || (await caches.match("/index.html"))
            || _errorResponse();
      }
    })());
    return;
  }

  // Cache-first для статики
  e.respondWith((async () => {
    const cached = await caches.match(req);
    if (cached) return cached;
    try {
      const r = await fetch(req);
      caches.open(CACHE).then(c => c.put(req, r.clone())).catch(() => {});
      return r;
    } catch (_) {
      return _errorResponse();
    }
  })());
});
