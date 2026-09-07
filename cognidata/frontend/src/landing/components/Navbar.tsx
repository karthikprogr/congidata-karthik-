import { Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Brain } from "lucide-react";

const NAV = [
  { href: "#problem", label: "Problem" },
  { href: "#solution", label: "Solution" },
  { href: "#features", label: "Features" },
  { href: "#agents", label: "Agents" },
  { href: "#architecture", label: "Architecture" },
  { href: "#faq", label: "FAQ" },
];

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const on = () => setScrolled(window.scrollY > 20);
    on();
    window.addEventListener("scroll", on, { passive: true });
    return () => window.removeEventListener("scroll", on);
  }, []);

  return (
    <header
      className={`fixed inset-x-0 top-0 z-50 transition-all duration-500 ${
        scrolled ? "py-2" : "py-4"
      }`}
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4">
        <div
          className={`flex w-full items-center justify-between gap-4 rounded-full px-4 py-2.5 transition-all duration-500 ${
            scrolled ? "glass-strong shadow-[0_10px_40px_-15px_oklch(0.05_0.05_260/0.8)]" : ""
          }`}
        >
          <Link to="/" className="flex items-center gap-2">
            <div className="relative grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-primary to-secondary shadow-[0_0_20px_-4px_oklch(0.58_0.24_295/0.8)]">
              <Brain className="h-4 w-4 text-white" strokeWidth={2.5} />
            </div>
            <span className="font-display text-lg font-semibold tracking-tight">
              Cogni<span className="text-gradient">Data</span>
            </span>
          </Link>

          <nav className="hidden items-center gap-1 md:flex">
            {NAV.map((n) => (
              <a
                key={n.href}
                href={n.href}
                className="rounded-full px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-white/5 hover:text-foreground"
              >
                {n.label}
              </a>
            ))}
          </nav>

          <a
            href="#contact"
            className="group relative inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-primary to-secondary px-4 py-2 text-sm font-medium text-white shadow-[0_0_24px_-6px_oklch(0.58_0.24_295/0.9)] transition-transform hover:scale-[1.03]"
          >
            <span>Get in touch</span>
          </a>
        </div>
      </div>
    </header>
  );
}
