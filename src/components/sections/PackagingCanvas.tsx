"use client";

import { useGLTF } from "@react-three/drei";
import { Canvas, useFrame } from "@react-three/fiber";
import { Suspense, useLayoutEffect, useRef } from "react";
import * as THREE from "three";
import { CanvasBoundary, DRACO, Studio, fittedFov } from "@/components/three/shared";
import { packagingMotion } from "@/lib/motion";

const MODEL = "/models/snugdog-packaging.glb";

/** Root nodes in the GLB (assets/3d/scripts/build_packaging.py), in the order the camera visits them. */
export const PACKS = ["Box", "Cup", "Bag"] as const;
// How far each pack is turned when it is the one in focus, so its print faces the viewer.
const REST_YAW = [0.5, 0.1, 0.42];

const SPACING = 6.4; // far enough apart that only the pack in focus is on screen at rest
const FOV = 26;
const MIN_ASPECT = 1.5;
// The camera looks to the left of the pack in focus, which leaves the pack on the right
// of the frame and the left free for the caption.
const LOOK_OFFSET = -1.15;
const damp = THREE.MathUtils.damp;

function Shelf({ onReady }: { onReady: () => void }) {
  const { scene } = useGLTF(MODEL, DRACO);
  const packs = useRef<THREE.Object3D[]>([]);
  const focus = useRef(0);

  useLayoutEffect(() => {
    packs.current = PACKS.flatMap((name, i) => {
      const node = scene.getObjectByName(name);
      if (!node) return [];
      node.position.set(i * SPACING, 0, 0);
      return [node];
    });
    scene.traverse((node) => {
      const mesh = node as THREE.Mesh;
      if (!mesh.isMesh) return;
      const map = (mesh.material as THREE.MeshStandardMaterial).map;
      if (map) map.anisotropy = 8;
    });
    onReady();
  }, [scene, onReady]);

  useFrame(({ camera, size, pointer }, delta) => {
    const dt = Math.min(delta, 0.05);
    // scroll says where to be; damping makes the camera glide there
    focus.current = damp(focus.current, packagingMotion.progress * (PACKS.length - 1), 3.2, dt);
    const f = focus.current;
    const x = f * SPACING;

    packs.current.forEach((pack, i) => {
      const away = f - i; // 0 when this pack is in focus
      pack.rotation.y = REST_YAW[i] - away * 0.9 + pointer.x * 0.08;
      pack.position.y = -Math.min(Math.abs(away), 1) * 0.12;
    });

    camera.position.set(x + LOOK_OFFSET + pointer.x * 0.25, 1.55 - pointer.y * 0.12, 7.2);
    camera.lookAt(x + LOOK_OFFSET, 0.82, 0);

    const lens = camera as THREE.PerspectiveCamera;
    const fov = fittedFov(FOV, size.width / size.height, MIN_ASPECT);
    if (Math.abs(lens.fov - fov) > 0.01) {
      lens.fov = fov;
      lens.updateProjectionMatrix();
    }
  });

  return <primitive object={scene} />;
}

type Props = {
  /** pause rendering while the section is off screen */
  active: boolean;
  onReady: () => void;
  /** WebGL unavailable or the model failed: the caller falls back to the flat artwork */
  onError: () => void;
};

export default function PackagingCanvas({ active, onReady, onError }: Props) {
  return (
    <CanvasBoundary onError={onError}>
      <Canvas
        frameloop={active ? "always" : "never"}
        dpr={[1, 1.75]}
        camera={{ position: [LOOK_OFFSET, 1.55, 7.2], fov: FOV, near: 1, far: 40 }}
        gl={{ antialias: true, alpha: true, powerPreference: "high-performance" }}
        onCreated={({ gl }) => {
          gl.toneMapping = THREE.NeutralToneMapping;
        }}
        aria-hidden="true"
      >
        <Suspense fallback={null}>
          {/* no shadow maps: nothing to catch them, and they darken the label panels */}
          <Studio scale={2} shadows={false} />
          {/* a cool rim from behind lifts the white stock off the black ground */}
          <directionalLight position={[6, 3, -6]} intensity={1.4} color="#dfe6ff" />
          <Shelf onReady={onReady} />
        </Suspense>
      </Canvas>
    </CanvasBoundary>
  );
}
