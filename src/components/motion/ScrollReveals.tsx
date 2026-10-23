"use client";

import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useEffect } from "react";
import { EASE, MEDIA } from "@/lib/motion";

/**
 * Page-wide scroll reveals, driven by markup:
 *   data-rise           the element fades up as it enters
 *   data-lines          each `.rise-line > span` inside rises through its mask, staggered
 *   data-draw-on-view   doodles inside draw themselves when they enter
 * Initial states are set here in JS (not CSS), so without scripts everything is simply visible.
 */
export function ScrollReveals() {
  useEffect(() => {
    gsap.registerPlugin(ScrollTrigger);
    const mm = gsap.matchMedia();
    mm.add(MEDIA.motionOk, () => {
      gsap.set("[data-rise]", { autoAlpha: 0, y: 36 });
      ScrollTrigger.batch("[data-rise]", {
        start: "top 88%",
        once: true,
        onEnter: (batch) => gsap.to(batch, { autoAlpha: 1, y: 0, duration: 0.9, ease: EASE.out, stagger: 0.08 }),
      });

      gsap.utils.toArray<HTMLElement>("[data-lines]").forEach((block) => {
        const lines = block.querySelectorAll(".rise-line > span");
        gsap.set(lines, { yPercent: 108 });
        ScrollTrigger.create({
          trigger: block,
          start: "top 85%",
          once: true,
          onEnter: () => gsap.to(lines, { yPercent: 0, duration: 1.05, ease: EASE.settle, stagger: 0.09 }),
        });
      });

      gsap.utils.toArray<HTMLElement>("[data-draw-on-view]").forEach((block) => {
        const strokes = block.querySelectorAll(".doodle > :not([data-fill])");
        const fills = block.querySelectorAll(".doodle > [data-fill]");
        gsap.set(strokes, { strokeDasharray: "1 1", strokeDashoffset: 1.001 });
        gsap.set(fills, { opacity: 0 });
        ScrollTrigger.create({
          trigger: block,
          start: "top 80%",
          once: true,
          onEnter: () => {
            gsap.to(strokes, { strokeDashoffset: 0, duration: 0.9, ease: EASE.draw, stagger: 0.06 });
            gsap.to(fills, { opacity: 1, duration: 0.3, delay: 0.7 });
          },
        });
      });
    });
    return () => mm.revert();
  }, []);

  return null;
}

/** Headline whose lines rise through masks when scrolled into view. */
export function RiseLines({ lines, as: Tag = "h2", className, id }: { lines: string[]; as?: "h2" | "h3" | "p"; className?: string; id?: string }) {
  return (
    <Tag id={id} className={className} data-lines>
      {lines.map((line) => (
        <span key={line} className="rise-line">
          <span>{line} </span>
        </span>
      ))}
    </Tag>
  );
}
