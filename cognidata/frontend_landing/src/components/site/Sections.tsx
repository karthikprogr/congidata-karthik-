import { useState } from "react";
import { motion } from "framer-motion";
import {
  AlertTriangle, Clock, Database, Gauge, HelpCircle, LineChart, Wand2,
  Upload, ShieldCheck, Brush, MessageSquare, LayoutDashboard, BarChart3,
  Lightbulb, TrendingUp, Radar, Compass, Sparkles, FileText, Download,
  Bot, Users, Zap,
  ShoppingBag, HeartPulse, Banknote, GraduationCap, Factory, Truck, Shield, Store,
  Check, X, Github, Linkedin, Mail, Send, Server, Cpu, BrainCircuit, Layers,
  Boxes, Code2, Container, Sigma, PieChart, Workflow,
} from "lucide-react";
import { Section, GlassCard } from "./Primitives";

/* ---------- 2. Problem ---------- */
export function ProblemSection() {
  const problems = [
    { icon: Database, title: "Too much business data", desc: "Data scattered across CRMs, ERPs, spreadsheets and SaaS tools." },
    { icon: Gauge, title: "Complex dashboards", desc: "Analysts spend hours wrangling metrics that no one reads." },
    { icon: HelpCircle, title: "Manual decision making", desc: "Leaders rely on gut-feel instead of statistical evidence." },
    { icon: Wand2, title: "No intelligent recommendations", desc: "Tools show numbers, not actions." },
    { icon: Clock, title: "Time consuming analysis", desc: "Weeks of prep before a single insight lands." },
    { icon: LineChart, title: "Poor forecasting", desc: "Static charts, no probabilistic view of the future." },
    { icon: AlertTriangle, title: "Lack of AI assistance", desc: "Legacy BI cannot reason, explain, or recommend." },
  ];
  return (
    <Section
      id="problem"
      eyebrow="The Problem"
      title={<>Business teams are <span className="text-gradient">drowning in data</span>, starving for decisions.</>}
      subtitle="Traditional Business Intelligence stops at dashboards. Executives still have to interpret, correlate, and act — manually."
    >
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {problems.map((p, i) => (
          <motion.div
            key={p.title}
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.5, delay: i * 0.05 }}
          >
            <GlassCard>
              <div className="mb-4 inline-grid h-11 w-11 place-items-center rounded-xl bg-gradient-to-br from-destructive/30 to-primary/20 text-destructive-foreground">
                <p.icon className="h-5 w-5 text-red-300" />
              </div>
              <h3 className="text-lg font-semibold">{p.title}</h3>
              <p className="mt-2 text-sm text-muted-foreground">{p.desc}</p>
            </GlassCard>
          </motion.div>
        ))}
      </div>
    </Section>
  );
}

/* ---------- 3. Solution ---------- */
export function SolutionSection() {
  const steps = [
    { icon: Upload, label: "Upload dataset" },
    { icon: ShieldCheck, label: "AI cleans data" },
    { icon: BarChart3, label: "AI analyzes business" },
    { icon: LayoutDashboard, label: "Generates dashboards" },
    { icon: TrendingUp, label: "Forecasts future trends" },
    { icon: Radar, label: "Detects risks" },
    { icon: Lightbulb, label: "Suggests strategies" },
    { icon: FileText, label: "Generates reports" },
  ];
  return (
    <Section
      id="solution"
      eyebrow="Our Solution"
      title={<>Meet <span className="text-gradient">CogniData</span> — the AI analyst that never sleeps.</>}
      subtitle="Drop a dataset in. Get validated data, executive dashboards, forecasts, risk flags and boardroom-ready recommendations out."
    >
      <div className="grid items-stretch gap-4 md:grid-cols-4">
        {steps.map((s, i) => (
          <motion.div
            key={s.label}
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: i * 0.05 }}
          >
            <GlassCard className="h-full">
              <div className="flex items-center gap-3">
                <div className="grid h-10 w-10 place-items-center rounded-lg bg-gradient-to-br from-primary/40 to-accent/30">
                  <s.icon className="h-4.5 w-4.5 text-white" />
                </div>
                <span className="text-xs font-medium uppercase tracking-widest text-muted-foreground">
                  Step {String(i + 1).padStart(2, "0")}
                </span>
              </div>
              <div className="mt-4 font-display text-lg font-semibold">{s.label}</div>
            </GlassCard>
          </motion.div>
        ))}
      </div>
    </Section>
  );
}

