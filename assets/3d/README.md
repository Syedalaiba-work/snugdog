# SNUGDOG 3D asset pipeline

Every 3D asset is built by a Blender Python script running headless, so assets are
reproducible, reviewable in git and never depend on someone clicking through the UI.

```
MODEL -> MATERIAL -> LIGHTING -> CAMERA -> ANIMATION -> OPTIMISATION -> GLB EXPORT -> WEB
```

## Layout

| Folder      | Contents                                                              |
| ----------- | --------------------------------------------------------------------- |
| `scripts/`  | Blender Python build scripts, shared helpers, the Node runner         |
| `source/`   | Generated `.blend` source files (open these to inspect or hand-tweak) |
| `blend/`    | Shared library `.blend` files (lighting rigs, reusable parts)         |
| `glb/`      | Exported, Draco-compressed GLB masters                                |
| `textures/` | Baked maps (albedo, normal, ORM) written by `shading.bake_pbr`        |
| `mascot/`   | The dachshund character: its own scripts, sources, exports and README |
| `renders/`  | Cycles stills: PNG master + cleaned WebP cutout                       |

Published copies land in `public/models` and `public/images` automatically.

## Running

```bash
npm run 3d:check     # prints the Blender binary and version that will be used
npm run 3d:hotdog    # builds the hero hot dog: .blend + .glb + still
npm run 3d:mascot    # builds the mascot: see mascot/README.md
npm run 3d:labels    # prints packaging artwork to textures/packaging_*.png (needs Chrome)
npm run 3d:packaging # builds box, cup and bag: .blend + .glb + still
node assets/3d/scripts/blender.mjs build_hotdog.py -- --no-render   # GLB only
node assets/3d/scripts/blender.mjs build_hotdog.py -- --samples 64  # faster preview
```

`blender.mjs` finds Blender without assuming a path: `BLENDER_PATH` env var, then
`PATH`, then the standard install locations per OS (newest version first).
Developed against Blender 5.2 LTS.

## Conventions

- **Units:** 1 Blender unit = 10 cm. +X is the long axis of the food, +Z is up
  (the exporter converts to glTF's +Y up).
- **Materials:** large surfaces get a procedural node material built with
  `shading.Graph` (it reads the per-vertex `Col` attribute for broad colour and masks),
  which Cycles uses directly for stills. `shading.bake_pbr` bakes it to albedo, normal
  and ORM maps, with ambient occlusion folded into the albedo as contact shadows, and
  the GLB ships those. Small parts stay vertex-coloured (`COLOR_0`, no textures).
- **Naming:** each addressable part is its own object (`Bun`, `Sausage`, `Mustard`,
  `Seeds`, `Toppings`). The web layer looks parts up by these names; for example the
  mustard draw-on animation targets `Mustard`.
- **Compression:** Draco (position 14 bit, normal 10, colour 10), WebP textures. The decoder is
  self-hosted in `public/draco`, copied from `three/examples/jsm/libs/draco/gltf`.
  Re-copy it when upgrading three.
- **Animation:** motion is authored on the web (GSAP timeline + scroll, damped in the
  render loop; see `src/lib/motion.ts`), so GLBs ship static. Bake animation into a
  GLB only when it cannot be expressed as transforms, e.g. a rigged mascot.
- **Stills:** rendered on a shadow catcher with a transparent film, then
  `clean_cutout` removes alpha haze and fades the shadow before the frame edge so the
  image sits on the paper background with no visible rectangle.

## Adding an asset

1. Copy `build_hotdog.py` to `build_<asset>.py` and build geometry with the helpers
   in `common.py` (`lofted_surface`, `mesh_object`, `vertex_color_material`).
2. Call `export_glb`, `studio`, `configure_cycles`, `save_blend`, `render_still`.
3. Add an `npm run 3d:<asset>` script.
4. Load it on the web with `useGLTF("/models/<asset>.glb", "/draco/")`.

## Asset status

| Asset                | Status | Notes                                                             |
| -------------------- | ------ | ----------------------------------------------------------------- |
| `snugdog-hotdog`     | v2     | Procedural + baked maps. About 0.5 MB GLB, 5 draw calls.          |
| `SNUGDOG_Dachshund`  | v1     | Rigged, 5 poses, two levels of detail. See `mascot/README.md`.    |
| `snugdog-packaging`  | v1     | Box, cup, bag with printed labels. About 120 KB GLB.              |

### Known limits of hot dog v2

Baked crust, casing and contact shadows moved it well toward food photography, but it
is still a procedural model: the shapes are a little too regular, and there is no
translucency in realtime. For true macro realism the remaining step is photography
(or a photoscanned asset) for the stills, with this model as the realtime stand-in.
