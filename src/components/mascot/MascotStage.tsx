"use client";

import dynamic from "next/dynamic";
import Image from "next/image";
import { useCallback, useEffect, useRef, useState } from "react";
import { MEDIA } from "@/lib/motion";
import { useMediaQuery } from "@/lib/useMediaQuery";
import { MASCOT_POSES, mascotStill, type MascotPose } from "./poses";
import s from "./MascotStage.module.css";

// three.js and the model only load where the realtime mascot is actually shown
const MascotCanvas = dynamic(() => import("./MascotCanvas"), { ssr: false });

type Props = {
  pose: MascotPose;
  /**
   * Show the rigged realtime model instead of the rendered still.
   * Off by default: the mascot's coat is strand fur, which only exists in the offline
   * renders. The realtime model is the same dog without it, so use it only where the
   * motion matters more than the finish.
   */
  realtime?: boolean;
  className?: string;
};

/**
 * The mascot, wherever it appears on the site.
 *   default          rendered still (full fur), cross-faded between poses
 *   realtime         desktop: detailed model, tablet: light model
 *   phone, reduced motion, no WebGL: always the rendered still
 * The still is always painted first, so there is never an empty stage while 3D loads.
 */
export function MascotStage({ pose, realtime = false, className }: Props) {
  const root = useRef<HTMLDivElement>(null);
  const motionOk = useMediaQuery(MEDIA.motionOk);
  const roomy = useMediaQuery(MEDIA.tabletUp);
  const desktop = useMediaQuery(MEDIA.desktop);
  const [failed, setFailed] = useState(false);
  const [ready, setReady] = useState(false);
  const [inView, setInView] = useState(false);
  const use3d = realtime && motionOk && roomy && !failed;
  const live = use3d && ready;

  const onReady = useCallback(() => setReady(true), []);
  const onError = useCallback(() => setFailed(true), []);

  useEffect(() => {
    const el = root.current;
    if (!el) return;
    const observer = new IntersectionObserver(([entry]) => setInView(entry.isIntersecting), { rootMargin: "200px" });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <div ref={root} className={className ? `${s.stage} ${className}` : s.stage} data-mode={live ? "3d" : "still"}>
      {/* every pose is stacked; only the current one is opaque, so pose changes cross-fade */}
      {MASCOT_POSES.map((item) => (
        <Image
          key={item.id}
          className={s.still}
          data-current={item.id === pose || undefined}
          src={mascotStill(item.id)}
          alt={item.id === pose && !live ? item.alt : ""}
          aria-hidden={item.id !== pose || live || undefined}
          width={1800}
          height={1300}
          sizes="(max-width: 600px) 100vw, (max-width: 1100px) 90vw, 60vw"
          loading={item.id === pose ? "eager" : "lazy"}
        />
      ))}
      {use3d && (
        <div className={s.canvas}>
          <MascotCanvas pose={pose} quality={desktop ? "hero" : "light"} active={inView} onReady={onReady} onError={onError} />
        </div>
      )}
    </div>
  );
}