/* ---------- 4. Features ---------- */
export function FeaturesSection() {
  const feats = [
    { icon: Upload, t: "Dataset Upload", d: "CSV, Excel, JSON, SQL — instant ingestion." },
    { icon: ShieldCheck, t: "Data Validation", d: "Schema, types and integrity checked automatically." },
    { icon: Brush, t: "Data Cleaning", d: "Missing values, outliers and duplicates handled by AI." },
    { icon: MessageSquare, t: "Natural Language Queries", d: "Ask business questions in plain English." },
    { icon: LayoutDashboard, t: "Business Dashboard", d: "Auto-generated executive dashboards." },
    { icon: BarChart3, t: "Interactive Charts", d: "Zoom, filter and drill down in real time." },
    { icon: Lightbulb, t: "Business Insights", d: "Trends and anomalies surfaced with context." },
    { icon: TrendingUp, t: "Forecasting", d: "Time-series projections with confidence bands." },
    { icon: Sigma, t: "Predictive Analytics", d: "ML models for churn, demand and revenue." },
    { icon: Radar, t: "Risk Analysis", d: "Detect financial, operational and market risk." },
    { icon: Compass, t: "Decision Support", d: "Scenario analysis and what-if modeling." },
    { icon: Sparkles, t: "Business Recommendations", d: "Strategic actions with expected impact." },
    { icon: FileText, t: "AI Report Generator", d: "Executive PDF reports in one click." },
    { icon: Download, t: "Download Reports", d: "Share with stakeholders instantly." },
    { icon: Bot, t: "Multi-Agent AI", d: "8 specialized agents cooperate on your data." },
    { icon: Users, t: "Role Based Access", d: "Analyst, manager and executive views." },
    { icon: Zap, t: "Real Time Analytics", d: "Streaming metrics with sub-second updates." },
    { icon: BrainCircuit, t: "Explainable AI", d: "Every insight ships with a reason." },
  ];
  return (
    <Section
      id="features"
      eyebrow="Features"
      title={<>Everything a modern analytics team <span className="text-gradient">actually needs</span>.</>}
      subtitle="From raw upload to executive report — one intelligent platform."
    >
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {feats.map((f, i) => (
          <motion.div
            key={f.t}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.4, delay: (i % 6) * 0.05 }}
          >
            <GlassCard className="h-full">
              <div className="mb-4 inline-grid h-10 w-10 place-items-center rounded-lg bg-gradient-to-br from-primary/30 via-secondary/20 to-accent/30">
                <f.icon className="h-5 w-5 text-white" />
              </div>
              <div className="font-display text-base font-semibold">{f.t}</div>
              <p className="mt-1.5 text-sm text-muted-foreground">{f.d}</p>
            </GlassCard>
          </motion.div>
        ))}
      </div>
    </Section>
  );
}

/* ---------- 5. How It Works ---------- */
export function HowItWorks() {
  const steps = [
    "Upload Dataset", "Validation Agent", "Cleaning Agent", "Analytics Agent",
    "Visualization Agent", "Forecast Agent", "Risk Agent",
    "Decision Support Agent", "Report Generation Agent", "Final Business Report",
  ];
  return (
    <Section
      id="how"
      eyebrow="How it works"
      title={<>An <span className="text-gradient">orchestrated pipeline</span> of AI agents.</>}
      subtitle="Each step is handled by a specialized agent that hands off structured context to the next."
    >
      <div className="relative">
        <div className="pointer-events-none absolute left-6 top-0 h-full w-px bg-gradient-to-b from-primary/60 via-secondary/40 to-accent/60 md:left-1/2" />
        <ol className="space-y-6">
          {steps.map((s, i) => (
            <motion.li
              key={s}
              initial={{ opacity: 0, x: i % 2 ? 30 : -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.5, delay: i * 0.05 }}
              className={`relative flex items-start gap-4 md:w-1/2 ${
                i % 2 ? "md:ml-auto md:pl-10" : "md:pr-10"
              }`}
            >
              <div className="absolute left-6 top-4 -translate-x-1/2 md:left-auto md:right-auto md:top-4"
                   style={{ [i % 2 ? "left" : "right"]: undefined }} />
              <div className={`relative z-10 grid h-12 w-12 shrink-0 place-items-center rounded-xl glass-strong ${
                i === steps.length - 1 ? "shadow-[0_0_30px_-4px_oklch(0.73_0.14_210/0.8)]" : ""
              } ${i % 2 ? "md:order-2" : ""}`}>
                <span className="font-display text-sm font-semibold text-gradient">{String(i + 1).padStart(2, "0")}</span>
              </div>
              <GlassCard className="min-w-0 flex-1">
                <div className="font-display text-lg font-semibold">{s}</div>
                <div className="mt-1 text-sm text-muted-foreground">
                  {i === 0
                    ? "User uploads business data in any structured format."
                    : i === steps.length - 1
                    ? "Executive-ready report with insights, forecasts and recommendations."
                    : "Autonomous agent processes context from previous step and emits structured output."}
                </div>
              </GlassCard>
            </motion.li>
          ))}
        </ol>
      </div>
    </Section>
  );
}

