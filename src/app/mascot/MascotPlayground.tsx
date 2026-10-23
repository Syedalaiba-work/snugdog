"use client";

import { useState } from "react";
import { MascotStage } from "@/components/mascot/MascotStage";
import { MASCOT_POSES, type MascotPose } from "@/components/mascot/poses";
import s from "./page.module.css";

export function MascotPlayground() {
  const [pose, setPose] = useState<MascotPose>("01_HeroStanding");
  const [realtime, setRealtime] = useState(false);

  return (
    <section className={s.playground} aria-label="Mascot poses">
      <div className={s.modes} role="group" aria-label="Display mode">
        <button type="button" className={`label ${s.mode}`} aria-pressed={!realtime} onClick={() => setRealtime(false)}>
          Rendered (full fur)
        </button>
        <button type="button" className={`label ${s.mode}`} aria-pressed={realtime} onClick={() => setRealtime(true)}>
          Realtime 3D (no fur)
        </button>
      </div>
      <MascotStage pose={pose} realtime={realtime} className={s.stage} />
      <div className={s.poses} role="group" aria-label="Choose a pose">
        {MASCOT_POSES.map((item, i) => (
          <button
            key={item.id}
            type="button"
            className={`label ${s.pose}`}
            aria-pressed={pose === item.id}
            onClick={() => setPose(item.id)}
          >
            <span>0{i + 1}</span>
            {item.label}
          </button>
        ))}
      </div>
    </section>
  );
}
