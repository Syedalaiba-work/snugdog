"use client";

import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import { Annotation, ArrowLoop } from "@/components/doodles";
import { RiseLines } from "@/components/motion/ScrollReveals";
import { Button } from "@/components/ui/Button";
import s from "./Menu.module.css";

// Prices and recipes are placeholders until the real menu is supplied.
const ITEMS = [
  {
    id: "classic",
    name: "The Classic",
    price: "9",
    image: "/images/snugdog-hotdog-classic.webp",
    line: "The one that started it. Snappy all-beef frank, yellow mustard, crispy onions, chives.",
    details: ["All-beef frank", "Toasted sesame bun", "Yellow mustard"],
    note: "start here",
  },
  {
    id: "reuben",
    name: "The Reuben",
    price: "11",
    image: "/images/snugdog-hotdog-reuben.webp",
    line: "A deli sandwich in a bun. Sauerkraut, Russian dressing, chopped pickle.",
    details: ["All-beef frank", "House sauerkraut", "Russian dressing"],
    note: "the messy one",
  },
  {
    id: "garden",
    name: "The Garden",
    price: "10",
    image: "/images/snugdog-hotdog-garden.webp",
    line: "Light and bright. Herb yoghurt, tomato, cucumber, a handful of soft herbs.",
    details: ["Plant-based frank", "Herb yoghurt", "Tomato and cucumber"],
    note: "no meat, no compromise",
  },
  {
    id: "spicy",
    name: "Spicy Snug",
    price: "10",
    image: "/images/snugdog-hotdog-spicy.webp",
    line: "It bites back. Sriracha, crispy shallots, fresh jalapeno.",
    details: ["All-beef frank", "Sriracha", "Fresh jalapeno"],
    note: "you were warned",
  },
] as const;

export function Menu() {
  const root = useRef<HTMLElement>(null);
  const [active, setActive] = useState(0);

  // The food stage follows whichever item sits in the middle of the viewport.
  useEffect(() => {
    gsap.registerPlugin(ScrollTrigger);
    const ctx = gsap.context(() => {
      gsap.utils.toArray<HTMLElement>(`.${s.item}`).forEach((item, i) => {
        ScrollTrigger.create({
          trigger: item,
          start: "top 55%",
          end: "bottom 55%",
          onToggle: (self) => self.isActive && setActive(i),
        });
      });
    }, root);
    return () => ctx.revert();
  }, []);

  return (
    <section ref={root} id="menu" className={s.menu} aria-labelledby="menu-title">
      <header className={s.head}>
        <p className={`label ${s.kicker}`} data-rise>
          02 / The menu
        </p>
        <RiseLines id="menu-title" className={`display ${s.title}`} lines={["Four dogs.", "No filler."]} />
      </header>

      <div className={s.body}>
        <ol className={s.list}>
          {ITEMS.map((item, i) => (
            <li key={item.id} className={s.item} data-active={active === i || undefined}>
              <div className={s.inline} aria-hidden="true">
                <Image src={item.image} alt="" width={2000} height={1250} sizes="100vw" />
              </div>
              <div className={s.meta}>
                <span className="label">0{i + 1}</span>
                <span className={`label ${s.price}`}>
                  <span className="sr-only">Price: </span>${item.price}
                </span>
              </div>
              <h3 className={`display ${s.name}`}>{item.name}</h3>
              <p className={s.line}>{item.line}</p>
              <ul className={s.details}>
                {item.details.map((detail) => (
                  <li key={detail} className="label">
                    {detail}
                  </li>
                ))}
              </ul>
              <Button href="#locations" size="sm" className={s.order}>
                Order {item.name}
              </Button>
            </li>
          ))}
        </ol>

        <div className={s.stage} aria-hidden="true">
          <div className={s.plate}>
            {ITEMS.map((item, i) => (
              <Image
                key={item.id}
                className={s.shot}
                data-active={active === i || undefined}
                src={item.image}
                alt=""
                width={2000}
                height={1250}
                sizes="55vw"
              />
            ))}
          </div>
          <div className={s.note} key={active}>
            <ArrowLoop />
            <Annotation>{ITEMS[active].note}</Annotation>
          </div>
          <p className={`label ${s.count}`}>
            0{active + 1} <span>/ 0{ITEMS.length}</span>
          </p>
        </div>
      </div>
    </section>
  );
}