/* ---------- 6. Multi-Agent AI ---------- */
export function AgentsSection() {
  const agents = [
    { icon: ShieldCheck, name: "Validation Agent", desc: "Validates uploaded data schema and integrity." },
    { icon: Brush, name: "Cleaning Agent", desc: "Removes missing values, outliers and duplicates." },
    { icon: BarChart3, name: "Analytics Agent", desc: "Analyzes KPIs, cohorts and correlations." },
    { icon: LayoutDashboard, name: "Visualization Agent", desc: "Creates interactive dashboards automatically." },
    { icon: TrendingUp, name: "Forecast Agent", desc: "Predicts future business trajectories." },
    { icon: Radar, name: "Risk Agent", desc: "Identifies operational and financial risks." },
    { icon: Lightbulb, name: "Recommendation Agent", desc: "Suggests strategic next actions." },
    { icon: FileText, name: "Report Agent", desc: "Generates executive-ready reports." },
  ];
  return (
    <Section
      id="agents"
      eyebrow="Multi-Agent AI"
      title={<>Eight specialized agents. <span className="text-gradient">One shared brain.</span></>}
      subtitle="Agents collaborate through a shared context bus — passing insights, not just data."
    >
      {/* Orchestrator visualization */}
      <div className="relative mx-auto mb-14 aspect-[2/1] max-w-3xl">
        <div className="absolute inset-0 grid place-items-center">
          <div className="relative grid h-24 w-24 place-items-center rounded-2xl glass-strong glow-ring">
            <BrainCircuit className="h-10 w-10 text-white animate-pulse-glow" />
            <span className="absolute -bottom-7 whitespace-nowrap text-xs font-medium uppercase tracking-widest text-muted-foreground">
              Orchestrator
            </span>
          </div>
        </div>
        {agents.map((a, i) => {
          const angle = (i / agents.length) * Math.PI * 2 - Math.PI / 2;
          const rx = 45, ry = 40;
          const x = 50 + Math.cos(angle) * rx;
          const y = 50 + Math.sin(angle) * ry;
          return (
            <motion.div
              key={a.name}
              initial={{ opacity: 0, scale: 0.6 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.08 }}
              className="absolute -translate-x-1/2 -translate-y-1/2"
              style={{ left: `${x}%`, top: `${y}%` }}
            >
              <div className="grid h-12 w-12 place-items-center rounded-xl glass-strong animate-float"
                   style={{ animationDelay: `${i * 0.4}s` }}>
                <a.icon className="h-5 w-5 text-accent" />
              </div>
            </motion.div>
          );
        })}
        {/* connection lines */}
        <svg className="pointer-events-none absolute inset-0 h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none">
          {agents.map((_, i) => {
            const angle = (i / agents.length) * Math.PI * 2 - Math.PI / 2;
            const x = 50 + Math.cos(angle) * 45;
            const y = 50 + Math.sin(angle) * 40;
            return (
              <line key={i} x1="50" y1="50" x2={x} y2={y}
                    stroke="url(#agent-line)" strokeWidth="0.15" strokeDasharray="0.6 0.6" />
            );
          })}
          <defs>
            <linearGradient id="agent-line" x1="0" x2="1">
              <stop offset="0%" stopColor="oklch(0.58 0.24 295)" />
              <stop offset="100%" stopColor="oklch(0.73 0.14 210)" />
            </linearGradient>
          </defs>
        </svg>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {agents.map((a, i) => (
          <motion.div
            key={a.name}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: i * 0.05 }}
          >
            <GlassCard className="h-full">
              <div className="mb-3 grid h-10 w-10 place-items-center rounded-lg bg-gradient-to-br from-primary/40 to-accent/30">
                <a.icon className="h-5 w-5 text-white" />
              </div>
              <div className="font-display text-base font-semibold">{a.name}</div>
              <p className="mt-1.5 text-sm text-muted-foreground">{a.desc}</p>
            </GlassCard>
          </motion.div>
        ))}
      </div>
    </Section>
  );
}

/* ---------- 7. Architecture ---------- */
export function ArchitectureSection() {
  const layers = [
    { icon: Users, name: "User", d: "Analyst, Manager, Executive" },
    { icon: Layers, name: "Frontend", d: "React · TypeScript · Tailwind" },
    { icon: Server, name: "Backend API", d: "FastAPI · REST · Auth" },
    { icon: BrainCircuit, name: "AI Engine", d: "LLM + NLP orchestration" },
    { icon: Bot, name: "Multi-Agent AI", d: "8 specialized agents" },
    { icon: Cpu, name: "Machine Learning", d: "Scikit-learn · Pandas · NumPy" },
    { icon: Database, name: "Database", d: "PostgreSQL" },
    { icon: PieChart, name: "Visualization Engine", d: "Plotly · Matplotlib" },
    { icon: LayoutDashboard, name: "Dashboard", d: "Real-time executive UI" },
  ];
  return (
    <Section
      id="architecture"
      eyebrow="System Architecture"
      title={<>A <span className="text-gradient">layered, modular</span> AI stack.</>}
      subtitle="Every layer is independently scalable and observable."
    >
      <div className="mx-auto grid max-w-3xl gap-3">
        {layers.map((l, i) => (
          <motion.div
            key={l.name}
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: i * 0.04 }}
            className="relative"
          >
            <GlassCard hover={false} className="flex items-center gap-4">
              <div className="grid h-11 w-11 shrink-0 place-items-center rounded-lg bg-gradient-to-br from-primary/40 to-accent/30">
                <l.icon className="h-5 w-5 text-white" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="font-display text-base font-semibold">{l.name}</div>
                <div className="text-sm text-muted-foreground">{l.d}</div>
              </div>
              <span className="hidden text-xs font-medium uppercase tracking-widest text-muted-foreground sm:block">
                Layer {String(i + 1).padStart(2, "0")}
              </span>
            </GlassCard>
            {i < layers.length - 1 && (
              <div className="my-1 flex justify-center">
                <div className="h-6 w-px bg-gradient-to-b from-primary/70 to-accent/50" />
              </div>
            )}
          </motion.div>
        ))}
      </div>
    </Section>
  );
}

/* ---------- 8. Tech Stack ---------- */
export function TechStackSection() {
  const groups = [
    { title: "Frontend", icon: Layers, items: ["React", "TypeScript", "Tailwind CSS"] },
    { title: "Backend", icon: Server, items: ["Python", "FastAPI"] },
    { title: "Database", icon: Database, items: ["PostgreSQL"] },
    { title: "Machine Learning", icon: Cpu, items: ["Scikit-learn", "Pandas", "NumPy"] },
    { title: "Visualization", icon: PieChart, items: ["Plotly", "Matplotlib"] },
    { title: "Artificial Intelligence", icon: BrainCircuit, items: ["OpenAI API", "Natural Language Processing"] },
    { title: "Deployment", icon: Container, items: ["Docker"] },
    { title: "Orchestration", icon: Workflow, items: ["Multi-Agent Framework"] },
  ];
  return (
    <Section
      id="stack"
      eyebrow="Technology Stack"
      title={<>Built on <span className="text-gradient">production-grade</span> tools.</>}
    >
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {groups.map((g, i) => (
          <motion.div
            key={g.title}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: i * 0.05 }}
          >
            <GlassCard className="h-full">
              <div className="mb-3 flex items-center gap-3">
                <div className="grid h-9 w-9 place-items-center rounded-lg bg-gradient-to-br from-primary/40 to-accent/30">
                  <g.icon className="h-4.5 w-4.5 text-white" />
                </div>
                <div className="font-display text-sm font-semibold uppercase tracking-widest text-muted-foreground">
                  {g.title}
                </div>
              </div>
              <ul className="space-y-1.5">
                {g.items.map((it) => (
                  <li key={it} className="flex items-center gap-2 text-sm">
                    <Code2 className="h-3.5 w-3.5 text-accent" />
                    {it}
                  </li>
                ))}
              </ul>
            </GlassCard>
          </motion.div>
        ))}
      </div>
    </Section>
  );
}

