"""Geometry for the SNUGDOG dachshund: volumes -> fused skin -> clean quads, plus the
rigid parts (eyes, lids, nose, ears)."""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import anatomy as an  # noqa: E402
import common as c  # noqa: E402


# ---------------------------------------------------------------- primitives
def _catmull(p0, p1, p2, p3, t):
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t)


def resample(path, samples):
    """Smoothly resample [(centre, r_side, r_up), ...] to `samples` stations."""
    pts = [path[0]] + list(path) + [path[-1]]
    out = []
    spans = len(path) - 1
    for i in range(samples):
        f = i / (samples - 1) * spans
        k = min(int(f), spans - 1)
        t = f - k
        a, b, cc, d = pts[k], pts[k + 1], pts[k + 2], pts[k + 3]
        out.append(tuple(_catmull(a[j], b[j], cc[j], d[j], t) for j in range(3)))
    return out


def tube(name, path, nv=20, samples=24, caps=4, side_hint=None):
    """Loft an elliptical section along a path, closed with rounded caps."""
    stations = resample(path, samples)
    centres = [s[0] for s in stations]
    rings = []

    def frame(i):
        t = (centres[min(i + 1, len(centres) - 1)] - centres[max(i - 1, 0)]).normalized()
        hint = side_hint or Vector((0, 1, 0))
        side = hint - t * hint.dot(t)
        if side.length < 1e-4:
            side = Vector((1, 0, 0)) - t * t.x
        side.normalize()
        return t, side, t.cross(side)

    def ring(centre, side, up, rs, ru):
        return [centre + side * math.cos(a) * rs + up * math.sin(a) * ru for a in (math.tau * j / nv for j in range(nv))]

    t0, s0, u0 = frame(0)
    c0, rs0, ru0 = stations[0]
    reach0 = (rs0 + ru0) / 2
    for k in range(1, caps + 1):
        a = k / (caps + 1) * math.pi / 2
        rings.append(ring(c0 - t0 * reach0 * math.cos(a), s0, u0, rs0 * math.sin(a), ru0 * math.sin(a)))
    for i, (centre, rs, ru) in enumerate(stations):
        _, s, u = frame(i)
        rings.append(ring(centre, s, u, rs, ru))
    t1, s1, u1 = frame(len(stations) - 1)
    c1, rs1, ru1 = stations[-1]
    reach1 = (rs1 + ru1) / 2
    for k in range(caps, 0, -1):
        a = k / (caps + 1) * math.pi / 2
        rings.append(ring(c1 + t1 * reach1 * math.cos(a), s1, u1, rs1 * math.sin(a), ru1 * math.sin(a)))
    verts, faces = c.lofted_surface(c0 - t0 * reach0, rings, c1 + t1 * reach1)
    return c.mesh_object(name, verts, faces)


def blob(name, centre, radii, segments=28, rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=1.0, location=centre)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = radii
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.shade_smooth()
    return obj


