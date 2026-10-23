"""SNUGDOG packaging: box, cup and bag in white stock with printed labels.

    node assets/3d/scripts/make_labels.mjs          (once, or when the artwork changes)
    node assets/3d/scripts/blender.mjs build_packaging.py [-- --no-render] [--samples N]

Outputs
    assets/3d/source/snugdog-packaging.blend
    assets/3d/glb/snugdog-packaging.glb      (copied to public/models)
    assets/3d/renders/snugdog-packaging.webp (copied to public/images)

Each pack is one root node (Box, Cup, Bag) built at the origin with its base on Z = 0,
so the web scene can place and turn them independently. Printed areas are separate label
panels a hair above the stock, textured from assets/3d/textures/packaging_*.png; panel and
stock share one paper colour, so the panel edge disappears.
Units: 1 = 10 cm. The front of every pack faces -Y (toward the viewer after export).
"""
import math
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import common as c  # noqa: E402

NAME = "snugdog-packaging"
PAPER = c.srgb(0.933, 0.914, 0.878)  # must match PAPER in make_labels.mjs (#eee9e0)
LIFT = 0.003  # how far a label panel sits above the stock


# ---------------------------------------------------------------- materials
def flat(name, color, roughness):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def printed(name):
    path = os.path.join(c.DIRS["textures"], f"packaging_{name}.png")
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} is missing: run make_labels.mjs first")
    mat = bpy.data.materials.new(f"Print_{name}")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(path)
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.82
    return mat


# ---------------------------------------------------------------- geometry helpers
def finish(obj, bevel=0.03):
    """Soft carton edges with flat faces."""
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    if bevel:
        mod = obj.modifiers.new("Bevel", "BEVEL")
        mod.width, mod.segments = bevel, 3
        bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.ops.object.shade_smooth()
    split = obj.modifiers.new("Edges", "EDGE_SPLIT")
    split.split_angle = math.radians(40)
    bpy.ops.object.modifier_apply(modifier=split.name)
    return obj


def block(name, size, centre, material, bevel=0.03):
    bpy.ops.mesh.primitive_cube_add(size=1, location=centre)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    # bake the placement into the mesh so every part keeps its origin at the pack base
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=True)
    obj.data.materials.append(material)
    return finish(obj, bevel)


def round_part(name, r_bottom, r_top, height, z, material, bevel=0.0):
    bpy.ops.mesh.primitive_cone_add(vertices=72, radius1=r_bottom, radius2=r_top, depth=height, location=(0, 0, z + height / 2))
    obj = bpy.context.active_object
    obj.name = name
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    obj.data.materials.append(material)
    return finish(obj, bevel)


def panel(name, corners, material):
    """Flat label: corners are bottom-left, bottom-right, top-right, top-left."""
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([Vector(p) for p in corners], [], [(0, 1, 2, 3)])
    mesh.uv_layers.new(name="UV").data.foreach_set("uv", [0, 0, 1, 0, 1, 1, 0, 1])
    mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def wrap_panel(name, radius_at, z0, z1, half_angle, material, nu=40, nv=6):
    """Label wrapped round the front of a tapered cup."""
    verts, faces, uvs = [], [], []
    for j in range(nv + 1):
        z = z0 + (z1 - z0) * j / nv
        r = radius_at(z) + LIFT
        for i in range(nu + 1):
            a = -half_angle + 2 * half_angle * i / nu
            verts.append(Vector((r * math.sin(a), -r * math.cos(a), z)))
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i
            faces.append((a, a + 1, a + nu + 2, a + nu + 1))
            for di, dj in ((0, 0), (1, 0), (1, 1), (0, 1)):
                uvs += [(i + di) / nu, (j + dj) / nv]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.uv_layers.new(name="UV").data.foreach_set("uv", uvs)
    mesh.polygons.foreach_set("use_smooth", [True] * len(faces))
    mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def adopt(parent, *children):
    for child in children:
        child.parent = parent
    return parent


# ---------------------------------------------------------------- packs
def build_box(stock):
    """Hot dog carton with a lift-off lid."""
    w, d, h, lid = 2.1, 0.95, 0.9, 0.2
    box = block("Box", (w, d, h), (0, 0, h / 2), stock)
    top = block("Box_Lid", (w + 0.05, d + 0.05, lid), (0, 0, h - lid / 2 + 0.012), stock)
    y = -d / 2 - LIFT
    front = panel("Box_Front", [(-0.9, y, 0.05), (0.9, y, 0.05), (0.9, y, 0.683), (-0.9, y, 0.683)], printed("box_front"))
    z = h + 0.012 + LIFT
    lid_art = panel("Box_Top", [(-0.95, -0.408, z), (0.95, -0.408, z), (0.95, 0.408, z), (-0.95, 0.408, z)], printed("box_top"))
    return adopt(box, top, front, lid_art)


