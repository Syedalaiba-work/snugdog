import type { Metadata } from "next";
import Image from "next/image";
import { MASCOT_POSES, mascotStill } from "@/components/mascot/poses";
import { MascotPlayground } from "./MascotPlayground";
import s from "./page.module.css";

export const metadata: Metadata = {
  title: "SNUGDOG — Mascot",
  robots: { index: false },
};

// Review page for the 3D mascot (terrier, built from the client's reference): every pose,
// rendered and realtime. Not linked from the site navigation.
export default function MascotSheet() {
  return (
    <main id="main" className={s.sheet}>
      <header className={s.head}>
        <p className="label">SNUGDOG / Brand character</p>
        <h1 className="display">The mascot</h1>
        <p className={s.intro}>
          A charcoal terrier with a beard, heavy brows and a red collar. The hot dog is the product; the dog is the
          mascot. He may look at the food, but never touches it.
        </p>
      </header>

      <MascotPlayground />

      <section className={s.block} aria-labelledby="stills-title">
        <h2 id="stills-title" className={`label ${s.blockTitle}`}>
          Pose library, rendered
        </h2>
        <ul className={s.grid}>
          {MASCOT_POSES.map((pose, i) => (
            <li key={pose.id} className={s.cell}>
              <Image src={mascotStill(pose.id)} alt={pose.alt} width={1800} height={1300} sizes="(max-width: 600px) 100vw, 33vw" />
              <span className="label">
                0{i + 1} {pose.label}
              </span>
            </li>
          ))}
        </ul>
      </section>

      <section className={s.block} aria-labelledby="turntable-title">
        <h2 id="turntable-title" className={`label ${s.blockTitle}`}>
          Turntable
        </h2>
        <Image
          className={s.turntable}
          src="/images/mascot/SNUGDOG_Terrier_turntable.webp"
          alt="Eight views around the SNUGDOG terrier"
          width={2560}
          height={1280}
          sizes="100vw"
        />
      </section>
    </main>
  );
}
