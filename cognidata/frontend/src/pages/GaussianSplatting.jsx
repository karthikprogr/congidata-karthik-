/**
 * Gaussian Splatting Geo View
 *
 * Renders dataset points as Gaussian splats — alpha-blended, depth-sorted
 * billboards in a Three.js WebGL scene. Each point becomes a soft glowing
 * sphere whose size, color and opacity encode data dimensions.
 *
 * Controls:
 *   - Left drag: orbit
 *   - Right drag / scroll: zoom
 *   - Column selectors: map X/Y/Z/Size/Color to dataset columns
 *   - Color scale: Viridis, Plasma, Inferno, Magma, Turbo
 */

import { useEffect, useRef, useState, useCallback } from "react";
import { api } from "../api/client";

// ── Color scales (sampled at 256 stops) ──────────────────────────────────────
const SCALES = {
  Viridis: [[68,1,84],[72,40,120],[62,83,160],[49,104,142],[38,130,142],[31,158,137],[53,183,121],[110,206,88],[181,222,43],[253,231,37]],
  Plasma:  [[13,8,135],[84,2,163],[139,10,165],[185,50,137],[219,92,104],[244,136,73],[254,188,43],[240,249,33]],
  Inferno: [[0,0,4],[40,11,84],[101,21,110],[159,42,99],[212,72,66],[245,125,21],[252,193,7],[252,255,164]],
  Magma:   [[0,0,4],[28,16,68],[79,18,123],[129,37,129],[181,54,122],[229,80,100],[251,135,97],[254,194,135],[252,253,191]],
  Turbo:   [[48,18,59],[86,83,201],[29,168,217],[26,214,105],[175,240,26],[253,182,15],[215,62,15],[122,4,3]],
};

function sampleScale(scale, t) {
  const stops = SCALES[scale] || SCALES.Viridis;
  const idx = Math.min(stops.length - 2, Math.floor(t * (stops.length - 1)));
  const frac = t * (stops.length - 1) - idx;
  const a = stops[idx], b = stops[idx + 1] || stops[idx];
  return [
    (a[0] + (b[0] - a[0]) * frac) / 255,
    (a[1] + (b[1] - a[1]) * frac) / 255,
    (a[2] + (b[2] - a[2]) * frac) / 255,
  ];
}

// ── Gaussian splat vertex shader ──────────────────────────────────────────────
const VERT = `
attribute float aSize;
attribute vec3  aColor;
attribute float aAlpha;
varying   vec3  vColor;
varying   float vAlpha;
void main() {
  vColor = aColor;
  vAlpha = aAlpha;
  vec4 mvPos = modelViewMatrix * vec4(position, 1.0);
  gl_PointSize = aSize * (300.0 / -mvPos.z);
  gl_Position  = projectionMatrix * mvPos;
}`;

// ── Gaussian splat fragment shader ───────────────────────────────────────────
const FRAG = `
varying vec3  vColor;
varying float vAlpha;
void main() {
  vec2  uv   = gl_PointCoord - 0.5;
  float r2   = dot(uv, uv);
  if (r2 > 0.25) discard;
  float g    = exp(-r2 * 8.0);   // Gaussian falloff
  gl_FragColor = vec4(vColor, vAlpha * g);
}`;

