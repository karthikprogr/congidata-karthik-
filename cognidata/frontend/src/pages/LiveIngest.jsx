import { useState, useEffect, useRef, useCallback } from "react";
import { api } from "../api/client";

// ── Styles ────────────────────────────────────────────────────────────────────
const S = {
  page: { padding: 24, background: "#09090b", minHeight: "100vh", color: "#e4e4e7" },
  card: { background: "#18181b", border: "1px solid rgba(255,255,255,.08)", borderRadius: 12, padding: 20, marginBottom: 16 },
  h1: { fontSize: 22, fontWeight: 700, margin: "0 0 2px", color: "#fff" },
  sub: { color: "#71717a", fontSize: 13, margin: "0 0 20px" },
  h2: { fontSize: 14, fontWeight: 600, margin: "0 0 12px", color: "#a1a1aa", textTransform: "uppercase", letterSpacing: 1 },
  input: { background: "#09090b", border: "1px solid rgba(255,255,255,.1)", borderRadius: 8, padding: "8px 12px", color: "#e4e4e7", fontSize: 13, width: "100%", boxSizing: "border-box" },
  btn: { padding: "8px 16px", borderRadius: 8, border: "none", background: "linear-gradient(135deg,#6366f1,#8b5cf6)", color: "#fff", fontSize: 13, fontWeight: 600, cursor: "pointer" },
  btnSm: { padding: "5px 10px", borderRadius: 6, border: "none", fontSize: 12, fontWeight: 600, cursor: "pointer" },
  code: { background: "#09090b", border: "1px solid rgba(255,255,255,.08)", borderRadius: 8, padding: 14, fontFamily: "monospace", fontSize: 12, color: "#a1a1aa", whiteSpace: "pre-wrap", wordBreak: "break-all" },
  dot: (on) => ({ width: 8, height: 8, borderRadius: "50%", background: on ? "#4ade80" : "#52525b", display: "inline-block", marginRight: 6, boxShadow: on ? "0 0 6px #4ade80" : "none" }),
};

// Stream colors palette
const PALETTE = ["#f43f5e","#ec4899","#a855f7","#6366f1","#3b82f6","#06b6d4","#10b981","#f59e0b"];

