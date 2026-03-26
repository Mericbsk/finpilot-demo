export default function Footer() {
  return (
    <footer className="border-t border-white/[0.06] px-6 py-10 bg-black">
      <div className="mx-auto max-w-[1200px] flex flex-col sm:flex-row items-center justify-between gap-4">
        <p className="text-xs text-[var(--text-tertiary)]">
          © {new Date().getFullYear()} FinPilot · Vienna, Austria
        </p>
        <p className="text-[10px] text-[var(--text-tertiary)] max-w-md text-center sm:text-right">
          Not financial advice. For educational and informational purposes only.
        </p>
      </div>
    </footer>
  );
}