/* ---------- 9. Business Applications ---------- */
export function ApplicationsSection() {
  const apps = [
    { icon: ShoppingBag, name: "Retail", d: "Demand forecasting & inventory intelligence." },
    { icon: HeartPulse, name: "Healthcare", d: "Patient analytics & operational KPIs." },
    { icon: Banknote, name: "Finance", d: "Risk modeling & portfolio insights." },
    { icon: Factory, name: "Manufacturing", d: "OEE, yield and predictive maintenance." },
    { icon: Truck, name: "Logistics", d: "Route optimization & delivery insights." },
    { icon: Shield, name: "Insurance", d: "Claims analytics & fraud detection." },
    { icon: GraduationCap, name: "Education", d: "Learning outcomes & retention analytics." },
    { icon: Store, name: "E-Commerce", d: "Conversion, LTV and cohort intelligence." },
    { icon: Boxes, name: "Small Business", d: "Enterprise-grade analytics, zero setup." },
    { icon: Layers, name: "Large Enterprise", d: "Scales to millions of records & users." },
    { icon: Users, name: "Analysts & Managers", d: "Ship insights without writing SQL." },
    { icon: Compass, name: "CEOs & Executives", d: "Boardroom-ready intelligence on demand." },
  ];
  return (
    <Section
      id="applications"
      eyebrow="Business Applications"
      title={<>Built for <span className="text-gradient">every industry</span> that runs on data.</>}
    >
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {apps.map((a, i) => (
          <motion.div
            key={a.name}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: i * 0.04 }}
          >
            <GlassCard className="h-full">
              <div className="mb-3 grid h-11 w-11 place-items-center rounded-xl bg-gradient-to-br from-primary/40 to-accent/30">
                <a.icon className="h-5 w-5 text-white" />
              </div>
              <div className="font-display text-base font-semibold">{a.name}</div>
              <p className="mt-1.5 text-sm text-muted-foreground">{a.d}</p>
            </GlassCard>
          </motion.div>
        ))}
      </div>
    </Section>
  );
}

/* ---------- 10. Comparison ---------- */
export function ComparisonSection() {
  const rows = [
    { f: "Interactive dashboards", legacy: true, cogni: true },
    { f: "Natural language AI queries", legacy: false, cogni: true },
    { f: "Automated forecasting", legacy: false, cogni: true },
    { f: "Strategic recommendations", legacy: false, cogni: true },
    { f: "Decision support & what-if", legacy: false, cogni: true },
    { f: "Multi-Agent AI orchestration", legacy: false, cogni: true },
    { f: "Explainable AI insights", legacy: false, cogni: true },
    { f: "Manual analyst effort", legacy: true, cogni: false },
  ];
  return (
    <Section
      id="comparison"
      eyebrow="Comparison"
      title={<>Traditional BI vs <span className="text-gradient">CogniData</span></>}
      subtitle="Power BI, Tableau, Looker — great at charts. CogniData reasons about your business."
    >
      <div className="mx-auto max-w-4xl overflow-hidden rounded-2xl glass-strong">
        <div className="grid grid-cols-[minmax(0,1fr)_auto_auto] items-center gap-4 border-b border-white/10 px-6 py-4 text-xs font-semibold uppercase tracking-widest text-muted-foreground">
          <div>Capability</div>
          <div className="w-24 text-center">Legacy BI</div>
          <div className="w-24 text-center text-gradient">CogniData</div>
        </div>
        {rows.map((r) => (
          <div key={r.f} className="grid grid-cols-[minmax(0,1fr)_auto_auto] items-center gap-4 border-b border-white/5 px-6 py-4 last:border-b-0">
            <div className="text-sm">{r.f}</div>
            <div className="grid w-24 place-items-center">
              {r.legacy ? <Check className="h-4 w-4 text-emerald-400" /> : <X className="h-4 w-4 text-muted-foreground/60" />}
            </div>
            <div className="grid w-24 place-items-center">
              {r.cogni ? <Check className="h-4 w-4 text-accent" /> : <X className="h-4 w-4 text-muted-foreground/60" />}
            </div>
          </div>
        ))}
      </div>
    </Section>
  );
}

