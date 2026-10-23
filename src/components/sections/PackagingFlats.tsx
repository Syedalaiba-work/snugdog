import type { ReactNode } from "react";
import { HotDogSketch, Paw, Star, Terrier, WrapperEdge, WrapperHatch } from "@/components/doodles";
import { RiseLines } from "@/components/motion/ScrollReveals";
import s from "./PackagingFlats.module.css";

// Packaging drawn as flat artwork in the brand's own language: white stock, black line,
// the wordmark, and Snug. Desktop gets the live 3D scene instead (see Packaging.tsx).

const Wordmark = ({ x, y, size, rotate = 0 }: { x: number; y: number; size: number; rotate?: number }) => (
  <text x={x} y={y} fontSize={size} textAnchor="middle" className={s.wordmark} transform={rotate ? `rotate(${rotate} ${x} ${y})` : undefined}>
    SNUGDOG
  </text>
);

function Flat({ children }: { children: ReactNode }) {
  return (
    <svg viewBox="0 0 360 440" className={s.flat} aria-hidden="true" focusable="false">
      {children}
    </svg>
  );
}

const PIECES: { name: string; note: string; art: ReactNode }[] = [
  {
    name: "The box",
    note: "Holds one dog, snug.",
    art: (
      <Flat>
        <path className={s.stock} d="M40 150 L180 110 L320 150 L320 340 L180 384 L40 340 Z" />
        <path className={s.fold} d="M40 150 L180 194 L320 150 M180 194 L180 384" />
        <path className={s.stock} d="M40 150 L180 110 L320 150 L180 194 Z" />
        <Wordmark x={110} y={268} size={34} rotate={17} />
        <Terrier x={196} y={236} width={108} height={75} className={s.ink} />
      </Flat>
    ),
  },
  {
    name: "The wrapper",
    note: "Greaseproof, tear-open.",
    art: (
      <Flat>
        <path className={s.stock} d="M70 96 L290 96 L308 372 L52 372 Z" />
        <WrapperEdge x={66} y={86} width={228} height={22} className={s.ink} />
        <HotDogSketch x={104} y={18} width={152} height={76} className={s.chalk} />
        <Wordmark x={180} y={236} size={46} />
        <path className={s.fold} d="M92 262 L268 262" />
        <WrapperHatch x={84} y={290} width={72} height={54} className={s.ink} />
        <Paw x={236} y={296} width={44} height={44} className={s.ink} />
      </Flat>
    ),
  },
  {
    name: "The cup",
    note: "Cold drinks, loud lid.",
    art: (
      <Flat>
        <path className={s.fold} d="M196 18 L206 96" />
        <path className={s.stock} d="M92 96 L268 96 L276 124 L84 124 Z" />
        <path className={s.stock} d="M96 124 L264 124 L240 396 L120 396 Z" />
        <Wordmark x={180} y={228} size={36} />
        <Terrier x={132} y={258} width={96} height={66} className={s.ink} />
        <Star x={232} y={150} width={24} height={24} className={s.ink} />
      </Flat>
    ),
  },
  {
    name: "The bag",
    note: "For when one is not enough.",
    art: (
      <Flat>
        <path className={s.fold} d="M132 92 C132 40 228 40 228 92" />
        <path className={s.stock} d="M64 92 L296 92 L296 400 L64 400 Z" />
        <path className={s.fold} d="M64 132 L296 132" />
        <Terrier x={98} y={166} width={164} height={114} className={s.ink} />
        <Wordmark x={180} y={346} size={48} />
      </Flat>
    ),
  },
];

/** Flat packaging artwork: shown on phones and tablets, for reduced motion, and if WebGL fails. */
export function PackagingFlats() {
  return (
    <section id="packaging" className={s.packaging} aria-labelledby="packaging-title">
      <div className={s.track}>
        <header className={s.head}>
          <p className={`label ${s.kicker}`} data-rise>
            04 / Packaging
          </p>
          <RiseLines id="packaging-title" className={`display ${s.title}`} lines={["White box.", "Black line.", "One good dog."]} />
          <p className={s.lede} data-rise>
            Plain stock, one colour of ink, and Snug on everything. You will know it across a street.
          </p>
        </header>

        <ul className={s.pieces}>
          {PIECES.map((piece, i) => (
            <li key={piece.name} className={s.piece}>
              {piece.art}
              <div className={s.caption}>
                <span className="label">0{i + 1}</span>
                <h3 className={`display ${s.name}`}>{piece.name}</h3>
                <p>{piece.note}</p>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
