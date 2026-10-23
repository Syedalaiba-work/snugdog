# SNUGDOG

Hot dogs for happier humans. A premium food brand site: editorial layout, monochrome
interface, food provides the colour, with a small number of high-quality 3D moments.

## Run

```bash
npm install
npm run dev          # http://localhost:3000 (this project has used: npm run dev -- --port 3210)
npm run build        # production build
npm run lint
```

`/doodles` is the internal reference sheet for the doodle system.
`/mascot` is the review page for the 3D mascot: all poses, rendered and realtime.

```bash
npm run typecheck
npm run 3d:hotdog    # rebuild the hot dog asset (needs Blender)
npm run 3d:mascot    # rebuild the mascot asset (needs Blender)
npm run 3d:labels    # print the packaging artwork to textures (needs Chrome)
npm run 3d:packaging # rebuild the packaging models (needs Blender)
```

## Stack

- Next.js (App Router), React, TypeScript, CSS Modules
- GSAP + ScrollTrigger for load and scroll choreography
- three.js via React Three Fiber + drei for the live packaging scene and the realtime mascot
- Blender (headless) for 3D assets: see [assets/3d/README.md](assets/3d/README.md)

## Where things live

| Path                                | What                                                        |
| ----------------------------------- | ----------------------------------------------------------- |
| `src/app/globals.css`               | Design tokens, type voices, doodle base, motion entry states |
| `src/lib/motion.ts`                 | Shared motion state, easings, media queries                 |
| `src/components/doodles/`           | Doodle system (SVG line art that can draw itself on)        |
| `src/components/ui/Button.tsx`      | CTA system: solid and text variants                         |
| `src/components/Navbar.tsx`         | Navigation                                                  |
| `src/components/hero/`              | Hero: photo cut-outs of the hot dog and Snug, with parallax |
| `src/components/sections/`          | Marquee, Menu, Story, Packaging, Locations, Footer          |
| `src/components/motion/`            | Scroll reveals (`data-rise`, `RiseLines`)                   |
| `src/components/mascot/`            | Rigged mascot: `MascotStage` (3D or still), canvas, poses   |
| `src/components/three/shared.tsx`   | Shared studio lights, ground shadow, lens fit, fallback     |
| `src/fonts/`                        | Self-hosted Archivo (variable) and Caveat, SIL OFL          |
| `assets/3d/`                        | Blender pipeline: scripts, sources, GLBs, renders           |
| `public/models`, `public/images`    | Published 3D outputs (written by the pipeline)              |
| `assets/photos/`                    | Source photos for the hero and the scripts that cut them out |
| `public/draco`                      | Self-hosted Draco decoder                                   |

## Design rules

- Interface is white, warm paper and black. No coloured UI. Food provides the colour.
- Display type (condensed 900) for headlines only; handwriting for annotations only.
- Whitespace beats doodles: one or two per composition.
- The hot dog is the product; Snug the terrier is the mascot. They share the hero
  (Snug eyes the hot dog), but the dog never touches or eats food.
- Motion is physical and controlled. The food never bounces or spins.

## How motion works

GSAP owns time: load timelines, scroll scrub and pointer parallax. WebGL scenes read
plain numbers from `src/lib/motion.ts` (for example `packagingMotion`) each frame and
add damping, so nothing snaps and React never re-renders during animation.

- Hero: two photo layers (the hot dog and Snug) that move by different amounts with
  the pointer and on scroll, plus a slow idle hover and breathing loop.
- Desktop (1101px and up, motion allowed): live 3D packaging scene.
- Tablet and mobile: recomposed stacked layouts; packaging shows flat artwork.
- `prefers-reduced-motion`: no choreography or idle loops; everything in its final state.
- No WebGL or a failed model load falls back to stills automatically.

## Page structure

Hero, marquee, menu, story (with the mascot), packaging, locations, footer.

- **Menu:** the list scrolls; a sticky food stage swaps to whichever dog is in view.
- **Story:** the mascot is pinned and changes pose as each belief scrolls past.
- **Packaging:** on desktop the section pins and scroll moves a live 3D camera along a
  shelf of box, cup and bag. Tablet, mobile, reduced motion and no-WebGL get flat
  artwork of the same packs instead.
- Anything marked `data-rise` fades up on entry; `RiseLines` headlines rise through masks.

## Status

Built: the full one-page site, the hero from photo cut-outs, the hot dog asset with
four menu variants, the doodle system, the motion architecture, the 3D pipeline,
the live packaging scene, and the terrier mascot.

Placeholder content to replace before launch: menu prices and recipes
(`sections/Menu.tsx`), shop names, addresses and hours (`sections/Locations.tsx`),
and the "Watch our story" and "Order" links, which only scroll within the page.

Not built yet: real ordering and a story video. There are no automated tests yet;
quality checks are `npm run lint`, `npm run typecheck` and `npm run build`.
