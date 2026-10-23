"use client";

import { useAnimations, useGLTF } from "@react-three/drei";
import { Canvas, useFrame } from "@react-three/fiber";
import { Suspense, useEffect, useLayoutEffect, useRef } from "react";
import * as THREE from "three";
import { CanvasBoundary, DRACO, GroundShadow, Studio, fittedFov } from "@/components/three/shared";
import { MASCOT_MODEL, MASCOT_POSES, type MascotPose } from "./poses";

// Camera matched to the Blender stills (assets/3d/mascot/scripts/build_mascot.py).
const TARGET = new THREE.Vector3(0.45, 2.05, 0);
// Blender (x, y, z) is glTF (x, z, -y): the stills camera at +Y sits at -Z here.
const CAMERA = new THREE.Vector3(0.85, 0.18, -1.0).normalize().multiplyScalar(19).add(TARGET);
const FOV = 17.5;
const MIN_ASPECT = 1.3;
const CROSSFADE = 0.7;
const BLINK = THREE.MathUtils.degToRad(50);
const UP = new THREE.Vector3(0, 1, 0);
const LID_AXIS = new THREE.Vector3(0, 0, 1);
const scratch = new THREE.Quaternion();

const damp = THREE.MathUtils.damp;

type ModelProps = {
  url: string;
  pose: MascotPose;
  /** subtle life: blink, tail, a glance toward the pointer. Off = a still statue. */
  alive: boolean;
  onReady?: () => void;
};

/** The rigged mascot (without its strand fur). Drop it inside any R3F <Canvas>; it brings no lights or camera. */
export function MascotModel({ url, pose, alive, onReady }: ModelProps) {
  const { scene, animations } = useGLTF(url, DRACO);
  const group = useRef<THREE.Group>(null);
  const { actions } = useAnimations(animations, group);
  const parts = useRef<{ lids: { node: THREE.Object3D; rest: THREE.Quaternion }[]; head?: THREE.Object3D; tail: THREE.Object3D[] }>({ lids: [], tail: [] });
  const life = useRef({ nextBlink: 2.5, blink: 0, glance: 0 });
  const current = useRef<THREE.AnimationAction | null>(null);

  useLayoutEffect(() => {
    scene.traverse((node) => {
      const mesh = node as THREE.Mesh;
      if (!mesh.isMesh) return;
      mesh.castShadow = mesh.receiveShadow = true;
      mesh.frustumCulled = false; // skinned bounds do not follow the pose
      const material = mesh.material as THREE.MeshStandardMaterial;
      for (const map of [material.map, material.normalMap, material.roughnessMap]) {
        if (map) map.anisotropy = 8;
      }
    });
    parts.current = {
      lids: ["Lid_U_L", "Lid_U_R"].flatMap((name) => {
        const node = scene.getObjectByName(name);
        return node ? [{ node, rest: node.quaternion.clone() }] : [];
      }),
      head: scene.getObjectByName("Head"),
      tail: ["Tail", "Tail_2", "Tail_3"].flatMap((name) => scene.getObjectByName(name) ?? []),
    };
    onReady?.();
  }, [scene, onReady]);

  // Poses are single-frame clips; changing pose is a cross-fade between them.
  useEffect(() => {
    const next = actions[`Pose_${pose}`];
    if (!next) return;
    next.reset().play();
    if (current.current && current.current !== next) {
      next.crossFadeFrom(current.current, alive ? CROSSFADE : 0, false);
    }
    current.current = next;
  }, [actions, pose, alive]);

  const yaw = MASCOT_POSES.find((p) => p.id === pose)?.yaw ?? 0;

  useFrame(({ clock, pointer }, delta) => {
    const dt = Math.min(delta, 0.05);
    if (group.current) {
      group.current.rotation.y = alive ? damp(group.current.rotation.y, yaw, 3.5, dt) : yaw;
    }
    if (!alive) return;
    const t = clock.elapsedTime;
    const state = life.current;
    const { lids, head, tail } = parts.current;

    // blink: quick close, slightly slower open
    if (t > state.nextBlink) {
      state.blink = 1;
      state.nextBlink = t + 2.8 + Math.random() * 3.4;
    }
    state.blink = Math.max(0, state.blink - dt * 6.5);
    const closed = Math.sin(Math.min(1, state.blink) * Math.PI);
    for (const { node, rest } of lids) {
      node.quaternion.copy(rest).multiply(scratch.setFromAxisAngle(LID_AXIS, -BLINK * closed));
    }

    // these layer on top of the pose the mixer wrote this frame
    state.glance = damp(state.glance, pointer.x * 0.16, 2.5, dt);
    head?.rotateOnWorldAxis(UP, state.glance);
    tail.forEach((bone, i) => bone.rotateOnWorldAxis(UP, Math.sin(t * 2.4 - i * 0.7) * 0.05 * (i + 1)));
  });

  return (
    <group ref={group}>
      <primitive object={scene} />
      <GroundShadow position={[0, 0.01, 0]} size={[5.2, 3.4]} strength={0.36} />
    </group>
  );
}

function Lens() {
  useFrame(({ camera, size }) => {
    const lens = camera as THREE.PerspectiveCamera;
    const fov = fittedFov(FOV, size.width / size.height, MIN_ASPECT);
    if (Math.abs(lens.fov - fov) > 0.01) {
      lens.fov = fov;
      lens.updateProjectionMatrix();
    }
    camera.lookAt(TARGET);
  });
  return null;
}

type Props = {
  pose: MascotPose;
  /** "hero" loads the detailed model, "light" the optimised one */
  quality?: keyof typeof MASCOT_MODEL;
  alive?: boolean;
  /** pause rendering while off screen */
  active?: boolean;
  onReady?: () => void;
  /** WebGL unavailable or the model failed: the caller falls back to the still */
  onError: () => void;
};

/** Self-contained mascot stage: studio lighting, fitted lens, the rigged model. */
export default function MascotCanvas({ pose, quality = "light", alive = true, active = true, onReady, onError }: Props) {
  return (
    <CanvasBoundary onError={onError}>
      <Canvas
        shadows
        frameloop={active ? "always" : "never"}
        dpr={[1, quality === "hero" ? 1.75 : 1.5]}
        camera={{ position: CAMERA.toArray(), fov: FOV, near: 1, far: 60 }}
        gl={{ antialias: true, alpha: true, powerPreference: "high-performance" }}
        onCreated={({ gl }) => {
          gl.toneMapping = THREE.NeutralToneMapping;
        }}
        aria-hidden="true"
      >
        <Suspense fallback={null}>
          <Studio scale={3} shadowBounds={[6, 5]} />
          <Lens />
          <MascotModel url={MASCOT_MODEL[quality]} pose={pose} alive={alive} onReady={onReady} />
        </Suspense>
      </Canvas>
    </CanvasBoundary>
  );
}
