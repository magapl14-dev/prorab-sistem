/* REST API wrapper — replaces google.script.run */

// API base URL detection:
// - Native Capacitor app (Android/iOS) → абсолютный URL продакшн-бекенда
// - Локальная разработка через localhost → http://localhost:8000
// - Иначе (веб) → относительный путь, тот же домен
const API_BASE = (() => {
  // Capacitor: WebView отдаёт страницу с протокола capacitor:// (Android)
  // или https://localhost (iOS), поэтому относительный путь не сработает
  const isCap = (window.Capacitor && window.Capacitor.isNativePlatform && window.Capacitor.isNativePlatform())
    || /^capacitor:/i.test(window.location.protocol);
  if (isCap) return "https://welldom05.duckdns.org/api/v1";
  if (window.location.hostname === "localhost") return "http://localhost:8000/api/v1";
  return "/api/v1";
})();

let _accessToken = localStorage.getItem("access_token") || null;
let _refreshToken = localStorage.getItem("refresh_token") || null;
let _user = JSON.parse(localStorage.getItem("user") || "null");

export const Auth = {
  get user() { return _user; },
  get isLoggedIn() { return !!_accessToken; },

  async login(phone, pin) {
    const r = await _post("/auth/login", { phone, pin }, false);
    _accessToken = r.access_token;
    _refreshToken = r.refresh_token;
    _user = r.user;
    localStorage.setItem("access_token", _accessToken);
    localStorage.setItem("refresh_token", _refreshToken);
    localStorage.setItem("user", JSON.stringify(_user));
    return r.user;
  },

  async logout() {
    try { await _post("/auth/logout", { refresh_token: _refreshToken }); } catch (_) {}
    _accessToken = null; _refreshToken = null; _user = null;
    localStorage.clear();
  },

  async me() {
    return _get("/auth/me");
  },

  async changePin(oldPin, newPin) {
    return _post("/auth/change-pin", { old_pin: oldPin, new_pin: newPin });
  },
};

export const Records = {
  list: (code, params = {}) => _get(`/projects/${code}/records`, params),
  get: (code, id) => _get(`/projects/${code}/records/${id}`),
  create: (code, data) => _post(`/projects/${code}/records`, data),
  update: (code, id, data) => _patch(`/projects/${code}/records/${id}`, data),
  delete: (code, id) => _delete(`/projects/${code}/records/${id}`),
  dictionaries: (code, kind) => _get(`/projects/${code}/dictionaries`, kind ? { kind } : {}),
};

export const Photos = {
  async upload(file, kind = "receipt", mediaType = "image") {
    if (!file || !file.size) throw { detail: "Файл пустой (0 байт)" };
    const urlResp = await _post("/photos/upload-url", {
      filename: file.name || (mediaType === "audio" ? "audio.webm" : "photo.jpg"),
      size: file.size,
      mime_type: file.type || (mediaType === "audio" ? "audio/webm" : "image/jpeg"),
      kind,
      media_type: mediaType,
    });
    const resp = await fetch(urlResp.upload_url, {
      method: "PUT",
      body: file,
      headers: { "Content-Type": file.type || (mediaType === "audio" ? "audio/webm" : "image/jpeg") },
    });
    if (!resp.ok) {
      const body = await resp.text().catch(() => "");
      throw { detail: `Upload failed ${resp.status}: ${body.slice(0, 200)}` };
    }
    return urlResp.photo_id;
  },

  confirm: (photoId, { recordId = null, taskId = null, commentId = null, durationSec = null } = {}) =>
    _post("/photos/confirm", {
      photo_id: photoId,
      ...(recordId ? { record_id: recordId } : {}),
      ...(taskId ? { task_id: taskId } : {}),
      ...(commentId ? { comment_id: commentId } : {}),
      ...(durationSec != null ? { duration_sec: durationSec } : {}),
    }),

  delete: (id) => _delete(`/photos/${id}`),
};

export const Earnings = {
  project: (code) => _get(`/projects/${code}/earnings`),
  all: () => _get("/earnings/all"),
  plan: (code) => _get(`/projects/${code}/plan`),
  periodStats: (code) => _get(`/projects/${code}/period-stats`),
  monthly: (code) => _get(`/projects/${code}/monthly`),
  chart14: (code) => _get(`/projects/${code}/chart14`),
};

