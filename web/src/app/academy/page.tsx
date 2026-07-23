"use client";

/**
 * FinSense Academy — public lessons browser.
 *
 * Data: static /academy_lessons.json produced by the academy exporter
 *   (Finsense: python -m academy.export_lessons --json --status published
 *              --out ../Borsa/web/public/academy_lessons.json)
 * Education only — not investment advice. Mirrors the /demo static-JSON pattern.
 */

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { ArrowLeft, BookOpen, Search, GraduationCap } from "lucide-react";

interface Lesson {
  id: string;
  title: string;
  domain: string;
  module: string;
  format: string;
  difficulty: string;
  minutes: number;
  content: string;
  key_takeaways: string[];
  quiz_count: number;
  flashcard_count: number;
  sources: unknown[];
}
interface Payload {
  schema: number;
  generated_at: string;
  count: number;
  domains: string[];
  disclaimer: string;
  lessons: Lesson[];
}

const FORMAT_LABEL: Record<string, string> = {
  guide: "Rehber",
  card: "Kart",
  coded: "Kodlu",
  compare: "Karşılaştırma",
  checklist: "Kontrol listesi",
};

function fmtChip(f: string): string {
  return FORMAT_LABEL[f] || (f ? f : "Ders");
}

export default function AcademyPage() {
  const [data, setData] = useState<Payload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const [domain, setDomain] = useState<string>("all");
  const [openId, setOpenId] = useState<string | null>(null);

  useEffect(() => {
    fetch("/academy_lessons.json", { cache: "no-store" })
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((d: Payload) => setData(d))
      .catch((e) => setError(String(e)));
  }, []);

  const filtered = useMemo(() => {
    if (!data) return [];
    const needle = q.trim().toLowerCase();
    return data.lessons.filter((l) => {
      if (domain !== "all" && l.domain !== domain) return false;
      if (!needle) return true;
      return (
        l.title.toLowerCase().includes(needle) ||
        l.content.toLowerCase().includes(needle) ||
        l.module.toLowerCase().includes(needle)
      );
    });
  }, [data, q, domain]);

  return (
    <main className="min-h-screen bg-[var(--ledger-paper,#faf8f3)] text-[var(--ledger-ink,#1a1a1a)]">
      <div className="mx-auto max-w-3xl px-4 py-8">
        <Link
          href="/"
          className="inline-flex items-center gap-1 text-sm text-[var(--ledger-ink-soft,#666)] hover:underline"
        >
          <ArrowLeft className="h-4 w-4" /> Ana sayfa
        </Link>

        <header className="mt-4 mb-6">
          <div className="flex items-center gap-2">
            <GraduationCap className="h-6 w-6" />
            <h1 className="text-2xl font-semibold">FinSense Academy</h1>
          </div>
          <p className="mt-1 text-sm text-[var(--ledger-ink-soft,#666)]">
            RAG-temelli, kaynaklı finansal eğitim dersleri. Eğitim içeriğidir —
            yatırım tavsiyesi değildir.
          </p>
        </header>

        {error && (
          <p className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            Dersler yüklenemedi ({error}). academy_lessons.json henüz üretilmemiş
            olabilir.
          </p>
        )}

        {!data && !error && (
          <p className="text-sm text-[var(--ledger-ink-soft,#666)]">Yükleniyor…</p>
        )}

        {data && (
          <>
            <div className="mb-4 flex flex-wrap items-center gap-2">
              <div className="relative flex-1 min-w-[180px]">
                <Search className="absolute left-2 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--ledger-ink-soft,#999)]" />
                <input
                  value={q}
                  onChange={(e) => setQ(e.target.value)}
                  placeholder="Ders ara…"
                  className="w-full rounded border border-[var(--ledger-rule,#ddd)] bg-white py-1.5 pl-8 pr-2 text-sm outline-none focus:border-[var(--ledger-steel,#4a6)]"
                />
              </div>
              <select
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                className="rounded border border-[var(--ledger-rule,#ddd)] bg-white px-2 py-1.5 text-sm"
              >
                <option value="all">Tüm alanlar</option>
                {data.domains.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            </div>

            <p className="mb-3 text-xs text-[var(--ledger-ink-soft,#999)]">
              {filtered.length} / {data.count} ders · güncelleme{" "}
              {new Date(data.generated_at).toLocaleDateString("tr-TR")}
            </p>

            <ul className="space-y-2">
              {filtered.map((l) => {
                const open = openId === l.id;
                return (
                  <li
                    key={l.id}
                    className="rounded-lg border border-[var(--ledger-rule,#e5e5e5)] bg-white"
                  >
                    <button
                      onClick={() => setOpenId(open ? null : l.id)}
                      className="flex w-full items-center gap-2 px-3 py-2.5 text-left"
                    >
                      <BookOpen className="h-4 w-4 shrink-0 text-[var(--ledger-steel,#4a6)]" />
                      <span className="flex-1 font-medium">{l.title}</span>
                      <span className="rounded bg-[var(--ledger-sage,#4a6)]/15 px-1.5 py-0.5 text-[0.7rem] text-[var(--ledger-sage,#376)]">
                        {fmtChip(l.format)}
                      </span>
                      <span className="hidden text-xs text-[var(--ledger-ink-soft,#999)] sm:inline">
                        {l.domain} · {l.minutes}dk
                      </span>
                    </button>
                    {open && (
                      <div className="border-t border-[var(--ledger-rule,#eee)] px-3 py-3 text-sm leading-relaxed">
                        <p className="whitespace-pre-wrap">{l.content}</p>
                        {l.key_takeaways?.length > 0 && (
                          <>
                            <h3 className="mt-3 mb-1 text-xs font-semibold text-[var(--ledger-ink-soft,#555)]">
                              Ana çıkarımlar
                            </h3>
                            <ul className="list-disc pl-5">
                              {l.key_takeaways.map((t, i) => (
                                <li key={i}>{t}</li>
                              ))}
                            </ul>
                          </>
                        )}
                        <p className="mt-3 text-xs text-[var(--ledger-ink-soft,#999)]">
                          Quiz: {l.quiz_count} · Flashcard: {l.flashcard_count} ·
                          Kaynak: {l.sources?.length ?? 0}
                        </p>
                      </div>
                    )}
                  </li>
                );
              })}
            </ul>

            <p className="mt-8 border-t border-[var(--ledger-rule,#eee)] pt-4 text-xs text-[var(--ledger-ink-soft,#999)]">
              {data.disclaimer}
            </p>
          </>
        )}
      </div>
    </main>
  );
}