/* ---------- Research Foundation ---------- */
export function ResearchFoundationSection() {
  const pillars = [
    "Business Intelligence", "Artificial Intelligence", "Machine Learning",
    "Decision Support Systems", "Predictive Analytics", "Explainable AI",
    "Natural Language Processing", "Multi-Agent AI",
  ];
  const stats = [
    { k: "20+", v: "Research Papers Studied" },
    { k: "8", v: "Disciplines Combined" },
    { k: "100%", v: "Research-Driven Design" },
  ];
  return (
    <Section
      id="research"
      eyebrow="Research Foundation"
      title={<>Grounded in <span className="text-gradient">peer-reviewed research</span>.</>}
      subtitle="CogniData was developed after studying 20+ recent research papers across BI, AI, ML, Decision Support, Predictive Analytics, Explainable AI, NLP and Multi-Agent AI."
    >
      <div className="mx-auto mb-10 grid max-w-4xl gap-4 sm:grid-cols-3">
        {stats.map((s) => (
          <GlassCard key={s.v} className="text-center">
            <div className="font-display text-4xl font-semibold text-gradient">{s.k}</div>
            <div className="mt-2 text-xs font-medium uppercase tracking-widest text-muted-foreground">{s.v}</div>
          </GlassCard>
        ))}
      </div>
      <div className="mx-auto flex max-w-3xl flex-wrap justify-center gap-3">
        {pillars.map((p, i) => (
          <motion.span
            key={p}
            initial={{ opacity: 0, scale: 0.8 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: i * 0.05 }}
            className="rounded-full glass px-5 py-2.5 text-sm font-medium"
          >
            {p}
          </motion.span>
        ))}
      </div>
    </Section>
  );
}

/* ---------- Existing Solutions ---------- */
export function ExistingSolutionsSection() {
  const tools = [
    { name: "Power BI", d: "Interactive dashboards, but no autonomous reasoning." },
    { name: "Tableau", d: "Great visualization, still requires an analyst to interpret." },
    { name: "Looker", d: "Modelled BI, limited AI and no strategic recommendations." },
    { name: "Traditional Reporting", d: "Static reports that arrive too late to act on." },
  ];
  const limits = [
    "Dashboard only — no decision support",
    "Manual interpretation required",
    "Technical expertise needed to operate",
    "Limited AI & no Multi-Agent reasoning",
    "Weak forecasting & no risk detection",
    "No natural language business queries",
  ];
  return (
    <Section
      id="existing"
      eyebrow="Existing Solutions"
      title={<>Today's BI tools stop <span className="text-gradient">where decisions begin</span>.</>}
      subtitle="Power BI, Tableau and Looker are visualization-first. They show the numbers — they don't explain, forecast or recommend."
    >
      <div className="grid gap-4 md:grid-cols-2">
        <div className="grid gap-3 sm:grid-cols-2">
          {tools.map((t) => (
            <GlassCard key={t.name}>
              <div className="font-display text-base font-semibold">{t.name}</div>
              <p className="mt-1.5 text-sm text-muted-foreground">{t.d}</p>
            </GlassCard>
          ))}
        </div>
        <GlassCard hover={false}>
          <div className="mb-3 text-xs font-medium uppercase tracking-widest text-muted-foreground">
            Common Limitations
          </div>
          <ul className="space-y-2.5">
            {limits.map((l) => (
              <li key={l} className="flex items-start gap-2 text-sm">
                <X className="mt-0.5 h-4 w-4 shrink-0 text-red-400" /> {l}
              </li>
            ))}
          </ul>
        </GlassCard>
      </div>
    </Section>
  );
}

/* ---------- Research Gap ---------- */
export function ResearchGapSection() {
  const current = ["Dashboards", "Charts", "Static Reports", "Manual KPIs"];
  const missing = [
    "AI-Powered Recommendations",
    "Business Decision Support",
    "Multi-Agent AI Orchestration",
    "Unified Analytics Platform",
    "Natural Language Business Queries",
    "Explainable Forecasts & Risk",
  ];
  return (
    <Section
      id="gap"
      eyebrow="Research Gap"
      title={<>The gap between <span className="text-gradient">seeing data</span> and making decisions.</>}
      subtitle="CogniData was designed specifically to close the intelligence gap left by traditional BI platforms."
    >
      <div className="mx-auto grid max-w-5xl gap-6 md:grid-cols-2">
        <GlassCard hover={false}>
          <div className="mb-3 text-xs font-medium uppercase tracking-widest text-muted-foreground">
            What Current Systems Provide
          </div>
          <ul className="space-y-2.5">
            {current.map((c) => (
              <li key={c} className="flex items-center gap-2 text-sm">
                <Check className="h-4 w-4 text-muted-foreground" /> {c}
              </li>
            ))}
          </ul>
        </GlassCard>
        <GlassCard hover={false} className="glow-ring">
          <div className="mb-3 text-xs font-medium uppercase tracking-widest text-gradient">
            What CogniData Adds
          </div>
          <ul className="space-y-2.5">
            {missing.map((m) => (
              <li key={m} className="flex items-center gap-2 text-sm">
                <Check className="h-4 w-4 text-accent" /> {m}
              </li>
            ))}
          </ul>
        </GlassCard>
      </div>
    </Section>
  );
}

/* ---------- What Clients Can Do ---------- */
export function WhatClientsSection() {
  const actions = [
    { icon: Upload, t: "Upload business datasets" },
    { icon: ShieldCheck, t: "Validate data automatically" },
    { icon: Brush, t: "Clean missing values & outliers" },
    { icon: LayoutDashboard, t: "Generate business dashboards" },
    { icon: BarChart3, t: "Analyze KPIs & cohorts" },
    { icon: TrendingUp, t: "Predict future trends" },
    { icon: Radar, t: "Detect business risks" },
    { icon: Lightbulb, t: "Receive AI recommendations" },
    { icon: FileText, t: "Generate reports automatically" },
    { icon: MessageSquare, t: "Ask questions in plain English" },
    { icon: Gauge, t: "Monitor business performance" },
    { icon: Compass, t: "Support strategic decisions" },
  ];
  return (
    <Section
      id="capabilities"
      eyebrow="What Clients Can Do"
      title={<>From raw data to <span className="text-gradient">boardroom decisions</span> — in minutes.</>}
      subtitle="Every organization using CogniData unlocks a full AI analytics workflow out of the box."
    >
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {actions.map((a, i) => (
          <motion.div key={a.t}
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.35, delay: (i % 6) * 0.05 }}
          >
            <GlassCard className="flex items-center gap-3">
              <div className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-gradient-to-br from-primary/40 to-accent/30">
                <a.icon className="h-5 w-5 text-white" />
              </div>
              <div className="text-sm font-medium">{a.t}</div>
            </GlassCard>
          </motion.div>
        ))}
      </div>
    </Section>
  );
}

