# SNUGDOG dachshund: mascot pipeline

The brand character: an original, adult, short-haired, dark chocolate dachshund.
Built entirely by script in headless Blender, so it is reproducible and reviewable.

**Brand rule: the hot dog is the product, the dachshund is the mascot. They never
share a scene, and the dog never touches, holds or eats food.**

```bash
npm run 3d:mascot                    # full build: GLBs + stills + turntable
npm run 3d:mascot -- -- --no-render  # GLBs and .blend only
npm run 3d:mascot -- -- --preview    # quick two-view shape check, no exports
npm run 3d:mascot -- -- --preview --pose 02_Curious
```

## Layout

| Folder      | Contents                                                             |
| ----------- | -------------------------------------------------------------------- |
| `scripts/`  | `anatomy.py`, `modeling.py`, `rig.py`, `build_mascot.py`             |
| `source/`   | `SNUGDOG_Dachshund.blend` (rigged, with the pose library as actions) |
| `textures/` | Baked coat maps: albedo, normal, ORM at 2K, plus `_1k` copies        |
| `renders/`  | Cycles stills (PNG master + cleaned WebP cutout) and the turntable   |
| `exports/`  | `SNUGDOG_Dachshund.glb`, `SNUGDOG_Dachshund_hero.glb`                |

Published copies go to `public/models` and `public/images/mascot`.
Shared helpers (studio, baking, export) come from `assets/3d/scripts`.

## Outputs

| File                                 | What                                               |
| ------------------------------------ | -------------------------------------------------- |
| `SNUGDOG_Dachshund.glb`              | Light model: about 15k triangles, 1K maps, 358 KB  |
| `SNUGDOG_Dachshund_hero.glb`         | Detailed model: about 60k triangles, 2K maps, 834 KB |
| `SNUGDOG_Dachshund_still.webp`       | Hero standing still                                |
| `SNUGDOG_Dachshund_pose_<id>.webp`   | One still per pose (also the web fallbacks)        |
| `SNUGDOG_Dachshund_turntable.webp`   | Eight views as a 4x2 contact sheet                 |

Both GLBs are Draco-compressed with WebP textures and carry the same skeleton and
the same five pose clips.

## How the model is made

1. **Anatomy** (`anatomy.py`): every measurement in one place. Units are 1 = 10 cm,
   nose toward +X, +Z up, the dog's left is +Y, paws on Z = 0.
2. **Volumes to skin** (`modeling.py`): tubes and ellipsoids for body, neck, skull,
   muzzle, limbs and tail are fused with a voxel remesh, smoothed, then
   retopologised to even quads (QuadriFlow) for clean deformation. Ears are separate
   thin flaps joined into the skin.
3. **Face**: eyes are seated by raycasting onto the skull so a fixed share of the
   eyeball shows. Each eye has an upper and lower lid shell that pivots on the eye's
   own axis, so a blink is one rotation.
4. **Coat** (`build_mascot.py`): per-vertex colour (dark chocolate, darker ears and
   topline, restrained warm points) feeds a procedural material with hair grain,
   which is baked to albedo, normal and ORM maps with contact shadows folded in.
5. **Rig** (`rig.py`): armature with automatic weights; ears get hand-written
   weights. Eyes, lids and nose ride the `Head` bone as rigid parts.
6. **Poses**: written as readable bone turns, stored as one action per pose on NLA
   tracks, exported as named clips.

## Hierarchy

```
SNUGDOG_Dachshund            (armature)
|-- Root                     hips; move/tilt the whole dog
|   |-- Body -> Chest -> Neck -> Head -> Muzzle
|   |                |             |-- Ear_L -> Ear_L_2
|   |                |             |-- Ear_R -> Ear_R_2
|   |                |             |-- Eye_L, Eye_R            (rigid meshes)
|   |                |             |-- Lid_U_L, Lid_U_R        (rigid meshes, blink)
|   |                |             |-- Lid_D_L, Lid_D_R        (rigid meshes)
|   |                |             `-- Nose                    (rigid mesh)
|   |                |-- Leg_FL -> Paw_FL
|   |                `-- Leg_FR -> Paw_FR
|   |-- Leg_BL -> Paw_BL
|   |-- Leg_BR -> Paw_BR
|   `-- Tail -> Tail_2 -> Tail_3
`-- Skin / Skin_Hero         (one skinned mesh: body, head, legs, paws, tail, ears)
```

Differences from the hierarchy suggested in the brief, and why:

- Body, head, legs, paws, tail and ears are **bones over one skinned mesh**, not
  separate meshes. Separate meshes would show seams at every joint; one skin is
  what a rig and animation need.
- Iris and pupil are painted into each `Eye_*` mesh rather than split out, so
  rotating the eye moves the gaze as a whole.
- **Mouth, teeth and tongue are not modelled.** The mouth is a closed line in the
  coat texture. An open mouth needs a jaw bone and interior geometry (see limits).
- **Accessories are not built yet.** The base character had to stand on its own
  first. A cap or bandana would attach as a rigid child of `Head` or `Neck`.

## Pose library

| Clip                   | Description                                            |
| ---------------------- | ------------------------------------------------------ |
| `Pose_01_HeroStanding` | Confident stance, head slightly toward camera          |
| `Pose_02_Curious`      | Head tilt, one ear lifted                              |
| `Pose_03_Walking`      | Mid-stride, diagonal legs                              |
| `Pose_04_Sitting`      | Relaxed sit                                            |
| `Pose_05_LookingBack`  | Body away, head turned back over the shoulder          |

To add a pose, add an entry to `POSES` in `rig.py` and a camera to `VIEWS` in
`build_mascot.py`. Steps are applied children first, and roll/pitch before yaw, so
each turn acts in the bone's own rest frame.

## Animation readiness

- **Pose to pose:** the web cross-fades between clips (`MascotCanvas.tsx`).
- **Blink:** rotate `Lid_U_L` / `Lid_U_R` about their local Z by about -50 degrees.
- **Look around:** rotate `Head` or the `Eye_*` nodes.
- **Ears, tail:** `Ear_*`, `Ear_*_2`, `Tail`, `Tail_2`, `Tail_3`.
- **Walk, turn, sit:** leg and paw bones exist; cycles are not authored yet.

## Known limits (v1)

- **Stylised, not studio-grade.** A scripted model gives a clean, characterful
  vinyl-figure look. It does not reach the sculpted anatomy, wrinkles and facial
  nuance of a hand-made commercial character.
- **No strand fur.** The coat is hair-grain texture plus sheen. `--fur` adds Cycles
  strands, but they currently render too pale under the studio lights and are off
  by default.
- **Paws have no toes; the sitting pose is approximate.** There is no IK, and the
  hind legs fold with simple two-bone chains.
- **No reference images were available** when this was built; it follows the written
  brief only.
