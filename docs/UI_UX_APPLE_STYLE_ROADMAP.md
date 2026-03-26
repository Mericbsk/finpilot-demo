# FinPilot — Apple-Stil, Elegant Web Arayüzü Yol Haritası

> **Tarih:** 2026-03-05
> **Kapsam:** Streamlit dashboard (views/) + public_website/ statik site
> **Hedef:** WCAG AA uyumlu, FCP < 1.5s, LCP < 2.5s, Lighthouse ≥ 90, marka-özgün design system

---

## 1. MEVCUt DURUM AUDİTİ

### 1.1 Mimari Envanter

| Katman | Teknoloji | Dosya | Satır |
|--------|-----------|-------|-------|
| **Uygulama çatısı** | Streamlit (Python) | `streamlit_app.py` | 121 |
| **Tema** | `.streamlit/config.toml` | 1 dosya | 16 |
| **Görünümler (Views)** | 15 Python dosyası | `views/*.py` | 6,672 |
| **Bileşenler** | 22 Python dosyası | `views/components/*.py` | 7,531 |
| **Design Tokens + CSS** | Tek monolitik dosya | `views/styles.py` | 1,047 |
| **Statik site** | Vanilla HTML/CSS | `public_website/` | 6 HTML + 1 CSS (421 satır) |
| **Varlıklar** | Tek SVG logo | `assets/logo.svg` | 1 dosya |
| **TOPLAM UI LOC** | | | **~14,200** |

### 1.2 Mevcut Design Token Sistemi (Sprint 7)

`views/styles.py` dosyasında CSS custom properties olarak tanımlı:

```
✅ Bulunan Token Kategorileri:
   • Renk: Brand (primary, hover), BG (4 katman + 2 glass), Text (4 seviye),
     Semantic (success/error/warning/info/ai — her biri soft + border + text varyantları)
   • Sınır: default, hover, focus
   • Boşluk: 4px tabanlı skala (space-1 → space-12, 8 kademe)
   • Yarıçap: 5 kademe (sm 6px → full 999px)
   • Gölge: 3 kademe (card, card-hover, glow)
   • Geçiş: 3 kademe (fast 0.15s, normal 0.25s, smooth 0.4s)

❌ Eksik Token Kategorileri:
   • Tipografi: font-family, font-size skalası, line-height, letter-spacing tanımsız
   • Z-index katmanları: Yok
   • Motion/easing: Sadece ease, spring/bezier yok
   • Breakpoint: styles.py'de yok (grid.py'de hardcoded: 480/768)
   • Opacity skalası: Yok
   • Light mode: Yok (sadece dark tema)
```

### 1.3 Performans Tahmini (Simüle Lighthouse)

Streamlit doğası gereği gerçek Lighthouse ölçümü kısıtlı, ancak yapısal analiz:

| Metrik | Tahmini Durum | Sorun |
|--------|--------------|-------|
| **FCP** | ~2.5-4s ⚠️ | Streamlit runtime + Python backend → yüksek TTFB |
| **LCP** | ~4-6s 🔴 | Dashboard kartları server-side render, full page redraw |
| **CLS** | 0.05-0.15 ⚠️ | Skeleton loader var ama st.rerun() layout kayması yaratıyor |
| **TBT** | Yüksek 🔴 | st.markdown(unsafe_allow_html) 70 kez — DOM mutation ağır |
| **Bundle boyutu** | N/A | Streamlit kendi JS runtime'ı kontrol ediyor |

### 1.4 Erişilebilirlik Auditi

| Kriter | Durum | Detay |
|--------|-------|-------|
| **ARIA attributes** | 🔴 8 / ~200 gerekli | Sadece 4 bileşende role/aria-label var |
| **Keyboard navigation** | 🟡 Kısmi | Streamlit widget'ları default erişilebilir, custom HTML değil |
| **Color contrast** | 🟡 Riskli | `--text-muted: rgba(148,163,184,0.75)` → #0f172a üzerinde kontrast 3.2:1 (AA = 4.5:1 gerekli) |
| **Focus indicators** | 🔴 Yok | styles.py'de :focus-visible tanımı yok |
| **Screen reader** | 🔴 Zayıf | 70 unsafe_allow_html blok, semantik etiket yok |
| **Reduced motion** | 🔴 Yok | prefers-reduced-motion sorgusu yok, 35+ animasyon var |
| **Alt text** | 🟡 | Logo SVG'de title yok, emoji-as-icon yaygın (412 emoji) |
| **Language** | 🟡 | `lang="en"` ama içerik Türkçe — mismatch |

### 1.5 İçerik ve Yapı Auditi

