import { Terrier } from "@/components/doodles";
import { Button } from "@/components/ui/Button";
import s from "./Footer.module.css";

const LINKS = [
  { href: "#menu", label: "Menu" },
  { href: "#story", label: "Story" },
  { href: "#packaging", label: "Packaging" },
  { href: "#locations", label: "Locations" },
];

export function Footer() {
  return (
    <footer className={s.footer}>
      <div className={s.top}>
        <p className={`display ${s.sign}`} data-rise>
          Hungry?
        </p>
        <div className={s.cta} data-rise>
          <Button href="#menu" className={s.button}>
            Order now
          </Button>
        </div>
      </div>

      <div className={s.mid}>
        <nav className={s.links} aria-label="Footer">
          {LINKS.map((link) => (
            <a key={link.href} href={link.href} className="label">
              {link.label}
            </a>
          ))}
        </nav>
        <div className={s.snug} data-draw-on-view>
          <Terrier />
        </div>
      </div>

      {/* decorative: the wordmark set as wide as the page */}
      <p className={`display ${s.wordmark}`} aria-hidden="true">
        Snugdog
      </p>

      <div className={s.base}>
        <span className="label">© SNUGDOG</span>
        <span className="label">Hot dogs for happier humans</span>
      </div>
    </footer>
  );
}
