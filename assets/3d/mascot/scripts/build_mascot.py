"""SNUGDOG terrier mascot: model -> material -> rig -> poses -> GLB + stills.

    node assets/3d/scripts/blender.mjs ../mascot/scripts/build_mascot.py [-- flags]

Flags
    --preview        clay render of the rest pose only (fast shape check)
    --no-render      build, bake and export GLBs, skip the Cycles stills
    --no-fur         stills without strand fur (fast; shows the bare skin model)
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
NAME = "SNUGDOG_Terrier"

# camera per pose: (direction from target, distance, target)
VIEWS = {
    "01_HeroStanding": ((0.85, 1.0, 0.18), 19.0, (0.45, 0, 2.05)),
    "02_Curious": ((1.0, 0.80, 0.16), 18.5, (0.55, 0, 2.1)),
    "03_Walking": ((0.40, 1.0, 0.14), 19.0, (0.45, 0, 2.05)),
    "04_Sitting": ((0.85, 1.0, 0.18), 19.0, (0.45, 0, 1.95)),
    "05_LookingBack": ((-0.75, 1.0, 0.22), 19.0, (0.3, 0, 2.05)),
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
    """Per-vertex coat colour in the rest pose: charcoal, greyer on the beard, brows, chest
    and legs, pink inside the ears. Alpha marks the legs so the grain runs downwards there."""
    base, grey, pink = c.srgb(0.070, 0.072, 0.078), c.srgb(0.21, 0.21, 0.22), c.srgb(0.62, 0.36, 0.36)
    ear = skin.vertex_groups["is_ear"].index
    brows = [an.paired(s)["brow"][0] for s in (1, -1)]
    colors = []
    for v in skin.data.vertices:
        p, n = v.co, v.normal
        is_ear = any(g.group == ear and g.weight > 0.5 for g in v.groups)
        lighter = max(
            c.smoothstep(2.70, 2.45, p.z) * c.smoothstep(1.70, 1.95, p.x),  # beard
            0.8 * max(math.exp(-((p - b).length / 0.24) ** 2) for b in brows),
            0.6 * c.smoothstep(0.9, 0.3, p.z) * (1 if abs(p.y) > 0.15 else 0),  # lower legs
            0.5 * math.exp(-((p - Vector((1.1, 0, 1.3))).length / 0.4) ** 2),  # chest
        )
        col = c.mix(base, grey, 0.75 * lighter)
        if is_ear and n.x > 0.25:
            col = c.mix(col, pink, c.smoothstep(0.25, 0.7, n.x))
        legs = c.smoothstep(1.02, 0.78, p.z) if abs(p.y) > 0.15 and not is_ear else 0.0
        colors.append(col[:3] + (legs,))
    c.set_colors(skin, colors)


def coat_material():
    """The skin under the fur, and the realtime stand-in for it: charcoal with a wiry grain."""
    g = sh.Graph(sh.principled("Coat", sheen=0.25, sheen_roughness=0.6, sheen_tint=c.srgb(0.55, 0.55, 0.6)))
    col, legs = g.vertex_color()
    along = g.noise(46, detail=3, stretch=(0.09, 1, 1))
    down = g.noise(46, detail=3, stretch=(1, 1, 0.09))
    grain = g.add(g.mul(along, g.math("SUBTRACT", 1.0, legs)), g.mul(down, legs))
    fine = g.noise(200, detail=2)
    color = g.mix(g.step(grain, 0.25, 0.8, 0.0, 0.55), col, c.srgb(0.02, 0.02, 0.022))
    color = g.mix(g.step(fine, 0.55, 0.85, 0.0, 0.3), color, c.srgb(0.34, 0.34, 0.36))
    height = g.add(g.mul(grain, 0.7), g.mul(fine, 0.3))
    rough = g.add(0.55, g.mul(grain, 0.25))
    return g.finish(color, rough, height, bump_strength=0.5, bump_distance=0.01)


def groom_groups(skin):
    """Vertex groups that drive the fur: how long it grows and where it grows at all.
    Long on the beard, brows, chest, belly and legs; short on the skull and muzzle top;
    none inside the ears or over the eyes and nose."""
    length = skin.vertex_groups.new(name="fur_length")
    density = skin.vertex_groups.new(name="fur_density")
    ear = skin.vertex_groups["is_ear"].index
    brows = [an.paired(s)["brow"][0] for s in (1, -1)]
    eyes = [an.eye_centre(s) for s in (1, -1)]
    nose = an.NOSE[0]
    for v in skin.data.vertices:
        p, n = v.co, v.normal
        is_ear = any(g.group == ear and g.weight > 0.5 for g in v.groups)
        grow, amount = 0.55, 1.0
        if is_ear:
            grow, amount = (0.10, 0.3) if n.x > 0.35 else (0.22, 1.0)
        elif p.x > 1.25 and p.z > 2.1:  # head
            beard = c.smoothstep(2.72, 2.50, p.z) * c.smoothstep(1.65, 1.90, p.x)
            brow = max(math.exp(-((p - b).length / 0.26) ** 2) for b in brows)
            grow = max(0.30, beard, 0.6 * brow)
            eye_gap = min((p - e).length for e in eyes) / an.EYE_RADIUS
            if eye_gap < 1.3 or (p - nose).length < 0.17:
                amount = 0.0
            elif eye_gap < 2.3:
                grow = min(grow, 0.16)  # short around the eyes so the whites stay visible
        else:  # body
            legs = c.smoothstep(1.05, 0.8, p.z) if abs(p.y) > 0.15 else 0.0
            belly = c.smoothstep(-0.2, -0.7, n.z)
            chest = math.exp(-((p - Vector((1.1, 0, 1.3))).length / 0.45) ** 2)
            grow = max(0.5, 0.62 * legs, 0.95 * belly, 0.85 * chest)
            if p.z < 0.3:
                grow = 0.4  # paws
        collar_centre, collar_axis, _ = an.COLLAR
        if abs((p - collar_centre).dot(collar_axis.normalized())) < 0.10 and not is_ear:
            grow = 0.12  # flattened under the collar
        length.add([v.index], grow, "REPLACE")
        density.add([v.index], amount, "REPLACE")


def hair_material():
    """Cycles-only fur strands: charcoal with a share of lighter hairs, darker at the root.
    A plain surface shader is used on purpose; the Principled Hair BSDF rendered far too
    pale in this studio whatever its absorption was set to."""
    mat = bpy.data.materials.new("Fur")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    info = nt.nodes.new("ShaderNodeHairInfo")

    grey = nt.nodes.new("ShaderNodeMapRange")  # which hairs are the pale ones
    grey.interpolation_type = "SMOOTHSTEP"
    for name, value in (("From Min", 0.74), ("From Max", 0.84), ("To Min", 0.0), ("To Max", 1.0)):
        grey.inputs[name].default_value = value
    nt.links.new(info.outputs["Random"], grey.inputs["Value"])

    tone = nt.nodes.new("ShaderNodeMix")
    tone.data_type = "RGBA"
    tone.inputs[6].default_value = c.srgb(0.085, 0.087, 0.095)
    tone.inputs[7].default_value = c.srgb(0.50, 0.50, 0.52)
    nt.links.new(grey.outputs["Result"], tone.inputs[0])

    root = nt.nodes.new("ShaderNodeMix")  # hairs darken toward the skin
    root.data_type, root.blend_type = "RGBA", "MULTIPLY"
    root.inputs[7].default_value = (0.35, 0.35, 0.37, 1.0)
    fade = nt.nodes.new("ShaderNodeMapRange")
    for name, value in (("From Min", 0.0), ("From Max", 0.6), ("To Min", 1.0), ("To Max", 0.0)):
        fade.inputs[name].default_value = value
    nt.links.new(info.outputs["Intercept"], fade.inputs["Value"])
    nt.links.new(fade.outputs["Result"], root.inputs[0])
    nt.links.new(tone.outputs[2], root.inputs[6])

    nt.links.new(root.outputs[2], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.45
    bsdf.inputs["Sheen Weight"].default_value = 0.2
    return mat


def add_fur(skin):
    """Wiry, shaggy terrier coat for the Cycles stills: guide hairs that lean back and
    down, clumped children, lengths and bald areas from the groom groups.

    In advanced mode a strand's length is about four times the size of its start velocity
    (normal_factor plus object_align_factor), scaled by the fur_length group; hair_length
    itself has little effect. The velocities below are sized for roughly 3 cm of coat."""
    skin.data.materials.append(hair_material())
    mod = skin.modifiers.new("Fur", "PARTICLE_SYSTEM")
    system = mod.particle_system
    system.vertex_group_length = "fur_length"
    system.vertex_group_density = "fur_density"
    ps = system.settings
    ps.type = "HAIR"
    ps.count = 18000
    ps.hair_length = 0.30
    ps.hair_step = 5
    ps.use_advanced_hair = True
    ps.normal_factor = 0.075
    ps.object_align_factor = (-0.028, 0.0, -0.040)
    ps.factor_random = 0.02
    ps.child_type = "INTERPOLATED"
    ps.rendered_child_count = 30
    ps.clump_factor = 0.35
    ps.clump_shape = -0.2
    ps.roughness_1 = 0.02
    ps.roughness_2 = 0.05
    ps.roughness_endpoint = 0.04
    ps.kink = "WAVE"
    ps.kink_amplitude = 0.012
    ps.kink_frequency = 4.0
    ps.root_radius = 1.0
    ps.tip_radius = 0.1
    ps.radius_scale = 0.007
    ps.material = len(skin.data.materials)
    return mod


# ---------------------------------------------------------------- model
def build_model():
    """Returns (low skin, high skin, rigid parts). Both skins share UVs, colours and weights-to-be."""
    skin = m.retopologise(m.fuse(m.build_volumes()))
    eyes = {side: m.seat_eye(skin, side) for side in (1, -1)}
    rigid = {"Nose": m.build_nose(skin), "Collar": m.build_collar()}
    for side, tag in ((1, "L"), (-1, "R")):
        rigid[f"Eye_{tag}"] = m.build_eye(side, eyes[side])
        # wide open: the whites show all round, which is where the expression comes from
        rigid[f"Lid_U_{tag}"] = m.build_lid(side, eyes[side], upper=True, open_deg=58, tilt_deg=-5)
        rigid[f"Lid_D_{tag}"] = m.build_lid(side, eyes[side], upper=False, open_deg=60)

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
    maps = sh.bake_pbr(hero, "terrier_coat", size=(2048, 2048), detail_size=(2048, 2048), ao_strength=0.55,
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

    looks = {
        "Eye": c.vertex_color_material("Eye", roughness=0.06, coat=1.0, coat_roughness=0.03),
        "Lid": flat_material("EyeRim", c.srgb(0.06, 0.06, 0.065), roughness=0.6),
        "Nose": flat_material("NosePad", c.srgb(0.02, 0.02, 0.022), roughness=0.38, coat=0.6, coat_roughness=0.2),
        "Collar": flat_material("Collar", c.srgb(0.62, 0.07, 0.07), roughness=0.7),
    }
    for name, obj in rigid.items():
        obj.data.materials.clear()
        obj.data.materials.append(next(mat for key, mat in looks.items() if name.startswith(key)))
    groom_groups(hero)


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
        mascot_studio(scene, (0.3, 0, 2.05), (math.cos(angle), math.sin(angle), 0.2), 21.0)
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
        ("three_quarter", (0.85, 1.0, 0.18), 17.0, (0.5, 0, 2.05)),
        ("face", (1.0, 0.5, 0.10), 8.5, (1.75, 0, 2.95)),
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
    dress(skin, hero, rigid)

    arm = rig.build_armature(NAME)
    rig.bind(skin, arm)
    rig.bind(hero, arm)
    for name, obj in rigid.items():
        rig.attach(obj, arm, "Neck" if name == "Collar" else "Head")

    if "--preview" in args:
        skin.hide_render = True
        if "--no-fur" not in args:
            add_fur(hero)
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
    if "--no-fur" not in args:
        add_fur(hero)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT["source"], f"{NAME}.blend"), compress=True)
    if "--no-render" not in args:
        render_poses(scene, arm, samples)
        render_turntable(scene, arm, max(samples // 2, 32))
        rig.reset(arm)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT["source"], f"{NAME}.blend"), compress=True)


main()