| Alan | Bulgu |
|------|-------|
| **Inline CSS** | 130 `style='...'` satırı views/*.py'de — bakımı imkânsız |
| **unsafe_allow_html** | 70 kullanım — XSS riski, erişilebilirlik sıfır |
| **Emoji-as-icon** | 412 emoji — ekran okuyucularda gürültü, farklı platformlarda tutarsız |
| **Font sistemi** | Streamlit default "sans serif" — marka kimliği yok |
| **Dark-only tema** | Light mode desteği yok |
| **Responsive** | grid.py var ama 480/768 breakpoint — modern cihazlara yetersiz |
| **PWA** | public_website'da manifest + service worker var, Streamlit'te yok |
| **i18n** | views/translations.py (531 LOC) + public_website/translations.js var |

---

## 2. DESIGN SYSTEM (DS) TOKEN TANIMI + FIGMA YAPISI

### 2.1 Tipografi Token Skalası

Apple-stil tipografi: SF Pro / Inter ailesi, net hiyerarşi, bol beyaz alan.

```css
:root {
  /* ── Font Family ── */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  --font-mono: 'SF Mono', 'JetBrains Mono', 'Fira Code', monospace;

  /* ── Type Scale (Major Third 1.250) ── */
  --text-xs:    0.694rem;   /* 11.1px — caption, footnote */
  --text-sm:    0.833rem;   /* 13.3px — label, badge */
  --text-base:  1rem;       /* 16px   — body default */
  --text-md:    1.125rem;   /* 18px   — body emphasis */
  --text-lg:    1.25rem;    /* 20px   — card title */
  --text-xl:    1.563rem;   /* 25px   — section heading */
  --text-2xl:   1.953rem;   /* 31.3px — page heading */
  --text-3xl:   2.441rem;   /* 39px   — hero heading */
  --text-4xl:   3.052rem;   /* 48.8px — display/splash */

  /* ── Line Height ── */
  --leading-none:  1;
  --leading-tight: 1.2;
  --leading-snug:  1.375;
  --leading-normal:1.5;
  --leading-relaxed:1.625;

  /* ── Font Weight ── */
  --weight-normal: 400;
  --weight-medium: 500;
  --weight-semibold: 600;
  --weight-bold: 700;
  --weight-extrabold: 800;

  /* ── Letter Spacing ── */
  --tracking-tight: -0.025em;
  --tracking-normal: 0;
  --tracking-wide: 0.025em;
  --tracking-wider: 0.05em;
  --tracking-caps: 0.1em;
}
```

### 2.2 Renk Token Genişlemesi

Mevcut palette'i koruya rak, Apple-stil soft/muted gradations ekliyoruz:

```css
:root {
  /* ── Brand (mevcut — kalıyor) ── */
  --color-primary: #00e6e6;
  --color-primary-hover: #0ea5e9;
  --color-primary-muted: rgba(0, 230, 230, 0.12);  /* YENİ */
  --color-primary-subtle: rgba(0, 230, 230, 0.06);  /* YENİ */

  /* ── Neutral Surface Scale (Apple dark style) ── */
  --surface-0: #000000;      /* True black — OLED */
  --surface-1: #0a0f1a;      /* Deepest BG */
  --surface-2: #0f172a;      /* = mevcut bg-primary */
  --surface-3: #1e293b;      /* = mevcut bg-secondary */
  --surface-4: #334155;      /* = mevcut bg-tertiary */
  --surface-5: #475569;      /* YENİ — elevated cards */
  --surface-glass: rgba(15, 23, 42, 0.72);
  --surface-glass-heavy: rgba(15, 23, 42, 0.88);

  /* ── Text Contrast-Safe Scale ── */
  --text-primary:    #f8fafc;   /* 16.8:1 on surface-2 ✅ AAA */
  --text-secondary:  #cbd5e1;   /* 10.6:1 on surface-2 ✅ AAA */
  --text-tertiary:   #94a3b8;   /* 5.6:1  on surface-2 ✅ AA  */
  --text-muted:      #64748b;   /* 3.4:1  on surface-2 ❌ large text only */
  --text-disabled:   #475569;   /* disabled state only */

  /* ── Semantic (mevcut'u inherit + accessible variants) ── */
  --color-success:       #22c55e;
  --color-success-light: #4ade80;  /* AA uyumlu text rengi */
  --color-error:         #ef4444;
  --color-error-light:   #fca5a5;
  --color-warning:       #eab308;
  --color-warning-light: #fde047;
  --color-info:          #3b82f6;
  --color-info-light:    #93c5fd;

  /* ── Elevation / Z-index ── */
  --z-base: 0;
  --z-dropdown: 100;
  --z-sticky: 200;
  --z-modal-backdrop: 300;
  --z-modal: 400;
  --z-toast: 500;
  --z-tooltip: 600;
}
```

### 2.3 Spacing + Breakpoint Token

```css
:root {
  /* ── Spacing (mevcut 4px base korunuyor, eksikler ekleniyor) ── */
  --space-0:  0px;
  --space-px: 1px;
  --space-0.5: 2px;   /* YENİ */
  --space-1:  4px;
  --space-1.5: 6px;   /* YENİ */
  --space-2:  8px;
  --space-3:  12px;
  --space-4:  16px;
  --space-5:  20px;
  --space-6:  24px;
  --space-8:  32px;
  --space-10: 40px;
  --space-12: 48px;
  --space-16: 64px;   /* YENİ — section gutter */
  --space-20: 80px;   /* YENİ — page gutter */
  --space-24: 96px;   /* YENİ — hero spacing */

  /* ── Breakpoints (CSS custom prop olarak kullanılmaz, referans) ── */
  /* --bp-xs: 375px;  — mobile small */
  /* --bp-sm: 640px;  — mobile large */
  /* --bp-md: 768px;  — tablet */
  /* --bp-lg: 1024px; — desktop */
  /* --bp-xl: 1280px; — wide desktop */
  /* --bp-2xl: 1536px; — ultrawide */
}
```

### 2.4 Figma Yapı Önerisi (3 Ana Sayfa + 6 Komponent)

**Figma Dosya Hiyerarşisi:**

```
📁 FinPilot DS v2.0
├── 📄 Cover & Index
├── 📁 Foundations
│   ├── 🎨 Colors (Primitive → Semantic → Component)
│   ├── 📝 Typography (Scale + Preset styles)
│   ├── 📐 Spacing & Grid (4px grid, 12-col layout)
│   ├── 🔲 Elevation & Shadows
│   └── ⚡ Motion & Easing
├── 📁 Components (Storybook 1:1)
│   ├── 🔘 Button (Primary / Secondary / Ghost / Danger / Icon-only)
│   ├── 🃏 Card (Signal / Metric / Feature / Empty state)
│   ├── 📋 Modal (Default / Confirmation / Full-screen)
│   ├── 📝 Form (Input / Select / Checkbox / Radio / Toggle)
│   ├── 🔝 Header (Nav bar + breadcrumb)
│   └── 🔚 Footer (Minimal + Extended)
├── 📁 Patterns
│   ├── Skeleton Loading
│   ├── Empty State
│   ├── Error State
│   ├── Toast / Notification
│   └── Data Table
└── 📁 Pages (3 Ana Sayfa Prototipi)
    ├── 🏠 Landing Page — Hero + Feature grid + CTA
    ├── 📊 Dashboard — Scan results + Signal cards + DRL panel
    └── 🎓 FinSense — Academy + Dictionary + Quiz
