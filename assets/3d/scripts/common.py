"""Shared helpers for the SNUGDOG Blender asset pipeline (run headless via blender.mjs)."""
import os
import shutil
import sys

import bpy
from mathutils import Vector

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
ROOT_3D = os.path.dirname(SCRIPTS)
PROJECT = os.path.dirname(os.path.dirname(ROOT_3D))
DIRS = {name: os.path.join(ROOT_3D, name) for name in ("source", "blend", "glb", "textures", "renders")}
PUBLIC_MODELS = os.path.join(PROJECT, "public", "models")
PUBLIC_IMAGES = os.path.join(PROJECT, "public", "images")


def script_args():
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


def srgb(r, g, b):
    """sRGB 0-1 triplet -> linear RGBA (vertex colours and glTF are linear)."""
    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (lin(r), lin(g), lin(b), 1.0)


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(len(a)))


def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def mesh_object(name, verts, faces, colors=None, uvs=None):
    """Create a smooth-shaded mesh object, optionally with a per-vertex 'Col' attribute
    and per-face-corner UVs (see lofted_uvs)."""
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    if colors is not None:
        set_colors(obj, colors)
    if uvs is not None:
        layer = mesh.uv_layers.new(name="UV")
        layer.data.foreach_set("uv", [v for uv in uvs for v in uv])
    return obj


def set_colors(obj, colors):
    """Write linear RGBA per vertex into the 'Col' attribute used by every SNUGDOG material."""
    mesh = obj.data
    attr = mesh.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    attr.data.foreach_set("color", [c for rgba in colors for c in rgba])
    mesh.color_attributes.active_color = attr
    mesh.color_attributes.render_color_index = 0


def lofted_surface(start, rings, end):
    """Rings (equal length, closed in v) capped by a pole point at each end -> verts, faces."""
    nv = len(rings[0])
    verts = [start]
    for ring in rings:
        verts.extend(ring)
    verts.append(end)
    faces = []
    for j in range(nv):
        faces.append((0, 1 + (j + 1) % nv, 1 + j))
    for i in range(len(rings) - 1):
        a, b = 1 + i * nv, 1 + (i + 1) * nv
        for j in range(nv):
            k = (j + 1) % nv
            faces.append((a + j, a + k, b + k, b + j))
    last, tip = 1 + (len(rings) - 1) * nv, len(verts) - 1
    for j in range(nv):
        faces.append((last + j, last + (j + 1) % nv, tip))
    return verts, faces


def lofted_uvs(ring_count, nv):
    """Face-corner UVs matching lofted_surface: u runs along the loft, v around it.
    The seam is handled per corner, so the closed surface unwraps to one clean rectangle."""
    def u(i):
        return (i + 1) / (ring_count + 1)

    uvs = []
    for j in range(nv):
        uvs += [(0.0, (j + 0.5) / nv), (u(0), (j + 1) / nv), (u(0), j / nv)]
    for i in range(ring_count - 1):
        for j in range(nv):
            uvs += [(u(i), j / nv), (u(i), (j + 1) / nv), (u(i + 1), (j + 1) / nv), (u(i + 1), j / nv)]
    last = ring_count - 1
    for j in range(nv):
        uvs += [(u(last), j / nv), (u(last), (j + 1) / nv), (1.0, (j + 0.5) / nv)]
    return uvs


def vertex_color_material(name, roughness=0.5, coat=0.0, coat_roughness=0.1, bump=None, subsurface=0.0):
    """Principled material driven by the 'Col' vertex colour (exports cleanly to glTF).

    `bump` = (noise_scale, strength) adds render-only procedural relief for Cycles stills.
    """
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes["Principled BSDF"]
    col = nodes.new("ShaderNodeVertexColor")
    col.layer_name = "Col"
    links.new(col.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Coat Weight"].default_value = coat
    bsdf.inputs["Coat Roughness"].default_value = coat_roughness
    if subsurface:
        bsdf.inputs["Subsurface Weight"].default_value = subsurface
        bsdf.inputs["Subsurface Radius"].default_value = (0.05, 0.03, 0.015)
        bsdf.inputs["Subsurface Scale"].default_value = 0.2
    if bump:
        tex = nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = bump[0]
        tex.inputs["Detail"].default_value = 6
        node = nodes.new("ShaderNodeBump")
        node.inputs["Strength"].default_value = bump[1]
        links.new(tex.outputs["Fac"], node.inputs["Height"])
        links.new(node.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def area_light(name, location, target, power, size, color=(1, 1, 1), shadow=True):
    data = bpy.data.lights.new(name, "AREA")
    data.energy, data.size, data.color = power, size, color
    data.use_shadow = shadow
    obj = bpy.data.objects.new(name, data)
    obj.location = location
    bpy.context.scene.collection.objects.link(obj)
    look_at(obj, target)
    return obj


def studio(scene, target=(0, 0, 0), camera_dir=(-0.45, -1.0, 0.75), distance=5.2, lens=85, floor_z=0.0):
    """Soft daylight product studio: key/fill/rim softboxes, white world, shadow-catcher floor."""
    world = bpy.data.worlds.new("Studio")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (1, 1, 1, 1)
    bg.inputs["Strength"].default_value = 0.35
    scene.world = world

    # only the key casts a shadow, so the catcher holds one clean soft shadow
    area_light("Key", (-2.0, -1.2, 3.6), target, 300, 3.2, (1.0, 0.96, 0.91))
    area_light("Fill", (3.0, -2.6, 1.4), target, 60, 4.0, shadow=False)
    area_light("Rim", (1.4, 3.2, 2.0), target, 150, 2.0, shadow=False)

    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, floor_z))
    floor = bpy.context.active_object
    floor.name = "ShadowCatcher"
    floor.is_shadow_catcher = True

    cam_data = bpy.data.cameras.new("Camera")
    cam_data.lens = lens
    cam = bpy.data.objects.new("Camera", cam_data)
    cam.location = Vector(target) + Vector(camera_dir).normalized() * distance
    scene.collection.objects.link(cam)
    look_at(cam, target)
    scene.camera = cam
    return cam


