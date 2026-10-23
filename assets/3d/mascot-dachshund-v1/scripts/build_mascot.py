"""SNUGDOG dachshund mascot: model -> material -> rig -> poses -> GLB + stills.

    node assets/3d/scripts/blender.mjs ../mascot/scripts/build_mascot.py [-- flags]

Flags
    --preview        clay render of the rest pose only (fast shape check)
    --no-render      build, bake and export GLBs, skip the Cycles stills
    --fur            experimental: add short strand fur to the stills (off by default)
    --pose NAME      with --preview: render that pose instead of the rest pose
    --samples N      Cycles samples for stills (default 128)

See assets/3d/mascot/README.md for outputs and conventions.
"""
import math
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(HERE)
sys.path.append(os.path.join(HERE, "..", "..", "scripts"))

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

import anatomy as an  # noqa: E402
import common as c  # noqa: E402
import modeling as m  # noqa: E402
import rig  # noqa: E402
import shading as sh  # noqa: E402

MASCOT = os.path.dirname(HERE)
OUT = {name: os.path.join(MASCOT, name) for name in ("source", "textures", "renders", "exports")}
PUBLIC_IMAGES = os.path.join(c.PUBLIC_IMAGES, "mascot")
NAME = "SNUGDOG_Dachshund"

# camera per pose: (direction from target, distance, target)
VIEWS = {
    "01_HeroStanding": ((0.80, 1.0, 0.24), 17.5, (0.45, 0, 1.55)),
    "02_Curious": ((1.0, 0.85, 0.20), 15.5, (0.9, 0, 1.7)),
    "03_Walking": ((0.35, 1.0, 0.16), 17.5, (0.3, 0, 1.5)),
    "04_Sitting": ((0.85, 1.0, 0.22), 16.5, (0.5, 0, 1.5)),
    "05_LookingBack": ((-0.75, 1.0, 0.26), 17.5, (0.2, 0, 1.55)),
}


# ---------------------------------------------------------------- materials
def flat_material(name, color, roughness=0.6, coat=0.0, coat_roughness=0.05):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Coat Weight"].default_value = coat
    bsdf.inputs["Coat Roughness"].default_value = coat_roughness
    return mat


def paint_coat(skin):
    """Per-vertex coat colour in the rest pose: dark chocolate, darker ears and topline,
    restrained warm points on brows, muzzle, chest and feet. Alpha marks the legs so the
    material can run the hair grain downwards there."""
    base, dark, warm = c.srgb(0.215, 0.120, 0.075), c.srgb(0.125, 0.068, 0.044), c.srgb(0.47, 0.28, 0.15)
    ear = skin.vertex_groups["is_ear"].index
    brows = [Vector((2.60, 0.23 * s, 3.03)) for s in (1, -1)]
    chest = [Vector((1.88, 0.20 * s, 1.32)) for s in (1, -1)]
    colors = []
    for v in skin.data.vertices:
        p, n = v.co, v.normal
        is_ear = any(g.group == ear and g.weight > 0.5 for g in v.groups)
        col = c.mix(base, dark, 0.45 * c.smoothstep(0.35, 0.95, n.z) * c.smoothstep(1.9, 1.5, p.x))
        points = max(
            c.smoothstep(2.62, 2.46, p.z) * c.smoothstep(2.56, 2.85, p.x),  # underside of the muzzle
            max(math.exp(-((p - b).length / 0.085) ** 2) for b in brows),
            0.8 * max(math.exp(-((p - q).length / 0.26) ** 2) for q in chest),
            c.smoothstep(0.60, 0.12, p.z) * (1 if abs(p.y) > 0.15 else 0),  # feet
        )
        col = c.mix(col, warm, 0.62 * points)
        if is_ear:
            col = c.mix(col, dark, 0.85)
        legs = c.smoothstep(1.02, 0.78, p.z) if abs(p.y) > 0.15 and not is_ear else 0.0
        colors.append(col[:3] + (legs,))
    c.set_colors(skin, colors)


