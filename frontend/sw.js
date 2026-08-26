const CACHE = "welldom-v22";
const STATIC = ["/", "/index.html", "/api.js", "/css/app.css", "/js/app.js", "/manifest.json"];

const _errorResponse = () =>
  new Response("", { status: 504, statusText: "Offline and not cached" });

function _isAppShell(req, url) {
  if (req.mode === "navigate" || req.destination === "document") return true;
  if (req.destination === "script" || req.destination === "style") return true;
  const p = url.pathname;
  return (
    p === "/sw.js" ||
    p === "/index.html" ||
    p === "/api.js" ||
    p === "/css/app.css" ||
    p === "/js/app.js" ||
    p.endsWith(".js") ||
    p.endsWith(".css")
  );
}

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
  const url = new URL(req.url);
  if (url.pathname.includes("/api/")) return;

  if (_isAppShell(req, url)) {
    e.respondWith((async () => {
      try {
        const r = await fetch(req, { cache: "no-store" });
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
