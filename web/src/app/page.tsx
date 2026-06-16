import Navbar from "@/components/Navbar";
import HeroGrid from "@/components/HeroGrid";
import Waitlist from "@/components/Waitlist";
import Footer from "@/components/Footer";

export default function Home() {
  return (
    <>
      <Navbar />
      <main>
        <HeroGrid />
        <Waitlist />
      </main>
      <Footer />
    </>
  );
}