// ── Streaming Particle Canvas ─────────────────────────────────────────────────
function StreamCanvas({ streams, streamData, paused }) {
  const canvasRef  = useRef(null);
  const stateRef   = useRef({ particles: {}, lastCount: {}, initialized: {} });
  const pausedRef  = useRef(paused);
  const streamsRef = useRef(streams);
  const dataRef    = useRef(streamData);

  useEffect(() => { pausedRef.current = paused; }, [paused]);
  useEffect(() => { streamsRef.current = streams; }, [streams]);
  useEffect(() => { dataRef.current = streamData; }, [streamData]);

  // Spawn particles for new rows
  useEffect(() => {
    const { particles, lastCount, initialized } = stateRef.current;
    streams.forEach((st, idx) => {
      const sid   = st.stream_id;
      const count = dataRef.current[sid]?.row_count || 0;
      if (!initialized[sid]) {
        initialized[sid] = true;
        lastCount[sid]   = count;
        return;
      }
      const newRows = count - (lastCount[sid] || 0);
      if (newRows > 0 && !pausedRef.current) {
        if (!particles[sid]) particles[sid] = [];
        const color = PALETTE[idx % PALETTE.length];
        // Spawn multiple particles per new row for density
        const spawnCount = Math.min(newRows * 3, 60);
        for (let i = 0; i < spawnCount; i++) {
          particles[sid].push({
            x: 8 + Math.random() * 4,
            y: (Math.random() - 0.5) * 6,
            vx: 0.8 + Math.random() * 1.4,   // slow — they accumulate
            vy: (Math.random() - 0.5) * 0.3,
            alpha: 0.85 + Math.random() * 0.15,
            size: 1.5 + Math.random() * 2,
            color,
            lane: idx,
          });
        }
        // Cap per stream to avoid memory bloat
        if (particles[sid].length > 4000) {
          particles[sid] = particles[sid].slice(-4000);
        }
      }
      lastCount[sid] = count;
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(streams.map(s => dataRef.current[s.stream_id]?.row_count || 0))]);

  // Single persistent RAF loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const { particles } = stateRef.current;

    const resize = () => {
      canvas.width  = canvas.offsetWidth  || 860;
      canvas.height = canvas.offsetHeight || 340;
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(canvas);

    let raf;
    const draw = () => {
      const W = canvas.width, H = canvas.height;
      const streams = streamsRef.current;
      const streamData = dataRef.current;
      const laneCount = Math.max(streams.length, 1);
      const laneH = (H - 50) / laneCount; // reserve 50px for histogram

      // Very subtle fade — keeps old particles visible (trail effect)
      ctx.fillStyle = "rgba(9,9,11,0.06)";
      ctx.fillRect(0, 0, W, H - 50);

      // Clear histogram area fully each frame
      ctx.fillStyle = "#09090b";
      ctx.fillRect(0, H - 50, W, 50);

      // Lane separator lines
      streams.forEach((_, idx) => {
        if (idx === 0) return;
        const y = laneH * idx;
        ctx.strokeStyle = "rgba(255,255,255,0.04)";
        ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
      });

      // "Now" vertical line on right
      ctx.strokeStyle = "rgba(255,255,255,0.12)";
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(W - 2, 0); ctx.lineTo(W - 2, H - 50); ctx.stroke();
      ctx.fillStyle = "#52525b";
      ctx.font = "10px sans-serif";
      ctx.fillText("Now", W - 30, H - 54);

      // Draw particles
      if (!pausedRef.current) {
        Object.entries(particles).forEach(([sid, parts]) => {
          const idx = streams.findIndex(s => s.stream_id === sid);
          if (idx < 0) return;
          const cy = laneH * idx + laneH / 2;

          for (let i = parts.length - 1; i >= 0; i--) {
            const p = parts[i];
            p.x  += p.vx;
            p.y  += p.vy;
            // Very slow fade — particles persist a long time
            p.alpha -= 0.0008;
            if (p.x > W - 2 || p.alpha <= 0.02) { parts.splice(i, 1); continue; }

            // Color shifts red→purple as particle ages (moves right)
            const progress = p.x / W; // 0=left, 1=right
            const r = Math.floor(220 - progress * 80);
            const g = Math.floor(50  + progress * 20);
            const b = Math.floor(100 + progress * 120);
            const hex = Math.floor(p.alpha * 255).toString(16).padStart(2, "0");

            ctx.beginPath();
            ctx.arc(p.x, cy + p.y, p.size, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${r},${g},${b},${p.alpha})`;
            ctx.fill();
          }
        });
      }

      // Lane labels (drawn on top of particles)
      streams.forEach((st, idx) => {
        const color = PALETTE[idx % PALETTE.length];
        const cy = laneH * idx + laneH / 2;
        // Dot with glow
        ctx.shadowColor = color;
        ctx.shadowBlur  = 10;
        ctx.beginPath();
        ctx.arc(16, cy, 7, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
        ctx.shadowBlur = 0;
        // Label
        ctx.fillStyle = "#d4d4d8";
        ctx.font = "bold 12px sans-serif";
        ctx.fillText(st.name, 30, cy + 4);
      });

      // Histogram bar at bottom
      const histH = 46, histY = H - histH;
      const barW = Math.max(Math.floor((W - 10) / 60), 4);
      streams.forEach((st, idx) => {
        const color = PALETTE[idx % PALETTE.length];
        const eps   = streamData[st.stream_id]?._eps || 0;
        // Draw a mini bar chart using particle density as proxy
        const parts = particles[st.stream_id] || [];
        // Divide canvas into 60 time buckets
        const buckets = new Array(60).fill(0);
        parts.forEach(p => {
          const b = Math.min(59, Math.floor((p.x / W) * 60));
          buckets[b]++;
        });
        const maxB = Math.max(...buckets, 1);
        buckets.forEach((cnt, b) => {
          const bh = Math.floor((cnt / maxB) * (histH - 6));
          if (bh < 1) return;
          const bx = 5 + b * barW;
          ctx.fillStyle = color + "cc";
          ctx.fillRect(bx, histY + histH - bh, Math.max(barW - 1, 2), bh);
        });
      });

      raf = requestAnimationFrame(draw);
    };

    raf = requestAnimationFrame(draw);
    return () => { cancelAnimationFrame(raf); ro.disconnect(); };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{ width: "100%", height: 340, borderRadius: 10, display: "block", background: "#09090b" }}
    />
  );
}

// ── KPI Card ──────────────────────────────────────────────────────────────────
function KpiCard({ stream, data, color, onGetSample }) {
  const eps = data?._eps ?? 0;
  const avgSize = data?._avgSize ?? 0;
  const total = data?.row_count ?? 0;
  return (
    <div style={{ background: "#18181b", border: `1px solid ${color}33`, borderRadius: 10, padding: "14px 16px", minWidth: 160, flex: "1 1 160px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 10 }}>
        <span style={{ width: 10, height: 10, borderRadius: "50%", background: color, display: "inline-block", boxShadow: `0 0 8px ${color}` }} />
        <span style={{ fontWeight: 600, fontSize: 13, color: "#e4e4e7" }}>{stream.name}</span>
      </div>
      <button onClick={() => onGetSample(stream)} style={{ ...S.btnSm, background: "rgba(255,255,255,.06)", color: "#a1a1aa", border: "1px solid rgba(255,255,255,.1)", marginBottom: 10, width: "100%" }}>
        Get Sample
      </button>
      <div style={{ fontSize: 11, color: "#52525b", marginBottom: 2 }}>Throughput</div>
      <div style={{ fontSize: 20, fontWeight: 700, color: "#fff", marginBottom: 8 }}>{eps.toFixed(0)} <span style={{ fontSize: 11, color: "#71717a" }}>eps</span></div>
      <div style={{ fontSize: 11, color: "#52525b", marginBottom: 2 }}>Average event size</div>
      <div style={{ fontSize: 20, fontWeight: 700, color: "#fff" }}>{avgSize.toFixed(0)} <span style={{ fontSize: 11, color: "#71717a" }}>bytes</span></div>
      <div style={{ fontSize: 11, color: "#52525b", marginTop: 8 }}>Total rows: <span style={{ color: "#a1a1aa" }}>{total.toLocaleString()}</span></div>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────
export default function LiveIngest() {
  const [streams, setStreams] = useState([]);
  const [streamData, setStreamData] = useState({});
  const [newName, setNewName] = useState("");
  const [paused, setPaused] = useState(false);
  const [tab, setTab] = useState("live");
  const [testPayload, setTestPayload] = useState('{"revenue": 1200, "region": "APAC", "units": 45}');
  const [selectedStream, setSelectedStream] = useState(null);
  const [sending, setSending] = useState(false);
  const pollRef = useRef(null);
  const epsRef = useRef({}); // stream_id -> {count, ts}

  const load = useCallback(async () => {
    const data = await api.get("/ingest/streams").then(r => r.data).catch(() => []);
    setStreams(data);
    if (data.length && !selectedStream) setSelectedStream(data[0]);
  }, [selectedStream]);

  const pollAll = useCallback(async (streamList) => {
    if (!streamList.length) return;
    const results = await Promise.all(
      streamList.map(s => api.get(`/ingest/streams/${s.stream_id}`).then(r => r.data).catch(() => null))
    );
    setStreamData(prev => {
      const next = { ...prev };
      results.forEach((d, i) => {
        if (!d) return;
        const sid = streamList[i].stream_id;
        const now = Date.now();
        const ep = epsRef.current[sid];
        const prevCount = ep?.count ?? null;
        const prevTs = ep?.ts ?? now;
        const dt = (now - prevTs) / 1000 || 1;
        // Only compute eps if we have a previous reading
        const eps = prevCount !== null ? Math.max(0, (d.row_count - prevCount) / dt) : 0;
        epsRef.current[sid] = { count: d.row_count, ts: now };
        // Estimate avg event size from schema keys
        const schemaKeys = Object.keys(d.schema || {}).length;
        const avgSize = schemaKeys * 24 + 40; // rough estimate
        next[sid] = { ...d, _eps: eps, _avgSize: avgSize };
      });
      return next;
    });
  }, []);

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    if (!streams.length) return;
    clearInterval(pollRef.current);
    pollRef.current = setInterval(() => {
      if (!paused) pollAll(streams);
    }, 1500);
    return () => clearInterval(pollRef.current);
  }, [streams, paused, pollAll]);

  const createStream = async () => {
    if (!newName.trim()) return;
    await api.post("/ingest/streams", { name: newName }).catch(() => {});
    setNewName("");
    await load();
  };

  const del = async (stream_id) => {
    await api.delete(`/ingest/streams/${stream_id}`).catch(() => {});
    setStreams(p => p.filter(s => s.stream_id !== stream_id));
    setStreamData(p => { const n = { ...p }; delete n[stream_id]; return n; });
  };

  const sendTest = async () => {
    if (!selectedStream) return;
    setSending(true);
    try {
      const payload = JSON.parse(testPayload);
      await api.post(`/ingest/${selectedStream.stream_id}`, payload, {
        headers: { "X-Stream-Key": selectedStream.api_key }
      });
      await pollAll(streams);
    } catch { alert("Invalid JSON or send failed"); }
    setSending(false);
  };

  const getSample = async (stream) => {
    const d = streamData[stream.stream_id];
    if (d?.recent?.length) {
      alert(JSON.stringify(d.recent[d.recent.length - 1], null, 2));
    } else {
      alert("No data yet in this stream.");
    }
  };

  const loadAsDataset = async (stream) => {
    await api.post(`/ingest/streams/${stream.stream_id}/load`).catch(() => {});
    alert(`Stream "${stream.name}" loaded as active dataset.`);
  };

  return (
    <div style={S.page}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
        <div>
          <h1 style={S.h1}>📡 Live Data Ingest</h1>
          <p style={S.sub}>Real-time streaming visualization — events flow in as particles, KPIs update live.</p>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <span style={{ ...S.dot(true), width: 8, height: 8 }} />
          <span style={{ fontSize: 12, color: "#4ade80", marginRight: 8 }}>Connected</span>
          <button onClick={() => setPaused(p => !p)} style={{ ...S.btnSm, background: paused ? "rgba(251,191,36,.15)" : "rgba(255,255,255,.06)", color: paused ? "#fbbf24" : "#a1a1aa", border: "1px solid rgba(255,255,255,.1)" }}>
            {paused ? "▶ Resume" : "⏸ Pause"}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
        {[["live","📡 Live View"],["manage","⚙ Manage"],["test","🧪 Test Send"],["code","💻 Code"]].map(([t, label]) => (
          <button key={t} onClick={() => setTab(t)} style={{ ...S.btnSm, background: tab === t ? "rgba(99,102,241,.2)" : "rgba(255,255,255,.05)", color: tab === t ? "#818cf8" : "#71717a", border: `1px solid ${tab === t ? "rgba(99,102,241,.4)" : "rgba(255,255,255,.08)"}` }}>
            {label}
          </button>
        ))}
      </div>

      {/* ── Live View ── */}
      {tab === "live" && (
        <>
          {streams.length === 0 ? (
            <div style={{ ...S.card, textAlign: "center", color: "#52525b", padding: 60 }}>
              No streams yet. Go to <strong style={{ color: "#818cf8" }}>Manage</strong> to create one.
            </div>
          ) : (
            <>
              {/* Particle canvas */}
              <div style={{ ...S.card, padding: 0, overflow: "hidden", position: "relative" }}>
                <div style={{ position: "absolute", top: 12, left: 16, fontSize: 11, color: "#52525b", zIndex: 1 }}>Incoming events</div>
                {paused && <div style={{ position: "absolute", top: 12, right: 16, fontSize: 11, color: "#fbbf24", zIndex: 1 }}>⏸ Paused</div>}
                <StreamCanvas streams={streams} streamData={streamData} paused={paused} />
              </div>

              {/* KPI cards */}
              <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                {streams.map((st, idx) => (
                  <KpiCard key={st.stream_id} stream={st} data={streamData[st.stream_id]} color={PALETTE[idx % PALETTE.length]} onGetSample={getSample} />
                ))}
              </div>
            </>
          )}
        </>
      )}

      {/* ── Manage ── */}
      {tab === "manage" && (
        <div style={{ display: "grid", gridTemplateColumns: "280px 1fr", gap: 16 }}>
          <div>
            <div style={S.card}>
              <h2 style={S.h2}>New Stream</h2>
              <input style={{ ...S.input, marginBottom: 10 }} placeholder="Stream name" value={newName} onChange={e => setNewName(e.target.value)} onKeyDown={e => e.key === "Enter" && createStream()} />
              <button style={{ ...S.btn, width: "100%" }} onClick={createStream}>+ Create Stream</button>
            </div>
            {streams.map((st, idx) => (
              <div key={st.stream_id} onClick={() => setSelectedStream(st)} style={{ ...S.card, cursor: "pointer", border: selectedStream?.stream_id === st.stream_id ? "1px solid rgba(99,102,241,.5)" : "1px solid rgba(255,255,255,.08)", marginBottom: 8 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <span style={{ width: 8, height: 8, borderRadius: "50%", background: PALETTE[idx % PALETTE.length], display: "inline-block" }} />
                    <span style={{ fontWeight: 600, fontSize: 13 }}>{st.name}</span>
                  </div>
                  <button style={{ ...S.btnSm, background: "rgba(239,68,68,.1)", color: "#f87171" }} onClick={e => { e.stopPropagation(); del(st.stream_id); }}>✕</button>
                </div>
                <div style={{ fontSize: 11, color: "#52525b", marginTop: 4 }}>{streamData[st.stream_id]?.row_count ?? st.row_count} rows</div>
              </div>
            ))}
          </div>

          <div>
            {selectedStream && streamData[selectedStream.stream_id] ? (() => {
              const d = streamData[selectedStream.stream_id];
              return (
                <>
                  <div style={S.card}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 14 }}>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: 16, color: "#fff" }}>{d.name}</div>
                        <div style={{ fontSize: 12, color: "#52525b", marginTop: 2 }}>{d.row_count} rows · {Object.keys(d.schema || {}).length} fields</div>
                      </div>
                      <button style={{ ...S.btnSm, background: "rgba(99,102,241,.15)", color: "#818cf8" }} onClick={() => loadAsDataset(selectedStream)}>📊 Load as Dataset</button>
                    </div>
                    <div style={{ fontSize: 12, color: "#71717a", marginBottom: 6 }}>Ingest endpoint:</div>
                    <div style={{ ...S.code, marginBottom: 12 }}>POST /api/ingest/{d.stream_id}{"\n"}X-Stream-Key: {d.api_key}</div>
                    <div style={{ fontSize: 12, color: "#71717a", marginBottom: 6 }}>Schema:</div>
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                      {Object.entries(d.schema || {}).map(([k, v]) => (
                        <span key={k} style={{ background: "rgba(99,102,241,.1)", color: "#818cf8", padding: "2px 8px", borderRadius: 4, fontSize: 11 }}>{k}: {v}</span>
                      ))}
                    </div>
                  </div>
                  <div style={S.card}>
                    <h2 style={S.h2}>Recent Rows</h2>
                    <div style={{ overflowX: "auto" }}>
                      {d.recent?.length > 0 ? (
                        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                          <thead><tr>{Object.keys(d.recent[0]).map(k => <th key={k} style={{ textAlign: "left", padding: "6px 10px", color: "#71717a", borderBottom: "1px solid rgba(255,255,255,.06)" }}>{k}</th>)}</tr></thead>
                          <tbody>{[...d.recent].reverse().map((row, i) => (
                            <tr key={i} style={{ borderBottom: "1px solid rgba(255,255,255,.04)" }}>
                              {Object.values(row).map((v, j) => <td key={j} style={{ padding: "6px 10px", color: "#e4e4e7" }}>{String(v).slice(0, 30)}</td>)}
                            </tr>
                          ))}</tbody>
                        </table>
                      ) : <div style={{ color: "#52525b", textAlign: "center", padding: 20 }}>No rows yet.</div>}
                    </div>
                  </div>
                </>
              );
            })() : (
              <div style={{ ...S.card, textAlign: "center", color: "#52525b", padding: 60 }}>Select a stream to view details</div>
            )}
          </div>
        </div>
      )}

      {/* ── Test Send ── */}
      {tab === "test" && (
        <div style={S.card}>
          <h2 style={S.h2}>Test Send</h2>
          <div style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 12, color: "#71717a", marginBottom: 6 }}>Target Stream</div>
            <select style={{ ...S.input, width: "auto" }} value={selectedStream?.stream_id || ""} onChange={e => setSelectedStream(streams.find(s => s.stream_id === e.target.value))}>
              <option value="">— select stream —</option>
              {streams.map(s => <option key={s.stream_id} value={s.stream_id}>{s.name}</option>)}
            </select>
          </div>
          <div style={{ fontSize: 12, color: "#71717a", marginBottom: 6 }}>JSON Payload</div>
          <textarea style={{ ...S.input, height: 120, fontFamily: "monospace", resize: "vertical" }} value={testPayload} onChange={e => setTestPayload(e.target.value)} />
          <button style={{ ...S.btn, marginTop: 12 }} onClick={sendTest} disabled={sending || !selectedStream}>
            {sending ? "Sending…" : "📤 Send Row"}
          </button>
        </div>
      )}

      {/* ── Code ── */}
      {tab === "code" && (
        <div style={S.card}>
          <h2 style={S.h2}>Integration Examples</h2>
          <div style={{ fontSize: 13, color: "#71717a", marginBottom: 8 }}>Python</div>
          <div style={S.code}>{`import requests, time, random

STREAM_ID = "YOUR_STREAM_ID"
API_KEY   = "YOUR_API_KEY"
URL       = f"http://localhost:8000/api/ingest/{STREAM_ID}"

# Continuous stream simulation
while True:
    requests.post(URL,
        json={"revenue": random.randint(500,5000), "region": "APAC", "units": random.randint(1,100)},
        headers={"X-Stream-Key": API_KEY}
    )
    time.sleep(0.5)`}</div>
          <div style={{ fontSize: 13, color: "#71717a", margin: "16px 0 8px" }}>curl (batch)</div>
          <div style={S.code}>{`curl -X POST http://localhost:8000/api/ingest/YOUR_STREAM_ID \\
  -H "X-Stream-Key: YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '[{"revenue":1200,"region":"APAC"},{"revenue":850,"region":"EU"}]'`}</div>
        </div>
      )}
    </div>
  );
}