export default function GaussianSplatting() {
  const canvasRef = useRef(null);
  const rendererRef = useRef(null);
  const sceneRef = useRef(null);
  const cameraRef = useRef(null);
  const pointsRef = useRef(null);
  const animRef = useRef(null);
  const mouseRef = useRef({ down:false, button:0, x:0, y:0 });
  const orbitRef = useRef({ theta:0.5, phi:1.0, radius:5 });
  const extraMeshesRef = useRef([]);

  const RENDER_TYPES = [
    { id:"splat",        label:"✨ Gaussian Splats",   desc:"Soft alpha-blended Gaussian billboards" },
    { id:"voxel",        label:"🧊 Voxel Grid",         desc:"3D voxelized point cloud" },
    { id:"wireframe",    label:"🔷 Wireframe Mesh",     desc:"Delaunay-style wireframe surface" },
    { id:"neural",       label:"🧠 Neural Field",       desc:"Glowing neural network connections" },
    { id:"particles",    label:"⚡ Particle Storm",     desc:"Animated turbulent particles" },
    { id:"ribbon",       label:"🎀 Ribbon Trail",       desc:"Smooth ribbon connecting sorted points" },
    { id:"constellation",label:"🌌 Constellation",      desc:"Star map with connecting lines" },
    { id:"heatmap3d",    label:"🔥 3D Heatmap",         desc:"Volumetric density heatmap" },
    { id:"dna",          label:"🧬 DNA Helix",          desc:"Double helix spiral through data" },
    { id:"tornado",      label:"🌪️ Tornado",            desc:"Spiraling vortex of points" },
    { id:"crystal",      label:"💎 Crystal Lattice",    desc:"Crystalline geometric structure" },
    { id:"flow",         label:"🌊 Flow Field",         desc:"Animated vector flow lines" },
    { id:"bubble",       label:"🫧 Bubble Cloud",       desc:"Transparent spheres sized by value" },
    { id:"matrix",       label:"🟩 Matrix Rain",        desc:"Falling data columns like The Matrix" },
    { id:"terrain",      label:"🏔️ 3D Terrain",         desc:"Heightmap terrain surface" },
    { id:"galaxy",       label:"🌀 Galaxy Spiral",      desc:"Spiral galaxy distribution" },
  ];

  const [renderType, setRenderType] = useState("splat");
  const [cols, setCols] = useState({ all_cols:[], numeric_cols:[] });
  const [xCol, setXCol] = useState("");
  const [yCol, setYCol] = useState("");
  const [zCol, setZCol] = useState("");
  const [sizeCol, setSizeCol] = useState("");
  const [colorCol, setColorCol] = useState("");
  const [scale, setScale] = useState("Viridis");
  const [splatSize, setSplatSize] = useState(1.0);
  const [opacity, setOpacity] = useState(0.85);
  const [pointCount, setPointCount] = useState(0);
  const [fps, setFps] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [rendered, setRendered] = useState(false);

  // Load column info
  useEffect(() => {
    api.get("/maps/columns")
      .then(({ data }) => {
        setCols(data);
        setXCol(data.lat_hints?.[0] || data.numeric_cols?.[0] || "");
        setYCol(data.lon_hints?.[0] || data.numeric_cols?.[1] || "");
        setZCol(data.numeric_cols?.[0] || "");
        setSizeCol(data.numeric_cols?.[1] || data.numeric_cols?.[0] || "");
        setColorCol(data.numeric_cols?.[0] || "");
      })
      .catch(() => setError("Upload a dataset first"));
  }, []);

  // Init Three.js
  useEffect(() => {
    if (!canvasRef.current) return;
    let cleanup = () => {};
    import("three").then(THREE => {
      const canvas = canvasRef.current;
      if (!canvas) return;

      // Force canvas to fill its container
      const container = canvas.parentElement;
      const W = container?.clientWidth || window.innerWidth;
      const H = container?.clientHeight || window.innerHeight - 160;
      canvas.width  = W;
      canvas.height = H;

      const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
      renderer.setSize(W, H, false);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.setClearColor(0x09090b, 1);
      rendererRef.current = renderer;

      const scene = new THREE.Scene();
      sceneRef.current = scene;

      const camera = new THREE.PerspectiveCamera(60, W / H, 0.01, 1000);
      camera.position.set(0, 0, 5);
      cameraRef.current = camera;

      scene.add(new THREE.AmbientLight(0xffffff, 0.3));
      scene.add(new THREE.AxesHelper(1));

      const grid = new THREE.GridHelper(4, 20, 0x27272a, 0x18181b);
      grid.position.y = -1.5;
      scene.add(grid);

      let lastTime = performance.now(), frames = 0;
      let rafId;

      const animate = () => {
        rafId = requestAnimationFrame(animate);
        frames++;
        const now = performance.now();
        if (now - lastTime > 1000) {
          setFps(frames);
          frames = 0;
          lastTime = now;
        }
        const { theta, phi, radius } = orbitRef.current;
        camera.position.set(
          radius * Math.sin(phi) * Math.sin(theta),
          radius * Math.cos(phi),
          radius * Math.sin(phi) * Math.cos(theta),
        );
        camera.lookAt(0, 0, 0);
        renderer.render(scene, camera);
      };
      animate();
      animRef.current = rafId;

      const onResize = () => {
        if (!canvas || !canvas.parentElement) return;
        const W2 = canvas.parentElement.clientWidth;
        const H2 = canvas.parentElement.clientHeight;
        if (W2 > 0 && H2 > 0) {
          renderer.setSize(W2, H2, false);
          camera.aspect = W2 / H2;
          camera.updateProjectionMatrix();
        }
      };
      window.addEventListener("resize", onResize);

      cleanup = () => {
        window.removeEventListener("resize", onResize);
        cancelAnimationFrame(rafId);
        renderer.dispose();
      };
    }).catch(e => setError(`Three.js failed to load: ${e.message}`));

    return () => cleanup();
  }, []);

  // Mouse orbit controls
  const onMouseDown = useCallback(e => {
    mouseRef.current = { down:true, button:e.button, x:e.clientX, y:e.clientY };
  }, []);

  const onMouseMove = useCallback(e => {
    if (!mouseRef.current.down) return;
    const dx = e.clientX - mouseRef.current.x;
    const dy = e.clientY - mouseRef.current.y;
    mouseRef.current.x = e.clientX;
    mouseRef.current.y = e.clientY;
    if (mouseRef.current.button === 0) {
      orbitRef.current.theta -= dx * 0.01;
      orbitRef.current.phi = Math.max(0.1, Math.min(Math.PI - 0.1, orbitRef.current.phi + dy * 0.01));
    } else {
      orbitRef.current.radius = Math.max(0.5, Math.min(20, orbitRef.current.radius + dy * 0.02));
    }
  }, []);

  const onMouseUp = useCallback(() => { mouseRef.current.down = false; }, []);
  const onWheel = useCallback(e => {
    orbitRef.current.radius = Math.max(0.5, Math.min(20, orbitRef.current.radius + e.deltaY * 0.005));
  }, []);

  // Build splats from dataset
  const buildSplats = useCallback(async () => {
    if (!xCol || !yCol) return;
    setLoading(true);
    setError(null);
    try {
      const { data: preview } = await api.get("/data/preview?n=2000");
      const rows = preview.data || [];
      if (!rows.length) { setError("No data"); setLoading(false); return; }

      const THREE = await import("three");

      // Extract columns
      const xs = rows.map(r => parseFloat(r[xCol]) || 0);
      const ys = rows.map(r => parseFloat(r[yCol]) || 0);
      const zs = zCol ? rows.map(r => parseFloat(r[zCol]) || 0) : Array(rows.length).fill(0);
      const sizes = sizeCol ? rows.map(r => parseFloat(r[sizeCol]) || 1) : Array(rows.length).fill(1);
      const colors = colorCol ? rows.map(r => parseFloat(r[colorCol]) || 0) : zs;

      // Normalize to [-1.5, 1.5]
      const norm = (arr) => {
        const mn = Math.min(...arr), mx = Math.max(...arr), rng = mx - mn || 1;
        return arr.map(v => ((v - mn) / rng - 0.5) * 3);
      };
      const nx = norm(xs), ny = norm(ys), nz = norm(zs);
      const ns = norm(sizes).map(v => (v + 1.5) * splatSize);
      const nc = norm(colors).map(v => (v + 1.5) / 3);

      // Build geometry
      const n = rows.length;
      const positions = new Float32Array(n * 3);
      const aSizes    = new Float32Array(n);
      const aColors   = new Float32Array(n * 3);
      const aAlphas   = new Float32Array(n);

      for (let i = 0; i < n; i++) {
        positions[i*3]   = nx[i];
        positions[i*3+1] = ny[i];
        positions[i*3+2] = nz[i];
        aSizes[i] = Math.max(0.1, ns[i]);
        const [r, g, b] = sampleScale(scale, Math.max(0, Math.min(1, nc[i])));
        aColors[i*3] = r; aColors[i*3+1] = g; aColors[i*3+2] = b;
        aAlphas[i] = opacity;
      }

      const geo = new THREE.BufferGeometry();
      geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
      geo.setAttribute("aSize",    new THREE.BufferAttribute(aSizes, 1));
      geo.setAttribute("aColor",   new THREE.BufferAttribute(aColors, 3));
      geo.setAttribute("aAlpha",   new THREE.BufferAttribute(aAlphas, 1));

      const mat = new THREE.ShaderMaterial({
        vertexShader: VERT,
        fragmentShader: FRAG,
        transparent: true,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
      });

      // Remove old splats
      if (pointsRef.current) {
        sceneRef.current.remove(pointsRef.current);
        pointsRef.current.geometry.dispose();
        pointsRef.current.material.dispose();
      }

      const points = new THREE.Points(geo, mat);
      sceneRef.current.add(points);
      pointsRef.current = points;
      setPointCount(n);
      setRendered(true);
    } catch(e) {
      setError(`Render error: ${e.message}`);
    }
    setLoading(false);
  }, [xCol, yCol, zCol, sizeCol, colorCol, scale, splatSize, opacity]);

  // Re-render when params change
  useEffect(() => {
    if (rendered) renderScene();
  }, [scale, splatSize, opacity, renderType]);

  const resetCamera = () => { orbitRef.current = { theta:0.5, phi:1.0, radius:5 }; };

  // ── Master render dispatcher ──────────────────────────────────────────────
  const renderScene = useCallback(async () => {
    if (renderType === "splat") { buildSplats(); return; }
    if (!xCol || !yCol) return;
    setLoading(true); setError(null);
    try {
      const THREE = await import("three");
      const { data: preview } = await api.get("/data/preview?n=2000");
      const rows = preview.data || [];
      if (!rows.length) { setError("No data"); setLoading(false); return; }

      const xs = rows.map(r => parseFloat(r[xCol]) || 0);
      const ys = rows.map(r => parseFloat(r[yCol]) || 0);
      const zs = zCol ? rows.map(r => parseFloat(r[zCol]) || 0) : Array(rows.length).fill(0);
      const vals = colorCol ? rows.map(r => parseFloat(r[colorCol]) || 0) : zs;

      const norm = arr => { const mn=Math.min(...arr),mx=Math.max(...arr),rng=mx-mn||1; return arr.map(v=>((v-mn)/rng-0.5)*3); };
      const normV = arr => { const mn=Math.min(...arr),mx=Math.max(...arr),rng=mx-mn||1; return arr.map(v=>(v-mn)/rng); };
      const nx=norm(xs), ny=norm(ys), nz=norm(zs), nc=normV(vals);
      const n = rows.length;

      // Clear old objects
      if (pointsRef.current) { sceneRef.current.remove(pointsRef.current); pointsRef.current.geometry.dispose(); pointsRef.current.material.dispose(); }
      extraMeshesRef.current.forEach(m => { sceneRef.current.remove(m); if(m.geometry) m.geometry.dispose(); if(m.material) m.material.dispose(); });
      extraMeshesRef.current = [];

      if (renderType === "voxel") {
        // 3D Voxel Grid — box for each point
        const boxGeo = new THREE.BoxGeometry(0.08, 0.08, 0.08);
        for (let i = 0; i < Math.min(n, 500); i++) {
          const [r,g,b] = sampleScale(scale, nc[i]);
          const mat = new THREE.MeshPhongMaterial({ color: new THREE.Color(r,g,b), transparent:true, opacity:0.8 });
          const mesh = new THREE.Mesh(boxGeo, mat);
          mesh.position.set(nx[i], ny[i], nz[i]);
          sceneRef.current.add(mesh);
          extraMeshesRef.current.push(mesh);
        }

      } else if (renderType === "wireframe") {
        // Wireframe — connect nearby points
        const positions = [];
        for (let i = 0; i < n; i++) {
          for (let j = i+1; j < Math.min(i+4, n); j++) {
            const dx=nx[i]-nx[j], dy=ny[i]-ny[j], dz=nz[i]-nz[j];
            if (Math.sqrt(dx*dx+dy*dy+dz*dz) < 0.5) {
              positions.push(nx[i],ny[i],nz[i], nx[j],ny[j],nz[j]);
            }
          }
        }
        const geo = new THREE.BufferGeometry();
        geo.setAttribute("position", new THREE.BufferAttribute(new Float32Array(positions), 3));
        const lines = new THREE.LineSegments(geo, new THREE.LineBasicMaterial({ color:0x6366f1, transparent:true, opacity:0.6 }));
        sceneRef.current.add(lines);
        extraMeshesRef.current.push(lines);
        // Also add points
        const pGeo = new THREE.BufferGeometry();
        const pPos = new Float32Array(n*3), pCol = new Float32Array(n*3);
        for (let i=0;i<n;i++) { pPos.set([nx[i],ny[i],nz[i]],i*3); const [r,g,b]=sampleScale(scale,nc[i]); pCol.set([r,g,b],i*3); }
        pGeo.setAttribute("position",new THREE.BufferAttribute(pPos,3));
        pGeo.setAttribute("color",new THREE.BufferAttribute(pCol,3));
        const pts = new THREE.Points(pGeo, new THREE.PointsMaterial({vertexColors:true,size:0.05}));
        sceneRef.current.add(pts); extraMeshesRef.current.push(pts);

      } else if (renderType === "neural") {
        // Neural network — nodes + glowing connections
        const nodeGeo = new THREE.SphereGeometry(0.04, 8, 8);
        const linePos = [];
        for (let i = 0; i < Math.min(n, 300); i++) {
          const [r,g,b] = sampleScale(scale, nc[i]);
          const mat = new THREE.MeshBasicMaterial({ color: new THREE.Color(r,g,b) });
          const mesh = new THREE.Mesh(nodeGeo, mat);
          mesh.position.set(nx[i], ny[i], nz[i]);
          sceneRef.current.add(mesh); extraMeshesRef.current.push(mesh);
          // Connect to 2 nearest
          for (let j = i+1; j < Math.min(i+3, n); j++) {
            linePos.push(nx[i],ny[i],nz[i], nx[j],ny[j],nz[j]);
          }
        }
        const lGeo = new THREE.BufferGeometry();
        lGeo.setAttribute("position", new THREE.BufferAttribute(new Float32Array(linePos), 3));
        const lines = new THREE.LineSegments(lGeo, new THREE.LineBasicMaterial({ color:0x818cf8, transparent:true, opacity:0.3 }));
        sceneRef.current.add(lines); extraMeshesRef.current.push(lines);

      } else if (renderType === "particles") {
        // Particle storm — animated with custom shader
        const geo = new THREE.BufferGeometry();
        const pos = new Float32Array(n*3), col = new Float32Array(n*3), vel = new Float32Array(n*3);
        for (let i=0;i<n;i++) {
          pos.set([nx[i],ny[i],nz[i]],i*3);
          const [r,g,b]=sampleScale(scale,nc[i]); col.set([r,g,b],i*3);
          vel.set([(Math.random()-.5)*.02,(Math.random()-.5)*.02,(Math.random()-.5)*.02],i*3);
        }
        geo.setAttribute("position",new THREE.BufferAttribute(pos,3));
        geo.setAttribute("color",new THREE.BufferAttribute(col,3));
        const mat = new THREE.PointsMaterial({vertexColors:true,size:0.06,transparent:true,opacity:0.9,blending:THREE.AdditiveBlending,depthWrite:false});
        const pts = new THREE.Points(geo,mat);
        sceneRef.current.add(pts); extraMeshesRef.current.push(pts);
        // Animate particles
        const origPos = pos.slice();
        const animateParticles = () => {
          const t = Date.now()*0.001;
          for (let i=0;i<n;i++) {
            pos[i*3]   = origPos[i*3]   + Math.sin(t+i*0.1)*0.1;
            pos[i*3+1] = origPos[i*3+1] + Math.cos(t+i*0.13)*0.1;
            pos[i*3+2] = origPos[i*3+2] + Math.sin(t*0.7+i*0.07)*0.1;
          }
          geo.attributes.position.needsUpdate = true;
        };
        // Store animator
        pts.userData.animate = animateParticles;

      } else if (renderType === "ribbon") {
        // Ribbon — smooth tube through sorted points
        const sorted = [...Array(n).keys()].sort((a,b)=>nx[a]-nx[b]);
        const curve = new THREE.CatmullRomCurve3(
          sorted.slice(0, Math.min(200, n)).map(i => new THREE.Vector3(nx[i],ny[i],nz[i]))
        );
        const tubeGeo = new THREE.TubeGeometry(curve, 200, 0.02, 8, false);
        const tubeMat = new THREE.MeshPhongMaterial({ color:0x818cf8, emissive:0x4444ff, transparent:true, opacity:0.8, side:THREE.DoubleSide });
        const tube = new THREE.Mesh(tubeGeo, tubeMat);
        sceneRef.current.add(tube); extraMeshesRef.current.push(tube);

      } else if (renderType === "constellation") {
        // Constellation — stars + connecting lines for nearby points
        const geo = new THREE.BufferGeometry();
        const pos = new Float32Array(n*3), col = new Float32Array(n*3), sizes = new Float32Array(n);
        for (let i=0;i<n;i++) {
          pos.set([nx[i],ny[i],nz[i]],i*3);
          const [r,g,b]=sampleScale(scale,nc[i]); col.set([r,g,b],i*3);
          sizes[i] = 0.05 + nc[i]*0.15;
        }
        geo.setAttribute("position",new THREE.BufferAttribute(pos,3));
        geo.setAttribute("color",new THREE.BufferAttribute(col,3));
        const pts = new THREE.Points(geo, new THREE.PointsMaterial({vertexColors:true,size:0.08,transparent:true,opacity:1,blending:THREE.AdditiveBlending}));
        sceneRef.current.add(pts); extraMeshesRef.current.push(pts);
        // Connect nearby stars
        const linePos = [];
        for (let i=0;i<n;i++) {
          for (let j=i+1;j<Math.min(i+5,n);j++) {
            const dx=nx[i]-nx[j],dy=ny[i]-ny[j],dz=nz[i]-nz[j];
            if (Math.sqrt(dx*dx+dy*dy+dz*dz)<0.4) linePos.push(nx[i],ny[i],nz[i],nx[j],ny[j],nz[j]);
          }
        }
        const lGeo=new THREE.BufferGeometry();
        lGeo.setAttribute("position",new THREE.BufferAttribute(new Float32Array(linePos),3));
        const lines=new THREE.LineSegments(lGeo,new THREE.LineBasicMaterial({color:0x4444aa,transparent:true,opacity:0.25}));
        sceneRef.current.add(lines); extraMeshesRef.current.push(lines);

      } else if (renderType === "heatmap3d") {
        // 3D Heatmap — colored cubes in a grid
        const gridSize = 10;
        const grid = {};
        for (let i=0;i<n;i++) {
          const gx=Math.round(nx[i]*gridSize/3), gy=Math.round(ny[i]*gridSize/3), gz=Math.round(nz[i]*gridSize/3);
          const key=`${gx},${gy},${gz}`;
          grid[key] = (grid[key]||0) + 1;
        }
        const maxCount = Math.max(...Object.values(grid));
        const boxGeo = new THREE.BoxGeometry(0.25, 0.25, 0.25);
        Object.entries(grid).forEach(([key, count]) => {
          const [gx,gy,gz] = key.split(",").map(Number);
          const t = count/maxCount;
          const [r,g,b] = sampleScale(scale, t);
          const mat = new THREE.MeshPhongMaterial({ color:new THREE.Color(r,g,b), transparent:true, opacity:0.4+t*0.5 });
          const mesh = new THREE.Mesh(boxGeo, mat);
          mesh.position.set(gx/gridSize*3, gy/gridSize*3, gz/gridSize*3);
          mesh.scale.y = 0.2 + t*1.5;
          sceneRef.current.add(mesh); extraMeshesRef.current.push(mesh);
        });

      } else if (renderType === "dna") {
        const lp1=[],lp2=[],rungs=[],total=Math.min(n,500);
        for(let i=0;i<total;i++){const t=i/total,a=t*Math.PI*8,x1=Math.cos(a)*1.2,z1=Math.sin(a)*1.2,y1=(t-0.5)*4,x2=Math.cos(a+Math.PI)*1.2,z2=Math.sin(a+Math.PI)*1.2;lp1.push(x1,y1,z1);lp2.push(x2,y1,z2);if(i%8===0)rungs.push(x1,y1,z1,x2,y1,z2);}
        const mk=(p,c)=>{const g=new THREE.BufferGeometry();g.setAttribute("position",new THREE.BufferAttribute(new Float32Array(p),3));const m=new THREE.Line(g,new THREE.LineBasicMaterial({color:c}));sceneRef.current.add(m);extraMeshesRef.current.push(m);};
        mk(lp1,0x6366f1);mk(lp2,0x10b981);
        const rg=new THREE.BufferGeometry();rg.setAttribute("position",new THREE.BufferAttribute(new Float32Array(rungs),3));const rl=new THREE.LineSegments(rg,new THREE.LineBasicMaterial({color:0xfbbf24,transparent:true,opacity:0.5}));sceneRef.current.add(rl);extraMeshesRef.current.push(rl);

      } else if (renderType === "tornado") {
        const tpos=new Float32Array(n*3),tcol=new Float32Array(n*3);
        for(let i=0;i<n;i++){const t=i/n,a=t*Math.PI*20,rad=t*2,y=(t-0.5)*4;tpos.set([Math.cos(a)*rad,y,Math.sin(a)*rad],i*3);const[r,g,b]=sampleScale(scale,nc[i]||t);tcol.set([r,g,b],i*3);}
        const tgeo=new THREE.BufferGeometry();tgeo.setAttribute("position",new THREE.BufferAttribute(tpos,3));tgeo.setAttribute("color",new THREE.BufferAttribute(tcol,3));
        sceneRef.current.add(new THREE.Points(tgeo,new THREE.PointsMaterial({vertexColors:true,size:0.04,transparent:true,opacity:0.9,blending:THREE.AdditiveBlending})));

      } else if (renderType === "crystal") {
        const icoGeo=new THREE.IcosahedronGeometry(0.06,0);
        for(let i=0;i<Math.min(n,400);i++){const[r,g,b]=sampleScale(scale,nc[i]);const mat=new THREE.MeshPhongMaterial({color:new THREE.Color(r,g,b),transparent:true,opacity:0.7,wireframe:i%3===0});const mesh=new THREE.Mesh(icoGeo,mat);mesh.position.set(nx[i],ny[i],nz[i]);mesh.rotation.set(Math.random()*Math.PI,Math.random()*Math.PI,0);sceneRef.current.add(mesh);extraMeshesRef.current.push(mesh);}

      } else if (renderType === "galaxy") {
        const gpos=new Float32Array(n*3),gcol=new Float32Array(n*3);
        for(let i=0;i<n;i++){const arm=i%3,t=i/n,a=t*Math.PI*6+(arm/3)*Math.PI*2,rad=t*2.5+(Math.random()-0.5)*0.3;gpos.set([Math.cos(a)*rad,(Math.random()-0.5)*0.15+(nc[i]||0)*0.3,Math.sin(a)*rad],i*3);const[r,g,b]=sampleScale(scale,t);gcol.set([r,g,b],i*3);}
        const ggeo=new THREE.BufferGeometry();ggeo.setAttribute("position",new THREE.BufferAttribute(gpos,3));ggeo.setAttribute("color",new THREE.BufferAttribute(gcol,3));
        sceneRef.current.add(new THREE.Points(ggeo,new THREE.PointsMaterial({vertexColors:true,size:0.03,transparent:true,opacity:0.9,blending:THREE.AdditiveBlending,depthWrite:false})));
        const core=new THREE.Mesh(new THREE.SphereGeometry(0.15,16,16),new THREE.MeshBasicMaterial({color:0xffffff,transparent:true,opacity:0.8}));sceneRef.current.add(core);extraMeshesRef.current.push(core);

      } else if (renderType === "flow") {
        for(let s=0;s<50;s++){const si=Math.floor(Math.random()*n);const lp=[];let cx=nx[si],cy=ny[si],cz=nz[si];for(let step=0;step<30;step++){lp.push(cx,cy,cz);const t=step/30;cx+=Math.sin(cy*2+t)*0.05;cy+=Math.cos(cx*2+t)*0.05;cz+=Math.sin((cx+cy)*1.5+t)*0.03;}const[r,g,b]=sampleScale(scale,s/50);const fgeo=new THREE.BufferGeometry();fgeo.setAttribute("position",new THREE.BufferAttribute(new Float32Array(lp),3));sceneRef.current.add(new THREE.Line(fgeo,new THREE.LineBasicMaterial({color:new THREE.Color(r,g,b),transparent:true,opacity:0.6})));}

      } else if (renderType === "bubble") {
        for(let i=0;i<Math.min(n,300);i++){const t=nc[i]||0.5;const[r,g,b]=sampleScale(scale,t);const rad=0.04+t*0.18;const mesh=new THREE.Mesh(new THREE.SphereGeometry(rad,12,12),new THREE.MeshPhongMaterial({color:new THREE.Color(r,g,b),transparent:true,opacity:0.15+t*0.25,side:THREE.DoubleSide}));mesh.position.set(nx[i],ny[i],nz[i]);sceneRef.current.add(mesh);extraMeshesRef.current.push(mesh);}

      } else if (renderType === "matrix") {
        for(let c=0;c<20;c++)for(let r2=0;r2<30;r2++){const t=r2/30;const[r,g,b]=sampleScale(scale,t);const mesh=new THREE.Mesh(new THREE.PlaneGeometry(0.08,0.08),new THREE.MeshBasicMaterial({color:new THREE.Color(r,g,b),transparent:true,opacity:t*0.9,side:THREE.DoubleSide}));mesh.position.set((c/20-0.5)*4,(r2/30-0.5)*4,(Math.random()-0.5)*0.5);sceneRef.current.add(mesh);extraMeshesRef.current.push(mesh);}

      } else if (renderType === "terrain") {
        const res=30,tgrid=Array.from({length:res},()=>Array(res).fill(0)),tcnt=Array.from({length:res},()=>Array(res).fill(0));
        for(let i=0;i<n;i++){const gx=Math.max(0,Math.min(res-1,Math.floor((nx[i]+1.5)/3*res))),gz=Math.max(0,Math.min(res-1,Math.floor((nz[i]+1.5)/3*res)));tgrid[gx][gz]+=nc[i];tcnt[gx][gz]++;}
        const tverts=[],tcolors=[],tidx=[];
        for(let i=0;i<res;i++)for(let j=0;j<res;j++){const h=tcnt[i][j]>0?(tgrid[i][j]/tcnt[i][j])*1.5:0;tverts.push((i/res-0.5)*4,h,(j/res-0.5)*4);const[r,g,b]=sampleScale(scale,h/1.5);tcolors.push(r,g,b);}
        for(let i=0;i<res-1;i++)for(let j=0;j<res-1;j++){const a=i*res+j;tidx.push(a,a+1,(i+1)*res+j,a+1,(i+1)*res+j+1,(i+1)*res+j);}
        const tgeo2=new THREE.BufferGeometry();tgeo2.setAttribute("position",new THREE.BufferAttribute(new Float32Array(tverts),3));tgeo2.setAttribute("color",new THREE.BufferAttribute(new Float32Array(tcolors),3));tgeo2.setIndex(tidx);tgeo2.computeVertexNormals();
        const tmesh=new THREE.Mesh(tgeo2,new THREE.MeshPhongMaterial({vertexColors:true,side:THREE.DoubleSide}));sceneRef.current.add(tmesh);extraMeshesRef.current.push(tmesh);
      }

      setPointCount(n); setRendered(true);
    } catch(e) { setError(`Render error: ${e.message}`); }
    setLoading(false);
  }, [xCol, yCol, zCol, colorCol, scale, splatSize, opacity, renderType, buildSplats]);

  const Sel = ({ label, val, set }) => (
    <div style={{flex:1,minWidth:120}}>
      <label style={S.label}>{label}</label>
      <select value={val} onChange={e=>set(e.target.value)} style={S.select}>
        <option value="">(none)</option>
        {cols.numeric_cols.map(c=><option key={c}>{c}</option>)}
        {cols.all_cols.filter(c=>!cols.numeric_cols.includes(c)).map(c=><option key={c}>{c}</option>)}
      </select>
    </div>
  );

  return (
    <div style={{ display:"flex", flexDirection:"column", height:"100vh", background:"#09090b", overflow:"hidden" }}>
      {/* Header */}
      <div style={{ padding:"12px 20px", borderBottom:"1px solid rgba(255,255,255,.06)", background:"rgba(9,9,11,.95)", flexShrink:0 }}>
        <div style={{ display:"flex", alignItems:"center", gap:12, marginBottom:10 }}>
          <div style={S.icon}>✨</div>
          <div>
            <div style={S.title}>Gaussian Splatting Geo View</div>
            <div style={S.sub}>WebGL · Three.js · {RENDER_TYPES.find(r=>r.id===renderType)?.label} · {pointCount.toLocaleString()} points · {fps} FPS</div>
          </div>
          <div style={{ marginLeft:"auto", display:"flex", gap:8 }}>
            <button onClick={resetCamera} style={S.outlineBtn}>↺ Reset Camera</button>
            <button onClick={renderScene} disabled={loading||!xCol||!yCol} style={S.btn}>
              {loading ? <><span className="spinner" style={{width:14,height:14}}/> Rendering…</> : `${RENDER_TYPES.find(r=>r.id===renderType)?.label.split(" ")[0]} Render`}
            </button>
          </div>
        </div>

        {/* Render type selector */}
        <div style={{ display:"flex", gap:6, flexWrap:"wrap", marginBottom:10 }}>
          {RENDER_TYPES.map(rt => (
            <button key={rt.id} onClick={() => setRenderType(rt.id)} title={rt.desc}
              style={{ padding:"4px 10px", borderRadius:20, border:"1px solid", fontSize:11, cursor:"pointer",
                background: renderType===rt.id ? "rgba(99,102,241,.2)" : "transparent",
                borderColor: renderType===rt.id ? "rgba(99,102,241,.5)" : "rgba(255,255,255,.1)",
                color: renderType===rt.id ? "#a5b4fc" : "#71717a" }}>
              {rt.label}
            </button>
          ))}
        </div>

        {/* Controls */}
        <div style={{ display:"flex", gap:10, flexWrap:"wrap", alignItems:"flex-end" }}>
          <Sel label="X Axis (Lat)" val={xCol} set={setXCol} />
          <Sel label="Y Axis (Lon)" val={yCol} set={setYCol} />
          <Sel label="Z Axis (Height)" val={zCol} set={setZCol} />
          <Sel label="Splat Size" val={sizeCol} set={setSizeCol} />
          <Sel label="Color" val={colorCol} set={setColorCol} />
          <div style={{minWidth:120}}>
            <label style={S.label}>Color Scale</label>
            <select value={scale} onChange={e=>setScale(e.target.value)} style={S.select}>
              {Object.keys(SCALES).map(s=><option key={s}>{s}</option>)}
            </select>
          </div>
          <div style={{minWidth:140}}>
            <div style={{display:"flex",justifyContent:"space-between",marginBottom:3}}>
              <label style={S.label}>Splat Size</label>
              <span style={{fontSize:10,color:"#6366f1",fontWeight:600}}>{splatSize.toFixed(1)}×</span>
            </div>
            <input type="range" min={0.1} max={3.0} step={0.1} value={splatSize} onChange={e=>setSplatSize(Number(e.target.value))} style={{width:"100%",accentColor:"#6366f1"}} />
          </div>
          <div style={{minWidth:140}}>
            <div style={{display:"flex",justifyContent:"space-between",marginBottom:3}}>
              <label style={S.label}>Opacity</label>
              <span style={{fontSize:10,color:"#6366f1",fontWeight:600}}>{opacity.toFixed(2)}</span>
            </div>
            <input type="range" min={0.1} max={1.0} step={0.05} value={opacity} onChange={e=>setOpacity(Number(e.target.value))} style={{width:"100%",accentColor:"#6366f1"}} />
          </div>
        </div>
      </div>

      {/* Canvas */}
      <div style={{ flex:1, position:"relative", overflow:"hidden", minHeight: 400 }}>
        <canvas
          ref={canvasRef}
          style={{ width:"100%", height:"100%", display:"block", cursor:"grab" }}
          onMouseDown={onMouseDown}
          onMouseMove={onMouseMove}
          onMouseUp={onMouseUp}
          onMouseLeave={onMouseUp}
          onWheel={onWheel}
          onContextMenu={e=>e.preventDefault()}
        />

        {/* Overlay — empty state */}
        {!rendered && !loading && (
          <div style={{ position:"absolute", inset:0, display:"flex", alignItems:"center", justifyContent:"center", pointerEvents:"none" }}>
            <div style={{ textAlign:"center", background:"rgba(9,9,11,.8)", border:"1px solid rgba(255,255,255,.07)", borderRadius:16, padding:"40px 56px" }}>
              <div style={{ fontSize:48, marginBottom:12 }}>✨</div>
              <div style={{ fontSize:15, fontWeight:600, color:"#f4f4f5", marginBottom:6 }}>Gaussian Splatting</div>
              <div style={{ fontSize:13, color:"#52525b", marginBottom:16 }}>Select columns and choose a render type</div>
              <div style={{ fontSize:11, color:"#3f3f46" }}>Left drag: orbit · Right drag / scroll: zoom</div>
            </div>
          </div>
        )}

        {/* Loading overlay */}
        {loading && (
          <div style={{ position:"absolute", inset:0, display:"flex", alignItems:"center", justifyContent:"center", background:"rgba(9,9,11,.6)", pointerEvents:"none" }}>
            <div style={{ display:"flex", alignItems:"center", gap:12, background:"rgba(24,24,27,.9)", border:"1px solid rgba(255,255,255,.08)", borderRadius:12, padding:"16px 24px" }}>
              <span className="spinner" style={{ width:20, height:20 }} />
              <span style={{ color:"#a1a1aa", fontSize:14 }}>Building Gaussian splats…</span>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div style={{ position:"absolute", top:16, left:"50%", transform:"translateX(-50%)", background:"rgba(239,68,68,.1)", border:"1px solid rgba(239,68,68,.3)", borderRadius:10, padding:"10px 20px", color:"#f87171", fontSize:13 }}>
            {error}
          </div>
        )}

        {/* Legend */}
        {rendered && (
          <div style={{ position:"absolute", bottom:16, right:16, background:"rgba(9,9,11,.85)", border:"1px solid rgba(255,255,255,.07)", borderRadius:10, padding:"10px 14px", fontSize:11, color:"#71717a" }}>
            <div style={{ marginBottom:6, fontWeight:600, color:"#a1a1aa" }}>Legend</div>
            <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:4 }}>
              <div style={{ width:60, height:8, borderRadius:4, background:`linear-gradient(to right, rgb(${SCALES[scale][0].join(",")}), rgb(${SCALES[scale][Math.floor(SCALES[scale].length/2)].join(",")}), rgb(${SCALES[scale][SCALES[scale].length-1].join(",")}))`}} />
              <span>{colorCol || "index"}</span>
            </div>
            <div>Size → {sizeCol || "uniform"}</div>
            <div>Z → {zCol || "flat"}</div>
            <div style={{ marginTop:6, color:"#3f3f46" }}>{pointCount.toLocaleString()} splats · {fps} FPS</div>
          </div>
        )}

        {/* Controls hint */}
        <div style={{ position:"absolute", bottom:16, left:16, fontSize:10, color:"#71717a" }}>
          Left drag: orbit · Right drag: zoom · Scroll: zoom
        </div>
      </div>
    </div>
  );
}

const S = {
  icon:       { width:36, height:36, borderRadius:10, background:"linear-gradient(135deg,#6366f1,#8b5cf6)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:16 },
  title:      { fontSize:15, fontWeight:600, color:"#f4f4f5" },
  sub:        { fontSize:11, color:"#52525b" },
  label:      { fontSize:11, color:"#71717a", display:"block", marginBottom:3 },
  select:     { padding:"6px 10px", borderRadius:8, background:"rgba(255,255,255,.05)", border:"1px solid rgba(255,255,255,.09)", color:"#f4f4f5", fontSize:12, outline:"none", width:"100%" },
  btn:        { padding:"8px 16px", borderRadius:10, border:"none", background:"linear-gradient(135deg,#6366f1,#8b5cf6)", color:"#fff", fontSize:13, fontWeight:600, cursor:"pointer", display:"inline-flex", alignItems:"center", gap:8 },
  outlineBtn: { padding:"8px 14px", borderRadius:10, border:"1px solid rgba(255,255,255,.09)", background:"transparent", color:"#71717a", fontSize:12, cursor:"pointer" },
};