def _only(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def apply_modifier(obj, mod):
    _only(obj)
    bpy.ops.object.modifier_apply(modifier=mod.name)


def join(objects, name):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    objects[0].name = name
    return objects[0]


# ---------------------------------------------------------------- skin
def build_volumes():
    """All the overlapping volumes that get fused into one skin."""
    parts = [
        tube("v_body", an.BODY, nv=28, samples=40),
        tube("v_neck", an.NECK, nv=22, samples=14),
        tube("v_muzzle", an.MUZZLE, nv=22, samples=18),
        tube("v_tail", an.TAIL, nv=14, samples=22),
        blob("v_head", *an.HEAD),
        blob("v_prosternum", *an.PROSTERNUM),
        blob("v_jaw", *an.JAW),
    ]
    for side in (1, -1):
        parts.append(tube(f"v_leg_f{side}", an.front_leg(side), nv=16, samples=14))
        parts.append(tube(f"v_leg_h{side}", an.hind_leg(side), nv=16, samples=14))
        for key, (centre, radii) in an.paired(side).items():
            parts.append(blob(f"v_{key}{side}", centre, radii))
    return parts


def fuse(parts, voxel=0.03, smooth=8):
    """Union the volumes into one watertight surface with soft, organic transitions."""
    obj = join(parts, "Skin")
    remesh = obj.modifiers.new("Fuse", "REMESH")
    remesh.mode = "VOXEL"
    remesh.voxel_size = voxel
    remesh.use_smooth_shade = True
    apply_modifier(obj, remesh)
    soften = obj.modifiers.new("Soften", "SMOOTH")
    soften.factor = 0.75
    soften.iterations = smooth
    apply_modifier(obj, soften)
    return obj


def retopologise(obj, faces=8000):
    """Even quad flow for clean deformation; falls back to decimation if QuadriFlow fails."""
    _only(obj)
    try:
        bpy.ops.object.quadriflow_remesh(mode="FACES", target_faces=faces, seed=3, use_mesh_symmetry=False,
                                         use_preserve_sharp=False, use_preserve_boundary=False, smooth_normals=True)
        print(f"[snugdog] quadriflow -> {len(obj.data.polygons)} faces")
    except RuntimeError as err:
        print(f"[snugdog] quadriflow failed ({err}); decimating instead")
        dec = obj.modifiers.new("Decimate", "DECIMATE")
        dec.ratio = faces * 2 / max(len(obj.data.polygons), 1)
        apply_modifier(obj, dec)
    bpy.ops.object.shade_smooth()
    return obj


# ---------------------------------------------------------------- ears
def build_ear(side):
    root = an.EAR_ROOT
    w, t = an.EAR_WIDTH, an.EAR_THICKNESS
    y = lambda v: v * side  # noqa: E731
    path = [
        (Vector((root.x - 0.02, y(root.y - 0.06), root.z + 0.02)), 0.13, t * 1.6),
        (Vector((root.x, y(root.y + 0.05), root.z - 0.16)), w * 0.82, t * 1.2),
        (Vector((root.x + 0.05, y(root.y + 0.08), root.z - 0.46)), w, t),
        (Vector((root.x + 0.10, y(root.y + 0.06), root.z - 0.76)), w * 0.92, t),
        (Vector((root.x + 0.13, y(root.y + 0.03), root.z - an.EAR_LENGTH)), w * 0.50, t),
    ]
    ear = tube(f"Ear_{'L' if side > 0 else 'R'}", path, nv=18, samples=20, caps=3, side_hint=Vector((1, 0, 0)))
    return ear


# ---------------------------------------------------------------- face parts
def _orient(obj, centre, forward):
    """Local +X looks along `forward`, local +Z stays as upright as possible."""
    x = forward.normalized()
    y = Vector((0, 0, 1)).cross(x).normalized()
    z = x.cross(y)
    obj.matrix_world = Matrix.Translation(centre) @ Matrix((x, y, z)).transposed().to_4x4()


def surface_point(skin, origin, direction):
    """First hit on the skin along a ray (world = object space)."""
    hit, location, normal, _ = skin.ray_cast(origin, direction.normalized())
    if not hit:
        raise RuntimeError(f"ray from {tuple(origin)} missed the skin")
    return location, normal


def seat_eye(skin, side, protrude=0.26):
    """Eye centre placed so a fixed share of the eyeball clears the skull surface."""
    forward = an.eye_forward(side)
    hit, _ = surface_point(skin, an.eye_centre(side) + forward * 1.5, -forward)
    return hit - forward * an.EYE_RADIUS * (1 - 2 * protrude)


def build_eye(side, centre):
    """Eyeball with iris and pupil painted by angle from the optical axis (local +X)."""
    r = an.EYE_RADIUS
    nu, nv = 28, 32
    rings, colors = [], []
    pupil = c.srgb(0.012, 0.010, 0.010)
    iris_in, iris_out = c.srgb(0.30, 0.15, 0.06), c.srgb(0.10, 0.05, 0.025)
    limbus, sclera = c.srgb(0.04, 0.025, 0.02), c.srgb(0.80, 0.76, 0.70)

    def shade(angle):
        deg = math.degrees(angle)
        if deg < 17:
            return pupil
        if deg < 50:
            return c.mix(c.mix(iris_in, iris_out, (deg - 17) / 33), limbus, c.smoothstep(44, 50, deg))
        return c.mix(limbus, sclera, c.smoothstep(50, 58, deg))

    for i in range(1, nu):
        angle = math.pi * i / nu
        ring = [Vector((math.cos(angle), math.sin(angle) * math.cos(a), math.sin(angle) * math.sin(a))) * r
                for a in (math.tau * j / nv for j in range(nv))]
        rings.append(ring)
        colors += [shade(angle)] * nv
    verts, faces = c.lofted_surface(Vector((r, 0, 0)), rings, Vector((-r, 0, 0)))
    name = f"Eye_{'L' if side > 0 else 'R'}"
    eye = c.mesh_object(name, verts, faces, [pupil] + colors + [sclera])
    _orient(eye, centre, an.eye_forward(side))
    return eye


def build_lid(side, centre, upper=True, open_deg=24.0, tilt_deg=0.0):
    """Eyelid as a spherical shell around the eye. It pivots on the eye's lateral axis,
    so a blink is a single rotation. `open_deg` is where its edge rests above/below the gaze."""
    r = an.EYE_RADIUS * 1.05
    nu, nv = 14, 26
    verts, faces = [], []
    lo, hi = (open_deg, 172.0) if upper else (-172.0, -open_deg)
    for i in range(nu + 1):
        phi = math.radians(lo + (hi - lo) * i / nu)
        for j in range(nv + 1):
            psi = math.radians(-89 + 178 * j / nv)
            verts.append(Vector((math.cos(psi) * math.cos(phi), math.sin(psi), math.cos(psi) * math.sin(phi))) * r)
    for i in range(nu):
        for j in range(nv):
            a = i * (nv + 1) + j
            faces.append((a, a + 1, a + nv + 2, a + nv + 1))
    name = f"Lid_{'U' if upper else 'D'}_{'L' if side > 0 else 'R'}"
    lid = c.mesh_object(name, verts, faces)
    _orient(lid, centre, an.eye_forward(side))
    if tilt_deg:
        lid.matrix_world = lid.matrix_world @ Matrix.Rotation(math.radians(tilt_deg * side), 4, "X")
    solid = lid.modifiers.new("Thickness", "SOLIDIFY")
    solid.thickness = 0.009
    solid.offset = 1.0
    apply_modifier(lid, solid)
    bpy.ops.object.shade_smooth()
    return lid


def build_nose(skin):
    """Nose pad seated on the tip of the muzzle."""
    centre, radii = an.NOSE
    tip, _ = surface_point(skin, Vector((centre.x + 1.5, 0, centre.z)), Vector((-1, 0, 0)))
    return blob("Nose", Vector((tip.x + radii.x * 0.25, 0, centre.z)), radii, segments=24, rings=14)
