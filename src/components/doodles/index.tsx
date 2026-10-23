// SNUGDOG doodle system.
// Every doodle is a single-colour line drawing that inherits `currentColor`, shares one
// stroke weight (--doodle-stroke) and can draw itself on: pass `draw` and the motion
// layer animates each stroke (all strokes are normalised with pathLength={1}).
// Rule of use: whitespace > doodles. One or two per composition.

import type { ReactNode, SVGProps } from "react";

export type DoodleProps = Omit<SVGProps<SVGSVGElement>, "children"> & {
  /** Start undrawn; the motion layer draws it on. */
  draw?: boolean;
  /** Accessible name. Omit for decorative doodles (the default). */
  title?: string;
};

type BaseProps = DoodleProps & { w: number; h: number; children: ReactNode };

function Doodle({ w, h, draw, title, className, children, ...rest }: BaseProps) {
  return (
    <svg
      viewBox={`0 0 ${w} ${h}`}
      width={w}
      height={h}
      className={className ? `doodle ${className}` : "doodle"}
      data-draw={draw ? "" : undefined}
      role={title ? "img" : undefined}
      aria-label={title}
      aria-hidden={title ? undefined : true}
      focusable="false"
      {...rest}
    >
      {children}
    </svg>
  );
}

/** Stroke normalised to length 1 so every doodle draws on with the same maths. */
const S = (props: SVGProps<SVGPathElement>) => <path pathLength={1} {...props} />;

// ---------------------------------------------------------------- brand character

/** The earlier dachshund mark. Superseded by Terrier; kept for reference. */
export function Dachshund(props: DoodleProps) {
  return (
    <Doodle w={240} h={112} {...props}>
      <S d="M10 34 C13 47 24 57 40 59 C74 52 124 52 158 55 C168 55 174 47 178 39 C182 29 195 25 207 30 C217 34 228 41 235 45 C240 48 239 54 233 54 C223 56 211 58 202 58 C196 63 192 71 190 79 L189 99 C189 105 177 105 177 99 L176 85 C142 91 98 91 70 85 L69 99 C69 105 57 105 57 99 L55 83 C44 79 37 70 40 59" />
      <S d="M187 34 C180 44 180 59 190 63 C198 59 200 45 195 33" />
      <S d="M160 88 L160 99 C160 104 150 104 150 99 L150 90" />
      <S d="M88 89 L88 99 C88 104 98 104 98 99 L98 90" />
      <circle data-fill cx="211" cy="39" r="2.2" />
      <ellipse data-fill cx="236" cy="48.5" rx="3.4" ry="2.8" />
    </Doodle>
  );
}

/** Snug, the SNUGDOG mascot: a bearded terrier with upright ears and a collar. Line version of the 3D character. */
export function Terrier(props: DoodleProps) {
  return (
    <Doodle w={156} h={108} {...props}>
      <S d="M30 50 C27 38 25 28 27 16 C32 26 35 36 38 47 C60 43 82 43 98 46 C100 36 101 26 103 18 L108 4 L113 18 L116 17 L122 5 L125 20 C130 22 134 26 134 31 L146 33 C151 34 151 40 146 41 L140 42 C141 50 138 58 130 60 C124 61 118 56 116 50 C114 58 112 64 112 70 L112 98 C112 103 100 103 100 98 L100 82 C84 86 62 86 50 82 L50 98 C50 103 38 103 38 98 L36 78 C30 70 28 58 30 50" />
      <S d="M121 27 C125 22 131 23 134 28" />
      <S d="M101 40 C105 45 111 47 116 46" />
      <S d="M122 46 L123 53 M128 47 L128 55 M134 46 L133 53" />
      <circle data-fill cx="128" cy="31" r="2.2" />
      <ellipse data-fill cx="147" cy="37" rx="3.4" ry="3" />
    </Doodle>
  );
}

/** A happy face: the "happier humans" in the tagline. */
export function Smile(props: DoodleProps) {
  return (
    <Doodle w={48} h={48} {...props}>
      <S d="M24 4 C36 3 45 12 44 24 C43 36 35 45 23 44 C11 43 3 35 4 23 C5 12 13 5 24 4 Z" />
      <S d="M14 27 C17 35 31 36 35 27" />
      <S d="M17 17 L17 21" />
      <S d="M31 17 L31 21" />
    </Doodle>
  );
}

