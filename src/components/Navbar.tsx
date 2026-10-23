"use client";

import Link from "next/link";
import { useEffect, useId, useState } from "react";
import { Button } from "@/components/ui/Button";
import s from "./Navbar.module.css";

const LINKS = [
  { href: "#menu", label: "Menu" },
  { href: "#packaging", label: "Packaging" },
  { href: "#story", label: "Story" },
  { href: "#locations", label: "Locations" },
];

export function Navbar() {
  const [open, setOpen] = useState(false);
  const panelId = useId();

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.documentElement.style.overflow = "hidden";
    window.addEventListener("keydown", onKey);
    return () => {
      document.documentElement.style.overflow = "";
      window.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <header className={s.bar} data-open={open || undefined}>
      <Link href="/" className={`display ${s.wordmark}`} aria-label="SNUGDOG home">
        Snugdog
      </Link>

      <nav className={s.links} aria-label="Primary">
        {LINKS.map((link) => (
          <a key={link.href} href={link.href} className={`label ${s.link}`}>
            {link.label}
          </a>
        ))}
      </nav>

      <div className={s.end}>
        <Button href="#menu" size="sm">
          Order
        </Button>
        <button
          type="button"
          className={s.toggle}
          aria-expanded={open}
          aria-controls={panelId}
          onClick={() => setOpen((v) => !v)}
        >
          <span className="sr-only">{open ? "Close menu" : "Open menu"}</span>
          <span className={s.bars} aria-hidden="true" />
        </button>
      </div>

      <nav id={panelId} className={s.panel} aria-label="Mobile" hidden={!open}>
        {LINKS.map((link, i) => (
          <a key={link.href} href={link.href} className={`display ${s.panelLink}`} onClick={() => setOpen(false)}>
            <span className="label">0{i + 1}</span>
            {link.label}
          </a>
        ))}
      </nav>
    </header>
  );
}
