/**
 * 3D Real-World Globe — Pure Three.js (no three-globe dependency)
 * NASA Blue Marble texture, data spikes, click tooltips
 */
import { useEffect, useRef, useState, useCallback } from "react";
import { api } from "../api/client";

const EARTH_DAY   = "https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg";
const EARTH_NIGHT = "https://unpkg.com/three-globe/example/img/earth-night.jpg";

const SCALES = {
  Viridis: [[68,1,84],[49,104,142],[53,183,121],[253,231,37]],
  Plasma:  [[13,8,135],[185,50,137],[244,136,73],[240,249,33]],
  Heat:    [[0,0,255],[0,200,100],[255,165,0],[255,0,0]],
  Neon:    [[0,255,200],[0,150,255],[180,0,255],[255,0,100]],
};

function sampleColor(scale, t) {
  const stops = SCALES[scale] || SCALES.Viridis;
  const i = Math.min(stops.length - 2, Math.floor(t * (stops.length - 1)));
  const f = t * (stops.length - 1) - i;
  const a = stops[i], b = stops[i + 1] || stops[i];
  return [(a[0]+(b[0]-a[0])*f)/255, (a[1]+(b[1]-a[1])*f)/255, (a[2]+(b[2]-a[2])*f)/255];
}

function latLonToXYZ(lat, lon, r) {
  const phi   = (90 - lat) * (Math.PI / 180);
  const theta = (lon + 180) * (Math.PI / 180);
  return [-r*Math.sin(phi)*Math.cos(theta), r*Math.cos(phi), r*Math.sin(phi)*Math.sin(theta)];
}