def configure_cycles(scene, width, height, samples=128):
    scene.render.engine = "CYCLES"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.render.film_transparent = True
    scene.render.resolution_x, scene.render.resolution_y = width, height
    scene.render.resolution_percentage = 100
    for attr, value in (("view_transform", "Standard"), ("look", "Medium High Contrast")):
        try:
            setattr(scene.view_settings, attr, value)
        except TypeError:
            print(f"[snugdog] view setting {attr}={value!r} unavailable, keeping default")
    scene.view_settings.exposure = -0.35
    use_gpu(scene)


def use_gpu(scene):
    """Pick the best available Cycles GPU backend, falling back to CPU."""
    prefs = bpy.context.preferences.addons["cycles"].preferences
    scene.cycles.device = "CPU"
    for backend in ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"):
        try:
            prefs.compute_device_type = backend
            prefs.get_devices()
            gpus = [d for d in prefs.devices if d.type == backend]
            if gpus:
                for d in prefs.devices:
                    d.use = d.type == backend
                scene.cycles.device = "GPU"
                print(f"[snugdog] Cycles device: {backend}")
                break
        except Exception:
            continue


def clean_cutout(src, dst, quality=90, floor=0.05, edge=0.10):
    """Tidy a shadow-catcher render for use as a cutout on the paper background.

    Removes the faint alpha haze the catcher picks up from ambient light and fades the
    soft shadow out before the frame edge, so the image never shows its rectangle.
    Opaque (food) pixels are left untouched.
    """
    import numpy as np

    img = bpy.data.images.load(src)
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(h, w, 4)
    alpha = px[..., 3]
    xs = np.linspace(0, 1, w)[None, :]
    ys = np.linspace(0, 1, h)[:, None]
    fade = np.clip(np.minimum(np.minimum(xs, 1 - xs), np.minimum(ys, 1 - ys)) / edge, 0, 1)
    fade = fade * fade * (3 - 2 * fade)
    cleaned = np.clip((alpha - floor) / (1 - floor), 0, 1) * fade
    px[..., 3] = np.where(alpha < 0.995, cleaned, alpha)
    img.pixels.foreach_set(px.ravel())
    img.filepath_raw = dst
    img.file_format = "WEBP"
    img.save(quality=quality)
    bpy.data.images.remove(img)


def render_still(scene, name, quality=90, publish=True, out_dir=None):
    """Render a PNG master to <out_dir or assets/3d/renders>, then write the cleaned WebP
    cutout beside it and optionally copy that into public/images."""
    out_dir = out_dir or DIRS["renders"]
    master = os.path.join(out_dir, f"{name}.png")
    path = os.path.join(out_dir, f"{name}.webp")
    settings = scene.render.image_settings
    settings.file_format = "PNG"
    settings.color_mode = "RGBA"
    scene.render.filepath = master
    bpy.ops.render.render(write_still=True)
    clean_cutout(master, path, quality=quality)
    if publish:
        os.makedirs(PUBLIC_IMAGES, exist_ok=True)
        shutil.copy2(path, PUBLIC_IMAGES)
    print(f"[snugdog] rendered {path}")
    return path


def export_glb(name, objects, draco=True, publish=True, out_dir=None, **overrides):
    """Export the given objects to <out_dir or assets/3d/glb>/<name>.glb; optionally copy
    into public/models. Extra keyword arguments are passed to the glTF exporter (e.g. animations)."""
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    path = os.path.join(out_dir or DIRS["glb"], f"{name}.glb")
    wanted = dict(
        filepath=path,
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_cameras=False,
        export_lights=False,
        export_animations=False,
        # vertex colours ship only for materials that read them (baked ones use textures)
        export_vertex_color="MATERIAL",
        export_image_format="WEBP",
        export_image_quality=86,
        export_all_vertex_colors=False,
        export_draco_mesh_compression_enable=draco,
        export_draco_mesh_compression_level=6,
        export_draco_position_quantization=14,
        export_draco_normal_quantization=10,
        export_draco_color_quantization=10,
    )
    wanted.update(overrides)
    # exporter options shift between Blender versions; pass only what this build knows
    known = bpy.ops.export_scene.gltf.get_rna_type().properties.keys()
    bpy.ops.export_scene.gltf(**{k: v for k, v in wanted.items() if k in known})
    if publish:
        os.makedirs(PUBLIC_MODELS, exist_ok=True)
        shutil.copy2(path, PUBLIC_MODELS)
    print(f"[snugdog] exported {path} ({os.path.getsize(path) / 1024:.0f} KB)")
    return path


def save_blend(name):
    path = os.path.join(DIRS["source"], f"{name}.blend")
    bpy.ops.wm.save_as_mainfile(filepath=path, compress=True)
    print(f"[snugdog] saved {path}")
    return path