/* ---------- Modules ---------- */
export function ModulesSection() {
  const mods = [
    { icon: Database, t: "Dataset Module", d: "Ingestion, storage & versioning of business data." },
    { icon: BarChart3, t: "Analytics Module", d: "KPI, cohort & correlation analysis engine." },
    { icon: LayoutDashboard, t: "Dashboard Module", d: "Auto-generated executive dashboards." },
    { icon: Bot, t: "AI Assistant Module", d: "Chat interface for natural language queries." },
    { icon: TrendingUp, t: "Forecasting Module", d: "Time-series predictions with confidence bands." },
    { icon: Lightbulb, t: "Recommendation Module", d: "Strategic actions with expected impact." },
    { icon: FileText, t: "Reports Module", d: "One-click executive PDF report generation." },
    { icon: Shield, t: "Admin Module", d: "Users, roles, permissions & audit logs." },
  ];
  return (
    <Section
      id="modules"
      eyebrow="Platform Modules"
      title={<>Eight <span className="text-gradient">composable modules</span>, one unified platform.</>}
    >
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {mods.map((m, i) => (
          <motion.div key={m.t}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: i * 0.05 }}
          >
            <GlassCard className="h-full">
              <div className="mb-3 grid h-10 w-10 place-items-center rounded-lg bg-gradient-to-br from-primary/40 to-accent/30">
                <m.icon className="h-5 w-5 text-white" />
              </div>
              <div className="font-display text-base font-semibold">{m.t}</div>
              <p className="mt-1.5 text-sm text-muted-foreground">{m.d}</p>
            </GlassCard>
          </motion.div>
        ))}
      </div>
    </Section>
  );
}

/* ---------- Live Dashboard Preview ---------- */
export function DashboardPreviewSection() {
  const kpis = [
    { label: "Revenue", value: "$2.48M", delta: "+18.4%", icon: TrendingUp },
    { label: "Sales", value: "42,180", delta: "+9.1%", icon: BarChart3 },
    { label: "Profit", value: "$612K", delta: "+22.7%", icon: Sigma },
    { label: "Forecast Q4", value: "$3.10M", delta: "+24.9%", icon: LineChart },
    { label: "Inventory", value: "94%", delta: "healthy", icon: Boxes },
    { label: "Customer Growth", value: "+12.6%", delta: "MoM", icon: Users },
  ];
  const recs = [
    "Increase ad spend on Segment A — projected +14% CVR.",
    "Restock SKU #4821 within 6 days to prevent stockout.",
    "Churn risk detected in 214 accounts — trigger retention flow.",
  ];
  return (
    <Section
      id="dashboard"
      eyebrow="Live Dashboard Preview"
      title={<>An <span className="text-gradient">executive-ready</span> control room.</>}
      subtitle="Real-time KPIs, AI forecasts and prescriptive recommendations — all in one view."
    >
      <div className="mx-auto max-w-6xl">
        <div className="glass-strong rounded-2xl p-3 shadow-card">
          <div className="flex items-center gap-1.5 px-3 py-2">
            <span className="h-2.5 w-2.5 rounded-full bg-red-400/70" />
            <span className="h-2.5 w-2.5 rounded-full bg-yellow-400/70" />
            <span className="h-2.5 w-2.5 rounded-full bg-green-400/70" />
            <span className="ml-3 text-xs text-muted-foreground">cognidata.ai — Executive Dashboard</span>
          </div>
          <div className="grid gap-3 rounded-xl bg-background/60 p-4 lg:grid-cols-3">
            <div className="lg:col-span-2 grid gap-3 sm:grid-cols-3">
              {kpis.map((k) => (
                <div key={k.label} className="rounded-lg glass p-4">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <k.icon className="h-3.5 w-3.5 text-accent" />
                    {k.label}
                  </div>
                  <div className="mt-2 font-display text-xl font-semibold">{k.value}</div>
                  <div className="mt-1 text-xs text-emerald-400">{k.delta}</div>
                </div>
              ))}
            </div>
            <div className="rounded-lg glass p-4">
              <div className="mb-3 flex items-center gap-2 text-xs font-medium uppercase tracking-widest text-muted-foreground">
                <Sparkles className="h-3.5 w-3.5 text-accent" /> AI Recommendations
              </div>
              <ul className="space-y-3 text-sm">
                {recs.map((r) => (
                  <li key={r} className="flex items-start gap-2">
                    <Lightbulb className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
                    <span className="text-muted-foreground">{r}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </Section>
  );
}

/* ---------- Client Benefits ---------- */
export function ClientBenefitsSection() {
  const benefits = [
    { icon: Clock, t: "Reduce manual reporting", d: "Automate hours of weekly analyst work." },
    { icon: Zap, t: "Faster decision making", d: "Insight to action in minutes, not weeks." },
    { icon: TrendingUp, t: "Better forecasting", d: "Probabilistic projections you can trust." },
    { icon: Lightbulb, t: "AI recommendations", d: "Next-best-action baked into every insight." },
    { icon: Radar, t: "Risk detection", d: "Spot financial and operational risk early." },
    { icon: Gauge, t: "Improved productivity", d: "Free analysts from repetitive reporting." },
    { icon: Compass, t: "Data-driven strategy", d: "Every decision backed by evidence." },
    { icon: Sigma, t: "Cost reduction", d: "Consolidate BI, ML and reporting tools." },
    { icon: Workflow, t: "Operational efficiency", d: "Streamline analytics across every team." },
  ];
  return (
    <Section
      id="benefits"
      eyebrow="Client Benefits"
      title={<>Measurable <span className="text-gradient">business impact</span> from day one.</>}
    >
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {benefits.map((b, i) => (
          <motion.div key={b.t}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: (i % 6) * 0.05 }}
          >
            <GlassCard className="h-full">
              <div className="mb-3 grid h-10 w-10 place-items-center rounded-lg bg-gradient-to-br from-accent/40 to-primary/30">
                <b.icon className="h-5 w-5 text-white" />
              </div>
              <div className="font-display text-base font-semibold">{b.t}</div>
              <p className="mt-1.5 text-sm text-muted-foreground">{b.d}</p>
            </GlassCard>
          </motion.div>
        ))}
      </div>
    </Section>
  );
}

/* ---------- 12. Future Scope ---------- */
export function FutureScopeSection() {
  const items = [
    { icon: Sparkles, t: "Generative AI", d: "Auto-generate narratives and reports." },
    { icon: Boxes, t: "AutoML", d: "Self-selecting models for every dataset." },
    { icon: Bot, t: "Autonomous Business Agents", d: "Agents that act, not just advise." },
    { icon: MessageSquare, t: "Voice Analytics", d: "Ask your business anything, out loud." },
    { icon: Zap, t: "Real-time Streaming", d: "Sub-second decisioning on live data." },
    { icon: Layers, t: "Digital Twins", d: "Simulate your business in silico." },
    { icon: Compass, t: "Predictive Decision Intelligence", d: "Recommend the next best action." },
  ];
  return (
    <Section
      id="future"
      eyebrow="Future Scope"
      title={<>Where CogniData is <span className="text-gradient">headed next</span>.</>}
    >
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((it, i) => (
          <motion.div key={it.t}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: i * 0.05 }}
          >
            <GlassCard className="h-full">
              <div className="mb-3 grid h-10 w-10 place-items-center rounded-lg bg-gradient-to-br from-accent/40 to-primary/30">
                <it.icon className="h-5 w-5 text-white" />
              </div>
              <div className="font-display text-base font-semibold">{it.t}</div>
              <p className="mt-1.5 text-sm text-muted-foreground">{it.d}</p>
            </GlassCard>
          </motion.div>
        ))}
      </div>
    </Section>
  );
}