export default function Globe3D() {
  const canvasRef  = useRef(null);
  const threeRef   = useRef({});
  const mouse      = useRef({ down: false, x: 0, y: 0, moved: false });
  const rot        = useRef({ x: 0.3, y: 0 });
  const zoom       = useRef(2.8);
  const autoR      = useRef(true);
  const ptsRef     = useRef([]);

  const [cols, setCols]       = useState([]);
  const [numCols, setNumCols] = useState([]);
  const [latCol, setLatCol]   = useState("");
  const [lonCol, setLonCol]   = useState("");
  const [valCol, setValCol]   = useState("");
  const [colorScale, setCS]   = useState("Viridis");
  const [spikeH, setSpikeH]   = useState(0.25);
  const [nightMode, setNight] = useState(false);
  const [autoRot, setAutoRot] = useState(true);
  const [pc, setPc]           = useState(0);
  const [fps, setFps]         = useState(0);
  const [loading, setLoad]    = useState(false);
  const [error, setError]     = useState("");
  const [rendered, setRendered] = useState(false);
  const [tooltip, setTooltip] = useState(null);

  const loadCols = useCallback(() => {
    api.get("/data/info").then(({ data }) => {
      const all = data?.column_names || [];
      const num = data?.numeric_columns || [];
      setCols(all); setNumCols(num);
      const lat = all.find(c => /^lat$/i.test(c)) || all.find(c => /lat/i.test(c)) || "";
      const lon = all.find(c => /^lo?ng?$/i.test(c)) || all.find(c => /lon|lng/i.test(c)) || "";
      if (lat) setLatCol(lat);
      if (lon) setLonCol(lon);
      if (num[0]) setValCol(num[0]);
      if (all.length) setError("");
    }).catch(() => {});
  }, []);

  useEffect(() => { loadCols(); }, []);

  // ── Init Three.js ──────────────────────────────────────────────────────────
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    let raf;

    import("three").then(THREE => {
      const W = canvas.parentElement.offsetWidth  || 900;
      const H = canvas.parentElement.offsetHeight || 600;

      const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
      renderer.setSize(W, H, false);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.setClearColor(0x000010, 1);

      const scene  = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(45, W / H, 0.01, 1000);

      // Stars
      const sp = new Float32Array(9000);
      for (let i = 0; i < 9000; i++) sp[i] = (Math.random() - 0.5) * 400;
      const sg = new THREE.BufferGeometry();
      sg.setAttribute("position", new THREE.BufferAttribute(sp, 3));
      scene.add(new THREE.Points(sg, new THREE.PointsMaterial({ color: 0xffffff, size: 0.25, transparent: true, opacity: 0.7 })));

      // Earth
      const loader = new THREE.TextureLoader();
      loader.setCrossOrigin("anonymous");
      const dayTex   = loader.load(EARTH_DAY);
      const nightTex = loader.load(EARTH_NIGHT);
      const globeGeo = new THREE.SphereGeometry(1, 64, 64);
      const globeMat = new THREE.MeshPhongMaterial({ map: dayTex, specular: new THREE.Color(0x222222), shininess: 10 });
      const globe    = new THREE.Mesh(globeGeo, globeMat);
      scene.add(globe);

      // Atmosphere
      const atmMat = new THREE.MeshBasicMaterial({ color: 0x4488ff, transparent: true, opacity: 0.07, side: THREE.BackSide });
      scene.add(new THREE.Mesh(new THREE.SphereGeometry(1.12, 64, 64), atmMat));

      // Lights
      scene.add(new THREE.AmbientLight(0x334466, 1.2));
      const sun = new THREE.DirectionalLight(0xffffff, 2);
      sun.position.set(5, 3, 5);
      scene.add(sun);

      threeRef.current = { THREE, renderer, scene, camera, globe, globeMat, dayTex, nightTex, spikes: null, dots: null };

      // Animate
      let lastT = performance.now(), frames = 0;
      const animate = () => {
        raf = requestAnimationFrame(animate);
        frames++;
        const now = performance.now();
        if (now - lastT > 1000) { setFps(frames); frames = 0; lastT = now; }

        if (autoR.current) rot.current.y += 0.003;
        globe.rotation.set(rot.current.x, rot.current.y, 0);
        const { spikes, dots } = threeRef.current;
        if (spikes) spikes.rotation.set(rot.current.x, rot.current.y, 0);
        if (dots)   dots.rotation.set(rot.current.x, rot.current.y, 0);

        camera.position.set(0, 0, zoom.current);
        renderer.render(scene, camera);
      };
      animate();

      const onResize = () => {
        const W2 = canvas.parentElement.offsetWidth;
        const H2 = canvas.parentElement.offsetHeight;
        if (W2 > 0 && H2 > 0) {
          renderer.setSize(W2, H2, false);
          camera.aspect = W2 / H2;
          camera.updateProjectionMatrix();
        }
      };
      window.addEventListener("resize", onResize);
      return () => { window.removeEventListener("resize", onResize); };
    });

    return () => { cancelAnimationFrame(raf); };
  }, []);

  // Toggle texture
  useEffect(() => {
    const { globeMat, dayTex, nightTex } = threeRef.current;
    if (!globeMat) return;
    globeMat.map = nightMode ? nightTex : dayTex;
    globeMat.needsUpdate = true;
  }, [nightMode]);

  // Build spikes
  const buildSpikes = useCallback(async () => {
    if (!latCol || !lonCol) return;
    const { THREE, scene } = threeRef.current;
    if (!THREE || !scene) return;
    setLoad(true); setError("");
    try {
      const { data: preview } = await api.get("/data/preview?n=5000");
      const rows = preview.data || [];

      const { spikes: oldS, dots: oldD } = threeRef.current;
      if (oldS) { scene.remove(oldS); oldS.geometry.dispose(); }
      if (oldD) { scene.remove(oldD); oldD.geometry.dispose(); }

      const pts = rows.map(r => ({
        lat: parseFloat(r[latCol]), lon: parseFloat(r[lonCol]),
        val: valCol ? (parseFloat(r[valCol]) || 0) : 1, row: r,
      })).filter(p => !isNaN(p.lat) && !isNaN(p.lon) && Math.abs(p.lat) <= 90 && Math.abs(p.lon) <= 180);

      if (!pts.length) { setError("No valid lat/lon values found"); setLoad(false); return; }

      const vals = pts.map(p => p.val);
      const minV = Math.min(...vals), maxV = Math.max(...vals);
      const norm = v => maxV === minV ? 0.5 : (v - minV) / (maxV - minV);

      const n = pts.length;
      const sPos = new Float32Array(n * 6), sCol = new Float32Array(n * 6);
      const dPos = new Float32Array(n * 3), dCol = new Float32Array(n * 3);

      for (let i = 0; i < n; i++) {
        const t = norm(pts[i].val);
        const h = 0.01 + t * spikeH;
        const [r, g, b] = sampleColor(colorScale, t);
        const [x0,y0,z0] = latLonToXYZ(pts[i].lat, pts[i].lon, 1.005);
        const [x1,y1,z1] = latLonToXYZ(pts[i].lat, pts[i].lon, 1.005 + h);
        sPos.set([x0,y0,z0,x1,y1,z1], i*6);
        sCol.set([r*.2,g*.2,b*.2,r,g,b], i*6);
        dPos.set([x1,y1,z1], i*3);
        dCol.set([r,g,b], i*3);
      }

      const sGeo = new THREE.BufferGeometry();
      sGeo.setAttribute("position", new THREE.BufferAttribute(sPos, 3));
      sGeo.setAttribute("color",    new THREE.BufferAttribute(sCol, 3));
      const spikes = new THREE.LineSegments(sGeo, new THREE.LineBasicMaterial({ vertexColors: true, transparent: true, opacity: 0.9 }));
      spikes.rotation.set(rot.current.x, rot.current.y, 0);
      scene.add(spikes);

      const dGeo = new THREE.BufferGeometry();
      dGeo.setAttribute("position", new THREE.BufferAttribute(dPos, 3));
      dGeo.setAttribute("color",    new THREE.BufferAttribute(dCol, 3));
      const dots = new THREE.Points(dGeo, new THREE.PointsMaterial({ vertexColors: true, size: 0.02, transparent: true, opacity: 1 }));
      dots.rotation.set(rot.current.x, rot.current.y, 0);
      scene.add(dots);

      threeRef.current.spikes = spikes;
      threeRef.current.dots   = dots;
      ptsRef.current = pts;
      setPc(n); setRendered(true);
    } catch(e) { setError(`Error: ${e.message}`); }
    setLoad(false);
  }, [latCol, lonCol, valCol, colorScale, spikeH]);

  // Click raycasting
  const onClick = useCallback(e => {
    if (mouse.current.moved) return;
    const { THREE, camera, dots } = threeRef.current;
    if (!THREE || !camera || !dots || !ptsRef.current.length) return;
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const ndcX =  ((e.clientX - rect.left) / rect.width)  * 2 - 1;
    const ndcY = -((e.clientY - rect.top)  / rect.height) * 2 + 1;
    const ray = new THREE.Raycaster();
    ray.setFromCamera({ x: ndcX, y: ndcY }, camera);
    ray.params.Points.threshold = 0.04;
    const hits = ray.intersectObject(dots);
    if (hits.length) {
      const pt = ptsRef.current[hits[0].index];
      if (pt) setTooltip({ x: e.clientX, y: e.clientY, row: pt.row, lat: pt.lat, lon: pt.lon, val: pt.val });
    } else setTooltip(null);
  }, []);

  const onMouseDown = e => { mouse.current = { down: true, x: e.clientX, y: e.clientY, moved: false }; };
  const onMouseMove = e => {
    if (!mouse.current.down) return;
    const dx = e.clientX - mouse.current.x, dy = e.clientY - mouse.current.y;
    if (Math.abs(dx) > 2 || Math.abs(dy) > 2) mouse.current.moved = true;
    mouse.current.x = e.clientX; mouse.current.y = e.clientY;
    rot.current.y += dx * 0.006;
    rot.current.x = Math.max(-1.4, Math.min(1.4, rot.current.x + dy * 0.006));
  };
  const onMouseUp = () => { mouse.current.down = false; };
  const onWheel   = e => { zoom.current = Math.max(1.3, Math.min(8, zoom.current + e.deltaY * 0.004)); };
  const toggleRot = () => { autoR.current = !autoR.current; setAutoRot(a => !a); };

  const Sel = ({ label, val, set, opts }) => (
    <div style={{ flex: "1 1 130px" }}>
      <div style={S.lbl}>{label}</div>
      {opts.length > 0
        ? <select value={val} onChange={e => set(e.target.value)} style={S.sel} className="globe-sel">
            <option value="">(select)</option>
            {opts.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        : <input value={val} onChange={e => set(e.target.value)} placeholder="type column…" style={S.sel} />
      }
    </div>
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", background: "#000010", overflow: "hidden" }}>
      <style>{`.globe-sel,.globe-sel option{background:#18181b;color:#f4f4f5;color-scheme:dark}`}</style>

      {/* Header */}
      <div style={{ padding: "10px 20px", background: "#0a0a1a", borderBottom: "1px solid rgba(99,102,241,.3)", flexShrink: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10, flexWrap: "wrap" }}>
          <div style={S.icon}>🌍</div>
          <div>
            <div style={S.title}>3D Real-World Globe</div>
            <div style={S.sub}>{pc.toLocaleString()} points · {fps} FPS</div>
          </div>
          <div style={{ marginLeft: "auto", display: "flex", gap: 6, flexWrap: "wrap" }}>
            <button onClick={() => setNight(n => !n)} style={{ ...S.outBtn, color: nightMode ? "#fbbf24" : "#818cf8" }}>
              {nightMode ? "☀️ Day" : "🌙 Night"}
            </button>
            <button onClick={toggleRot} style={{ ...S.outBtn, color: autoRot ? "#4ade80" : "#71717a" }}>
              {autoRot ? "⏸ Pause" : "▶ Rotate"}
            </button>
            <button onClick={loadCols} style={{ ...S.outBtn, fontSize: 11 }}>🔄 Cols</button>
            <button onClick={buildSpikes} disabled={loading || !latCol || !lonCol} style={S.btn}>
              {loading ? "Rendering…" : "🌍 Plot Data"}
            </button>
          </div>
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "flex-end" }}>
          <Sel label="Latitude" val={latCol} set={setLatCol} opts={cols} />
          <Sel label="Longitude" val={lonCol} set={setLonCol} opts={cols} />
          <Sel label="Value (height)" val={valCol} set={setValCol} opts={numCols} />
          <div style={{ flex: "1 1 110px" }}>
            <div style={S.lbl}>Color Scale</div>
            <select value={colorScale} onChange={e => setCS(e.target.value)} style={S.sel} className="globe-sel">
              {Object.keys(SCALES).map(s => <option key={s}>{s}</option>)}
            </select>
          </div>
          <div style={{ flex: "1 1 140px" }}>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={S.lbl}>Spike Height</span>
              <span style={{ fontSize: 10, color: "#6366f1", fontWeight: 700 }}>{spikeH.toFixed(2)}</span>
            </div>
            <input type="range" min={0.02} max={0.8} step={0.02} value={spikeH}
              onChange={e => setSpikeH(Number(e.target.value))}
              style={{ width: "100%", accentColor: "#6366f1" }} />
          </div>
        </div>
      </div>

      {/* Canvas container */}
      <div style={{ flex: 1, position: "relative", overflow: "hidden" }}>
        <canvas
          ref={canvasRef}
          style={{ position: "absolute", top: 0, left: 0, width: "100%", height: "100%", display: "block" }}
          onMouseDown={onMouseDown}
          onMouseMove={onMouseMove}
          onMouseUp={onMouseUp}
          onMouseLeave={onMouseUp}
          onWheel={onWheel}
          onClick={onClick}
          onContextMenu={e => e.preventDefault()}
        />

        {!rendered && !loading && !error && (
          <div style={S.overlay}>
            <div style={S.box}>
              <div style={{ fontSize: 52, marginBottom: 10 }}>🌍</div>
              <div style={{ fontSize: 15, fontWeight: 700, color: "#f4f4f5", marginBottom: 6 }}>3D Real-World Globe</div>
              <div style={{ fontSize: 13, color: "#52525b" }}>Select lat/lon columns → click Plot Data</div>
              <div style={{ fontSize: 11, color: "#3f3f46", marginTop: 8 }}>Drag: rotate · Scroll: zoom · Click: details</div>
            </div>
          </div>
        )}

        {loading && (
          <div style={{ ...S.overlay, background: "rgba(0,0,16,.6)", pointerEvents: "none" }}>
            <div style={{ color: "#818cf8", fontSize: 14 }}>Plotting data on globe…</div>
          </div>
        )}

        {error && (
          <div style={{ position: "absolute", top: 16, left: "50%", transform: "translateX(-50%)", background: "rgba(239,68,68,.1)", border: "1px solid rgba(239,68,68,.3)", borderRadius: 10, padding: "10px 20px", color: "#f87171", fontSize: 13, zIndex: 10 }}>
            {error}
          </div>
        )}

        {tooltip && (
          <div style={{ position: "fixed", left: Math.min(tooltip.x + 12, window.innerWidth - 290), top: Math.min(tooltip.y - 10, window.innerHeight - 280), background: "rgba(0,0,16,.97)", border: "1px solid rgba(99,102,241,.4)", borderRadius: 12, padding: "14px 16px", zIndex: 100, minWidth: 220, maxWidth: 300, boxShadow: "0 8px 32px rgba(0,0,0,.8)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 10 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: "#a5b4fc" }}>📍 Data Point</div>
              <button onClick={() => setTooltip(null)} style={{ background: "transparent", border: "none", color: "#52525b", cursor: "pointer", fontSize: 16 }}>✕</button>
            </div>
            <div style={{ fontSize: 11, color: "#52525b", marginBottom: 8 }}>{tooltip.lat?.toFixed(4)}°, {tooltip.lon?.toFixed(4)}°</div>
            <div style={{ borderTop: "1px solid rgba(255,255,255,.06)", paddingTop: 8 }}>
              {Object.entries(tooltip.row || {}).slice(0, 10).map(([k, v]) => (
                <div key={k} style={{ display: "flex", justifyContent: "space-between", padding: "3px 0", borderBottom: "1px solid rgba(255,255,255,.03)" }}>
                  <span style={{ fontSize: 11, color: "#71717a" }}>{k}</span>
                  <span style={{ fontSize: 11, color: "#e4e4e7", fontWeight: 500, maxWidth: 150, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{String(v ?? "—").slice(0, 30)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {rendered && (
          <div style={{ position: "absolute", bottom: 16, right: 16, background: "rgba(0,0,16,.85)", border: "1px solid rgba(99,102,241,.2)", borderRadius: 10, padding: "10px 14px", fontSize: 11, color: "#71717a", zIndex: 5 }}>
            <div style={{ fontWeight: 600, color: "#a1a1aa", marginBottom: 6 }}>Legend</div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
              <div style={{ width: 60, height: 6, borderRadius: 3, background: `linear-gradient(to right, rgb(${SCALES[colorScale][0].join(",")}), rgb(${SCALES[colorScale][SCALES[colorScale].length-1].join(",")}))` }} />
              <span>{valCol || "uniform"}</span>
            </div>
            <div>{pc.toLocaleString()} points · {fps} FPS</div>
          </div>
        )}
      </div>
    </div>
  );
}

const S = {
  icon:    { width: 36, height: 36, borderRadius: 10, background: "linear-gradient(135deg,#1a6aff,#6366f1)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18, flexShrink: 0 },
  title:   { fontSize: 15, fontWeight: 600, color: "#f4f4f5" },
  sub:     { fontSize: 11, color: "#52525b" },
  lbl:     { fontSize: 11, color: "#a1a1aa", marginBottom: 3 },
  sel:     { padding: "6px 10px", borderRadius: 8, background: "#18181b", border: "1px solid rgba(255,255,255,.15)", color: "#f4f4f5", fontSize: 12, outline: "none", width: "100%", cursor: "pointer" },
  btn:     { padding: "8px 16px", borderRadius: 10, border: "none", background: "linear-gradient(135deg,#1a6aff,#6366f1)", color: "#fff", fontSize: 13, fontWeight: 600, cursor: "pointer" },
  outBtn:  { padding: "6px 12px", borderRadius: 10, border: "1px solid rgba(255,255,255,.12)", background: "transparent", color: "#71717a", fontSize: 12, cursor: "pointer" },
  overlay: { position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", pointerEvents: "none", zIndex: 5 },
  box:     { textAlign: "center", background: "rgba(0,0,16,.9)", border: "1px solid rgba(99,102,241,.25)", borderRadius: 16, padding: "40px 56px" },
};
