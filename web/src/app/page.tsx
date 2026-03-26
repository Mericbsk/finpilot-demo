import Navbar from "@/components/Navbar";
import HeroGrid from "@/components/HeroGrid";
import Footer from "@/components/Footer";

export default function Home() {
  return (
    <>
      <Navbar />
      <main>
        <HeroGrid />
      </main>
      <Footer />
    </>
  );
}