```

### 2.5 Altı Temel Komponent — Storybook Tanımları

#### 2.5.1 Button

```
Komponent: FPButton
Varyantlar: primary | secondary | ghost | danger | icon-only
Boyutlar:   sm (32px) | md (40px) | lg (48px)
Durumlar:   default | hover | active | focus | disabled | loading

Props:
  label:     string
  variant:   "primary" | "secondary" | "ghost" | "danger"
  size:      "sm" | "md" | "lg"
  icon?:     ReactNode (sol ikon)
  iconOnly?: boolean
  loading?:  boolean
  disabled?: boolean
  fullWidth?:boolean

Erişilebilirlik:
  • role="button"
  • aria-label (iconOnly olduğunda zorunlu)
  • aria-disabled={disabled}
  • aria-busy={loading}
  • :focus-visible → 2px solid var(--color-primary), offset 2px

Stil Detayları (Primary):
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-hover))
  border: none
  border-radius: var(--radius-md)    /* 12px */
  color: var(--surface-2)            /* dark text on bright bg */
  font-weight: var(--weight-semibold)
  font-size: var(--text-sm)
  padding: var(--space-2) var(--space-5)
  transition: transform var(--transition-fast), box-shadow var(--transition-normal)
  hover: translateY(-1px), shadow-card-hover
  active: translateY(0), scale(0.98)
```

#### 2.5.2 Card

```
Komponent: FPCard
Varyantlar: signal | metric | feature | empty
Boyutlar:   compact | default | expanded

Props:
  variant:    "signal" | "metric" | "feature" | "empty"
  title:      string
  subtitle?:  string
  badge?:     { label: string, color: "success" | "warning" | "error" | "info" }
  metrics?:   Array<{ label: string, value: string | number }>
  children:   ReactNode
  onClick?:   () => void
  hoverable?: boolean  (default: true)

Erişilebilirlik:
  • role="article" veya role="region"
  • aria-label="{title}"
  • role="button" + tabindex="0" (onClick varsa)

Stil Detayları:
  background: var(--surface-3)
  border: 1px solid var(--border-default)
  border-radius: var(--radius-lg)    /* 16px */
  padding: var(--space-5) var(--space-6)
  box-shadow: var(--shadow-card)
  transition: transform var(--transition-normal), box-shadow var(--transition-normal)
  hover: translateY(-2px), border-color var(--border-hover), shadow-card-hover

  /* Apple-stil frosted glass efekti */
  @supports (backdrop-filter: blur(20px)) {
    background: var(--surface-glass);
    backdrop-filter: blur(20px) saturate(180%);
    -webkit-backdrop-filter: blur(20px) saturate(180%);
  }
```

#### 2.5.3 Modal

```
Komponent: FPModal
Varyantlar: default | confirmation | fullscreen

Props:
  isOpen:     boolean
  onClose:    () => void
  title:      string
  size:       "sm" (480px) | "md" (640px) | "lg" (800px) | "fullscreen"
  children:   ReactNode
  footer?:    ReactNode
  closeOnOverlay?: boolean (default: true)

Erişilebilirlik:
  • role="dialog"
  • aria-modal="true"
  • aria-labelledby="{titleId}"
  • Focus trap: Tab döngüsü modal içinde
  • Escape tuşu ile kapatılır
  • Açılınca ilk focusable element'e focus
  • Kapanınca trigger element'e focus dönüşü

Stil Detayları:
  Backdrop: background rgba(0,0,0,0.6) + backdrop-filter blur(8px)
  Panel: background var(--surface-3), border-radius var(--radius-xl) (20px)
  Animasyon: opacity 0→1 + translateY(16px→0), 0.3s cubic-bezier(0.32,0.72,0,1) — Apple spring
```

#### 2.5.4 Form (Input Group)

```
Komponent: FPInput / FPSelect / FPCheckbox / FPToggle

FPInput Props:
  label:       string
  placeholder: string
  type:        "text" | "number" | "email" | "password" | "search"
  value:       string
  onChange:    (value: string) => void
  error?:      string
  hint?:       string
  icon?:       ReactNode (sol)
  disabled?:   boolean
  required?:   boolean

Erişilebilirlik:
  • <label> ile htmlFor bağlantısı (id auto-gen)
  • aria-describedby → hint ve error message
  • aria-invalid={!!error}
  • aria-required={required}
  • :focus-visible → ring-2 var(--border-focus)

Stil Detayları:
  background: var(--surface-2)
  border: 1px solid var(--border-default)
  border-radius: var(--radius-md)
  padding: var(--space-3) var(--space-4)
  color: var(--text-primary)
  font-size: var(--text-base)
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast)
  focus: border-color var(--color-primary), box-shadow 0 0 0 3px var(--color-primary-muted)
  error: border-color var(--color-error), box-shadow 0 0 0 3px var(--color-error-soft)
```

#### 2.5.5 Header (Navigation)

```
Komponent: FPHeader

