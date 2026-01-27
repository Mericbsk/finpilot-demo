import { SettingsCard } from "./components/SettingsCard";
import { PerformanceSection } from "./components/PerformanceSection";
import { PrimaryCtaBar } from "./components/PrimaryCtaBar";

function App() {
  return (
    <div className="min-h-screen bg-slate-950 bg-[radial-gradient(circle_at_top,_rgba(0,230,230,0.12),_transparent_50%)] px-4 pb-12 pt-6">
      <PrimaryCtaBar />
      <main className="mx-auto mt-12 flex w-full max-w-6xl flex-col gap-10">
        <SettingsCard />
        <PerformanceSection />
      </main>
    </div>
  );
}

export default App;
