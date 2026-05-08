/* ================================================================
   SHARED STOCK DATA — Single source of truth for all dashboard pages
   ================================================================ */

/* ── Inline colour constants ──────────────────────────────── */
export const C = {
  bg: "#000000",
  card: "#111118",
  cardHover: "#1a1a24",
  primary: "#0a0a10",
  text1: "#f5f5f7",
  text2: "#a1a1a6",
  text3: "#6e6e73",
  border: "rgba(255,255,255,0.12)",
  borderHover: "rgba(255,255,255,0.25)",
  cyan: "#00d4ff",
  blue: "#0a84ff",
  green: "#30d158",
  red: "#ff453a",
  yellow: "#ffd60a",
  purple: "#bf5af2",
};

/* ── Deterministic hash (Math.imul based) ─────────────────── */
export function hashStr(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (Math.imul(31, h) + s.charCodeAt(i)) | 0;
  return Math.abs(h);
}

/* ── Seeded pseudo-random [0, 1) ──────────────────────────── */
export function seededRandom(seed: number): number {
  const x = Math.sin(seed + 1) * 10000;
  return x - Math.floor(x);
}

/* ── Company names (comprehensive — 80+ entries) ──────────── */
export const companyNames: Record<string, string> = {
  // Tech — Large Cap
  AAPL: "Apple Inc", MSFT: "Microsoft Corp", NVDA: "NVIDIA Corp", GOOGL: "Alphabet Inc",
  AMZN: "Amazon.com Inc", META: "Meta Platforms", TSLA: "Tesla Inc", AMD: "Advanced Micro Devices",
  NFLX: "Netflix Inc", CRM: "Salesforce Inc", ORCL: "Oracle Corp", ADBE: "Adobe Inc",
  INTC: "Intel Corp", QCOM: "Qualcomm Inc", AVGO: "Broadcom Inc", TXN: "Texas Instruments",
  IBM: "IBM Corp", NOW: "ServiceNow Inc", SHOP: "Shopify Inc", SQ: "Block Inc",
  INTU: "Intuit Inc", ISRG: "Intuitive Surgical", LRCX: "Lam Research", KLAC: "KLA Corp",
  AMAT: "Applied Materials", MU: "Micron Technology", ARM: "Arm Holdings", SMCI: "Super Micro Computer",
  // Tech — Growth / Cloud
  PYPL: "PayPal Holdings", COIN: "Coinbase Global", PLTR: "Palantir Technologies",
  SNOW: "Snowflake Inc", NET: "Cloudflare Inc", DDOG: "Datadog Inc", ZS: "Zscaler Inc",
  CRWD: "CrowdStrike Holdings", PANW: "Palo Alto Networks", MDB: "MongoDB Inc",
  // Fintech & Finance
  V: "Visa Inc", MA: "Mastercard Inc", JPM: "JPMorgan Chase", BAC: "Bank of America",
  GS: "Goldman Sachs", MS: "Morgan Stanley", WFC: "Wells Fargo", C: "Citigroup Inc",
  BLK: "BlackRock Inc", SCHW: "Charles Schwab",
  // Healthcare
  UNH: "UnitedHealth Group", JNJ: "Johnson & Johnson", PFE: "Pfizer Inc", ABBV: "AbbVie Inc",
  MRK: "Merck & Co", LLY: "Eli Lilly", TMO: "Thermo Fisher", ABT: "Abbott Labs",
  AMGN: "Amgen Inc", GILD: "Gilead Sciences", BMY: "Bristol-Myers Squibb",
  // Energy
  XOM: "Exxon Mobil", CVX: "Chevron Corp", COP: "ConocoPhillips", SLB: "Schlumberger",
  NEE: "NextEra Energy", DUK: "Duke Energy", SO: "Southern Company",
  // Consumer
  DIS: "Walt Disney", CMCSA: "Comcast Corp", T: "AT&T Inc", VZ: "Verizon Communications",
  KO: "Coca-Cola Co", PEP: "PepsiCo Inc", MCD: "McDonald's Corp", SBUX: "Starbucks Corp",
  NKE: "Nike Inc", WMT: "Walmart Inc", COST: "Costco Wholesale", HD: "Home Depot",
  LOW: "Lowe's Companies", TGT: "Target Corp", PG: "Procter & Gamble",
  // Mobility & Gig
  UBER: "Uber Technologies", LYFT: "Lyft Inc", ABNB: "Airbnb Inc", DASH: "DoorDash Inc",
  RBLX: "Roblox Corp", U: "Unity Software",
  // EV & Auto
  RIVN: "Rivian Automotive", LCID: "Lucid Group", F: "Ford Motor Co", GM: "General Motors",
  // Industrial & Aerospace
  BA: "Boeing Co", CAT: "Caterpillar Inc", DE: "Deere & Co", GE: "GE Aerospace",
  HON: "Honeywell International", UPS: "United Parcel Service", FDX: "FedEx Corp",
  LMT: "Lockheed Martin", RTX: "RTX Corp", NOC: "Northrop Grumman",
  // Crypto-adjacent
  MARA: "Marathon Digital", RIOT: "Riot Platforms", HOOD: "Robinhood Markets",
  SOFI: "SoFi Technologies",
  // Space
  SPCE: "Virgin Galactic",
  // Misc
  ACN: "Accenture plc",
};