Props:
  logo:       ReactNode
  navItems:   Array<{ label: string, href: string, active?: boolean }>
  user?:      { name: string, avatar?: string }
  onLogout?:  () => void

Erişilebilirlik:
  • <header role="banner">
  • <nav role="navigation" aria-label="Ana menü">
  • aria-current="page" aktif link'te
  • Hamburger menü: aria-expanded, aria-controls

Stil Detayları:
  position: sticky, top: 0, z-index: var(--z-sticky)
  background: var(--surface-glass-heavy)
  backdrop-filter: blur(20px) saturate(180%)
  border-bottom: 1px solid var(--border-default)
  padding: var(--space-3) var(--space-6)
  height: 64px
```

#### 2.5.6 Footer

```
Komponent: FPFooter

Props:
  links:      Array<{ label: string, href: string }>
  copyright:  string
  socials?:   Array<{ icon: ReactNode, href: string, label: string }>
  variant:    "minimal" | "extended"

Erişilebilirlik:
  • <footer role="contentinfo">
  • Sosyal medya linkleri: aria-label="Twitter'da FinPilot" vb.

Stil Detayları:
  background: var(--surface-1)
  border-top: 1px solid var(--border-default)
  padding: var(--space-8) var(--space-6)
  font-size: var(--text-sm)
  color: var(--text-tertiary)
```

---

## 3. NEXT.JS + TAILWIND SCAFFOLD ÖNERİSİ

### 3.1 Neden Streamlit'ten Geçiş?

| Kriter | Streamlit | Next.js + Tailwind |
|--------|-----------|-------------------|
| **FCP** | 2.5-4s (Python TTFB) | 0.5-1s (Edge/static) |
| **SEO** | Yok (SPA, JS render) | SSR/SSG native |
| **Erişilebilirlik** | Sınırlı (70 unsafe_allow_html) | Tam kontrol (semantic HTML) |
| **Tasarım esnekliği** | CSS injection | Tailwind + CSS Modules |
| **Bundle size** | ~3.5 MB (Streamlit runtime) | ~80-150 KB (tree-shaken) |
| **PWA** | Yok | next-pwa native |
| **Komponent reuse** | Python fonksiyonları | React component tree |
| **Auth** | Custom (auth/ modülü) | NextAuth.js |
| **Backend** | Streamlit server | API Routes / tRPC |

### 3.2 Geçiş Stratejisi: Kademeli (Yıkıcı Değil)

```
FAZ 1 (Hemen): Streamlit DS iyileştirme — mevcut styles.py token genişletme
FAZ 2 (Hafta 3-4): public_website/ → Next.js migration (static pages)
FAZ 3 (Hafta 5-6): Dashboard → Next.js + API (Streamlit backend korunur)
FAZ 4 (Hafta 7-8): Tam geçiş, Streamlit → FastAPI + Next.js
```

### 3.3 Next.js Proje Yapısı

```
finpilot-web/
├── app/                           # Next.js 14 App Router
│   ├── layout.tsx                 # Root layout + font loading
│   ├── page.tsx                   # Landing page (SSG)
│   ├── dashboard/
│   │   ├── layout.tsx             # Auth-gated layout
│   │   ├── page.tsx               # Ana panel
│   │   └── scan/[id]/page.tsx     # Scan detail
│   ├── academy/
│   │   ├── page.tsx               # FinSense
│   │   └── quiz/page.tsx
│   ├── demo/page.tsx
│   ├── auth/
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   └── api/                       # API Routes (FastAPI proxy/bridge)
│       ├── scan/route.ts
│       ├── signals/route.ts
│       └── auth/[...nextauth]/route.ts
├── components/                    # Storybook-aligned
│   ├── ui/                        # Atomic
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Modal.tsx
│   │   ├── Input.tsx
│   │   ├── Badge.tsx
│   │   ├── Skeleton.tsx
│   │   └── Tooltip.tsx
│   ├── layout/
│   │   ├── Header.tsx
│   │   ├── Footer.tsx
│   │   ├── Sidebar.tsx
│   │   └── PageContainer.tsx
│   ├── dashboard/
│   │   ├── SignalCard.tsx
│   │   ├── MetricPanel.tsx
│   │   ├── ScanControls.tsx
│   │   └── DRLPanel.tsx
│   └── academy/
│       ├── DictionaryBrowser.tsx
│       └── QuizModule.tsx
├── lib/
│   ├── api.ts                     # Fetch helpers
│   ├── auth.ts                    # NextAuth config
│   └── hooks/                     # Custom hooks
│       ├── useScan.ts
│       └── useSignals.ts
├── styles/
│   ├── globals.css                # @tailwind directives + token overrides
│   └── tokens.css                 # Design token custom properties (2.1-2.3)
├── public/
│   ├── fonts/                     # Inter self-hosted (GDPR)
│   ├── icons/
│   └── manifest.json
├── tailwind.config.ts
├── next.config.ts
├── .storybook/                    # Storybook 8 config
│   ├── main.ts
│   └── preview.ts
├── package.json
└── tsconfig.json
```

### 3.4 Design Token → Tailwind Eşleştirme

```typescript
// tailwind.config.ts
import type { Config } from 'tailwindcss'

