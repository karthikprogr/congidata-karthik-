import { useState, useEffect, useCallback, useRef } from "react";
import api from "../api/client";

const Badge = ({ ok, label }) => (
  <span className={`px-2 py-0.5 rounded text-xs font-mono ${ok ? "bg-green-900 text-green-300" : "bg-red-900 text-red-300"}`}>
    {label}
  </span>
);

const Card = ({ title, children, action }) => (
  <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
    <div className="flex items-center justify-between mb-3">
      <h3 className="text-sm font-semibold text-gray-200">{title}</h3>
      {action}
    </div>
    {children}
  </div>
);

const Btn = ({ onClick, disabled, children, variant = "default", size = "sm" }) => {
  const base = "rounded font-medium transition-colors disabled:opacity-50";
  const sizes = { sm: "px-3 py-1 text-xs", md: "px-4 py-2 text-sm" };
  const variants = {
    default: "bg-gray-700 hover:bg-gray-600 text-gray-200",
    primary: "bg-blue-600 hover:bg-blue-500 text-white",
    danger: "bg-red-700 hover:bg-red-600 text-white",
    success: "bg-green-700 hover:bg-green-600 text-white",
  };
  return (
    <button onClick={onClick} disabled={disabled} className={`${base} ${sizes[size]} ${variants[variant]}`}>
      {children}
    </button>
  );
};

const TABS = ["System", "API Health", "Dataset", "Model", "Traces", "Logs", "Scanner", "Watcher", "Performance"];