/* ── Generate stock data (single canonical source) ─────────── */
export interface StockData {
  ticker: string;
  name: string;
  price: number;
  change: number;
  score: number;
  signal: string;
}

export function genStock(ticker: string): StockData {
  const h = hashStr(ticker);
  const price = 10 + seededRandom(h) * 490;           // $10 – $500
  const change = (seededRandom(h + 1) - 0.47) * 14;   // ~-6.6% to +7.4%
  const score = Math.round(12 + seededRandom(h + 2) * 83); // 12 – 95
  const signal =
    score >= 75 ? "BUY" :
    score >= 55 ? "HOLD" :
    score >= 40 ? "CAUTION" :
    "SELL";
  return {
    ticker,
    name: companyNames[ticker] || ticker,
    price: Math.round(price * 100) / 100,
    change: Math.round(change * 100) / 100,
    score,
    signal,
  };
}

/* ── Extended stock data (for pages needing more fields) ──── */
export interface StockDataExtended extends StockData {
  confidence: number;
  rsi: number;
  regime: string;
  rr: number;
  target: number;
  stop: number;
}

export function genStockExtended(ticker: string): StockDataExtended {
  const base = genStock(ticker);
  const h = hashStr(ticker);
  const confidence = Math.round(40 + seededRandom(h + 3) * 55);
  const rsi = Math.round(15 + seededRandom(h + 4) * 70);
  const rr = +(0.5 + seededRandom(h + 5) * 3.5).toFixed(1);
  const regimes = ["Trend", "Volatile", "Range", "Breakout"];
  const regime = regimes[Math.floor(seededRandom(h + 6) * regimes.length)];
  const target = +(base.price * (1 + 0.04 + seededRandom(h + 7) * 0.12)).toFixed(2);
  const stop = +(base.price * (1 - 0.02 - seededRandom(h + 8) * 0.08)).toFixed(2);
  return { ...base, confidence, rsi, regime, rr, target, stop };
}

/* ── Overlay live prices onto generated data ──────────────── */
export function withLivePrice<T extends { price: number; change: number }>(stock: T, live?: { price: number; change: number }): T {
  if (!live || live.price === 0) return stock;
  const ratio = live.price / stock.price;
  const result: Record<string, unknown> = { ...stock, price: live.price, change: live.change };
  if (typeof result.target === "number") result.target = +(result.target as number * ratio).toFixed(2);
  if (typeof result.stop === "number") result.stop = +(result.stop as number * ratio).toFixed(2);
  if (typeof result.tp1 === "number") result.tp1 = +(result.tp1 as number * ratio).toFixed(2);
  if (typeof result.tp2 === "number") result.tp2 = +(result.tp2 as number * ratio).toFixed(2);
  if (typeof result.tp3 === "number") result.tp3 = +(result.tp3 as number * ratio).toFixed(2);
  if (typeof result.sma50 === "number") result.sma50 = +(result.sma50 as number * ratio).toFixed(2);
  if (typeof result.sma200 === "number") result.sma200 = +(result.sma200 as number * ratio).toFixed(2);
  if (typeof result.bb_upper === "number") result.bb_upper = +(result.bb_upper as number * ratio).toFixed(2);
  if (typeof result.bb_lower === "number") result.bb_lower = +(result.bb_lower as number * ratio).toFixed(2);
  if (typeof result.high52w === "number") result.high52w = +(result.high52w as number * ratio).toFixed(2);
  if (typeof result.low52w === "number") result.low52w = +(result.low52w as number * ratio).toFixed(2);
  if (Array.isArray(result.sparkline)) result.sparkline = (result.sparkline as number[]).map((v) => +(v * ratio).toFixed(2));
  return result as T;
}

/* ── Sparkline data generator ─────────────────────────────── */
export function genSparkline(ticker: string, days: number = 14): number[] {
  const h = hashStr(ticker + "spark");
  const pts: number[] = [];
  let v = 50;
  for (let i = 0; i < days; i++) {
    v += (seededRandom(h + i * 7) - 0.48) * 8;
    v = Math.max(10, Math.min(90, v));
    pts.push(v);
  }
  return pts;
}
