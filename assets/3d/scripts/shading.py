"""Procedural shading + texture baking for the SNUGDOG asset pipeline.

Materials are authored as procedural node graphs (used directly by Cycles stills),
then baked to albedo / normal / ORM maps so the realtime GLB carries the same detail.
"""
import os

import bpy
import numpy as np

import common as c


class Graph:
    """Tiny builder so shader maths reads like expressions. Values may be floats or sockets."""

    def __init__(self, material):
        self.mat = material
        self.nt = material.node_tree
        self.bsdf = self.nt.nodes["Principled BSDF"]
        self.out = next(n for n in self.nt.nodes if n.type == "OUTPUT_MATERIAL")
        self.coords = self.nt.nodes.new("ShaderNodeTexCoord").outputs["Object"]

    def _set(self, socket, value):
        if isinstance(value, bpy.types.NodeSocket):
            self.nt.links.new(value, socket)
        else:
            socket.default_value = value

    def math(self, op, a, b=0.0, clamp=False):
        node = self.nt.nodes.new("ShaderNodeMath")
        node.operation, node.use_clamp = op, clamp
        self._set(node.inputs[0], a)
        self._set(node.inputs[1], b)
        return node.outputs[0]

    def add(self, a, b):
        return self.math("ADD", a, b)

    def mul(self, a, b):
        return self.math("MULTIPLY", a, b)

    def step(self, x, lo, hi, out_lo=0.0, out_hi=1.0):
        """Smoothstep remap of x from [lo, hi] to [out_lo, out_hi]."""
        node = self.nt.nodes.new("ShaderNodeMapRange")
        node.interpolation_type = "SMOOTHSTEP"
        for name, value in (("Value", x), ("From Min", lo), ("From Max", hi), ("To Min", out_lo), ("To Max", out_hi)):
            self._set(node.inputs[name], value)
        return node.outputs["Result"]

    def mix(self, fac, a, b, blend="MIX"):
        """Colour mix; a/b are RGBA tuples or sockets."""
        node = self.nt.nodes.new("ShaderNodeMix")
        node.data_type, node.blend_type, node.clamp_factor = "RGBA", blend, True
        self._set(node.inputs[0], fac)
        self._set(node.inputs[6], a)
        self._set(node.inputs[7], b)
        return node.outputs[2]

    def vector(self, scale=(1, 1, 1)):
        """Object coordinates, optionally stretched (for streaks / grain direction)."""
        if tuple(scale) == (1, 1, 1):
            return self.coords
        node = self.nt.nodes.new("ShaderNodeMapping")
        node.inputs["Scale"].default_value = scale
        self.nt.links.new(self.coords, node.inputs["Vector"])
        return node.outputs["Vector"]

    def noise(self, scale, detail=4.0, roughness=0.55, stretch=(1, 1, 1)):
        node = self.nt.nodes.new("ShaderNodeTexNoise")
        self.nt.links.new(self.vector(stretch), node.inputs["Vector"])
        node.inputs["Scale"].default_value = scale
        node.inputs["Detail"].default_value = detail
        node.inputs["Roughness"].default_value = roughness
        return node.outputs["Fac"]

    def cells(self, scale, feature="F1", randomness=1.0, stretch=(1, 1, 1)):
        node = self.nt.nodes.new("ShaderNodeTexVoronoi")
        node.feature = feature
        self.nt.links.new(self.vector(stretch), node.inputs["Vector"])
        node.inputs["Scale"].default_value = scale
        node.inputs["Randomness"].default_value = randomness
        return node.outputs["Distance"]

    def axis(self, name):
        """One object-space coordinate ('X', 'Y' or 'Z') as a socket."""
        if not hasattr(self, "_xyz"):
            self._xyz = self.nt.nodes.new("ShaderNodeSeparateXYZ")
            self.nt.links.new(self.coords, self._xyz.inputs[0])
        return self._xyz.outputs[name]

    def vertex_color(self):
        """('Col' colour socket, alpha socket). Alpha carries a per-asset mask."""
        node = self.nt.nodes.new("ShaderNodeVertexColor")
        node.layer_name = "Col"
        return node.outputs["Color"], node.outputs["Alpha"]

    def finish(self, color, roughness, height=None, bump_strength=0.3, bump_distance=0.01):
        """Wire the graph into the BSDF and remember the sockets for baking."""
        links = self.nt.links
        self._set(self.bsdf.inputs["Base Color"], color)
        self._set(self.bsdf.inputs["Roughness"], roughness)
        if height is not None:
            bump = self.nt.nodes.new("ShaderNodeBump")
            bump.inputs["Strength"].default_value = bump_strength
            bump.inputs["Distance"].default_value = bump_distance
            links.new(height, bump.inputs["Height"])
            links.new(bump.outputs["Normal"], self.bsdf.inputs["Normal"])
        self.mat["snug_color"] = color.node.name + "|" + color.identifier
        self.mat["snug_rough"] = roughness.node.name + "|" + roughness.identifier
        return self.mat