export default function DebugAgent() {
  const [tab, setTab] = useState("System");
  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-6">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold mb-1">Debug Agent</h1>
        <p className="text-gray-400 text-sm mb-6">System diagnostics, performance monitoring, and code analysis</p>
        <div className="flex flex-wrap gap-1 mb-6 border-b border-gray-700 pb-2">
          {TABS.map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-4 py-2 text-sm rounded-t transition-colors ${tab === t ? "bg-blue-600 text-white" : "text-gray-400 hover:text-gray-200 hover:bg-gray-800"}`}>
              {t}
            </button>
          ))}
        </div>
        {tab === "System" && <SystemTab />}
        {tab === "API Health" && <ApiHealthTab />}
        {tab === "Dataset" && <DatasetTab />}
        {tab === "Model" && <ModelTab />}
        {tab === "Traces" && <TracesTab />}
        {tab === "Logs" && <LogsTab />}
        {tab === "Scanner" && <ScannerTab />}
        {tab === "Watcher" && <WatcherTab />}
        {tab === "Performance" && <PerformanceTab />}
      </div>
    </div>
  );
}
function SystemTab() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const load = useCallback(async () => {
    setLoading(true);
    try { setData((await api.get("/debug/system")).data); } catch { setData(null); }
    setLoading(false);
  }, []);
  useEffect(() => { load(); }, [load]);
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <Card title="System Info" action={<Btn onClick={load} disabled={loading}>{loading ? "..." : "Refresh"}</Btn>}>
        {data ? (
          <dl className="space-y-2 text-sm">
            {Object.entries(data).map(([k, v]) => (
              <div key={k} className="flex justify-between">
                <dt className="text-gray-400 capitalize">{k.replace(/_/g, " ")}</dt>
                <dd className="text-gray-200 font-mono text-xs max-w-xs truncate">{String(v)}</dd>
              </div>
            ))}
          </dl>
        ) : <p className="text-gray-500 text-sm">No data</p>}
      </Card>
    </div>
  );
}
function ApiHealthTab() {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const check = useCallback(async () => {
    setLoading(true);
    try { setResults((await api.get("/debug/health")).data); } catch { setResults([]); }
    setLoading(false);
  }, []);
  useEffect(() => { check(); }, [check]);
  return (
    <Card title="Endpoint Health" action={<Btn onClick={check} disabled={loading}>{loading ? "Checking..." : "Re-check"}</Btn>}>
      <div className="space-y-2">
        {results.map((r, i) => (
          <div key={i} className="flex items-center justify-between bg-gray-900 rounded p-2">
            <span className="font-mono text-xs text-gray-300">{r.endpoint}</span>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-400">{r.duration_ms}ms</span>
              <Badge ok={r.ok} label={r.ok ? `${r.status} OK` : `${r.status} FAIL`} />
            </div>
          </div>
        ))}
        {results.length === 0 && <p className="text-gray-500 text-sm">No results yet</p>}
      </div>
    </Card>
  );
}
function DatasetTab() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const load = useCallback(async () => {
    setLoading(true);
    try { setData((await api.get("/debug/dataset")).data); } catch { setData(null); }
    setLoading(false);
  }, []);
  useEffect(() => { load(); }, [load]);
  if (!data || !data.loaded) return (
    <Card title="Dataset Diagnostics" action={<Btn onClick={load} disabled={loading}>{loading ? "..." : "Load"}</Btn>}>
      <p className="text-gray-500 text-sm">No dataset loaded</p>
    </Card>
  );
  return (
    <div className="space-y-4">
      <Card title="Dataset Overview" action={<Btn onClick={load} disabled={loading}>{loading ? "..." : "Refresh"}</Btn>}>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div><div className="text-2xl font-bold text-blue-400">{data.shape?.[0]}</div><div className="text-xs text-gray-400">Rows</div></div>
          <div><div className="text-2xl font-bold text-purple-400">{data.shape?.[1]}</div><div className="text-xs text-gray-400">Columns</div></div>
          <div><div className="text-2xl font-bold text-green-400">{data.memory_mb}MB</div><div className="text-xs text-gray-400">Memory</div></div>
        </div>
      </Card>
      <Card title="Column Types">
        <div className="grid grid-cols-2 gap-1">
          {Object.entries(data.dtypes || {}).map(([col, dtype]) => (
            <div key={col} className="flex justify-between bg-gray-900 rounded px-2 py-1 text-xs">
              <span className="text-gray-300 truncate">{col}</span>
              <span className="text-blue-400 font-mono ml-2">{dtype}</span>
            </div>
          ))}
        </div>
      </Card>
      <Card title="Missing Values">
        <div className="grid grid-cols-2 gap-1">
          {Object.entries(data.missing || {}).filter(([, v]) => v > 0).map(([col, count]) => (
            <div key={col} className="flex justify-between bg-gray-900 rounded px-2 py-1 text-xs">
              <span className="text-gray-300">{col}</span>
              <span className="text-red-400 font-mono">{count}</span>
            </div>
          ))}
          {Object.values(data.missing || {}).every(v => v === 0) && (
            <p className="text-green-400 text-xs col-span-2">No missing values</p>
          )}
        </div>
      </Card>
    </div>
  );
}
function ModelTab() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const load = useCallback(async () => {
    setLoading(true);
    try { setData((await api.get("/debug/model")).data); } catch { setData(null); }
    setLoading(false);
  }, []);
  useEffect(() => { load(); }, [load]);
  return (
    <Card title="Model State" action={<Btn onClick={load} disabled={loading}>{loading ? "..." : "Refresh"}</Btn>}>
      {data?.exists ? (
        <dl className="space-y-2 text-sm">
          {[["Type", data.model_type], ["Target", data.target], ["Task", data.task],
            ["Metric", data.metric], ["Score", typeof data.score === "number" ? data.score.toFixed(4) : data.score]
          ].map(([k, v]) => (
            <div key={k} className="flex justify-between">
              <dt className="text-gray-400">{k}</dt>
              <dd className="text-gray-200 font-mono">{String(v ?? "—")}</dd>
            </div>
          ))}
        </dl>
      ) : <p className="text-gray-500 text-sm">No model trained yet</p>}
    </Card>
  );
}

function TracesTab() {
  const [traces, setTraces] = useState([]);
  const [loading, setLoading] = useState(false);
  const load = useCallback(async () => {
    setLoading(true);
    try { setTraces((await api.get("/debug/traces")).data); } catch { setTraces([]); }
    setLoading(false);
  }, []);
  useEffect(() => { load(); }, [load]);
  return (
    <Card title="Agent Traces" action={<Btn onClick={load} disabled={loading}>{loading ? "..." : "Refresh"}</Btn>}>
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {traces.length === 0 && <p className="text-gray-500 text-sm">No traces yet</p>}
        {traces.map((t, i) => (
          <div key={i} className="bg-gray-900 rounded p-2 text-xs">
            <div className="flex justify-between mb-1">
              <span className="text-blue-400 font-mono">{t.agent}</span>
              <span className="text-gray-500">{String(t.ts || "").slice(0, 19)}</span>
            </div>
            <div className="text-gray-300">{t.action}</div>
            {t.detail && <div className="text-gray-500 mt-1 truncate">{JSON.stringify(t.detail)}</div>}
          </div>
        ))}
      </div>
    </Card>
  );
}
function LogsTab() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState("");
  const load = useCallback(async () => {
    setLoading(true);
    try { setLogs((await api.get("/debug/logs")).data); } catch { setLogs([]); }
    setLoading(false);
  }, []);
  useEffect(() => { load(); }, [load]);
  const filtered = filter
    ? logs.filter(l => (l.endpoint || "").includes(filter) || (l.method || "").includes(filter))
    : logs;
  return (
    <Card title="Request Logs"
      action={
        <div className="flex gap-2">
          <input value={filter} onChange={e => setFilter(e.target.value)} placeholder="Filter..."
            className="bg-gray-700 text-gray-200 text-xs px-2 py-1 rounded border border-gray-600 w-32" />
          <Btn onClick={load} disabled={loading}>{loading ? "..." : "Refresh"}</Btn>
        </div>
      }>
      <div className="overflow-x-auto max-h-96 overflow-y-auto">
        <table className="w-full text-xs">
          <thead className="text-gray-400 border-b border-gray-700">
            <tr>
              <th className="text-left py-1 pr-3">Time</th>
              <th className="text-left py-1 pr-3">Method</th>
              <th className="text-left py-1 pr-3">Endpoint</th>
              <th className="text-right py-1 pr-3">Status</th>
              <th className="text-right py-1">ms</th>
            </tr>
          </thead>
          <tbody>
            {filtered.slice(0, 100).map((l, i) => (
              <tr key={i} className="border-b border-gray-800 hover:bg-gray-800">
                <td className="py-1 pr-3 text-gray-500 font-mono">{String(l.ts || "").slice(11, 19)}</td>
                <td className="py-1 pr-3 text-blue-400">{l.method}</td>
                <td className="py-1 pr-3 text-gray-300 font-mono truncate max-w-xs">{l.endpoint}</td>
                <td className={`py-1 pr-3 text-right font-mono ${l.status >= 400 ? "text-red-400" : "text-green-400"}`}>{l.status}</td>
                <td className="py-1 text-right text-gray-400">{l.duration_ms}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && <p className="text-gray-500 text-sm py-2">No logs</p>}
      </div>
    </Card>
  );
}
function ScannerTab() {
  const [scan, setScan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [code, setCode] = useState("");
  const [fixResult, setFixResult] = useState(null);
  const [fixing, setFixing] = useState(false);
  const [packages, setPackages] = useState(null);
  const [installing, setInstalling] = useState("");

  const runScan = useCallback(async () => {
    setLoading(true);
    try { setScan((await api.get("/debug/scan")).data); } catch { setScan(null); }
    setLoading(false);
  }, []);

  const fixCode = useCallback(async () => {
    if (!code.trim()) return;
    setFixing(true);
    try { setFixResult((await api.post("/debug/fix-code", { code })).data); } catch { setFixResult(null); }
    setFixing(false);
  }, [code]);

  const loadPackages = useCallback(async () => {
    try { setPackages((await api.get("/debug/packages")).data); } catch {}
  }, []);

  const installPkg = useCallback(async (pkg) => {
    setInstalling(pkg);
    try { await api.post("/debug/install", { package: pkg }); await loadPackages(); } catch {}
    setInstalling("");
  }, [loadPackages]);

  useEffect(() => { loadPackages(); }, [loadPackages]);

  return (
    <div className="space-y-4">
      <Card title="Project Scanner" action={<Btn onClick={runScan} disabled={loading} variant="primary">{loading ? "Scanning..." : "Scan Project"}</Btn>}>
        {scan ? (
          <div className="space-y-3">
            <div className="grid grid-cols-3 gap-3 text-center">
              <div><div className="text-xl font-bold text-blue-400">{scan.files_scanned}</div><div className="text-xs text-gray-400">Files</div></div>
              <div><div className="text-xl font-bold text-green-400">{scan.clean_files}</div><div className="text-xs text-gray-400">Clean</div></div>
              <div><div className="text-xl font-bold text-red-400">{scan.syntax_errors}</div><div className="text-xs text-gray-400">Errors</div></div>
            </div>
            {scan.errors?.length > 0 && (
              <div className="space-y-1 max-h-48 overflow-y-auto">
                {scan.errors.map((e, i) => (
                  <div key={i} className="bg-red-900/30 border border-red-800 rounded p-2 text-xs">
                    <div className="text-red-300 font-mono">{e.path}</div>
                    <div className="text-red-400 mt-1">{e.error}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : <p className="text-gray-500 text-sm">Click Scan Project to analyze Python files</p>}
      </Card>

      <Card title="Code Fixer">
        <textarea value={code} onChange={e => setCode(e.target.value)}
          placeholder="Paste Python code to fix..."
          className="w-full h-32 bg-gray-900 text-gray-200 font-mono text-xs p-2 rounded border border-gray-700 resize-none" />
        <div className="flex gap-2 mt-2">
          <Btn onClick={fixCode} disabled={fixing || !code.trim()} variant="primary">{fixing ? "Fixing..." : "Fix Code"}</Btn>
          {fixResult && <Badge ok={fixResult.syntax_ok} label={fixResult.syntax_ok ? "Syntax OK" : "Syntax Error"} />}
        </div>
        {fixResult?.diff && (
          <pre className="mt-3 bg-gray-900 rounded p-2 text-xs font-mono overflow-x-auto max-h-48 overflow-y-auto text-gray-300">
            {fixResult.diff}
          </pre>
        )}
      </Card>

      <Card title="Package Status" action={<Btn onClick={loadPackages}>Refresh</Btn>}>
        {packages ? (
          <div className="space-y-2">
            <div className="flex flex-wrap gap-1">
              {(packages.installed || []).map(p => <Badge key={p} ok={true} label={p} />)}
            </div>
            {(packages.missing || []).length > 0 && (
              <div>
                <p className="text-xs text-red-400 mb-1">Missing:</p>
                <div className="flex flex-wrap gap-1">
                  {packages.missing.map(p => (
                    <button key={p} onClick={() => installPkg(p)} disabled={installing === p}
                      className="px-2 py-0.5 rounded text-xs bg-red-900 text-red-300 hover:bg-red-800 disabled:opacity-50">
                      {installing === p ? "Installing..." : `+ ${p}`}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : <p className="text-gray-500 text-sm">Loading...</p>}
      </Card>
    </div>
  );
}
function PerformanceTab() {
  const [metrics, setMetrics] = useState(null);
  const [bgStatus, setBgStatus] = useState(null);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [actionMsg, setActionMsg] = useState("");

  const loadAll = useCallback(async () => {
    setLoading(true);
    try {
      const [m, bg, ev] = await Promise.all([
        api.get("/debug/performance"),
        api.get("/debug/background/status"),
        api.get("/debug/background/events"),
      ]);
      setMetrics(m.data);
      setBgStatus(bg.data);
      setEvents(ev.data?.events || []);
    } catch {}
    setLoading(false);
  }, []);

  useEffect(() => {
    loadAll();
    const t = setInterval(loadAll, 10000);
    return () => clearInterval(t);
  }, [loadAll]);

  const doAction = useCallback(async (action) => {
    try {
      const r = await api.post("/debug/performance-action", { action });
      setActionMsg(r.data?.message || "Done");
      setTimeout(() => setActionMsg(""), 3000);
      loadAll();
    } catch {}
  }, [loadAll]);

  const startBg = useCallback(async () => {
    try { await api.post("/debug/background/start"); loadAll(); } catch {}
  }, [loadAll]);

  const stopBg = useCallback(async () => {
    try { await api.post("/debug/background/stop"); loadAll(); } catch {}
  }, [loadAll]);

  const statusColor = (s) => s === "running" ? "text-green-400" : "text-red-400";

  return (
    <div className="space-y-4">
      <Card title="Live Metrics" action={<Btn onClick={loadAll} disabled={loading}>{loading ? "..." : "Refresh"}</Btn>}>
        {metrics ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div><div className="text-2xl font-bold text-blue-400">{metrics.memory_mb ?? "—"}</div><div className="text-xs text-gray-400">Memory MB</div></div>
            <div><div className="text-2xl font-bold text-yellow-400">{metrics.cpu_percent ?? "—"}</div><div className="text-xs text-gray-400">CPU %</div></div>
            <div><div className="text-2xl font-bold text-purple-400">{metrics.memory_percent ?? "—"}</div><div className="text-xs text-gray-400">Mem %</div></div>
            <div><div className="text-2xl font-bold text-green-400">{metrics.uptime}</div><div className="text-xs text-gray-400">Uptime</div></div>
          </div>
        ) : <p className="text-gray-500 text-sm">Loading metrics...</p>}
      </Card>

      <Card title="Background Services">
        {bgStatus ? (
          <div className="space-y-3">
            <div className="grid grid-cols-3 gap-3">
              {[
                ["Performance Agent", bgStatus.performance_agent],
                ["Report Scheduler", bgStatus.report_scheduler],
                ["Geo Stream", bgStatus.geo_stream],
              ].map(([name, status]) => (
                <div key={name} className="bg-gray-900 rounded p-3 text-center">
                  <div className={`text-sm font-semibold ${statusColor(status)}`}>{(status || "unknown").toUpperCase()}</div>
                  <div className="text-xs text-gray-400 mt-1">{name}</div>
                </div>
              ))}
            </div>
            {bgStatus.metrics && (
              <div className="flex gap-4 text-xs text-gray-400">
                <span>Uptime: <span className="text-gray-200">{bgStatus.metrics.uptime}</span></span>
                {bgStatus.metrics.memory_mb && <span>Mem: <span className="text-gray-200">{bgStatus.metrics.memory_mb}MB</span></span>}
                {bgStatus.metrics.cpu_percent !== undefined && <span>CPU: <span className="text-gray-200">{bgStatus.metrics.cpu_percent}%</span></span>}
              </div>
            )}
            <div className="flex gap-2">
              <Btn onClick={startBg} variant="success">Start All</Btn>
              <Btn onClick={stopBg} variant="danger">Stop All</Btn>
            </div>
          </div>
        ) : <p className="text-gray-500 text-sm">Loading...</p>}
      </Card>

      <Card title="Maintenance">
        <div className="flex flex-wrap gap-2">
          <Btn onClick={() => doAction("force_gc")} variant="primary">Force GC</Btn>
          <Btn onClick={() => doAction("clear_caches")}>Clear Caches</Btn>
          <Btn onClick={() => doAction("vacuum_db")}>Vacuum DB</Btn>
        </div>
        {actionMsg && <p className="mt-2 text-sm text-green-400">{actionMsg}</p>}
      </Card>

      <Card title="Performance Agent Events">
        <div className="space-y-1 max-h-64 overflow-y-auto">
          {events.length === 0 && <p className="text-gray-500 text-sm">No events yet — agent runs every 30s</p>}
          {events.map((e, i) => (
            <div key={i} className={`flex justify-between text-xs rounded px-2 py-1 ${
              e.level === "ERROR" ? "bg-red-900/30 text-red-300" :
              e.level === "WARN" ? "bg-yellow-900/30 text-yellow-300" :
              "bg-gray-900 text-gray-300"
            }`}>
              <span>{e.message}</span>
              <span className="text-gray-500 ml-4 shrink-0">{String(e.ts || "").slice(11, 19)}</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
function WatcherTab() {
  const [running, setRunning] = useState(false);
  const [events, setEvents]   = useState([]);
  const [loading, setLoading] = useState(false);
  const intervalRef = useRef(null);

  const load = useCallback(async () => {
    try {
      const r = await api.get("/debug/watcher-events");
      setEvents(r.data?.events || []);
      setRunning(r.data?.running || false);
    } catch {}
  }, []);

  useEffect(() => {
    load();
    return () => clearInterval(intervalRef.current);
  }, [load]);

  useEffect(() => {
    if (running) {
      intervalRef.current = setInterval(load, 3000);
    } else {
      clearInterval(intervalRef.current);
    }
    return () => clearInterval(intervalRef.current);
  }, [running, load]);

  const startWatcher = async () => {
    setLoading(true);
    try { await api.post("/debug/watcher/start"); setRunning(true); await load(); } catch {}
    setLoading(false);
  };

  const stopWatcher = async () => {
    setLoading(true);
    try { await api.post("/debug/watcher/stop"); setRunning(false); await load(); } catch {}
    setLoading(false);
  };

  const clearEvents = async () => {
    try { await api.post("/debug/watcher/clear"); setEvents([]); } catch {}
  };

  return (
    <div className="space-y-4">
      <Card title="Live File Watcher"
        action={
          <div className="flex items-center gap-2">
            <div className={`flex items-center gap-1.5 text-xs font-semibold ${running ? "text-green-400" : "text-gray-500"}`}>
              <span className={`w-2 h-2 rounded-full ${running ? "bg-green-400 animate-pulse" : "bg-gray-600"}`} />
              {running ? "RUNNING" : "STOPPED"}
            </div>
          </div>
        }>
        <p className="text-gray-500 text-xs mb-3">Monitors Python files for changes. Requires <code className="text-blue-400">watchdog</code> package.</p>
        <div className="flex gap-2 flex-wrap">
          <Btn onClick={startWatcher} disabled={loading || running} variant="success">▶ Start Watcher</Btn>
          <Btn onClick={stopWatcher} disabled={loading || !running} variant="danger">⏹ Stop Watcher</Btn>
          <Btn onClick={clearEvents}>Clear Events</Btn>
          <Btn onClick={load}>↺ Refresh</Btn>
        </div>
      </Card>

      <Card title={`Events (${events.length})`}>
        <div className="space-y-1 max-h-96 overflow-y-auto">
          {events.length === 0 && <p className="text-gray-500 text-sm">No events yet — start the watcher and edit a Python file.</p>}
          {events.map((e, i) => (
            <div key={i} className={`rounded px-3 py-2 text-xs ${
              e.event_type === "error" ? "bg-red-900/30 text-red-300" :
              e.event_type === "started" || e.event_type === "stopped" ? "bg-blue-900/30 text-blue-300" :
              e.confidence < 0.5 ? "bg-yellow-900/30 text-yellow-300" :
              "bg-gray-900 text-gray-300"
            }`}>
              <div className="flex justify-between items-start">
                <span className="font-mono truncate max-w-xs">{e.filename}</span>
                <div className="flex items-center gap-2 ml-2 shrink-0">
                  <span className="text-gray-500">{String(e.ts || "").slice(11, 19)}</span>
                  <span className={`px-1.5 py-0.5 rounded text-xs ${
                    e.event_type === "modified" ? "bg-blue-900/50 text-blue-300" :
                    e.event_type === "created" ? "bg-green-900/50 text-green-300" :
                    "bg-gray-700 text-gray-400"
                  }`}>{e.event_type}</span>
                </div>
              </div>
              {e.diff && <div className="mt-1 text-red-400 text-xs truncate">{e.diff}</div>}
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
