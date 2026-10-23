"use client";

import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import dynamic from "next/dynamic";
import { useCallback, useEffect, useRef, useState } from "react";
import { RiseLines } from "@/components/motion/ScrollReveals";
import { MEDIA, packagingMotion } from "@/lib/motion";
import { useMediaQuery } from "@/lib/useMediaQuery";
import { PackagingFlats } from "./PackagingFlats";
import s from "./Packaging.module.css";

// three.js and the model load only where the live scene is shown
const PackagingCanvas = dynamic(() => import("./PackagingCanvas"), { ssr: false });

const CAPTIONS = [
  { name: "The box", note: "Holds one dog, snug. Lift-off lid, nothing to tear." },
  { name: "The cup", note: "Cold drinks, loud lid. The straw is the only black thing on it." },
  { name: "The bag", note: "For when one is not enough. Folds flat, stands up on its own." },
];

/**
 * Packaging.
 *   desktop, motion allowed   live 3D: the section pins and scroll moves the camera along the shelf
 *   everything else           flat artwork (phones, tablets, reduced motion, no WebGL)
 */
export function Packaging() {
  const wants3d = useMediaQuery(MEDIA.full3d);
  const [failed, setFailed] = useState(false);
  const onError = useCallback(() => setFailed(true), []);
  return wants3d && !failed ? <PackagingLive onError={onError} /> : <PackagingFlats />;
}

function PackagingLive({ onError }: { onError: () => void }) {
  const root = useRef<HTMLElement>(null);
  const bar = useRef<HTMLSpanElement>(null);
  const [active, setActive] = useState(0);
  const [ready, setReady] = useState(false);
  const [inView, setInView] = useState(false);
  const onReady = useCallback(() => setReady(true), []);

  useEffect(() => {
    gsap.registerPlugin(ScrollTrigger);
    const ctx = gsap.context(() => {
      ScrollTrigger.create({
        trigger: root.current,
        start: "top top",
        end: "+=240%",
        pin: true,
        scrub: true,
        onUpdate: (self) => {
          packagingMotion.progress = self.progress;
          setActive(Math.min(CAPTIONS.length - 1, Math.round(self.progress * (CAPTIONS.length - 1))));
          if (bar.current) bar.current.style.transform = `scaleX(${self.progress})`;
        },
      });
    }, root);
    // Render only while the section is on screen. An observer (not a second trigger) is
    // used because the element stays visible for the whole pinned distance.
    const observer = new IntersectionObserver(([entry]) => setInView(entry.isIntersecting), { rootMargin: "200px" });
    if (root.current) observer.observe(root.current);
    // this section changes the page height, so later triggers must re-measure
    ScrollTrigger.refresh();
    return () => {
      observer.disconnect();
      ctx.revert();
      packagingMotion.progress = 0;
      ScrollTrigger.refresh();
    };
  }, []);

  const caption = CAPTIONS[active];

  return (
    <section ref={root} id="packaging" className={s.packaging} aria-labelledby="packaging-title">
      <div className={s.canvas} data-ready={ready || undefined}>
        <PackagingCanvas active={inView} onReady={onReady} onError={onError} />
      </div>

      <header className={s.head}>
        <p className={`label ${s.kicker}`} data-rise>
          04 / Packaging
        </p>
        <RiseLines id="packaging-title" className={`display ${s.title}`} lines={["White box.", "Black line.", "One good dog."]} />
      </header>

      <div className={s.caption} key={active}>
        <span className="label">0{active + 1}</span>
        <h3 className={`display ${s.name}`}>{caption.name}</h3>
        <p>{caption.note}</p>
      </div>

      <div className={s.progress} aria-hidden="true">
        <span className="label">
          0{active + 1} <span>/ 0{CAPTIONS.length}</span>
        </span>
        <span className={s.rail}>
          <span ref={bar} className={s.bar} />
        </span>
      </div>

      {/* the live scene is decorative; this carries the same content for assistive tech */}
      <ul className="sr-only">
        {CAPTIONS.map((item) => (
          <li key={item.name}>
            {item.name}: {item.note}
          </li>
        ))}
      </ul>
    </section>
  );
}