/* ---------- 13. About + 14. Team ---------- */
export function AboutSection() {
  return (
    <Section
      id="about"
      eyebrow="About the Project"
      title={<>A <span className="text-gradient">Final Year Project</span> built to change how business decides.</>}
      subtitle="CogniData is an AI-based Business Analytics Platform developed for intelligent decision making — combining research from BI, AI, ML and Multi-Agent Systems."
    >
      <div className="grid gap-4 md:grid-cols-4">
        {[
          { label: "Developer", value: "Your Name" },
          { label: "Project Guide", value: "Prof. Guide Name" },
          { label: "College", value: "Your College" },
          { label: "Duration", value: "2025 — 2026" },
        ].map((t) => (
          <GlassCard key={t.label} className="text-center">
            <div className="text-xs font-medium uppercase tracking-widest text-muted-foreground">
              {t.label}
            </div>
            <div className="mt-2 font-display text-lg font-semibold">{t.value}</div>
          </GlassCard>
        ))}
      </div>
    </Section>
  );
}

/* ---------- 15. FAQ ---------- */
import { ChevronDown } from "lucide-react";

export function FaqSection() {
  const faqs = [
    { q: "What is CogniData?", a: "CogniData is an AI-powered Business Analytics Platform that combines BI, ML, forecasting and Multi-Agent AI to turn raw data into decisions." },
    { q: "How is it different from Power BI or Tableau?", a: "Legacy tools stop at dashboards. CogniData reasons about your business — forecasting, recommending strategies, explaining insights and generating reports." },
    { q: "What is Multi-Agent AI?", a: "Instead of one large model doing everything, CogniData uses 8 specialized agents (validation, cleaning, analytics, visualization, forecasting, risk, recommendations, reporting) that cooperate through a shared context." },
    { q: "Can non-technical users use it?", a: "Yes. Natural Language Queries let anyone ask business questions in plain English and get an intelligent answer." },
    { q: "Can it forecast business trends?", a: "Yes — the Forecast Agent uses time-series ML to project revenue, demand and other KPIs with confidence intervals." },
  ];
  const [open, setOpen] = useState<number | null>(0);
  return (
    <Section
      id="faq"
      eyebrow="FAQ"
      title={<>Common <span className="text-gradient">questions</span>.</>}
    >
      <div className="mx-auto max-w-3xl space-y-3">
        {faqs.map((f, i) => {
          const isOpen = open === i;
          return (
            <GlassCard key={f.q} hover={false} className="!p-0">
              <button
                onClick={() => setOpen(isOpen ? null : i)}
                className="flex w-full items-center justify-between gap-4 px-6 py-5 text-left"
              >
                <span className="font-display text-base font-semibold">{f.q}</span>
                <ChevronDown className={`h-4 w-4 shrink-0 text-muted-foreground transition-transform ${isOpen ? "rotate-180" : ""}`} />
              </button>
              <div className={`grid overflow-hidden transition-[grid-template-rows] duration-300 ${isOpen ? "grid-rows-[1fr]" : "grid-rows-[0fr]"}`}>
                <div className="min-h-0">
                  <p className="px-6 pb-5 text-sm text-muted-foreground">{f.a}</p>
                </div>
              </div>
            </GlassCard>
          );
        })}
      </div>
    </Section>
  );
}

