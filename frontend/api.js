/* REST API wrapper — replaces google.script.run */

const API_BASE = window.location.hostname === "localhost"
  ? "http://localhost:8000/api/v1"
  : "/api/v1";

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

const _get = (path, params) => _request("GET", _buildUrl(path, params));
const _post = (path, body, auth = true) => _request("POST", path, body, auth);
const _patch = (path, body) => _request("PATCH", path, body);
const _delete = (path) => _request("DELETE", path);
