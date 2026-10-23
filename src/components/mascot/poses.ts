// The mascot's pose library. Ids match the clips baked into the GLB (assets/3d/mascot/scripts/rig.py)
// and the stills published to /public/images/mascot.

export const MASCOT_MODEL = {
  /** about 15k triangles, 1K maps: tablets and small canvases */
  light: "/models/SNUGDOG_Terrier.glb",
  /** about 60k triangles, 2K maps: desktop */
  hero: "/models/SNUGDOG_Terrier_hero.glb",
} as const;

// `yaw` turns the realtime model so its view matches the camera used for that pose's still.
export const MASCOT_POSES = [
  { id: "01_HeroStanding", label: "Hero standing", yaw: 0, alt: "The SNUGDOG terrier standing with one paw lifted, glancing sideways" },
  { id: "02_Curious", label: "Curious", yaw: 0.19, alt: "The SNUGDOG terrier tilting its head" },
  { id: "03_Walking", label: "Walking", yaw: -0.34, alt: "The SNUGDOG terrier mid-stride" },
  { id: "04_Sitting", label: "Sitting", yaw: 0, alt: "The SNUGDOG terrier sitting" },
  { id: "05_LookingBack", label: "Looking back", yaw: -1.32, alt: "The SNUGDOG terrier facing away and looking back over its shoulder" },
] as const;

export type MascotPose = (typeof MASCOT_POSES)[number]["id"];

export const mascotStill = (pose: MascotPose) => `/images/mascot/SNUGDOG_Terrier_pose_${pose}.webp`;
