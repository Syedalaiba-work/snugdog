"use client";

import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useEffect, useRef } from "react";
import { MEDIA } from "@/lib/motion";
import s from "./Marquee.module.css";

const WORDS = ["Snappy franks", "Toasted buns", "Proper toppings", "Happier humans"];

/** A band of oversized type that slides sideways as the page scrolls. It never moves on its own. */
export function Marquee() {
  const root = useRef<HTMLDivElement>(null);
  const track = useRef<HTMLDivElement>(null);

  useEffect(() => {
    gsap.registerPlugin(ScrollTrigger);
    const mm = gsap.matchMedia();
    mm.add(MEDIA.motionOk, () => {
      gsap.fromTo(
        track.current,
        { xPercent: 0 },
        { xPercent: -28, ease: "none", scrollTrigger: { trigger: root.current, start: "top bottom", end: "bottom top", scrub: 0.6 } },
      );
    });
    return () => mm.revert();
  }, []);

  return (
    <div ref={root} className={s.band} aria-hidden="true">
      <div ref={track} className={`display ${s.track}`}>
        {[0, 1, 2].map((copy) =>
          WORDS.map((word, i) => (
            <span key={`${copy}-${word}`} className={i % 2 ? s.outline : undefined}>
              {word}
            </span>
          )),
        )}
      </div>
    </div>
  );
}
