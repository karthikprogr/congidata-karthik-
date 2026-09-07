/**
 * COGNIDATA Unified Proxy — port 3000
 * Routes everything through one URL so the browser never leaves the tab.
 *
 *   /api/*   → FastAPI Backend   (port 8000)
 *   /app/*   → React Dashboard   (port 5173)
 *   /login, /chat, /dashboard … → React Dashboard (port 5173)
 *   everything else             → Landing Page    (port 8080)
 */
import http from "http";
import httpProxy from "http-proxy";

const BACKEND   = "http://localhost:8000";
const DASHBOARD = "http://localhost:5173";
const LANDING   = "http://localhost:8080";

// All React app routes
const APP_ROUTES = [
  "/login", "/chat", "/upload", "/dashboard", "/analyst", "/automl",
  "/geo", "/viz", "/reports", "/roadmap", "/workspaces", "/analytics",
  "/maps", "/alerts", "/federated", "/semantic", "/pipeline", "/catalog",
  "/esg", "/splat", "/debug", "/profile", "/settings", "/admin",
  "/actions", "/ingest", "/deep-analyst", "/devhub", "/globe", "/help",
  "/realtime", "/oauth", "/reset-password",
];

const proxy = httpProxy.createProxyServer({ ws: true });

proxy.on("error", (err, req, res) => {
  const msg = err.message || "unknown error";
  console.error(`[proxy] ${req.url} → ${msg}`);
  if (res && res.writeHead && !res.headersSent) {
    res.writeHead(502, { "Content-Type": "text/html; charset=utf-8" });
    res.end(`
      <!DOCTYPE html>
      <html>
      <head>
        <meta http-equiv="refresh" content="3">
        <style>
          body { background:#09090b; color:#e4e4e7; font-family:sans-serif;
                 display:flex; align-items:center; justify-content:center;
                 height:100vh; margin:0; flex-direction:column; gap:16px; }
          h2   { color:#facc15; font-size:1.4rem; }
          p    { color:#71717a; font-size:.9rem; }
          .dot { width:12px; height:12px; border-radius:50%; background:#facc15;
                 animation: pulse 1s ease-in-out infinite; }
          @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }
        </style>
      </head>
      <body>
        <div class="dot"></div>
        <h2>Services are starting up…</h2>
        <p>This page will refresh automatically in 3 seconds.</p>
        <p style="font-size:.75rem;color:#3f3f46">${msg}</p>
      </body>
      </html>
    `);
  }
});

const server = http.createServer((req, res) => {
  const url = req.url || "/";

  // 1. Backend API
  if (url.startsWith("/api") || url.startsWith("/docs") || url.startsWith("/openapi")) {
    proxy.web(req, res, { target: BACKEND });
    return;
  }

  // 2. Explicit /app/* prefix → dashboard (strip prefix)
  if (url.startsWith("/app")) {
    req.url = url.replace(/^\/app/, "") || "/";
    proxy.web(req, res, { target: DASHBOARD });
    return;
  }

  // 3. Known React app routes → dashboard
  const isAppRoute = APP_ROUTES.some(
    r => url === r || url.startsWith(r + "/") || url.startsWith(r + "?")
  );
  if (isAppRoute) {
    proxy.web(req, res, { target: DASHBOARD });
    return;
  }

  // 4. Static assets — use Referer header to pick the right target
  const isAsset = /^(\/(@|src\/|node_modules\/|__))/.test(url) ||
    /\.(js|jsx|ts|tsx|css|svg|ico|png|jpg|woff2?|ttf|map)(\?|$)/.test(url) ||
    url.includes("?v=") || url.includes("?t=") || url.includes("hmr");

  if (isAsset) {
    const ref = req.headers.referer || "";
    const fromApp = APP_ROUTES.some(r => ref.includes(r)) || ref.includes("/app");
    proxy.web(req, res, { target: fromApp ? DASHBOARD : LANDING });
    return;
  }

  // 5. Default → Landing page
  proxy.web(req, res, { target: LANDING });
});

// WebSocket (Vite HMR)
server.on("upgrade", (req, socket, head) => {
  const url = req.url || "/";
  const ref = req.headers.referer || "";
  const fromApp = APP_ROUTES.some(r => ref.includes(r)) || url.includes("5173");
  proxy.ws(req, socket, head, { target: fromApp ? DASHBOARD : LANDING });
});

server.listen(3000, () => {
  console.log("\n  ╔══════════════════════════════════════════╗");
  console.log("  ║   COGNIDATA — Unified Proxy: port 3000  ║");
  console.log("  ╠══════════════════════════════════════════╣");
  console.log("  ║  → http://localhost:3000                 ║");
  console.log("  ║  Landing page loads first.               ║");
  console.log("  ║  Login stays in the SAME TAB.            ║");
  console.log("  ╚══════════════════════════════════════════╝\n");
});