def principled(name, coat=0.0, coat_roughness=0.1, subsurface=0.0, sheen=0.0, sheen_roughness=0.5, sheen_tint=(1, 1, 1, 1)):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Coat Weight"].default_value = coat
    bsdf.inputs["Coat Roughness"].default_value = coat_roughness
    bsdf.inputs["Sheen Weight"].default_value = sheen
    bsdf.inputs["Sheen Roughness"].default_value = sheen_roughness
    bsdf.inputs["Sheen Tint"].default_value = sheen_tint
    if subsurface:
        bsdf.inputs["Subsurface Weight"].default_value = subsurface
        bsdf.inputs["Subsurface Radius"].default_value = (0.05, 0.03, 0.015)
        bsdf.inputs["Subsurface Scale"].default_value = 0.2
    return mat


# ---------------------------------------------------------------- baking
def _socket(mat, key):
    node_name, identifier = mat[key].split("|")
    node = mat.node_tree.nodes[node_name]
    return next(s for s in node.outputs if s.identifier == identifier)


def _pixels(image):
    w, h = image.size
    px = np.empty(w * h * 4, dtype=np.float32)
    image.pixels.foreach_get(px)
    return px.reshape(h, w, 4)


def _save(image, path):
    image.filepath_raw = path
    image.file_format = "PNG"
    image.save()


def _bake(obj, mat, image, kind, samples, emit_socket=None):
    scene = bpy.context.scene
    nt = mat.node_tree
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    bsdf = nt.nodes["Principled BSDF"]
    target = nt.nodes.new("ShaderNodeTexImage")
    target.image = image
    for node in nt.nodes:
        node.select = False
    target.select = True
    nt.nodes.active = target

    emission = None
    if emit_socket is not None:
        emission = nt.nodes.new("ShaderNodeEmission")
        nt.links.new(emit_socket, emission.inputs["Color"])
        nt.links.new(emission.outputs[0], out.inputs["Surface"])

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    scene.cycles.samples = samples
    bpy.ops.object.bake(type=kind, margin=16, use_clear=True)

    if emission is not None:
        nt.nodes.remove(emission)
        nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    nt.nodes.remove(target)