def coat_material():
    """Short, sleek coat: hair grain with darker roots and brighter tips, a soft sheen,
    and the mouth drawn as a fine line with a slight upturn at the corner."""
    g = sh.Graph(sh.principled("Coat", sheen=0.18, sheen_roughness=0.5, sheen_tint=c.srgb(0.62, 0.44, 0.32)))
    col, legs = g.vertex_color()
    along = g.noise(70, detail=3, stretch=(0.07, 1, 1))
    down = g.noise(70, detail=3, stretch=(1, 1, 0.07))
    grain = g.add(g.mul(along, g.math("SUBTRACT", 1.0, legs)), g.mul(down, legs))
    fine = g.noise(260, detail=2)
    color = g.mix(g.step(grain, 0.25, 0.8, 0.0, 0.5), col, c.srgb(0.05, 0.028, 0.018))
    color = g.mix(g.step(fine, 0.55, 0.85, 0.0, 0.2), color, c.srgb(0.50, 0.31, 0.18))

    x, z = g.axis("X"), g.axis("Z")
    corner = g.mul(g.math("MAXIMUM", g.math("SUBTRACT", 2.80, x), 0.0), 0.28)
    line = g.add(g.add(2.50, g.mul(g.math("SUBTRACT", x, 2.6), -0.086)), corner)
    gap = g.math("ABSOLUTE", g.math("SUBTRACT", z, line))
    mouth = g.mul(g.mul(g.step(gap, 0.006, 0.02, 1, 0), g.step(x, 2.66, 2.72)), g.step(x, 3.30, 3.40, 1, 0))
    color = g.mix(g.mul(mouth, 0.85), color, c.srgb(0.03, 0.02, 0.015))

    height = g.add(g.add(g.mul(grain, 0.6), g.mul(fine, 0.25)), g.mul(mouth, -1.5))
    rough = g.add(0.48, g.mul(grain, 0.22))
    return g.finish(color, rough, height, bump_strength=0.35, bump_distance=0.006)


def hair_material(albedo):
    """Cycles-only fur strands, coloured from the baked coat so stills and realtime agree."""
    mat = bpy.data.materials.new("Fur")
    mat.use_nodes = True
    nt = mat.node_tree
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = albedo
    hair = nt.nodes.new("ShaderNodeBsdfHairPrincipled")
    hair.parametrization = "COLOR"
    hair.inputs["Roughness"].default_value = 0.34
    hair.inputs["Radial Roughness"].default_value = 0.5
    nt.links.new(tex.outputs["Color"], hair.inputs["Color"])
    nt.links.new(hair.outputs[0], out.inputs["Surface"])
    return mat


def add_fur(skin, albedo):
    """Experimental (--fur): a very short, dense coat that only softens the silhouette.
    The dachshund is smooth-haired, so the look must stay sleek; the default stills use
    the groomed-grain coat material without strands."""
    skin.data.materials.append(hair_material(albedo))
    mod = skin.modifiers.new("Fur", "PARTICLE_SYSTEM")
    ps = mod.particle_system.settings
    ps.type = "HAIR"
    ps.count = 320000
    ps.hair_length = 0.035
    ps.hair_step = 2
    ps.child_type = "NONE"  # interpolated children lose the emitter UVs, and with them the coat colour
    ps.root_radius = 1.0
    ps.tip_radius = 0.3
    ps.radius_scale = 0.005
    ps.material = len(skin.data.materials)
    return mod


# ---------------------------------------------------------------- model
def build_model():
    """Returns (low skin, high skin, rigid parts). Both skins share UVs, colours and weights-to-be."""
    skin = m.retopologise(m.fuse(m.build_volumes()))
    eyes = {side: m.seat_eye(skin, side) for side in (1, -1)}
    rigid = {"Nose": m.build_nose(skin)}
    for side, tag in ((1, "L"), (-1, "R")):
        rigid[f"Eye_{tag}"] = m.build_eye(side, eyes[side])
        rigid[f"Lid_U_{tag}"] = m.build_lid(side, eyes[side], upper=True, open_deg=19, tilt_deg=7)
        rigid[f"Lid_D_{tag}"] = m.build_lid(side, eyes[side], upper=False, open_deg=32)

    ears = [m.build_ear(1), m.build_ear(-1)]
    for ear in ears:
        ear.vertex_groups.new(name="is_ear").add(range(len(ear.data.vertices)), 1.0, "REPLACE")
    skin = m.join([skin] + ears, "Skin")
    bpy.ops.object.shade_smooth()

    # one unwrap shared by both levels of detail
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.006)
    bpy.ops.object.mode_set(mode="OBJECT")

    bpy.ops.object.duplicate()
    hero = bpy.context.active_object
    hero.name = "Skin_Hero"
    smooth = hero.modifiers.new("Subdivide", "SUBSURF")
    smooth.levels = 1
    m.apply_modifier(hero, smooth)
    return skin, hero, rigid


