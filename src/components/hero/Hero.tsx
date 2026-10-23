"use client";

import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Image from "next/image";
import { useEffect, useRef } from "react";
import { Annotation, ArrowCurve, ArrowLoop } from "@/components/doodles";
import { Button } from "@/components/ui/Button";
import { EASE, MEDIA } from "@/lib/motion";
import s from "./Hero.module.css";

// The hero scene is two cut-outs from the client's own pictures (assets/photos): the real
// hot dog, and Snug. Snug stands below the hot dog with his eyes on it; that glance is the
// link between them. Depth comes from moving the two layers by different amounts.
export function Hero() {
  const root = useRef<HTMLElement>(null);

  useEffect(() => {
    gsap.registerPlugin(ScrollTrigger);
    const mm = gsap.matchMedia(root);

    mm.add(MEDIA.motionOk, () => {
      const strokes = ".doodle[data-draw] > :not([data-fill])";
      const fills = ".doodle[data-draw] > [data-fill]";

      // ---- load: type settles, food arrives, Snug notices it, notes draw, actions appear
      gsap
        .timeline({ defaults: { ease: EASE.settle } })
        .fromTo("[data-line]", { yPercent: 108 }, { yPercent: 0, duration: 1.1, stagger: 0.09 }, 0.1)
        .fromTo(`.${s.food}`, { autoAlpha: 0, xPercent: 26, rotate: 10 }, { autoAlpha: 1, xPercent: 0, rotate: 0, duration: 1.6 }, 0.25)
        .fromTo(`.${s.lede}, .${s.actions}`, { autoAlpha: 0, y: 18 }, { autoAlpha: 1, y: 0, duration: 0.9, stagger: 0.08 }, 0.65)
        .fromTo(`.${s.snug}`, { autoAlpha: 0, yPercent: 14 }, { autoAlpha: 1, yPercent: 0, duration: 1.1 }, 0.85)
        .fromTo(`.${s.note}, .${s.foot}`, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.5, ease: EASE.out, stagger: 0.08 }, 1.3)
        .to(strokes, { strokeDashoffset: 0, duration: 0.8, ease: EASE.draw, stagger: 0.07 }, 1.35)
        .to(fills, { opacity: 1, duration: 0.3, ease: EASE.out }, ">-0.2");

      // ---- scroll: headline eases back, the food lifts away, Snug stays put a moment longer
      gsap
        .timeline({
          defaults: { ease: "none" },
          scrollTrigger: { trigger: root.current, start: "top top", end: "bottom top", scrub: 0.6 },
        })
        .to(`.${s.title}`, { yPercent: -8, scale: 0.93 }, 0)
        .to(`.${s.foodDrift}`, { yPercent: -16, rotate: -7, scale: 1.08 }, 0)
        .to(`.${s.snugDrift}`, { yPercent: 6 }, 0)
        .to(`.${s.note}`, { opacity: 0, duration: 0.3 }, 0)
        .to(`.${s.foot}`, { opacity: 0, duration: 0.25 }, 0);

      // ---- pointer: the food is nearer the viewer than Snug, so it moves further
      if (!window.matchMedia("(pointer: fine)").matches) return;
      const move = (target: string, amount: number) => ({
        x: gsap.quickTo(target, "x", { duration: 0.9, ease: "power3" }),
        y: gsap.quickTo(target, "y", { duration: 0.9, ease: "power3" }),
        amount,
      });
      const layers = [move(`.${s.foodShift}`, -26), move(`.${s.snugShift}`, -10)];
      const onMove = (e: PointerEvent) => {
        const px = (e.clientX / window.innerWidth) * 2 - 1;
        const py = (e.clientY / window.innerHeight) * 2 - 1;
        for (const layer of layers) {
          layer.x(px * layer.amount);
          layer.y(py * layer.amount * 0.6);
        }
      };
      window.addEventListener("pointermove", onMove, { passive: true });
      return () => window.removeEventListener("pointermove", onMove);
    });

    return () => mm.revert();
  }, []);

  return (
    <section ref={root} className={s.hero} aria-labelledby="hero-title">
      <div className={s.copy}>
        <h1 id="hero-title" className={`display ${s.title}`}>
          <span className={s.line}>
            <span data-line>Hot dogs </span>
          </span>
          <span className={s.line}>
            <span data-line>for happier </span>
          </span>
          <span className={s.line}>
            <span data-line>humans.</span>
          </span>
        </h1>

        <p className={s.lede} data-reveal>
          Snappy franks, toasted buns, proper toppings. Made slow, served fast, eaten happily.
        </p>

        <div className={s.actions} data-reveal>
          <Button href="#menu">Order now</Button>
          <Button href="#story" variant="text" icon="play">
            Watch our story
          </Button>
        </div>
      </div>

      <div className={s.scene}>
        <div className={s.food} data-reveal>
          <div className={s.foodShift}>
            <div className={s.foodDrift}>
              <Image
                src="/images/hero-hotdog.webp"
                alt="A frank in a toasted brioche bun, loaded with roasted red peppers, leaves and three spoonfuls of cream cheese with black sesame"
                width={588}
                height={579}
                sizes="(max-width: 1100px) 70vw, 36vw"
                priority
              />
            </div>
          </div>
        </div>

        <div className={s.snug} data-reveal>
          <div className={s.snugShift}>
            <div className={s.snugDrift}>
              <Image
                src="/images/hero-snug.webp"
                alt="Snug, the SNUGDOG terrier, a bone in his mouth and his eyes on the hot dog"
                width={808}
                height={779}
                sizes="(max-width: 1100px) 46vw, 24vw"
                priority
              />
            </div>
          </div>
        </div>

        <div className={`${s.note} ${s.noteFood}`} data-reveal aria-hidden="true">
          <Annotation>toasted, loaded, real</Annotation>
          <ArrowCurve draw />
        </div>
        <div className={`${s.note} ${s.noteSnug}`} data-reveal aria-hidden="true">
          <ArrowLoop draw />
          <Annotation>Snug would swap the bone</Annotation>
        </div>
      </div>

      <div className={s.foot} data-reveal>
        <a href="#menu" className={`label ${s.scroll}`}>
          Scroll
          <span aria-hidden="true" className={s.scrollLine} />
        </a>
        <p className={`label ${s.caption}`}>
          <span>N° 00</span> The Signature
        </p>
      </div>
    </section>
  );
}
