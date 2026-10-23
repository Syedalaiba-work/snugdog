"use client";

import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useEffect, useRef, useState } from "react";
import { Annotation, ArrowCurve } from "@/components/doodles";
import { MascotStage } from "@/components/mascot/MascotStage";
import type { MascotPose } from "@/components/mascot/poses";
import { RiseLines } from "@/components/motion/ScrollReveals";
import s from "./Story.module.css";

// Each belief has its own mascot pose; scrolling from one to the next is the animation.
const BELIEFS: { title: string; body: string; pose: MascotPose }[] = [
  { title: "Real food.", body: "Franks made from cuts you could name. Buns baked this morning. Nothing we would not eat ourselves.", pose: "01_HeroStanding" },
  { title: "Good ingredients.", body: "Short lists, good sources. If it does not make the dog better, it does not go in.", pose: "02_Curious" },
  { title: "Bold flavour.", body: "Sharp mustard, proper heat, real crunch. Quiet food is for other people.", pose: "03_Walking" },
  { title: "A little more joy.", body: "It is a hot dog. It should make your day slightly better. That is the whole job.", pose: "04_Sitting" },
];

export function Story() {
  const root = useRef<HTMLElement>(null);
  const [active, setActive] = useState(0);

  useEffect(() => {
    gsap.registerPlugin(ScrollTrigger);
    const ctx = gsap.context(() => {
      gsap.utils.toArray<HTMLElement>(`.${s.belief}`).forEach((item, i) => {
        ScrollTrigger.create({
          trigger: item,
          start: "top 58%",
          end: "bottom 58%",
          onToggle: (self) => self.isActive && setActive(i),
        });
      });
    }, root);
    return () => ctx.revert();
  }, []);

  return (
    <section ref={root} id="story" className={s.story} aria-labelledby="story-title">
      <header className={s.head}>
        <p className={`label ${s.kicker}`} data-rise>
          03 / Why Snugdog
        </p>
        <RiseLines id="story-title" className={`display ${s.title}`} lines={["Made by people", "who really like", "hot dogs."]} />
      </header>

      <div className={s.body}>
        <div className={s.mascot}>
          {/* The mascot has this stage to itself: no food shares the scene. */}
          <MascotStage pose={BELIEFS[active].pose} />
          <div className={s.hello} data-draw-on-view aria-hidden="true">
            <Annotation>this is Snug</Annotation>
            <ArrowCurve />
          </div>
        </div>

        <ol className={s.beliefs}>
          {BELIEFS.map((belief, i) => (
            <li key={belief.title} className={s.belief} data-active={active === i || undefined}>
              <span className="label">0{i + 1}</span>
              <h3 className={`display ${s.beliefTitle}`}>{belief.title}</h3>
              <p className={s.beliefBody}>{belief.body}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
