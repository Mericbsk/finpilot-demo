"use client";

import { useState } from "react";
import { ArrowRight, CheckCircle } from "lucide-react";

export default function Waitlist() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setLoading(true);
    // Simulate submission — replace with real API
    await new Promise((r) => setTimeout(r, 800));
    setSubmitted(true);
    setLoading(false);
  };

  return (
    <section
      id="waitlist"
      className="relative px-6 py-32"
    >
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/2 bottom-0 h-[500px] w-[800px] -translate-x-1/2 rounded-full bg-[var(--accent-cyan)] opacity-[0.04] blur-[150px]" />
      </div>

      <div className="relative z-10 mx-auto max-w-2xl text-center">
        <p className="mb-3 text-sm font-medium uppercase tracking-[0.2em] text-[var(--accent-cyan)]">
          Erken Erişim
        </p>
        <h2 className="mb-4 text-3xl font-bold tracking-tight text-[var(--text-primary)] sm:text-4xl lg:text-5xl">
          İlk öğrenen sen ol.
        </h2>
        <p className="mb-10 text-lg text-[var(--text-secondary)]">
          FinPilot erken erişim listesine katıl. Ücretsiz plan dahil
          — kredi kartı gerekmez.
        </p>

        {!submitted ? (
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
              className="flex-1 rounded-full border border-[var(--border-subtle)] bg-[var(--bg-card)] px-5 py-3 text-sm text-[var(--text-primary)] placeholder-[var(--text-tertiary)] outline-none transition-all focus:border-[var(--accent-cyan)] focus:ring-1 focus:ring-[var(--accent-cyan)]"
            />
            <button
              type="submit"
              disabled={loading}
              className="group flex items-center justify-center gap-2 rounded-full bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-blue)] px-6 py-3 text-sm font-semibold text-black transition-all hover:shadow-[0_0_20px_var(--glow-cyan)] disabled:opacity-50"
            >
              {loading ? "..." : "Katıl"}
              {!loading && (
                <ArrowRight
                  size={16}
                  className="transition-transform group-hover:translate-x-1"
                />
              )}
            </button>
          </form>
        ) : (
          <div className="mx-auto flex max-w-md items-center justify-center gap-3 rounded-2xl border border-[var(--accent-green)] bg-[rgba(48,209,88,0.08)] px-6 py-4">
            <CheckCircle size={20} className="text-[var(--accent-green)]" />
            <span className="text-sm text-[var(--accent-green)]">
              Listedesin! FinPilot lansmanında seni bilgilendireceğiz.
            </span>
          </div>
        )}

        <p className="mt-4 text-xs text-[var(--text-tertiary)]">
          60+ kişi zaten listede. Spam yok, asla.
        </p>
      </div>
    </section>
  );
}
