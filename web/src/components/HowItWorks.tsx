"use client";

const steps = [
  {
    step: "01",
    title: "Hisse Seç veya Tarat",
    description:
      "Ticker yaz ya da AI tarayıcımız 300+ hissede fırsatları otomatik bulsun.",
    visual: "🔍",
  },
  {
    step: "02",
    title: "AI Analizini Oku",
    description:
      "DRL modelleri ve Chart-to-Text motoru teknik göstergeleri, fiyat hareketini ve piyasa rejimini analiz edip sade dilde anlatır.",
    visual: "🧠",
  },
  {
    step: "03",
    title: "Anla ve Karar Ver",
    description:
      "Her içgörüde gerekçe var: ne oluyor, neden önemli, genelde ne olur. Karar tamamen sende.",
    visual: "✅",
  },
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="relative px-6 py-32">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/3 top-1/2 h-[500px] w-[500px] -translate-y-1/2 rounded-full bg-[var(--accent-blue)] opacity-[0.03] blur-[120px]" />
      </div>

      <div className="relative z-10 mx-auto max-w-5xl">
        <div className="mb-16 text-center">
          <p className="mb-3 text-sm font-medium uppercase tracking-[0.2em] text-[var(--accent-cyan)]">
            Nasıl Çalışır
          </p>
          <h2 className="text-3xl font-bold tracking-tight text-[var(--text-primary)] sm:text-4xl lg:text-5xl">
            Üç adımda
            <br />
            <span className="text-[var(--text-secondary)]">
              daha akıllı yatırım.
            </span>
          </h2>
        </div>

        <div className="grid gap-8 md:grid-cols-3">
          {steps.map((item) => (
            <div key={item.step} className="relative text-center">
              {/* Step number */}
              <div className="mb-6 inline-flex h-16 w-16 items-center justify-center rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-card)] text-2xl">
                {item.visual}
              </div>
              <div className="mb-2 text-xs font-bold uppercase tracking-widest text-[var(--accent-cyan)]">
                Step {item.step}
              </div>
              <h3 className="mb-3 text-xl font-semibold text-[var(--text-primary)]">
                {item.title}
              </h3>
              <p className="text-sm leading-relaxed text-[var(--text-secondary)]">
                {item.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
