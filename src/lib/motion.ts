// Motion architecture: GSAP owns time (load timelines + scroll scrub) and writes into plain
// mutable objects; WebGL scenes read them every frame and add their own inertia.
// Keeping them outside React means no re-renders while animating.

/** Packaging scene: 0 -> 1 as the pinned section scrolls from the first pack to the last. */
export const packagingMotion = { progress: 0 };

export const EASE = {
  /** long, physical settle for things arriving */
  settle: "expo.out",
  /** general purpose reveal */
  out: "power3.out",
  /** drawing strokes and anything that should feel hand-paced */
  draw: "power2.inOut",
} as const;

/** Media queries shared by CSS and JS decisions about the full experience. */
export const MEDIA = {
  motionOk: "(prefers-reduced-motion: no-preference)",
  tabletUp: "(min-width: 601px)",
  desktop: "(min-width: 1101px)",
  full3d: "(min-width: 1101px) and (prefers-reduced-motion: no-preference)",
} as const;