export function Heart(props: DoodleProps) {
  return (
    <Doodle w={44} h={40} {...props}>
      <S d="M22 36 C10 27 4 20 5 13 C6 6 15 4 22 12 C29 4 38 6 39 13 C40 20 34 27 22 36 Z" />
    </Doodle>
  );
}

/** Short rays, for "fresh", "hot" or "look here". */
export function Burst(props: DoodleProps) {
  return (
    <Doodle w={60} h={44} {...props}>
      <S d="M8 38 C10 32 12 27 15 22" />
      <S d="M22 30 C22 22 22 14 23 5" />
      <S d="M36 32 C39 25 43 18 48 11" />
      <S d="M46 39 C50 36 54 33 57 31" />
    </Doodle>
  );
}

export function Crown(props: DoodleProps) {
  return (
    <Doodle w={60} h={46} {...props}>
      <S d="M8 34 C7 26 6 18 5 11 C10 15 14 19 19 23 C22 17 26 11 30 5 C34 11 38 17 42 23 C46 19 50 15 55 11 C54 19 53 26 52 34 Z" />
      <S d="M9 41 C23 39 38 39 52 41" />
    </Doodle>
  );
}

export function Paw(props: DoodleProps) {
  return (
    <Doodle w={48} h={48} {...props}>
      <S d="M24 44 C14 45 9 37 14 31 C18 25 30 25 34 31 C39 37 34 45 24 44 Z" />
      <ellipse pathLength={1} cx="10" cy="21" rx="4" ry="5" transform="rotate(-20 10 21)" />
      <ellipse pathLength={1} cx="19" cy="11" rx="4" ry="5.2" transform="rotate(-8 19 11)" />
      <ellipse pathLength={1} cx="30" cy="11" rx="4" ry="5.2" transform="rotate(8 30 11)" />
      <ellipse pathLength={1} cx="39" cy="21" rx="4" ry="5" transform="rotate(20 39 21)" />
    </Doodle>
  );
}

// ---------------------------------------------------------------- food sketches

export function HotDogSketch(props: DoodleProps) {
  return (
    <Doodle w={124} h={62} {...props}>
      <S d="M11 36 C8 48 22 55 62 55 C102 55 116 48 113 36" />
      <S d="M9 31 C4 23 10 16 19 17 L105 17 C114 16 120 23 115 31 C112 37 106 38 101 37 L23 37 C18 38 12 37 9 31 Z" />
      <S d="M24 27 L34 22 L44 31 L54 22 L64 31 L74 22 L84 31 L94 23 L100 28" />
    </Doodle>
  );
}

export function Tomato(props: DoodleProps) {
  return (
    <Doodle w={48} h={48} {...props}>
      <S d="M24 5 C36 4 44 13 43 25 C42 37 34 44 23 43 C12 42 4 34 5 23 C6 12 13 6 24 5 Z" />
      <S d="M24 14 C19 14 15 18 15 23" />
      <S d="M24 24 L24 17 M24 24 L30 28 M24 24 L18 28" />
    </Doodle>
  );
}

export function OnionRing(props: DoodleProps) {
  return (
    <Doodle w={48} h={48} {...props}>
      <S d="M24 5 C36 5 43 13 43 24 C43 36 35 43 24 43 C12 43 5 35 5 24 C5 12 13 5 24 5 Z" />
      <S d="M24 13 C31 13 35 18 35 24 C35 31 30 35 24 35 C17 35 13 30 13 24 C13 17 18 13 24 13 Z" />
    </Doodle>
  );
}

export function Pickle(props: DoodleProps) {
  return (
    <Doodle w={56} h={40} {...props}>
      <S d="M8 30 C2 24 6 15 15 13 L40 7 C49 5 55 12 51 20 C49 24 45 26 41 27 L17 33 C13 34 10 33 8 30 Z" />
      <S d="M19 22 L19.5 22 M29 18 L29.5 18 M39 15 L39.5 15 M26 26 L26.5 26" />
    </Doodle>
  );
}