export default {
  content: ['./app/**/*.tsx', './components/**/*.tsx'],
  theme: {
    extend: {
      // ── Typography ──
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'system-ui', 'sans-serif'],
        mono: ['SF Mono', 'JetBrains Mono', 'Fira Code', 'monospace'],
      },
      fontSize: {
        'xs':   ['0.694rem', { lineHeight: '1.2' }],
        'sm':   ['0.833rem', { lineHeight: '1.375' }],
        'base': ['1rem',     { lineHeight: '1.5' }],
        'md':   ['1.125rem', { lineHeight: '1.5' }],
        'lg':   ['1.25rem',  { lineHeight: '1.375' }],
        'xl':   ['1.563rem', { lineHeight: '1.2' }],
        '2xl':  ['1.953rem', { lineHeight: '1.2' }],
        '3xl':  ['2.441rem', { lineHeight: '1.1' }],
        '4xl':  ['3.052rem', { lineHeight: '1.05' }],
      },

      // ── Colors ──
      colors: {
        brand: {
          DEFAULT: '#00e6e6',
          hover: '#0ea5e9',
          muted: 'rgba(0, 230, 230, 0.12)',
          subtle: 'rgba(0, 230, 230, 0.06)',
        },
        surface: {
          0: '#000000',
          1: '#0a0f1a',
          2: '#0f172a',
          3: '#1e293b',
          4: '#334155',
          5: '#475569',
        },
        // Semantic colors: success, error, warning, info — Tailwind defaults
      },

      // ── Spacing (4px base, extend beyond default) ──
      spacing: {
        '0.5': '2px',
        '1.5': '6px',
        '13':  '52px',
        '15':  '60px',
        '18':  '72px',
        '22':  '88px',
      },

      // ── Border Radius ──
      borderRadius: {
        sm: '6px',
        DEFAULT: '12px',
        lg: '16px',
        xl: '20px',
      },

      // ── Shadows (Apple-style diffused) ──
      boxShadow: {
        card: '0 4px 24px -8px rgba(14, 165, 233, 0.25)',
        'card-hover': '0 8px 32px -8px rgba(14, 165, 233, 0.4)',
        glow: '0 20px 48px -20px rgba(14, 165, 233, 0.55)',
        modal: '0 24px 64px -16px rgba(0, 0, 0, 0.5)',
      },

      // ── Transitions ──
      transitionDuration: {
        fast: '150ms',
        normal: '250ms',
        smooth: '400ms',
      },

      // ── Z-index ──
      zIndex: {
        dropdown: '100',
        sticky: '200',
        'modal-backdrop': '300',
        modal: '400',
        toast: '500',
        tooltip: '600',
      },

      // ── Backdrop Blur (glassmorphism) ──
      backdropBlur: {
        glass: '20px',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
} satisfies Config
```

### 3.5 Token Eşleştirme Adımları

```
Adım 1: styles/tokens.css oluştur → tüm CSS custom properties
Adım 2: tailwind.config.ts → token'ları theme.extend'e map et
Adım 3: globals.css → @layer base, @layer components, @layer utilities
Adım 4: Her Figma komponent → Tailwind class combination belgele
Adım 5: Storybook → her komponent için light/dark, responsive, a11y story
```

**Örnek Token → Tailwind → JSX akışı:**

```tsx
// Figma'da: Button/Primary/MD
// Token:   bg=brand, radius=md, text=surface-2, weight=semibold
// Tailwind: bg-brand rounded text-surface-2 font-semibold px-5 py-2

export function Button({ label, variant = 'primary', size = 'md' }: ButtonProps) {
  return (
    <button
      className={cn(
        // Base
        'inline-flex items-center justify-center rounded font-semibold',
        'transition-all duration-fast',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:ring-offset-surface-2',
        // Variant
        variant === 'primary' && 'bg-gradient-to-r from-brand to-brand-hover text-surface-2 shadow-card hover:-translate-y-px hover:shadow-card-hover active:scale-[0.98]',
        variant === 'secondary' && 'border border-brand/30 bg-surface-3 text-white hover:bg-brand/10',
        variant === 'ghost' && 'text-brand hover:bg-brand/10',
        // Size
        size === 'sm' && 'h-8 px-3 text-xs',
        size === 'md' && 'h-10 px-5 text-sm',
        size === 'lg' && 'h-12 px-6 text-base',
      )}
    >
      {label}
    </button>
  )
}
```

---

## 4. ERİŞİLEBİLİRLİK, PERFORMANS VE SEO YAPILACAKLAR LİSTESİ

### 4.1 Erişilebilirlik — WCAG 2.1 AA Uyumu

| # | Görev | Etki | Öncelik |
|---|-------|------|---------|
| A1 | **Renk kontrastı düzelt:** `--text-muted` 3.2:1 → 4.5:1 (`#94a3b8 → #a0aec0`) | WCAG 1.4.3 | 🔴 P0 |
| A2 | **Focus-visible göstergesi ekle:** Tüm interactive element'lere `outline: 2px solid var(--color-primary)` | WCAG 2.4.7 | 🔴 P0 |
| A3 | **ARIA role + label:** 70 unsafe_allow_html bloğuna semantik role ve aria-label | WCAG 4.1.2 | 🔴 P0 |
| A4 | **Emoji → icon swap:** 412 emoji yerine SVG icon (Lucide/Heroicons) + `aria-hidden="true"` | WCAG 1.1.1 | 🟡 P1 |
| A5 | **`lang="tr"` düzelt:** public_website `lang="en"` → `lang="tr"` (veya multi-lang desteği) | WCAG 3.1.1 | 🟡 P1 |
| A6 | **Reduced motion:** `@media (prefers-reduced-motion: reduce)` → tüm animasyonları kapat | WCAG 2.3.3 | 🟡 P1 |
| A7 | **Keyboard navigation:** Custom HTML kartlarda Tab/Enter/Space desteği + tabindex | WCAG 2.1.1 | 🟡 P1 |
| A8 | **Skip to content:** Sayfa başlarına "Ana içeriğe geç" link'i | WCAG 2.4.1 | 🟢 P2 |
| A9 | **Form label bağlama:** Streamlit custom form'lardaki input'lara label + describedby | WCAG 1.3.1 | 🟢 P2 |
| A10 | **Error messages:** Accessible error announcements (aria-live="assertive") | WCAG 3.3.1 | 🟢 P2 |
| A11 | **Color-blind safe palette:** Semantic renklerde shape + icon ek gösterge (yeşil/kırmızı ayrımı) | WCAG 1.4.1 | 🟢 P2 |

### 4.2 Performans — Core Web Vitals Hedefleri

| Metrik | Mevcut (Tahm.) | Hedef | Nasıl |
|--------|---------------|-------|-------|
| **FCP** | ~3s | **< 1.5s** | SSR/SSG (Next.js), font preload, critical CSS inline |
| **LCP** | ~5s | **< 2.5s** | Hero image → SVG inline, lazy-load below-fold, edge CDN |
| **CLS** | ~0.1 | **< 0.05** | Skeleton boyutları sabit, font fallback metrikleri eşle |
| **TBT** | Yüksek | **< 200ms** | unsafe_allow_html → React component, code splitting |
| **INP** | Bilinmiyor | **< 200ms** | Event handler'ları debounce, React.memo, transitions |

| # | Görev | Etki | Öncelik |
|---|-------|------|---------|
| P1 | **Font optimizasyonu:** Inter woff2 self-host, `font-display: swap`, size-adjust fallback | FCP -0.3s | 🔴 P0 |
| P2 | **Critical CSS inline:** İlk ekran için gereken CSS'i `<head>`'e inline et | FCP -0.5s | 🔴 P0 |
| P3 | **Image optimization:** SVG inline, WebP/AVIF lazy-load, `<Image>` Next.js component | LCP -1s | 🔴 P0 |
| P4 | **Code splitting:** Dashboard, Academy, Demo ayrı chunk'lar → initial bundle küçültme | TBT -%40 | 🟡 P1 |
| P5 | **API response caching:** SWR/React Query ile stale-while-revalidate | TTI -1s | 🟡 P1 |
| P6 | **Service Worker (Streamlit):** Offline shell + cache-first stratejisi | Repeat visit -%50 | 🟢 P2 |
| P7 | **Edge deployment:** Vercel Edge / Cloudflare Pages | TTFB < 100ms | 🟢 P2 |

### 4.3 SEO Yapılacaklar

| # | Görev | Etki | Öncelik |
|---|-------|------|---------|
| S1 | **Meta tags:** Her sayfa için benzersiz `<title>`, `<meta description>`, `og:image` | Arama görünürlüğü | 🔴 P0 |
| S2 | **Semantic HTML:** `<header>`, `<main>`, `<nav>`, `<article>`, `<footer>` doğru kullanım | Crawl quality | 🔴 P0 |
| S3 | **Structured data:** JSON-LD — Organization, WebApplication, FAQPage şemaları | Rich snippets | 🟡 P1 |
| S4 | **Sitemap.xml:** Otomatik generate (next-sitemap) | Indexing hızı | 🟡 P1 |
| S5 | **robots.txt:** Doğru allow/disallow, sitemap referansı | Crawl kontrolü | 🟡 P1 |
| S6 | **Canonical URL:** Her sayfada `<link rel="canonical">` | Duplicate content | 🟢 P2 |
| S7 | **hreflang:** TR/EN için `<link rel="alternate" hreflang="tr">` | Multi-lang SEO | 🟢 P2 |
| S8 | **Performance SEO:** Core Web Vitals → Google ranking signal | Sıralama iyileşme | 🟢 P2 |

---

## 5. SEKİZ HAFTALIK ÖNCELİKLENDİRİLMİŞ YOL HARİTASI

### Genel Bakış

```
H1-H2:  Foundation        → DS token genişletme, a11y critical fix, font sistemi
H3-H4:  Component Layer   → 6 core komponent build, Storybook, inline style tasfiye
H5-H6:  Page Migration    → public_website Next.js, Dashboard prototype
H7-H8:  Polish & Ship     → Perf optimization, SEO, test, launch
```

---

### HAFTA 1 — Design Token & Erişilebilirlik Temeli

| Görev | Detay | İş Gücü | Risk | KPI Etkisi |
|-------|-------|---------|------|-----------|
| `styles.py` tipografi token'ları ekle | §2.1'deki font-family, text-scale, line-height, weight | 1 gün | 🟢 Düşük | Tipografi tutarlılığı: 0% → 100% |
| Renk kontrastı düzelt (A1) | `--text-muted` → 4.5:1 AA uyumlu, 3 problem renk | 0.5 gün | 🟢 Düşük | WCAG AA contrst ihlali: ~15 → 0 |
| Focus-visible ekle (A2) | Global `:focus-visible` kural + outline token | 0.5 gün | 🟢 Düşük | Keyboard a11y: 0% → ~60% |
| Inter font self-host + preload | `assets/fonts/inter-*.woff2` + CSS @font-face | 0.5 gün | 🟢 Düşük | FCP: -0.2-0.3s |
| `.streamlit/config.toml` güncelle | Font: "sans serif" → Inter fallback chain | 0.5 gün | 🟢 Düşük | Marka tutarlılığı |

**Hafta 1 Toplam: 3 gün | Risk: 🟢 Düşük**
**KPI:** Kontrast ihlalleri sıfırlanır, tipografi sistemi kurulur.

---

### HAFTA 2 — ARIA, Semantic Markup & Reduced Motion

| Görev | Detay | İş Gücü | Risk | KPI Etkisi |
|-------|-------|---------|------|-----------|
| ARIA audit: ilk 20 unsafe_allow_html (A3) | En çok kullanılan kartlar + panellere role/aria-label | 2 gün | 🟡 Orta | Erişilebilir komponent: 4 → 24 |
| Reduced motion media query (A6) | `@media (prefers-reduced-motion)` global kural | 0.5 gün | 🟢 Düşük | Motion-safe kullanıcı desteği: 0 → %100 |
| `lang="tr"` düzeltmesi (A5) | public_website + Streamlit meta tag | 0.5 gün | 🟢 Düşük | i18n doğruluğu |
| Spacing token genişletme | §2.3'teki space-16/20/24 + breakpoint referans | 0.5 gün | 🟢 Düşük | Layout tutarlılığı |
| Color palette QA + color-blind test | Figma Color Blind plugin veya Sim Daltonism ile doğrulama | 0.5 gün | 🟢 Düşük | Color-blind uyumluluk |

**Hafta 2 Toplam: 4 gün | Risk: 🟡 Orta (ARIA kırılma riski)**
**KPI:** WCAG AA erişilebilirlik skoru: ~35 → ~65/100 tahmini.

---

### HAFTA 3 — Core Component Build (Button, Card, Badge)

| Görev | Detay | İş Gücü | Risk | KPI Etkisi |
|-------|-------|---------|------|-----------|
| FPButton: Python helper → HTML | §2.5.1 spec, 5 varyant, 3 boyut, tüm durumlar | 1.5 gün | 🟡 Orta | Buton tutarlılığı: ~20% → 100% |
| FPCard: Signal/Metric/Feature/Empty | §2.5.2 spec, glassmorphism, hover mikroanimasyonu | 2 gün | 🟡 Orta | Kart stilı: inline → token-based |
| FPBadge: Status/Signal/Score | Buy/Hold/Sell + info/warning varyantları | 0.5 gün | 🟢 Düşük | Badge tutarlılığı |
| Inline style cleanup başlangıcı | İlk 30/130 inline style → CSS class migration | 1 gün | 🟡 Orta | Inline style: 130 → ~100 |

**Hafta 3 Toplam: 5 gün | Risk: 🟡 Orta (regression potansiyeli)**
**KPI:** 3 core komponent üretime hazır, inline CSS %23 azalır.

---

### HAFTA 4 — Core Component Build (Modal, Form, Header, Footer)

| Görev | Detay | İş Gücü | Risk | KPI Etkisi |
|-------|-------|---------|------|-----------|
| FPModal: Default + Confirmation | §2.5.3 spec, focus trap, Escape, animasyon | 1.5 gün | 🟡 Orta | Modal a11y: 0% → 100% |
| FPInput/FPSelect: Form controls | §2.5.4 spec, label bağlama, error state | 1.5 gün | 🟡 Orta | Form a11y: ~30% → 90% |
| FPHeader + FPFooter | §2.5.5-6 spec, sticky nav, responsive | 1 gün | 🟢 Düşük | Nav tutarlılığı |
| Storybook setup (Streamlit alternatif) | Python-based component catalog sayfası veya docs | 1 gün | 🟡 Orta | Komponent dokümantasyonu |

**Hafta 4 Toplam: 5 gün | Risk: 🟡 Orta**
**KPI:** 6/6 core komponent hazır. Tüm formlar accessible. Storybook/catalog canlı.

---

### HAFTA 5 — Public Website Next.js Migration

| Görev | Detay | İş Gücü | Risk | KPI Etkisi |
|-------|-------|---------|------|-----------|
| Next.js 14 scaffold | §3.3 yapı, tailwind.config.ts token mapping | 1 gün | 🟡 Orta | Modern framework temeli |
| Landing page migration | `public_website/index.html` → `app/page.tsx` SSG | 2 gün | 🟡 Orta | FCP: ~3s → <1s |
| About/Contact/Terms pages | 4 statik sayfa Next.js'e | 1 gün | 🟢 Düşük | SEO: full SSG |
| Meta tags + structured data (S1, S3) | Her sayfa unique title/desc + JSON-LD | 0.5 gün | 🟢 Düşük | SEO: rich snippets |
| sitemap.xml + robots.txt (S4, S5) | next-sitemap config | 0.5 gün | 🟢 Düşük | Indexing hızı |

**Hafta 5 Toplam: 5 gün | Risk: 🟡 Orta (yeni teknoloji stack)**
**KPI:** Public site Lighthouse: ~55 → ~90. FCP: 3s → <1s. SEO: meta tag kapsamı 100%.

---

### HAFTA 6 — Dashboard Prototype (Next.js + FastAPI Bridge)

| Görev | Detay | İş Gücü | Risk | KPI Etkisi |
|-------|-------|---------|------|-----------|
| FastAPI bridge endpoint'leri | `/api/scan`, `/api/signals`, `/api/auth` — Streamlit backend proxy | 2 gün | 🔴 Yüksek | Backend bağlantısı |
| Dashboard page prototype | SignalCard + MetricPanel + ScanControls Next.js'te | 2 gün | 🔴 Yüksek | Dashboard proof-of-concept |
| Auth integration | NextAuth.js + mevcut auth/ modülü adapter | 1 gün | 🔴 Yüksek | Kullanıcı oturum yönetimi |

**Hafta 6 Toplam: 5 gün | Risk: 🔴 Yüksek (backend entegrasyon)**
**KPI:** Dashboard fonksiyonel prototype. En az 3 sinyal kartı canlı veri ile render.

---

### HAFTA 7 — Performans Optimizasyonu & Polish

| Görev | Detay | İş Gücü | Risk | KPI Etkisi |
|-------|-------|---------|------|-----------|
| Font optimization wrap-up (P1) | font-display: swap, size-adjust, preload tag'ları | 0.5 gün | 🟢 Düşük | FCP: -0.3s |
| Image optimization (P3) | Logo → inline SVG, OG images → WebP | 0.5 gün | 🟢 Düşük | LCP: -0.5s |
| Code splitting (P4) | Next.js dynamic import — Dashboard/Academy/Demo | 0.5 gün | 🟢 Düşük | TBT: -%40 |
| Kalan inline CSS temizliği | 100 → 0 inline style (Streamlit views) | 2 gün | 🟡 Orta | Bakım kolaylığı: büyük artış |
| Micro-interaction polish | Apple-stil hover, press, skeleton transitions | 1.5 gün | 🟢 Düşük | Kullanıcı memnuniyeti (UX puanı) |

**Hafta 7 Toplam: 5 gün | Risk: 🟡 Orta**
**KPI:** Lighthouse Performance: ≥90. LCP < 2.5s. CLS < 0.05. Inline CSS: 0.

---

### HAFTA 8 — QA, A/B Test Setup & Launch

| Görev | Detay | İş Gücü | Risk | KPI Etkisi |
|-------|-------|---------|------|-----------|
| A11y automated test suite | axe-core CI integration — her PR'da WCAG scan | 1 gün | 🟢 Düşük | Regression koruması |
| Cross-browser QA | Chrome, Firefox, Safari, Edge + mobil (3 cihaz) | 1 gün | 🟡 Orta | Tarayıcı uyumluluk: %100 |
| Lighthouse CI gate | GitHub Actions'a lighthouse-ci — skor < 85 → fail | 0.5 gün | 🟢 Düşük | Performans regresyon koruması |
| Analytics setup | Vercel Analytics / Plausible (GDPR-uyumlu) | 0.5 gün | 🟢 Düşük | Veri toplama başlangıcı |
| A/B test framework | Feature flag sistemi (eski vs yeni UI toggle) | 1 gün | 🟡 Orta | Risk azaltma: rollback imkânı |
| Production deploy + monitoring | Edge CDN, error tracking (Sentry), uptime check | 1 gün | 🟡 Orta | %99.9 uptime hedefi |

**Hafta 8 Toplam: 5 gün | Risk: 🟡 Orta**
**KPI:** Otomatik test kapsamı: a11y + perf CI. Production launch. A/B mekanizması aktif.

---

### Yol Haritası Özet Tablosu

| Hafta | Odak | İş Gücü | Risk | Kümülatif Kazanım |
|-------|------|---------|------|-------------------|
| **H1** | Token + Font + Kontrast | 3 gün | 🟢 | Tipografi sistemi, kontrast düzeltmesi |
| **H2** | ARIA + Reduced Motion | 4 gün | 🟡 | WCAG skoru ~35 → ~65 |
| **H3** | Button + Card + Badge | 5 gün | 🟡 | 3 core komponent, inline CSS -%23 |
| **H4** | Modal + Form + Header/Footer | 5 gün | 🟡 | 6/6 komponent, form a11y %90+ |
| **H5** | Public site → Next.js | 5 gün | 🟡 | Lighthouse ~55 → ~90, FCP <1s |
| **H6** | Dashboard prototype | 5 gün | 🔴 | Canlı veri ile sinyal kartları |
| **H7** | Perf polish + CSS cleanup | 5 gün | 🟡 | LCP <2.5s, CLS <0.05, 0 inline CSS |
| **H8** | QA + CI + Launch | 5 gün | 🟡 | axe-core CI, A/B test, prod deploy |
| **TOPLAM** | | **37 gün** | | |

### Beklenen Nihai KPI'lar (8 Hafta Sonunda)

| KPI | Öncesi | Sonrası | Değişim |
|-----|--------|---------|---------|
| **Lighthouse Performance** | ~45 | ≥ 90 | +100% |
| **Lighthouse Accessibility** | ~35 | ≥ 90 | +157% |
| **Lighthouse SEO** | ~50 | ≥ 95 | +90% |
| **FCP** | ~3s | < 1.5s | -%50 |
| **LCP** | ~5s | < 2.5s | -%50 |
| **CLS** | ~0.1 | < 0.05 | -%50 |
| **WCAG AA ihlalleri** | ~50+ | 0 | -%100 |
| **Inline CSS satırı** | 130 | 0 | -%100 |
| **Core komponent kütüphanesi** | 0 | 6 | ∞ |
| **Design token kapsamı** | %60 | %100 | +67% |
| **unsafe_allow_html kullanımı** | 70 | ≤ 20 | -%71 |
| **Emoji-as-icon** | 412 | ≤ 50 | -%88 |

---

## DİKKAT EDİLECEK RİSKLER

| Risk | Etki | Azaltma |
|------|------|---------|
| **Streamlit → Next.js migration scope creep** | Timeline kayması | H5-6'yı public_website ile sınırla; dashboard'ı aşamalı geçir |
| **Hazır tema tuzağı** | Marka-özgünlük kaybı | Kendi token sisteminizi kurun (§2), hazır UI kit kullanmayın |
| **ARIA ekleme → regression** | Mevcut işlevsellik bozulur | Her ARIA değişikliği için smoke test, axe-core CI kapısı |
| **Agresif optimizasyon → UX bozulma** | Kullanıcı deneyimi bozulur | A/B test framework (H8), feature flag ile kademeli rollout |
| **Font/CSS değişiklik → görsel kırılma** | Mevcut arayüz bozulur | Screenshot regression test (Percy/Chromatic) |
| **Backend API bridge karmaşıklığı** | H6 tamamlanmaz | İlk iteration'da read-only endpoint'ler, write H9+'a ||

---

*Bu yol haritası FinPilot projesinin 2026-03-05 itibarıyla 14,200 LOC UI katmanının kapsamlı auditine dayanmaktadır.*
