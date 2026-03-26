"use client";

import {
  Brain,
  BarChart3,
  GraduationCap,
  Globe,
  Zap,
  Shield,
} from "lucide-react";

const features = [
  {
    icon: Brain,
    title: "Deep Reinforcement Learning",
    description:
      "15 eğitimli DRL modeli (PPO, SAC, TD3), 5+ yıllık piyasa verisinden optimal alım/satım zamanlaması öğrenir.",
    accent: "var(--accent-cyan)",
    span: "sm:col-span-2",
  },
  {
    icon: BarChart3,
    title: "AI Piyasa Tarayıcı",
    description:
      "30 kategoride 300+ hissede gerçek zamanlı örüntü tanıma. İnsan gözünün kaçırdığı fırsatları yüzeye çıkarır.",
    accent: "var(--accent-blue)",
    span: "",
  },
  {
    icon: Zap,
    title: "Chart-to-Text Motoru",
    description:
      "Karmaşık teknik göstergeleri sade dile çevirir. 'NVDA aşırı alımda — tarihsel olarak 2 hafta içinde %3-5 geri çekilir.'",
    accent: "var(--accent-purple)",
    span: "",
  },
  {
    icon: Shield,
    title: "Şeffaf AI",
    description:
      "Kara kutu yok. Her öneri arkasında model adı, güven skoru ve gerekçe. Karar seninken, veri de senin.",
    accent: "var(--accent-blue)",
    span: "",
  },
  {
    icon: GraduationCap,
    title: "FinSense Academy",
    description:
      "Her içgörü 'neden'i de açıklar. 100+ terimlik sözlük, interaktif quiz, bileşik faiz simülatörü. Yatırımcı yetiştiriyoruz.",
    accent: "var(--accent-green)",
    span: "sm:col-span-2",
  },
  {
    icon: Globe,
    title: "3 Dil Desteği",
    description:
      "English, Deutsch, Türkçe — ilk günden küresel perakende yatırımcı için tasarlandı.",
    accent: "var(--accent-cyan)",
    span: "",
  },
];

export default function Features() {
  return (
    <section id="features" className="relative px-6 py-32">
      <div className="mx-auto max-w-7xl">
        {/* Section header */}
        <div className="mb-16 text-center">
          <p className="mb-3 text-sm font-medium uppercase tracking-[0.2em] text-[var(--accent-cyan)]">
            Özellikler
          </p>
          <h2 className="text-3xl font-bold tracking-tight text-[var(--text-primary)] sm:text-4xl lg:text-5xl">
            İhtiyacın olan her şey.
            <br />
            <span className="text-[var(--text-secondary)]">
              Fazlası değil.
            </span>
          </h2>
        </div>

        {/* Apple bento grid — 3 columns, some span 2 */}
        <div className="grid gap-4 sm:grid-cols-3">
          {features.map((feature) => (
            <div
              key={feature.title}
              className={`group rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-card)] p-8 transition-all duration-300 hover:border-[var(--border-hover)] hover:bg-[var(--bg-card-hover)] ${feature.span}`}
            >
              <div
                className="mb-5 flex h-12 w-12 items-center justify-center rounded-xl"
                style={{ backgroundColor: `${feature.accent}15` }}
              >
                <feature.icon
                  size={24}
                  style={{ color: feature.accent }}
                />
              </div>
              <h3 className="mb-3 text-lg font-semibold text-[var(--text-primary)]">
                {feature.title}
              </h3>
              <p className="text-sm leading-relaxed text-[var(--text-secondary)]">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
