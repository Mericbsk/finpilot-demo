"use client";

import { Check } from "lucide-react";
import Link from "next/link";

const plans = [
  {
    name: "Ücretsiz",
    price: "$0",
    period: "sonsuza dek",
    description: "AI ile yatırım öğren — kredi kartı gerekmez.",
    features: [
      "FinSense Academy (tam erişim)",
      "İnteraktif finansal sözlük",
      "Günde 5 AI analizi",
      "1 dil desteği",
      "Topluluk erişimi",
    ],
    cta: "Ücretsiz Başla",
    href: "#waitlist",
    highlighted: false,
  },
  {
    name: "Pro",
    price: "$29",
    period: "/ay",
    description: "Kişisel AI borsa analistin. Sınırsız her şey.",
    features: [
      "Sınırsız AI analizi",
      "Gerçek zamanlı DRL tarayıcı (300+ hisse)",
      "Telegram alertleri",
      "3 dil (EN/DE/TR)",
      "Portföy takibi",
      "Öncelikli destek",
      "Gelişmiş DRL sinyalleri",
    ],
    cta: "Waitlist — Pro",
    href: "#waitlist",
    highlighted: true,
  },
  {
    name: "Yıllık",
    price: "$249",
    period: "/yıl",
    description: "Pro plan, %28 indirimli. Ciddi yatırımcı için en uygun.",
    features: [
      "Pro'daki her şey",
      "Yılda $99 tasarruf",
      "Yeni özelliklere erken erişim",
      "1'e 1 başlangıç görüşmesi",
      "API erişimi (yakında)",
    ],
    cta: "Waitlist — Yıllık",
    href: "#waitlist",
    highlighted: false,
  },
];

export default function Pricing() {
  return (
    <section id="pricing" className="relative px-6 py-32">
      <div className="mx-auto max-w-7xl">
        <div className="mb-16 text-center">
          <p className="mb-3 text-sm font-medium uppercase tracking-[0.2em] text-[var(--accent-cyan)]">
            Fiyatlandırma
          </p>
          <h2 className="text-3xl font-bold tracking-tight text-[var(--text-primary)] sm:text-4xl lg:text-5xl">
            Bloomberg yılda $24K.
            <br />
            <span className="text-[var(--text-secondary)]">
              Biz $0'dan başlıyoruz.
            </span>
          </h2>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`relative rounded-2xl border p-8 transition-all duration-300 ${
                plan.highlighted
                  ? "border-[var(--accent-cyan)] bg-[var(--bg-card)] glow-cyan"
                  : "border-[var(--border-subtle)] bg-[var(--bg-card)] hover:border-[var(--border-hover)]"
              }`}
            >
              {plan.highlighted && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-blue)] px-4 py-1 text-xs font-semibold text-black">
                  En Popüler
                </div>
              )}

              <h3 className="mb-2 text-lg font-semibold text-[var(--text-primary)]">
                {plan.name}
              </h3>
              <div className="mb-1 flex items-baseline gap-1">
                <span className="text-4xl font-bold text-[var(--text-primary)]">
                  {plan.price}
                </span>
                <span className="text-sm text-[var(--text-tertiary)]">
                  {plan.period}
                </span>
              </div>
              <p className="mb-6 text-sm text-[var(--text-secondary)]">
                {plan.description}
              </p>

              <Link
                href={plan.href}
                className={`mb-8 block w-full rounded-full py-3 text-center text-sm font-semibold transition-all ${
                  plan.highlighted
                    ? "bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-blue)] text-black hover:shadow-[0_0_20px_var(--glow-cyan)]"
                    : "border border-[var(--border-subtle)] text-[var(--text-primary)] hover:border-[var(--border-hover)]"
                }`}
              >
                {plan.cta}
              </Link>

              <ul className="space-y-3">
                {plan.features.map((feature) => (
                  <li
                    key={feature}
                    className="flex items-start gap-3 text-sm text-[var(--text-secondary)]"
                  >
                    <Check
                      size={16}
                      className="mt-0.5 shrink-0 text-[var(--accent-green)]"
                    />
                    {feature}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
