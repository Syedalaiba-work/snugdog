import { Hero } from "@/components/hero/Hero";
import { ScrollReveals } from "@/components/motion/ScrollReveals";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/sections/Footer";
import { Locations } from "@/components/sections/Locations";
import { Marquee } from "@/components/sections/Marquee";
import { Menu } from "@/components/sections/Menu";
import { Packaging } from "@/components/sections/Packaging";
import { Story } from "@/components/sections/Story";

// One continuous scroll: product, then brand. The food and the mascot each get their own
// scenes and never appear together.
export default function Home() {
  return (
    <>
      <Navbar />
      <main id="main">
        <Hero />
        <Marquee />
        <Menu />
        <Story />
        <Packaging />
        <Locations />
      </main>
      <Footer />
      <ScrollReveals />
    </>
  );
}
