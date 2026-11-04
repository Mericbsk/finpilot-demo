"use client";

/**
 * FinSense Academy — public lessons browser.
 *
 * Data: active FinSense release via the Borsa Academy catalog API.
 * The API verifies the active manifest and packaged file hashes before serving.
 * Education only — not investment advice. Mirrors the /demo static-JSON pattern.
 */

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { ArrowLeft, BookOpen, Search, GraduationCap } from "lucide-react";
import {
  getAcademyCatalog,
  type AcademyLevel,
  type AcademyLocale,
} from "@/lib/finsenseAcademyApi";

const LOCALE_LABEL: Record<AcademyLocale, string> = {
  tr: "Türkçe",
  en: "English",
  de: "Deutsch",
};

const LEVEL_LABEL: Record<AcademyLevel, string> = {
  beginner: "Başlangıç",
  intermediate: "Orta",
  advanced: "İleri",
};

export default function AcademyPage() {
  const [data, setData] = useState<Awaited<ReturnType<typeof getAcademyCatalog>> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const [locale, setLocale] = useState<AcademyLocale>("tr");
  const [level, setLevel] = useState<"all" | AcademyLevel>("all");
  const [openId, setOpenId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setData(null);
    setError(null);
    setOpenId(null);
    getAcademyCatalog(locale)
      .then((catalog) => {
        if (!cancelled) setData(catalog);
      })
      .catch(() => {
        if (!cancelled) setError("Kanonik ders kataloğu şu anda kullanılamıyor.");
      });
    return () => {
      cancelled = true;
    };
  }, [locale]);

  const filtered = useMemo(() => {
    if (!data) return [];
    const needle = q.trim().toLowerCase();
    return data.lessons.filter(({ lesson }) => {
      if (level !== "all" && lesson.level !== level) return false;
      if (!needle) return true;
      const searchable = [
        lesson.title,
        lesson.body_md,
        ...lesson.learning_objectives,
        ...lesson.claims.map((claim) => claim.text),
      ];
      return searchable.some((value) => value.toLowerCase().includes(needle));
    });
  }, [data, q, level]);

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
            Kaynaklı finansal eğitim dersleri. Eğitim içeriğidir; kişiselleştirilmiş
            yatırım tavsiyesi değildir.
          </p>
        </header>

        {error && (
          <p className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {error}
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
                  aria-label="Ders ara"
                  className="w-full rounded border border-[var(--ledger-rule,#ddd)] bg-white py-1.5 pl-8 pr-2 text-sm outline-none focus:border-[var(--ledger-steel,#4a6)]"
                />
              </div>
              <label className="flex items-center gap-2 text-sm">
                Dil
                <select
                  aria-label="Dil"
                  value={locale}
                  onChange={(e) => setLocale(e.target.value as AcademyLocale)}
                  className="rounded border border-[var(--ledger-rule,#ddd)] bg-white px-2 py-1.5"
                >
                  {Object.entries(LOCALE_LABEL).map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </label>
              <label className="flex items-center gap-2 text-sm">
                Seviye
                <select
                  aria-label="Seviye"
                  value={level}
                  onChange={(e) => setLevel(e.target.value as "all" | AcademyLevel)}
                  className="rounded border border-[var(--ledger-rule,#ddd)] bg-white px-2 py-1.5"
                >
                  <option value="all">Tümü</option>
                  {Object.entries(LEVEL_LABEL).map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </label>
            </div>

            <p className="mb-3 text-xs text-[var(--ledger-ink-soft,#999)]">
              {filtered.length} / {data.lessons.length} ders · release{" "}
              {data.manifest.release_id}
            </p>

            <ul className="space-y-2">
              {filtered.map(({ lesson, sources }) => {
                const lessonId = `${lesson.concept_id}:${lesson.locale}`;
                const open = openId === lessonId;
                return (
                  <li
                    key={lessonId}
                    className="rounded-lg border border-[var(--ledger-rule,#e5e5e5)] bg-white"
                  >
                    <button
                      type="button"
                      onClick={() => setOpenId(open ? null : lessonId)}
                      className="flex w-full items-center gap-2 px-3 py-2.5 text-left"
                    >
                      <BookOpen className="h-4 w-4 shrink-0 text-[var(--ledger-steel,#4a6)]" />
                      <span className="flex-1 font-medium">{lesson.title}</span>
                      <span className="rounded bg-[var(--ledger-sage,#4a6)]/15 px-1.5 py-0.5 text-[0.7rem] text-[var(--ledger-sage,#376)]">
                        {LEVEL_LABEL[lesson.level]}
                      </span>
                      <span className="hidden text-xs text-[var(--ledger-ink-soft,#999)] sm:inline">
                        {LOCALE_LABEL[lesson.locale]} · v{lesson.version}
                      </span>
                    </button>
                    {open && (
                      <div className="border-t border-[var(--ledger-rule,#eee)] px-3 py-3 text-sm leading-relaxed">
                        <h3 className="mb-1 text-xs font-semibold text-[var(--ledger-ink-soft,#555)]">
                          Öğrenme hedefleri
                        </h3>
                        <ul className="mb-4 list-disc pl-5">
                          {lesson.learning_objectives.map((objective) => (
                            <li key={objective}>{objective}</li>
                          ))}
                        </ul>
                        <h3 className="mb-1 text-xs font-semibold text-[var(--ledger-ink-soft,#555)]">
                          Ders içeriği
                        </h3>
                        <p className="mb-4 whitespace-pre-wrap">{lesson.body_md}</p>
                        {lesson.claims.length > 0 && (
                          <>
                            <h3 className="mb-1 text-xs font-semibold text-[var(--ledger-ink-soft,#555)]">
                              Kaynaklı iddialar
                            </h3>
                            <ul className="list-disc pl-5">
                              {lesson.claims.map((claim) => (
                                <li key={claim.id}>
                                  <p>{claim.text}</p>
                                  {claim.source_ids.length > 0 && (
                                    <ul className="mb-2 list-none pl-0 text-xs">
                                      {claim.source_ids.map((sourceId) => {
                                        const source = sources.find((item) => item.id === sourceId);
                                        if (!source) return null;
                                        return (
                                          <li key={source.id}>
                                            <a href={source.url} target="_blank" rel="noreferrer" className="underline">
                                              {source.title} ({source.publisher})
                                            </a>
                                          </li>
                                        );
                                      })}
                                    </ul>
                                  )}
                                </li>
                              ))}
                            </ul>
                          </>
                        )}
                        {lesson.quiz.length > 0 && (
                          <section className="mt-4 border-t border-[var(--ledger-rule,#eee)] pt-3">
                            <h3 className="mb-2 text-xs font-semibold text-[var(--ledger-ink-soft,#555)]">
                              Sorular ({lesson.quiz.length})
                            </h3>
                            {lesson.quiz.map((question) => (
                              <details key={question.id} className="mb-2 rounded border border-[var(--ledger-rule,#eee)] px-2 py-1.5">
                                <summary className="cursor-pointer">{question.question}</summary>
                                <ol className="my-2 list-decimal pl-5">
                                  {question.options.map((option) => <li key={option}>{option}</li>)}
                                </ol>
                                <details className="text-xs">
                                  <summary className="cursor-pointer">Yanıtı ve açıklamayı göster</summary>
                                  <p className="mt-1 font-medium">{question.options[question.correct_index]}</p>
                                  <p>{question.explanation}</p>
                                </details>
                              </details>
                            ))}
                          </section>
                        )}
                      </div>
                    )}
                  </li>
                );
              })}
            </ul>

            <p className="mt-8 border-t border-[var(--ledger-rule,#eee)] pt-4 text-xs text-[var(--ledger-ink-soft,#999)]">
              Eğitim içeriğidir; kişiselleştirilmiş yatırım tavsiyesi değildir.
            </p>
          </>
        )}
      </div>
    </main>
  );
}
