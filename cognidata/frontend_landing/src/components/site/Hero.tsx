import { motion } from "framer-motion";
import { ArrowRight, PlayCircle, Sparkles, TrendingUp, LineChart, Cpu, Database } from "lucide-react";

export function Hero() {
  return (
    <section className="relative overflow-hidden pb-24 pt-40 sm:pt-48">
      {/* Background layers */}
      <div className="pointer-events-none absolute inset-0 -z-10 bg-grid" />
      <div className="pointer-events-none absolute -top-40 left-1/2 -z-10 h-[40rem] w-[70rem] -translate-x-1/2 rounded-full bg-primary/25 blur-[140px]" />
      <div className="pointer-events-none absolute -bottom-40 right-0 -z-10 h-[30rem] w-[40rem] rounded-full bg-accent/20 blur-[120px]" />

      {/* Floating particles */}
      {Array.from({ length: 14 }).map((_, i) => (
        <motion.span
          key={i}
          className="pointer-events-none absolute h-1 w-1 rounded-full bg-white/40"
          style={{
            top: `${(i * 53) % 90 + 5}%`,
            left: `${(i * 37) % 95 + 2}%`,
          }}
          animate={{ y: [0, -20, 0], opacity: [0.2, 0.9, 0.2] }}
          transition={{ duration: 4 + (i % 5), repeat: Infinity, delay: i * 0.3 }}
        />
      ))}

      <div className="mx-auto max-w-7xl px-6">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="mx-auto max-w-4xl text-center"
        >
          <div className="mx-auto mb-6 inline-flex items-center gap-2 rounded-full glass px-4 py-1.5 text-xs font-medium">
            <Sparkles className="h-3.5 w-3.5 text-accent" />
            <span className="text-muted-foreground">
              Multi-Agent AI · Business Intelligence · Predictive Analytics
            </span>
          </div>

          <h1 className="text-balance text-5xl font-semibold leading-[1.05] sm:text-7xl">
            <span className="text-gradient">Transform Business Data</span>
            <br />
            into Intelligent Decisions.
          </h1>

          <p className="mx-auto mt-6 max-w-2xl text-pretty text-base text-muted-foreground sm:text-lg">
            CogniData is an AI-powered Business Analytics Platform that combines Artificial
            Intelligence, Machine Learning, Predictive Analytics, Natural Language Processing,
            and Multi-Agent AI to help organizations make smarter decisions — faster.
          </p>

          <div className="mt-9 flex flex-wrap items-center justify-center gap-3">
            <a
              href="#solution"
              className="group relative inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-primary to-secondary px-6 py-3 text-sm font-medium text-white shadow-[0_0_40px_-8px_oklch(0.58_0.24_295/0.9)] transition-transform hover:scale-[1.03]"
            >
              Explore Platform
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </a>
            <a
              href="#how"
              className="inline-flex items-center gap-2 rounded-full glass px-6 py-3 text-sm font-medium text-foreground transition-colors hover:bg-white/10"
            >
              <PlayCircle className="h-4 w-4 text-accent" />
              Watch Demo
            </a>
          </div>
        </motion.div>

        {/* Hero dashboard mock */}
        <motion.div
          initial={{ opacity: 0, y: 60, scale: 0.96 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 1, delay: 0.2, ease: "easeOut" }}
          className="relative mx-auto mt-16 max-w-5xl"
        >
          <div className="absolute -inset-4 -z-10 rounded-[2rem] bg-gradient-to-r from-primary/30 via-secondary/20 to-accent/30 blur-2xl animate-gradient" />
          <div className="glass-strong rounded-2xl p-3 shadow-[0_40px_120px_-20px_oklch(0.05_0.05_260/0.8)]">
            <div className="flex items-center gap-1.5 px-3 py-2">
              <span className="h-2.5 w-2.5 rounded-full bg-red-400/70" />
              <span className="h-2.5 w-2.5 rounded-full bg-yellow-400/70" />
              <span className="h-2.5 w-2.5 rounded-full bg-green-400/70" />
              <span className="ml-3 text-xs text-muted-foreground">cognidata.ai — Executive Dashboard</span>
            </div>
            <div className="grid gap-3 rounded-xl bg-background/60 p-4 sm:grid-cols-4">
              {[
                { icon: TrendingUp, label: "Revenue", value: "$2.48M", delta: "+18.4%" },
                { icon: LineChart, label: "Forecast Q4", value: "$3.10M", delta: "+24.9%" },
                { icon: Cpu, label: "AI Agents", value: "8 active", delta: "live" },
                { icon: Database, label: "Records", value: "1.2M rows", delta: "clean" },
              ].map((k) => (
                <div key={k.label} className="rounded-lg glass p-4">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <k.icon className="h-3.5 w-3.5 text-accent" />
                    {k.label}
                  </div>
                  <div className="mt-2 font-display text-2xl font-semibold">{k.value}</div>
                  <div className="mt-1 text-xs text-emerald-400">{k.delta}</div>
                </div>
              ))}
              <div className="col-span-full h-48 rounded-lg glass p-4">
                <MiniChart />
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

function MiniChart() {
  const points = [12, 22, 18, 30, 26, 40, 36, 52, 48, 60, 58, 74, 70, 88];
  const max = Math.max(...points);
  const w = 800;
  const h = 160;
  const step = w / (points.length - 1);
  const path = points
    .map((p, i) => `${i === 0 ? "M" : "L"} ${i * step} ${h - (p / max) * (h - 20) - 10}`)
    .join(" ");
  const area = `${path} L ${w} ${h} L 0 ${h} Z`;
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="h-full w-full">
      <defs>
        <linearGradient id="g1" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor="oklch(0.66 0.24 305)" stopOpacity="0.5" />
          <stop offset="100%" stopColor="oklch(0.66 0.24 305)" stopOpacity="0" />
        </linearGradient>
        <linearGradient id="g2" x1="0" x2="1" y1="0" y2="0">
          <stop offset="0%" stopColor="oklch(0.73 0.14 210)" />
          <stop offset="100%" stopColor="oklch(0.66 0.24 305)" />
        </linearGradient>
      </defs>
      <path d={area} fill="url(#g1)" />
      <path d={path} fill="none" stroke="url(#g2)" strokeWidth="2.5" strokeLinecap="round" />
      {points.map((p, i) => (
        <circle
          key={i}
          cx={i * step}
          cy={h - (p / max) * (h - 20) - 10}
          r="2.5"
          fill="oklch(0.99 0 0)"
        />
      ))}
    </svg>
  );
}
