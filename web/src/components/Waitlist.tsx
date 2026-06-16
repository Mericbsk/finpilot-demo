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
        setError(data.detail ?? "Bir hata oluştu. Tekrar dene.");
      } else {
        setPosition(data.position ?? null);
        setSubmitted(true);
      }
    } catch {
      setError("Bağlantı hatası. Tekrar dene.");
    } finally {
      setLoading(false);
    }
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
            {error && (
              <p className="mt-3 text-sm text-red-400">{error}</p>
            )}
          </>
        ) : (
          <div className="mx-auto flex max-w-md flex-col items-center justify-center gap-2 rounded-2xl border border-[var(--accent-green)] bg-[rgba(48,209,88,0.08)] px-6 py-4">
            <div className="flex items-center gap-3">
              <CheckCircle size={20} className="text-[var(--accent-green)]" />
              <span className="text-sm text-[var(--accent-green)]">
                Listedesin! FinPilot lansmanında seni bilgilendireceğiz.
              </span>
            </div>
            {position && (
              <p className="text-xs text-[var(--text-tertiary)]">
                Sıra numaran: #{position}
              </p>
            )}
          </div>
        )}

        <p className="mt-4 text-xs text-[var(--text-tertiary)]">
          {count !== null ? `${count}+ kişi zaten listede.` : "60+ kişi zaten listede."} Spam yok, asla.
        </p>
      </div>
    </section>
  );
}