def build_cup(stock, plastic, ink):
    r0, r1, h = 0.30, 0.42, 1.30
    cup = round_part("Cup", r0, r1, h, 0.0, stock)
    rim = round_part("Cup_Lid", 0.445, 0.445, 0.06, h - 0.01, plastic, bevel=0.012)
    dome = round_part("Cup_LidTop", 0.39, 0.36, 0.06, h + 0.05, plastic, bevel=0.012)
    straw = round_part("Cup_Straw", 0.027, 0.027, 1.1, h - 0.45, ink)
    straw.rotation_euler = (math.radians(9), math.radians(-6), 0)
    straw.location = (0.24, 0.02, -0.02)
    label = wrap_panel("Cup_Label", lambda z: r0 + (r1 - r0) * z / h, 0.26, 1.02, math.radians(58), printed("cup"))
    return adopt(cup, rim, dome, straw, label)


def build_bag(stock):
    """Paper bag, pinched and folded at the top."""
    w, d, body, top = 0.65, 0.35, 1.35, 1.80
    verts = [(-w, -d, 0), (w, -d, 0), (w, d, 0), (-w, d, 0),
             (-w, -d, body), (w, -d, body), (w, d, body), (-w, d, body),
             (-w, -0.04, top), (w, -0.04, top), (w, 0.04, top), (-w, 0.04, top)]
    faces = [(3, 2, 1, 0), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),
             (4, 5, 9, 8), (5, 6, 10, 9), (6, 7, 11, 10), (7, 4, 8, 11), (8, 9, 10, 11)]
    mesh = bpy.data.meshes.new("Bag")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(stock)
    bag = bpy.data.objects.new("Bag", mesh)
    bpy.context.scene.collection.objects.link(bag)
    finish(bag, 0.018)
    fold = block("Bag_Fold", (2 * w + 0.02, 0.1, 0.26), (0, -0.03, top - 0.13), stock, bevel=0.012)
    y = -d - LIFT
    label = panel("Bag_Label", [(-0.53, y, 0.14), (0.53, y, 0.14), (0.53, y, 1.20), (-0.53, y, 1.20)], printed("bag"))
    return adopt(bag, fold, label)


# ---------------------------------------------------------------- still
def studio(scene):
    world = bpy.data.worlds.new("Studio")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (1, 1, 1, 1)
    bg.inputs["Strength"].default_value = 0.12
    scene.world = world
    target = (0, 0, 0.75)
    c.area_light("Key", (-4.5, -5.0, 6.0), target, 800, 6.0, (1.0, 0.97, 0.93))
    c.area_light("Fill", (6.0, -5.0, 2.0), target, 160, 8.0, shadow=False)
    c.area_light("Rim", (2.0, 6.0, 4.5), target, 700, 5.0, shadow=False)
    cam_data = bpy.data.cameras.new("Camera")
    cam_data.lens = 70
    cam = bpy.data.objects.new("Camera", cam_data)
    cam.location = (1.2, -13.0, 3.4)
    scene.collection.objects.link(cam)
    c.look_at(cam, target)
    scene.camera = cam


def main():
    args = c.script_args()
    samples = int(args[args.index("--samples") + 1]) if "--samples" in args else 128
    scene = c.reset_scene()

    stock = flat("Stock", PAPER, 0.82)
    plastic = flat("LidPlastic", c.srgb(0.95, 0.95, 0.95), 0.35)
    ink = flat("Ink", c.srgb(0.045, 0.045, 0.045), 0.5)
    box, cup, bag = build_box(stock), build_cup(stock, plastic, ink), build_bag(stock)
    c.export_glb(NAME, [obj for obj in scene.objects])

    # arranged group for the fallback still
    box.location, box.rotation_euler = (-2.2, 0.2, 0), (0, 0, math.radians(18))
    cup.location = (0.35, -0.35, 0)
    bag.location, bag.rotation_euler = (2.1, 0.3, 0), (0, 0, math.radians(-16))
    studio(scene)
    c.configure_cycles(scene, 2000, 1100, samples=samples)
    scene.view_settings.exposure = 0.0
    c.save_blend(NAME)
    if "--no-render" not in args:
        c.render_still(scene, NAME)


main()
