import axios from "axios";

export const api = axios.create({ baseURL: "/api" });

// ── In-flight request deduplication ──────────────────────────────────────────
// Prevents the same GET endpoint being called multiple times simultaneously
const _inflight = new Map();

api.interceptors.request.use((c) => {
  const t = localStorage.getItem("token");
  if (t) c.headers.Authorization = `Bearer ${t}`;

  // Deduplicate concurrent identical GET requests
  if (c.method === "get") {
    const key = c.baseURL + c.url;
    if (_inflight.has(key)) {
      c._dedup_key = key;
      c.adapter = () => _inflight.get(key);
    } else {
      const promise = new Promise((resolve, reject) => {
        c._resolve = resolve;
        c._reject = reject;
      });
      _inflight.set(key, promise);
      c._dedup_key = key;
      c._is_origin = true;
    }
  }
  return c;
});

api.interceptors.response.use(
  (r) => {
    if (r.config._is_origin && r.config._dedup_key) {
      _inflight.delete(r.config._dedup_key);
    }
    return r;
  },
  (e) => {
    if (e.config?._is_origin && e.config?._dedup_key) {
      _inflight.delete(e.config._dedup_key);
    }
    const url = e.config?.url || "";
    const isAuthRoute = url.includes("/auth/");
    const isApiKeyRoute = url.includes("/ai/") || url.includes("/ml/") || url.includes("/viz/");
    if (e.response?.status === 401 && !isAuthRoute && !isApiKeyRoute) {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(e);
  }
);

export const authApi = {
  login:           (email, password) => api.post("/auth/login", { email, password }),
  register:        (email, password) => api.post("/auth/register", { email, password }),
  logout:          ()                => api.post("/auth/logout"),
  googleUrl:       ()                => api.get("/auth/oauth/google/url"),
  githubUrl:       ()                => api.get("/auth/oauth/github/url"),
  googleCallback:  (code, state)     => api.post("/auth/oauth/google/callback", { code, state }),
  githubCallback:  (code, state)     => api.post("/auth/oauth/github/callback", { code, state }),
  setup2fa:        ()                => api.post("/auth/2fa/setup"),
  confirm2fa:      (code)            => api.post("/auth/2fa/confirm", { code }),
  verify2fa:       (temp_token, code) => api.post("/auth/2fa/verify", { temp_token, code }),
  disable2fa:      (code)            => api.post("/auth/2fa/disable", { code }),
};

export const dataApi = {
  upload:  (file)   => { const f = new FormData(); f.append("file", file); return api.post("/data/upload", f); },
  preview: (n = 10) => api.get(`/data/preview?n=${n}`),
  info:    ()       => api.get("/data/info"),
  clean:   ()       => api.post("/data/clean"),
  stats:   ()       => api.get("/data/stats"),
};

export const aiApi = {
  chat:        (query)           => {
    const apiKey = localStorage.getItem("groq_key") || localStorage.getItem("aiml_key") || localStorage.getItem("openai_key") || "";
    return api.post("/ai/chat", { query }, apiKey ? { headers: { "X-Api-Key": apiKey } } : {});
  },
  query:       (question, data)  => {
    const apiKey = localStorage.getItem("groq_key") || localStorage.getItem("aiml_key") || localStorage.getItem("openai_key") || "";
    return api.post("/ai/query", { question, data }, apiKey ? { headers: { "X-Api-Key": apiKey } } : {});
  },
  taskType:    (question)        => api.get(`/ai/task-type?question=${encodeURIComponent(question)}`),
  clearMemory: ()                => api.delete("/ai/memory"),
};

export const vizApi = {
  overview: (max = 6, palette = "Indigo") => api.get(`/viz/overview?max_charts=${max}&palette=${palette}`),
  kpis:     (palette = "Indigo")          => api.get(`/viz/kpis?palette=${palette}`),
  custom:   (req)                         => api.post("/viz/custom", req),
};

export const sqlApi = {
  query: (question) => api.post("/sql/query", { question }),
};

export const ragApi = {
  index: ()         => api.post("/rag/index"),
  query: (question) => api.post("/rag/query", { question }),
};

export const debugApi = {
  system:  () => api.get("/debug/system"),
  health:  () => api.get("/debug/health"),
  dataset: () => api.get("/debug/dataset"),
  model:   () => api.get("/debug/model"),
  traces:  () => api.get("/debug/traces"),
  logs:    () => api.get("/debug/logs"),
};

export const analyticsApi = {
  stats:      ()           => api.get("/analytics/stats"),
  cluster:    (k = 3)      => api.post("/analytics/cluster", { k }),
  anomaly:    ()           => api.get("/analytics/anomaly"),
  timeseries: (col)        => api.get(`/analytics/timeseries?col=${encodeURIComponent(col)}`),
  engineer:   (expr, name) => api.post("/analytics/engineer", { expression: expr, new_col: name }),
};

export const workspaceApi = {
  list:           ()                    => api.get("/workspaces"),
  create:         (name, description)   => api.post("/workspaces", { name, description }),
  delete:         (id)                  => api.delete(`/workspaces/${id}`),
  members:        (id)                  => api.get(`/workspaces/${id}/members`),
  removeMember:   (id, uid)             => api.delete(`/workspaces/${id}/members/${uid}`),
  invite:         (id, email, role)     => api.post(`/workspaces/${id}/invite`, { email, role }),
  invitations:    (id)                  => api.get(`/workspaces/${id}/invitations`),
  resendInvite:   (wsId, invId)         => api.post(`/workspaces/${wsId}/invitations/${invId}/resend`),
  revokeInvite:   (wsId, invId)         => api.delete(`/workspaces/${wsId}/invitations/${invId}`),
  join:           (token)               => api.post("/workspaces/join", { token }),
  joinInfo:       (token)               => api.get(`/workspaces/join/info?token=${token}`),
};

export default api;


