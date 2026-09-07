import { Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Brain, X, LogIn, CalendarCheck } from "lucide-react";

const NAV = [
  { href: "#problem",      label: "Problem" },
  { href: "#solution",     label: "Solution" },
  { href: "#features",     label: "Features" },
  { href: "#agents",       label: "Agents" },
  { href: "#architecture", label: "Architecture" },
  { href: "#faq",          label: "FAQ" },
];

/* ── Request-a-Demo modal ─────────────────────────────────────────── */
function DemoModal({ onClose }: { onClose: () => void }) {
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    await new Promise((r) => setTimeout(r, 1200));
    setLoading(false);
    setSent(true);
  };

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center p-4"
      style={{ background: "rgba(0,0,0,0.75)", backdropFilter: "blur(8px)" }}
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-md rounded-2xl border p-8"
        style={{
          background: "#0a0a0a",
          border: "1px solid rgba(250,204,21,0.2)",
          boxShadow: "0 0 60px -10px rgba(250,204,21,0.25)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute right-4 top-4 rounded-lg p-1.5 text-zinc-500 transition hover:text-white"
        >
          <X className="h-4 w-4" />
        </button>

        {sent ? (
          <div className="py-6 text-center">
            <div className="mx-auto mb-4 grid h-14 w-14 place-items-center rounded-full"
              style={{ background: "rgba(250,204,21,0.15)", border: "1px solid rgba(250,204,21,0.3)" }}>
              <CalendarCheck className="h-7 w-7 text-yellow-400" />
            </div>
            <h3 className="text-xl font-semibold">You're on the list!</h3>
            <p className="mt-2 text-sm text-zinc-400">
              We'll reach out within 24 hours to schedule your personalised demo.
            </p>
            <button onClick={onClose}
              className="mt-6 w-full rounded-xl py-2.5 text-sm font-medium transition"
              style={{ background: "rgba(250,204,21,0.12)", color: "#facc15", border: "1px solid rgba(250,204,21,0.25)" }}>
              Close
            </button>
          </div>
        ) : (
          <>
            <div className="mb-6 flex items-center gap-3">
              <div className="grid h-10 w-10 place-items-center rounded-xl"
                style={{ background: "linear-gradient(135deg,#facc15,#f59e0b)" }}>
                <Brain className="h-5 w-5 text-black" />
              </div>
              <div>
                <h2 className="text-lg font-semibold">Request a Demo</h2>
                <p className="text-xs text-zinc-500">See CogniData in action — live.</p>
              </div>
            </div>

            <form onSubmit={submit} className="flex flex-col gap-4">
              {[
                { name: "name",    label: "Full Name",    type: "text",  ph: "Jane Smith" },
                { name: "email",   label: "Work Email",   type: "email", ph: "jane@company.com" },
                { name: "company", label: "Company",      type: "text",  ph: "Acme Corp" },
              ].map(({ name, label, type, ph }) => (
                <div key={name}>
                  <label className="mb-1.5 block text-xs font-medium uppercase tracking-widest text-zinc-500">
                    {label}
                  </label>
                  <input
                    name={name} type={type} required placeholder={ph}
                    className="w-full rounded-xl px-4 py-2.5 text-sm outline-none transition"
                    style={{
                      background: "rgba(255,255,255,0.05)",
                      border: "1px solid rgba(255,255,255,0.1)",
                      color: "#fff",
                    }}
                  />
                </div>
              ))}

              <button
                type="submit" disabled={loading}
                className="mt-1 w-full rounded-xl py-3 text-sm font-semibold transition"
                style={{
                  background: loading ? "rgba(250,204,21,0.4)" : "linear-gradient(90deg,#facc15,#f59e0b)",
                  color: "#000",
                  cursor: loading ? "not-allowed" : "pointer",
                }}
              >
                {loading ? "Sending…" : "Request Demo →"}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}

/* ── Navbar ───────────────────────────────────────────────────────── */
export function Navbar() {
  const [scrolled, setScrolled]   = useState(false);
  const [showDemo, setShowDemo]   = useState(false);

  useEffect(() => {
    const on = () => setScrolled(window.scrollY > 20);
    on();
    window.addEventListener("scroll", on, { passive: true });
    return () => window.removeEventListener("scroll", on);
  }, []);

  return (
    <>
      <header
        className={`fixed inset-x-0 top-0 z-50 transition-all duration-500 ${
          scrolled ? "py-2" : "py-4"
        }`}
      >
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4">
          <div
            className={`flex w-full items-center justify-between gap-4 rounded-full px-4 py-2.5 transition-all duration-500 ${
              scrolled ? "glass-strong shadow-[0_10px_40px_-15px_rgba(0,0,0,0.8)]" : ""
            }`}
          >
            {/* Logo */}
            <Link to="/" className="flex items-center gap-2 shrink-0">
              <div className="relative grid h-8 w-8 place-items-center rounded-lg"
                style={{ background: "linear-gradient(135deg,#facc15,#f59e0b)", boxShadow: "0 0 20px -4px rgba(250,204,21,0.6)" }}>
                <Brain className="h-4 w-4 text-black" strokeWidth={2.5} />
              </div>
              <span className="font-display text-lg font-semibold tracking-tight">
                Cogni<span style={{ color: "#facc15" }}>Data</span>
              </span>
            </Link>

            {/* Nav links */}
            <nav className="hidden items-center gap-1 md:flex">
              {NAV.map((n) => (
                <a
                  key={n.href}
                  href={n.href}
                  className="rounded-full px-3 py-1.5 text-sm text-zinc-400 transition-colors hover:bg-white/5 hover:text-white"
                >
                  {n.label}
                </a>
              ))}
            </nav>

            {/* CTA buttons */}
            <div className="flex items-center gap-2 shrink-0">
              {/* Request a Demo */}
              <button
                onClick={() => setShowDemo(true)}
                className="hidden sm:inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition-all hover:scale-[1.03]"
                style={{
                  background: "rgba(250,204,21,0.1)",
                  border: "1px solid rgba(250,204,21,0.3)",
                  color: "#facc15",
                }}
              >
                <CalendarCheck className="h-3.5 w-3.5" />
                Request a Demo
              </button>

              {/* Login — same tab via proxy /app/login */}
              <a
                href="/app/login"
                className="inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-semibold transition-all hover:scale-[1.03]"
                style={{
                  background: "linear-gradient(90deg,#facc15,#f59e0b)",
                  color: "#000",
                  boxShadow: "0 0 24px -6px rgba(250,204,21,0.7)",
                }}
              >
                <LogIn className="h-3.5 w-3.5" />
                Login
              </a>
            </div>
          </div>
        </div>
      </header>

      {showDemo && <DemoModal onClose={() => setShowDemo(false)} />}
    </>
  );
}