export const Admin = {
  projects: {
    list: () => _get("/admin/projects"),
    create: (data) => _post("/admin/projects", data),
    update: (code, data) => _patch(`/admin/projects/${code}`, data),
    assignUser: (code, data) => _post(`/admin/projects/${code}/users`, data),
    revokeUser: (code, userId) => _delete(`/admin/projects/${code}/users/${userId}`),
    activate: (code) => _patch(`/admin/projects/${code}/activate`, {}),
    deactivate: (code) => _patch(`/admin/projects/${code}/deactivate`, {}),
    delete: (code) => _delete(`/admin/projects/${code}`),
    syncSheets: (code) => _post(`/admin/projects/${code}/sync-sheets`, {}),
  },
  users: {
    list: () => _get("/admin/users"),
    create: (data) => _post("/admin/users", data),
    update: (id, data) => _patch(`/admin/users/${id}`, data),
    deactivate: (id) => _patch(`/admin/users/${id}/deactivate`, {}),
    activate: (id) => _patch(`/admin/users/${id}/activate`, {}),
    delete: (id) => _delete(`/admin/users/${id}`),
    projects: (id) => _get(`/admin/users/${id}/projects`),
  },
  dictionaries: {
    list: () => _get("/admin/dictionaries"),
    create: (data) => _post("/admin/dictionaries", data),
    update: (id, data) => _patch(`/admin/dictionaries/${id}`, data),
    delete: (id) => _delete(`/admin/dictionaries/${id}`),
  },
  settings: {
    update: (data) => _patch("/admin/settings", data),
  },
  permissions: {
    get: () => _get("/admin/permissions"),
    update: (items) => _patch("/admin/permissions", { items }),
  },
  roles: {
    list: () => _get("/admin/roles"),
    create: (data) => _post("/admin/roles", data),
    delete: (name) => _delete(`/admin/roles/${encodeURIComponent(name)}`),
  },
  bitrix: {
    get: () => _get("/admin/bitrix"),
    update: (data) => _patch("/admin/bitrix", data),
    test: () => _post("/admin/bitrix/test", {}),
  },
  analytics: {
    users: (params = {}) => {
      const qs = new URLSearchParams();
      Object.entries(params).forEach(([k, v]) => { if (v) qs.set(k, v); });
      const s = qs.toString();
      return _get(`/admin/analytics/users${s ? '?' + s : ''}`);
    },
  },
};

export const AI = {
  health: () => _get("/ai/health").catch(() => ({ active: false })),
  // Отправляет голосовой Blob в Grok и получает поля формы.
  // context: "expense" | "master_payment" | "client_payment" | "task"
  // currentValues: объект уже заполненных полей (чтобы Grok не перебивал).
  // Возвращает { transcript, fields, warnings }.
  // Кидает { status: 503, ... } если Grok не настроен — фронт по этому статусу
  // сваливается на браузерный STT.
  async voiceFill(audioBlob, context, currentValues = {}) {
    const form = new FormData();
    form.append("audio", audioBlob, audioBlob.name || "voice.webm");
    form.append("context", context);
    form.append("current_json", JSON.stringify(currentValues || {}));
    const headers = {};
    if (_accessToken) headers["Authorization"] = `Bearer ${_accessToken}`;
    const res = await fetch(API_BASE + "/ai/voice-fill", {
      method: "POST",
      body: form,
      headers,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw { status: res.status, detail: data.detail || data };
    return data;
  },
};

export const Masters = {
  list: (includeInactive = false, projectCode = null) => {
    const q = new URLSearchParams();
    if (includeInactive) q.set('include_inactive', 'true');
    if (projectCode)     q.set('project_code', projectCode);
    const s = q.toString();
    return _get(`/masters${s ? '?' + s : ''}`);
  },
  get: (id, projectCode = null) =>
    _get(`/masters/${id}${projectCode ? '?project_code=' + encodeURIComponent(projectCode) : ''}`),
  create: (data) => _post("/masters", data),
  update: (id, data) => _patch(`/masters/${id}`, data),
  delete: (id, { force = false } = {}) =>
    _delete(`/masters/${id}${force ? '?force=true' : ''}`),
};

export const Tasks = {
  list: (params = {}) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => { if (v !== undefined && v !== null && v !== '') qs.set(k, v); });
    const s = qs.toString();
    return _get(`/tasks${s ? '?' + s : ''}`);
  },
  get: (id) => _get(`/tasks/${id}`),
  create: (data) => _post("/tasks", data),
  update: (id, data) => _patch(`/tasks/${id}`, data),
  delete: (id) => _delete(`/tasks/${id}`),
  users: () => _get("/tasks/_users"),
  projects: () => _get("/tasks/_projects"),
  types: () => _get("/tasks/_types"),
  comments: {
    list: (taskId) => _get(`/tasks/${taskId}/comments`),
    add: (taskId, data) => _post(`/tasks/${taskId}/comments`, data),
    delete: (taskId, commentId) => _delete(`/tasks/${taskId}/comments/${commentId}`),
  },
};