/* ---------- 16. Contact ---------- */
export function ContactSection() {
  return (
    <Section
      id="contact"
      eyebrow="Contact"
      title={<>Let's <span className="text-gradient">talk data</span>.</>}
      subtitle="Reach out about the project, research, collaboration or a demo."
    >
      <div className="mx-auto grid max-w-4xl gap-6 lg:grid-cols-[1.2fr_1fr]">
        <GlassCard hover={false}>
          <form
            className="space-y-4"
            onSubmit={(e) => {
              e.preventDefault();
              alert("Thanks! This is a demo form — wire it to your backend.");
            }}
          >
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Name" name="name" placeholder="Ada Lovelace" />
              <Field label="Email" name="email" type="email" placeholder="you@company.com" />
            </div>
            <Field label="Subject" name="subject" placeholder="Demo request" />
            <div>
              <label className="mb-1.5 block text-xs font-medium uppercase tracking-widest text-muted-foreground">
                Message
              </label>
              <textarea
                required
                rows={5}
                className="w-full rounded-xl bg-white/5 px-4 py-3 text-sm outline-none ring-1 ring-white/10 transition focus:ring-primary/60"
                placeholder="Tell us about your data & goals…"
              />
            </div>
            <button
              type="submit"
              className="group inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-primary to-secondary px-5 py-2.5 text-sm font-medium text-white shadow-[0_0_30px_-6px_oklch(0.58_0.24_295/0.9)] transition-transform hover:scale-[1.03]"
            >
              Send message
              <Send className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </button>
          </form>
        </GlassCard>

        <div className="space-y-3">
          {[
            { icon: Mail, label: "Email", value: "hello@cognidata.ai" },
            { icon: Linkedin, label: "LinkedIn", value: "linkedin.com/in/cognidata" },
            { icon: Github, label: "GitHub", value: "github.com/cognidata" },
          ].map((c) => (
            <GlassCard key={c.label} className="flex items-center gap-4">
              <div className="grid h-11 w-11 place-items-center rounded-xl bg-gradient-to-br from-primary/40 to-accent/30">
                <c.icon className="h-5 w-5 text-white" />
              </div>
              <div className="min-w-0">
                <div className="text-xs font-medium uppercase tracking-widest text-muted-foreground">
                  {c.label}
                </div>
                <div className="truncate font-display text-sm font-semibold">{c.value}</div>
              </div>
            </GlassCard>
          ))}
        </div>
      </div>
    </Section>
  );
}

function Field({ label, name, type = "text", placeholder }: { label: string; name: string; type?: string; placeholder?: string }) {
  return (
    <div>
      <label htmlFor={name} className="mb-1.5 block text-xs font-medium uppercase tracking-widest text-muted-foreground">
        {label}
      </label>
      <input
        id={name}
        name={name}
        type={type}
        required
        placeholder={placeholder}
        className="w-full rounded-xl bg-white/5 px-4 py-2.5 text-sm outline-none ring-1 ring-white/10 transition focus:ring-primary/60"
      />
    </div>
  );
}

/* ---------- Footer ---------- */
export function Footer() {
  return (
    <footer className="relative border-t border-white/5 py-14">
      <div className="mx-auto max-w-7xl px-6">
        <div className="grid gap-10 md:grid-cols-4">
          <div className="md:col-span-2">
            <div className="flex items-center gap-2">
              <div className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-primary to-secondary shadow-[0_0_20px_-4px_oklch(0.58_0.24_295/0.8)]">
                <BrainCircuit className="h-4 w-4 text-white" />
              </div>
              <span className="font-display text-lg font-semibold tracking-tight">
                Cogni<span className="text-gradient">Data</span>
              </span>
            </div>
            <p className="mt-4 max-w-sm text-sm text-muted-foreground">
              An Intelligent Business Analytics Platform using Multi-Agent AI. A Final Year Project.
            </p>
          </div>
          <div>
            <div className="mb-3 text-xs font-medium uppercase tracking-widest text-muted-foreground">
              Explore
            </div>
            <ul className="space-y-2 text-sm">
              {[
                ["Problem", "#problem"], ["Solution", "#solution"], ["Features", "#features"],
                ["Agents", "#agents"], ["Architecture", "#architecture"], ["FAQ", "#faq"],
              ].map(([l, h]) => (
                <li key={l}><a href={h} className="text-muted-foreground transition-colors hover:text-foreground">{l}</a></li>
              ))}
            </ul>
          </div>
          <div>
            <div className="mb-3 text-xs font-medium uppercase tracking-widest text-muted-foreground">
              Connect
            </div>
            <div className="flex gap-2">
              {[Github, Linkedin, Mail].map((I, i) => (
                <a key={i} href="#contact" className="grid h-9 w-9 place-items-center rounded-lg glass transition-colors hover:bg-white/10">
                  <I className="h-4 w-4" />
                </a>
              ))}
            </div>
          </div>
        </div>
        <div className="mt-10 flex flex-col items-center justify-between gap-4 border-t border-white/5 pt-6 text-xs text-muted-foreground sm:flex-row">
          <div>© {new Date().getFullYear()} CogniData. All rights reserved.</div>
          <div>Crafted with intelligence — for intelligent decisions.</div>
        </div>
      </div>
    </footer>
  );
}
