"use client";

// Pieces every SNUGDOG WebGL scene shares: studio lighting, the soft ground shadow,
// lens fitting and the error boundary that lets callers fall back to a still.

import { Environment, Lightformer } from "@react-three/drei";
import { Component, useMemo, type ReactNode } from "react";
import * as THREE from "three";

/** Draco decoder is self-hosted in /public/draco. */
export const DRACO = "/draco/";

type StudioProps = {
  /** Size of the subject relative to the hot dog (about 2 units long). */
  scale?: number;
  /** Half extents [x, y] of the key light's shadow frustum, in world units. */
  shadowBounds?: [number, number];
  /** Whether the key light casts shadows (the canvas must also enable them). */
  shadows?: boolean;
};

/** Soft daylight studio built from light cards, so no HDR download is needed. */
export function Studio({ scale = 1, shadowBounds = [2.4, 1.6], shadows = true }: StudioProps) {
  const [bx, by] = shadowBounds;
  return (
    <>
      <ambientLight intensity={0.35} />
      <directionalLight
        position={[-2.5 * scale, 4 * scale, 2 * scale]}
        intensity={2.1}
        color="#fff4e6"
        castShadow={shadows}
        shadow-mapSize={[2048, 2048]}
        shadow-bias={-0.0004}
        shadow-normalBias={0.015 * scale}
      >
        <orthographicCamera attach="shadow-camera" args={[-bx, bx, by, -by, 1 * scale, 10 * scale]} />
      </directionalLight>
      <Environment resolution={256} frames={1}>
        <color attach="background" args={["#8f8b84"]} />
        <Lightformer form="rect" intensity={5} color="#fff6ea" position={[-3, 4, 2]} scale={[5, 5, 1]} target={[0, 0, 0]} />
        <Lightformer form="rect" intensity={1.6} position={[4, 1.5, 3]} scale={[5, 4, 1]} target={[0, 0, 0]} />
        <Lightformer form="rect" intensity={3} position={[1.5, 2.5, -4]} scale={[6, 2, 1]} target={[0, 0, 0]} />
      </Environment>
    </>
  );
}

type GroundShadowProps = {
  position: [number, number, number];
  /** [length, depth] of the shadow on the ground */
  size: [number, number];
  /** 0..1 darkness at the centre */
  strength?: number;
};

/** Soft contact shadow as a single gradient quad: it travels with its subject and costs no extra render pass. */
export function GroundShadow({ position, size, strength = 0.42 }: GroundShadowProps) {
  const texture = useMemo(() => {
    const px = 256;
    const canvas = document.createElement("canvas");
    canvas.width = canvas.height = px;
    const ctx = canvas.getContext("2d")!;
    const gradient = ctx.createRadialGradient(px / 2, px / 2, 0, px / 2, px / 2, px / 2);
    gradient.addColorStop(0, `rgba(20, 14, 8, ${strength})`);
    gradient.addColorStop(0.45, `rgba(20, 14, 8, ${strength * 0.43})`);
    gradient.addColorStop(1, "rgba(20, 14, 8, 0)");
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, px, px);
    return new THREE.CanvasTexture(canvas);
  }, [strength]);

  return (
    <mesh position={position} rotation-x={-Math.PI / 2} renderOrder={-1}>
      <planeGeometry args={size} />
      <meshBasicMaterial map={texture} transparent depthWrite={false} toneMapped={false} />
    </mesh>
  );
}

/** Vertical field of view that keeps the subject fitted to the canvas width on tall canvases. */
export function fittedFov(fov: number, aspect: number, minAspect: number) {
  if (aspect >= minAspect) return fov;
  const half = Math.tan(THREE.MathUtils.degToRad(fov / 2));
  return THREE.MathUtils.radToDeg(2 * Math.atan((half * minAspect) / aspect));
}

/** If WebGL is unavailable or a model fails, render nothing and tell the caller to show the still. */
export class CanvasBoundary extends Component<{ onError: () => void; children: ReactNode }, { failed: boolean }> {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch() {
    this.props.onError();
  }

  render() {
    return this.state.failed ? null : this.props.children;
  }
}