def bake_pbr(obj, tex_name, size=(1024, 1024), detail_size=None, ao_strength=0.8, ao_hidden=(), out_dir=None):
    """Bake obj's procedural material to <tex_name>_albedo / _normal / _orm PNGs.

    Contact shadows (ambient occlusion from every visible object, minus `ao_hidden`)
    are multiplied into the albedo so realtime gets grounded contact points for free.
    Returns the three images.
    """
    out_dir = out_dir or c.DIRS["textures"]
    os.makedirs(out_dir, exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    c.use_gpu(scene)
    mat = obj.data.materials[0]
    detail_size = detail_size or size

    def new(suffix, dims, srgb):
        img = bpy.data.images.new(f"{tex_name}_{suffix}", dims[0], dims[1], alpha=False)
        img.colorspace_settings.name = "sRGB" if srgb else "Non-Color"
        return img

    albedo = new("albedo", size, True)
    _bake(obj, mat, albedo, "EMIT", 4, emit_socket=_socket(mat, "snug_color"))

    rough = new("rough", detail_size, False)
    _bake(obj, mat, rough, "EMIT", 4, emit_socket=_socket(mat, "snug_rough"))

    normal = new("normal", detail_size, False)
    scene.render.bake.normal_space = "TANGENT"
    _bake(obj, mat, normal, "NORMAL", 8)

    ao = new("ao", detail_size, False)
    for other in ao_hidden:
        other.hide_render = True
    _bake(obj, mat, ao, "AO", 96)
    for other in ao_hidden:
        other.hide_render = False

    # fold contact shadows into the albedo
    ao_px = _pixels(ao)[..., 0]
    if detail_size != size:
        ys = (np.arange(size[1]) * detail_size[1] // size[1])[:, None]
        xs = (np.arange(size[0]) * detail_size[0] // size[0])[None, :]
        ao_full = ao_px[ys, xs]
    else:
        ao_full = ao_px
    alb = _pixels(albedo)
    alb[..., :3] *= (1 - ao_strength + ao_strength * ao_full)[..., None]
    albedo.pixels.foreach_set(alb.ravel())

    # glTF packing: R = occlusion, G = roughness, B = metallic
    orm = new("orm", detail_size, False)
    packed = np.ones((detail_size[1], detail_size[0], 4), dtype=np.float32)
    packed[..., 0] = ao_px
    packed[..., 1] = _pixels(rough)[..., 0]
    packed[..., 2] = 0.0
    orm.pixels.foreach_set(packed.ravel())

    for img, suffix in ((albedo, "albedo"), (normal, "normal"), (orm, "orm")):
        _save(img, os.path.join(out_dir, f"{tex_name}_{suffix}.png"))
    bpy.data.images.remove(rough)
    bpy.data.images.remove(ao)
    print(f"[snugdog] baked {tex_name} ({size[0]}x{size[1]} albedo, {detail_size[0]}x{detail_size[1]} detail)")
    return albedo, normal, orm


def baked_material(source, albedo, normal, orm):
    """Realtime twin of a procedural material: same lobes, textures instead of nodes."""
    mat = bpy.data.materials.new(source.name + "_Baked")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    src = source.node_tree.nodes["Principled BSDF"]
    for name in ("Coat Weight", "Coat Roughness", "Sheen Weight", "Sheen Roughness", "Sheen Tint"):
        bsdf.inputs[name].default_value = src.inputs[name].default_value

    def tex(image):
        node = nt.nodes.new("ShaderNodeTexImage")
        node.image = image
        return node

    nt.links.new(tex(albedo).outputs["Color"], bsdf.inputs["Base Color"])
    nmap = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tex(normal).outputs["Color"], nmap.inputs["Color"])
    nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    split = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(tex(orm).outputs["Color"], split.inputs["Color"])
    nt.links.new(split.outputs["Green"], bsdf.inputs["Roughness"])
    nt.links.new(split.outputs["Blue"], bsdf.inputs["Metallic"])
    return mat


class BakedSwap:
    """Context manager: export with baked materials, then restore the procedural ones."""

    def __init__(self, pairs):
        self.pairs = pairs  # [(object, baked_material)]
        self.original = []

    def __enter__(self):
        for obj, baked in self.pairs:
            self.original.append(obj.data.materials[0])
            obj.data.materials[0] = baked
        return self

    def __exit__(self, *exc):
        for (obj, _), mat in zip(self.pairs, self.original):
            obj.data.materials[0] = mat
        return False
