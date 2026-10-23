import type { Metadata } from "next";
import { Annotation, DOODLES } from "@/components/doodles";
import s from "./page.module.css";

export const metadata: Metadata = {
  title: "SNUGDOG — Doodle system",
  robots: { index: false },
};

// Internal reference sheet for the doodle system.
export default function DoodleSheet() {
  return (
    <main id="main" className={s.sheet}>
      <header className={s.head}>
        <p className="label">SNUGDOG / Design system</p>
        <h1 className="display">Doodles</h1>
        <p className={s.rule}>
          One weight, one colour, drawn by hand. Use one or two per composition: whitespace beats doodles.
        </p>
      </header>
      <ul className={s.grid}>
        {Object.entries(DOODLES).map(([name, Component]) => (
          <li key={name} className={s.cell}>
            <div className={s.art}>
              <Component />
            </div>
            <span className="label">{name}</span>
          </li>
        ))}
        <li className={s.cell}>
          <div className={s.art}>
            <Annotation>snappy all-beef frank</Annotation>
          </div>
          <span className="label">Annotation</span>
        </li>
      </ul>
    </main>
  );
}
