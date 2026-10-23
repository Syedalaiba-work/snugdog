import type { Metadata, Viewport } from "next";
import localFont from "next/font/local";
import "./globals.css";

// Fonts are self-hosted (src/fonts, SIL OFL) so builds never depend on a font CDN.
// One variable family covers both voices: condensed 900 for display, regular width for UI/body.
const archivo = localFont({
  src: "../fonts/archivo-variable.woff2",
  variable: "--font-archivo",
  weight: "100 900",
  declarations: [{ prop: "font-stretch", value: "62% 125%" }],
  display: "swap",
});

// Handwriting is reserved for annotations and doodle callouts.
const caveat = localFont({
  src: "../fonts/caveat-600.woff2",
  variable: "--font-caveat",
  weight: "600",
  display: "swap",
});

export const metadata: Metadata = {
  title: "SNUGDOG — Hot dogs for happier humans",
  description: "Snappy franks, toasted buns and proper toppings. SNUGDOG makes hot dogs for happier humans.",
};

export const viewport: Viewport = {
  themeColor: "#faf8f3",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${archivo.variable} ${caveat.variable}`}>
      <body>
        <noscript>
          <style>{`[data-reveal]{visibility:visible!important}.doodle[data-draw]>*{stroke-dashoffset:0!important;opacity:1!important}`}</style>
        </noscript>
        {/* Filters for the hand-drawn "boil": each redraws line work with a slightly different wobble. */}
        <svg width="0" height="0" style={{ position: "absolute" }} aria-hidden="true" focusable="false">
          <filter id="boil-a">
            <feTurbulence type="fractalNoise" baseFrequency="0.03" numOctaves="2" seed="3" />
            <feDisplacementMap in="SourceGraphic" scale="3" />
          </filter>
          <filter id="boil-b">
            <feTurbulence type="fractalNoise" baseFrequency="0.03" numOctaves="2" seed="11" />
            <feDisplacementMap in="SourceGraphic" scale="3" />
          </filter>
        </svg>
        <a className="skip-link label" href="#main">
          Skip to content
        </a>
        {children}
      </body>
    </html>
  );
}