def dress(skin, hero, rigid):
    """Materials: procedural coat baked to maps (shared by both skins), simple lobes for the rest."""
    paint_coat(hero)
    hero.data.materials.append(coat_material())
    maps = sh.bake_pbr(hero, "dachshund_coat", size=(2048, 2048), detail_size=(2048, 2048), ao_strength=0.55,
                       ao_hidden=[skin], out_dir=OUT["textures"])
    coat = sh.baked_material(hero.data.materials[0], *maps)
    coat.name = "Coat"
    hero.data.materials[0] = coat
    skin.data.materials.clear()

    # the light GLB carries half-size maps
    small = []
    for image in maps:
        copy = image.copy()
        copy.scale(1024, 1024)
        copy.filepath_raw = image.filepath_raw.replace(".png", "_1k.png")
        copy.file_format = "PNG"
        copy.save()
        small.append(copy)
    coat_small = sh.baked_material(coat, *small)
    coat_small.name = "Coat_1k"
    skin.data.materials.append(coat_small)

    eye = c.vertex_color_material("Eye", roughness=0.06, coat=1.0, coat_roughness=0.03)
    rim = flat_material("EyeRim", c.srgb(0.12, 0.066, 0.042), roughness=0.6)
    nose = flat_material("NosePad", c.srgb(0.03, 0.025, 0.025), roughness=0.5, coat=0.35, coat_roughness=0.25)
    for name, obj in rigid.items():
        obj.data.materials.clear()
        obj.data.materials.append(eye if name.startswith("Eye") else nose if name == "Nose" else rim)
    return maps[0]


# ---------------------------------------------------------------- stills
def mascot_studio(scene, target, camera_dir, distance, lens=85):
    """Product-style studio sized for the dog: soft key, fill, rim, shadow-catcher floor."""
    for obj in list(scene.objects):
        if obj.type in {"LIGHT", "CAMERA"} or obj.name.startswith("ShadowCatcher"):
            bpy.data.objects.remove(obj)
    if scene.world is None:
        world = bpy.data.worlds.new("Studio")
        world.use_nodes = True
        bg = world.node_tree.nodes["Background"]
        bg.inputs["Color"].default_value = (1, 1, 1, 1)
        bg.inputs["Strength"].default_value = 0.3
        scene.world = world

    direction = Vector(camera_dir).normalized()
    right = direction.cross(Vector((0, 0, 1))).normalized()
    t = Vector(target)
    c.area_light("Key", t + direction * 5 - right * 5 + Vector((0, 0, 7)), target, 1500, 7.0, (1.0, 0.96, 0.92))
    c.area_light("Fill", t + direction * 6 + right * 7 + Vector((0, 0, 2)), target, 380, 9.0, shadow=False)
    c.area_light("Rim", t - direction * 7 + right * 2 + Vector((0, 0, 5)), target, 1100, 5.0, shadow=False)

    bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, 0))
    floor = bpy.context.active_object
    floor.name = "ShadowCatcher"
    floor.is_shadow_catcher = True

    cam_data = bpy.data.cameras.new("Camera")
    cam_data.lens = lens
    cam = bpy.data.objects.new("Camera", cam_data)
    cam.location = t + direction * distance
    scene.collection.objects.link(cam)
    c.look_at(cam, target)
    scene.camera = cam


def publish(path):
    os.makedirs(PUBLIC_IMAGES, exist_ok=True)
    shutil.copy2(path, PUBLIC_IMAGES)


def render_poses(scene, arm, samples):
    for pose, (direction, distance, target) in VIEWS.items():
        rig.apply_pose(arm, pose)
        mascot_studio(scene, target, direction, distance)
        c.configure_cycles(scene, 1800, 1300, samples=samples)
        scene.view_settings.exposure = 0.0
        publish(c.render_still(scene, f"{NAME}_pose_{pose}", publish=False, out_dir=OUT["renders"]))
    hero = os.path.join(OUT["renders"], f"{NAME}_pose_01_HeroStanding.webp")
    still = os.path.join(OUT["renders"], f"{NAME}_still.webp")
    shutil.copy2(hero, still)
    publish(still)


