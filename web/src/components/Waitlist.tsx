"use client";

import { useEffect, useState } from "react";
import { ArrowRight, CheckCircle } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

export default function Waitlist() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [position, setPosition] = useState<number | null>(null);
  const [count, setCount] = useState<number | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/waitlist/count`)
      .then((r) => r.json())
      .then((d) => setCount(d.count ?? null))
      .catch(() => {});
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/waitlist`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, source: "landing" }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail ?? "Something went wrong. Please try again.");
      } else {
        setPosition(data.position ?? null);
        setSubmitted(true);
      }
    } catch {
      setError("Connection error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section
      id="waitlist"
      className="relative border-t px-6 py-24"
      style={{ borderColor: "var(--ledger-rule)" }}
    >

      <div className="relative z-10 mx-auto max-w-2xl text-center">
        <p className="mb-3 font-ledger-mono text-xs uppercase tracking-[0.25em]" style={{ color: "var(--ledger-gold)" }}>
          Early Access
        </p>
        <h2 className="mb-4 font-ledger-serif text-3xl font-bold tracking-tight sm:text-4xl" style={{ color: "var(--ledger-ink)" }}>
          Be the first to read it.
        </h2>
        <p className="mb-10 text-base" style={{ color: "var(--ledger-ink-soft)" }}>
          Join the FinPilot waitlist — free tier included, no credit card required.
        </p>

        {!submitted ? (
          <>
            <form
              onSubmit={handleSubmit}
              className="mx-auto flex max-w-md flex-col gap-3 sm:flex-row"
            >
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                className="flex-1 border-2 px-5 py-3 text-sm outline-none transition-all"
                style={{ borderColor: "var(--ledger-ink)", background: "var(--ledger-paper)", color: "var(--ledger-ink)" }}
              />
              <button
                type="submit"
                disabled={loading}
                className="group flex items-center justify-center gap-2 border-2 px-6 py-3 text-sm font-semibold uppercase tracking-widest transition-all disabled:opacity-50"
                style={{ borderColor: "var(--ledger-ink)", background: "var(--ledger-ink)", color: "var(--ledger-paper)" }}
              >
                {loading ? "..." : "Join"}
                {!loading && (
                  <ArrowRight
                    size={16}
                    className="transition-transform group-hover:translate-x-1"
                  />
                )}
              </button>
            </form>
            {error && (
              <p className="mt-3 text-sm" style={{ color: "var(--ledger-brick)" }}>{error}</p>
            )}
          </>
        ) : (
          <div
            className="mx-auto flex max-w-md flex-col items-center justify-center gap-2 border-2 px-6 py-4"
            style={{ borderColor: "var(--ledger-sage)", background: "var(--ledger-paper-dim)" }}
          >
            <div className="flex items-center gap-3">
              <CheckCircle size={20} style={{ color: "var(--ledger-sage)" }} />
              <span className="text-sm" style={{ color: "var(--ledger-sage)" }}>
                You&apos;re on the list. We&apos;ll email you when FinPilot launches.
              </span>
            </div>
            {position && (
              <p className="text-xs" style={{ color: "var(--ledger-ink-soft)" }}>
                Your position: #{position}
              </p>
            )}
          </div>
        )}

        <p className="mt-4 text-xs" style={{ color: "var(--ledger-ink-soft)" }}>
          {count !== null ? `${count}+ readers already on the list.` : "60+ readers already on the list."} No spam, ever.
        </p>
      </div>
    </section>
  );
}