export function Chili(props: DoodleProps) {
  return (
    <Doodle w={52} h={48} {...props}>
      <S d="M12 14 C8 30 22 44 46 42 C34 37 25 28 22 13 C19 10 14 10 12 14 Z" />
      <S d="M17 11 C16 7 19 4 24 5" />
    </Doodle>
  );
}

// ---------------------------------------------------------------- marks

export function Star(props: DoodleProps) {
  return (
    <Doodle w={40} h={40} {...props}>
      <S d="M20 4 L24.4 15 L36 16 L27 23.6 L30 35 L20 28.6 L10 35 L13 23.6 L4 16 L15.6 15 Z" />
    </Doodle>
  );
}

export function Sparkle(props: DoodleProps) {
  return (
    <Doodle w={40} h={40} {...props}>
      <S d="M20 3 C21 13 27 19 37 20 C27 21 21 27 20 37 C19 27 13 21 3 20 C13 19 19 13 20 3 Z" />
    </Doodle>
  );
}

/** Three short ticks: steam, snap, "fresh". */
export function MotionMarks(props: DoodleProps) {
  return (
    <Doodle w={40} h={36} {...props}>
      <S d="M9 31 C7 25 6 19 6 12" />
      <S d="M20 28 C20 20 20 12 21 4" />
      <S d="M31 31 C33 25 34 19 34 12" />
    </Doodle>
  );
}

export function Squiggle(props: DoodleProps) {
  return (
    <Doodle w={160} h={14} {...props}>
      <S d="M3 8 C16 2 24 13 38 7 C52 1 60 13 74 7 C88 1 96 13 110 7 C124 1 132 13 146 7 L157 5" />
    </Doodle>
  );
}

/** Deckled edge of the paper wrapper. */
export function WrapperEdge(props: DoodleProps) {
  return (
    <Doodle w={160} h={16} {...props}>
      <S d="M2 12 L12 4 L22 12 L32 4 L42 12 L52 4 L62 12 L72 4 L82 12 L92 4 L102 12 L112 4 L122 12 L132 4 L142 12 L152 4 L158 9" />
    </Doodle>
  );
}

/** Hand-ruled hatch used on wrapper and packaging graphics. */
export function WrapperHatch(props: DoodleProps) {
  return (
    <Doodle w={64} h={48} {...props}>
      <S d="M4 14 L16 4" />
      <S d="M4 30 L32 5" />
      <S d="M5 45 L48 6" />
      <S d="M22 45 L60 11" />
      <S d="M40 45 L60 27" />
    </Doodle>
  );
}

// ---------------------------------------------------------------- arrows

export function ArrowCurve(props: DoodleProps) {
  return (
    <Doodle w={90} h={60} {...props}>
      <S d="M6 9 C32 4 64 16 78 47" />
      <S d="M63 42 L79 49 L83 32" />
    </Doodle>
  );
}

export function ArrowLoop(props: DoodleProps) {
  return (
    <Doodle w={100} h={60} {...props}>
      <S d="M6 42 C24 10 50 6 52 25 C53 38 37 40 38 27 C39 11 70 13 90 35" />
      <S d="M75 35 L91 37 L91 21" />
    </Doodle>
  );
}

export function ArrowStraight(props: DoodleProps) {
  return (
    <Doodle w={60} h={20} {...props}>
      <S d="M4 10 C20 8 38 12 54 10" />
      <S d="M46 4 L55 10 L47 16" />
    </Doodle>
  );
}

// ---------------------------------------------------------------- annotation

/** Handwritten callout. Compose with an arrow doodle as a sibling and position per layout. */
export function Annotation({ children, className, ...rest }: React.HTMLAttributes<HTMLSpanElement>) {
  return (
    <span className={className ? `hand ${className}` : "hand"} {...rest}>
      {children}
    </span>
  );
}

/** Registry used by the /doodles reference sheet. */
export const DOODLES = {
  Terrier,
  Smile,
  Heart,
  Burst,
  Dachshund,
  Crown,
  Paw,
  HotDogSketch,
  Tomato,
  OnionRing,
  Pickle,
  Chili,
  Star,
  Sparkle,
  MotionMarks,
  Squiggle,
  WrapperEdge,
  WrapperHatch,
  ArrowCurve,
  ArrowLoop,
  ArrowStraight,
} as const;