def render_turntable(scene, arm, samples, frames=8, size=640):
    """Eight views around the hero pose, assembled into one 4x2 contact sheet."""
    rig.apply_pose(arm, "01_HeroStanding")
    tiles = []
    for i in range(frames):
        angle = math.tau * i / frames + math.radians(52)
        mascot_studio(scene, (0.3, 0, 1.55), (math.cos(angle), math.sin(angle), 0.24), 19.0)
        c.configure_cycles(scene, size, size, samples=samples)
        scene.view_settings.exposure = 0.0
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.color_mode = "RGBA"
        scene.render.filepath = os.path.join(OUT["renders"], f"_turn_{i}.png")
        bpy.ops.render.render(write_still=True)
        image = bpy.data.images.load(scene.render.filepath)
        px = np.empty(size * size * 4, dtype=np.float32)
        image.pixels.foreach_get(px)
        tiles.append(px.reshape(size, size, 4))
        bpy.data.images.remove(image)
        os.remove(scene.render.filepath)
    cols = 4
    rows = [np.concatenate(tiles[r * cols:(r + 1) * cols], axis=1) for r in range(frames // cols)]
    sheet = np.concatenate(rows[::-1], axis=0)  # image rows run bottom-up
    out = bpy.data.images.new("turntable", size * cols, size * (frames // cols), alpha=True)
    out.pixels.foreach_set(sheet.ravel())
    out.filepath_raw = os.path.join(OUT["renders"], f"{NAME}_turntable.webp")
    out.file_format = "WEBP"
    out.save(quality=88)
    publish(out.filepath_raw)


def preview(scene, objects, samples):
    for tag, direction, dist, target in (
        ("three_quarter", (0.80, 1.0, 0.28), 17.0, (0.5, 0, 1.5)),
        ("face", (1.0, 0.45, 0.12), 7.0, (2.7, 0, 2.6)),
    ):
        mascot_studio(scene, target, direction, dist)
        c.configure_cycles(scene, 1400, 900, samples=samples)
        scene.view_settings.exposure = 0.0
        scene.render.image_settings.file_format = "PNG"
        scene.render.filepath = os.path.join(OUT["renders"], f"_preview_{tag}.png")
        bpy.ops.render.render(write_still=True)


# ---------------------------------------------------------------- build
def main():
    args = c.script_args()
    samples = int(args[args.index("--samples") + 1]) if "--samples" in args else 128
    for path in list(OUT.values()):
        os.makedirs(path, exist_ok=True)
    scene = c.reset_scene()
    scene.render.engine = "CYCLES"

    skin, hero, rigid = build_model()
    albedo = dress(skin, hero, rigid)

    arm = rig.build_armature(NAME)
    rig.bind(skin, arm)
    rig.bind(hero, arm)
    for obj in rigid.values():
        rig.attach(obj, arm, "Head")

    if "--preview" in args:
        skin.hide_render = True
        if "--fur" in args:
            add_fur(hero, albedo)
        if "--pose" in args:
            rig.apply_pose(arm, args[args.index("--pose") + 1])
        preview(scene, [hero, *rigid.values()], min(samples, 48))
        return

    rig.store_poses(arm)
    rig.set_tracks_muted(arm, False)
    animation = dict(export_animations=True, export_animation_mode="NLA_TRACKS", export_force_sampling=True,
                     export_frame_range=False, export_anim_single_armature=True)
    parts = list(rigid.values())
    c.export_glb(NAME, [arm, skin, *parts], out_dir=OUT["exports"], **animation)
    c.export_glb(f"{NAME}_hero", [arm, hero, *parts], out_dir=OUT["exports"], **animation)
    rig.set_tracks_muted(arm, True)

    skin.hide_render = True
    if "--fur" in args:
        add_fur(hero, albedo)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT["source"], f"{NAME}.blend"), compress=True)
    if "--no-render" not in args:
        render_poses(scene, arm, samples)
        render_turntable(scene, arm, max(samples // 2, 32))
        rig.reset(arm)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT["source"], f"{NAME}.blend"), compress=True)


main()