export const Settings = {
  get: () => _get("/settings"),
};

// ── HTTP helpers ──────────────────────────────────────────────────────────────

async function _request(method, path, body, auth = true) {
  const headers = { "Content-Type": "application/json" };
  if (auth && _accessToken) headers["Authorization"] = `Bearer ${_accessToken}`;

  let res = await fetch(API_BASE + path, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (res.status === 401 && auth && _refreshToken) {
    const refreshed = await _tryRefresh();
    if (refreshed) {
      headers["Authorization"] = `Bearer ${_accessToken}`;
      res = await fetch(API_BASE + path, {
        method, headers,
        body: body !== undefined ? JSON.stringify(body) : undefined,
      });
    }
  }

  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw { status: res.status, detail: data.detail || data };
  return data;
}

async function _tryRefresh() {
  try {
    const r = await fetch(API_BASE + "/auth/refresh", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: _refreshToken }),
    });
    if (!r.ok) { Auth.logout(); return false; }
    const d = await r.json();
    _accessToken = d.access_token;
    localStorage.setItem("access_token", _accessToken);
    return true;
  } catch (_) {
    return false;
  }
}

function _buildUrl(path, params = {}) {
  const q = new URLSearchParams(
    Object.fromEntries(Object.entries(params).filter(([, v]) => v != null))
  ).toString();
  return path + (q ? "?" + q : "");
}

// ── GET cache (для оффлайн-чтения исторических данных) ──────────────────────
const _CACHE_PREFIX = "apicache_v1_";
const _CACHE_TTL_MS = 30 * 24 * 60 * 60 * 1000; // 30 дней
const _CACHE_MAX_ENTRIES = 200;
const _CACHE_INDEX_KEY = "apicache_index_v1";

function _cacheGet(url) {
  try {
    const raw = localStorage.getItem(_CACHE_PREFIX + url);
    if (!raw) return null;
    const { ts, data } = JSON.parse(raw);
    if (Date.now() - ts > _CACHE_TTL_MS) return null;
    return { data, ts };
  } catch (_) { return null; }
}
function _cacheSet(url, data) {
  try {
    const payload = JSON.stringify({ ts: Date.now(), data });
    // Не кешируем гигантские ответы (>500KB)
    if (payload.length > 500_000) return;
    localStorage.setItem(_CACHE_PREFIX + url, payload);
    let idx;
    try { idx = JSON.parse(localStorage.getItem(_CACHE_INDEX_KEY) || "[]"); } catch (_) { idx = []; }
    idx = idx.filter(u => u !== url);
    idx.push(url);
    // LRU-эвикция: если слишком много, выкидываем старые
    while (idx.length > _CACHE_MAX_ENTRIES) {
      const old = idx.shift();
      localStorage.removeItem(_CACHE_PREFIX + old);
    }
    localStorage.setItem(_CACHE_INDEX_KEY, JSON.stringify(idx));
  } catch (e) {
    // Quota exceeded — чистим кеш и забываем
    if (e?.name === "QuotaExceededError") {
      try {
        const idx = JSON.parse(localStorage.getItem(_CACHE_INDEX_KEY) || "[]");
        // Удалим половину
        const drop = idx.splice(0, Math.ceil(idx.length / 2));
        drop.forEach(u => localStorage.removeItem(_CACHE_PREFIX + u));
        localStorage.setItem(_CACHE_INDEX_KEY, JSON.stringify(idx));
      } catch (_) {}
    }
  }
}

const _get = async (path, params) => {
  const url = _buildUrl(path, params);
  // Если знаем, что оффлайн — сразу из кеша
  if (typeof navigator !== "undefined" && navigator.onLine === false) {
    const c = _cacheGet(url);
    if (c) return c.data;
    throw { status: 0, detail: "Нет связи — данные не закешированы" };
  }
  try {
    const data = await _request("GET", url);
    _cacheSet(url, data);
    return data;
  } catch (e) {
    // Сеть отвалилась — пробуем из кеша
    const isNetErr = e?.status === 0 || /Failed to fetch|NetworkError|net::/i.test(String(e?.message || e?.detail || ""));
    if (isNetErr) {
      const c = _cacheGet(url);
      if (c) {
        try { window.dispatchEvent(new CustomEvent("apicache:hit", { detail: { url, age: Date.now() - c.ts } })); } catch (_) {}
        return c.data;
      }
    }
    throw e;
  }
};
const _post = (path, body, auth = true) => _request("POST", path, body, auth);
const _patch = (path, body) => _request("PATCH", path, body);
const _delete = (path) => _request("DELETE", path);
