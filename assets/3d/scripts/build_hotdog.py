"""SNUGDOG hero hot dog: model -> material -> lighting -> camera -> GLB + still.

    node assets/3d/scripts/blender.mjs build_hotdog.py [-- --no-render] [--samples N]
    node assets/3d/scripts/blender.mjs build_hotdog.py -- --variant classic|reuben|garden|spicy

Outputs
    assets/3d/source/snugdog-hotdog.blend
    assets/3d/glb/snugdog-hotdog.glb      (copied to public/models)
    assets/3d/renders/snugdog-hotdog.webp (copied to public/images)

Everything is procedural and seeded, so the asset is reproducible. Bun and frank get
procedural materials (pores, browning, casing sheen) baked to albedo / normal / ORM
maps with contact shadows folded in; the small parts stay vertex-coloured. Nodes are
Bun / Sausage / Mustard / Seeds / Toppings so the web layer can address them separately.
Units: 1 = 10 cm, +X is the long axis.
"""
import math
import os
import random
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mathutils import Vector, noise  # noqa: E402

import common as c  # noqa: E402
import shading as sh  # noqa: E402

NAME = "snugdog-hotdog"
random.seed(7)

# Menu variants: the same bun and frank, dressed differently. Each is (sauce bright, sauce
# deep), (crumb light, crumb dark, count), (bits a, bits b, count). Rendered as stills only
# with --variant NAME; the realtime GLB is always The Classic.
VARIANTS = {
    "classic": (((0.98, 0.82, 0.12), (0.90, 0.68, 0.04)),  # yellow mustard, crispy onions, chives
                ((0.78, 0.50, 0.16), (0.52, 0.27, 0.07), 70), ((0.22, 0.45, 0.12), (0.45, 0.62, 0.20), 46)),
    "reuben": (((0.95, 0.60, 0.42), (0.86, 0.46, 0.30)),  # russian dressing, sauerkraut, pickle
               ((0.94, 0.91, 0.72), (0.82, 0.78, 0.52), 170), ((0.36, 0.44, 0.16), (0.52, 0.58, 0.26), 34)),
    "garden": (((0.97, 0.96, 0.90), (0.90, 0.88, 0.78)),  # herb yoghurt, tomato, cucumber and herbs
               ((0.82, 0.17, 0.10), (0.62, 0.10, 0.07), 80), ((0.24, 0.50, 0.14), (0.52, 0.70, 0.24), 100)),
    "spicy": (((0.80, 0.11, 0.05), (0.62, 0.06, 0.03)),  # sriracha, crispy shallots, jalapeno
              ((0.70, 0.38, 0.10), (0.40, 0.18, 0.05), 60), ((0.30, 0.55, 0.12), (0.52, 0.72, 0.22), 84)),
}
_args = c.script_args()
# "signature" is the hero dog (and the realtime GLB): loaded with roasted peppers, leaves
# and cream cheese, after the client's reference photos. It has no sauce squiggle.
VARIANT = _args[_args.index("--variant") + 1] if "--variant" in _args else "signature"
SAUCE, CRUMBS, BITS = VARIANTS.get(VARIANT, VARIANTS["classic"])

# ---------------------------------------------------------------- bun
BUN_L, BUN_W, BUN_H = 0.84, 0.40, 0.29
BUN_BASE_Z = -0.08  # ends taper towards this height so the base stays flat
CLEFT_WIDTH, CLEFT_DEPTH = 0.36, 0.80


def _bun_profile(samples=2000, power=0.625):
    """(x, scale) along the loaf, resampled by arc length so rings are evenly spaced."""
    pts = []
    for i in range(samples + 1):
        phi = -math.pi / 2 + math.pi * i / samples
        sp, cp = math.sin(phi), math.cos(phi)
        pts.append((BUN_L * math.copysign(abs(sp) ** power, sp), abs(cp) ** power))
    acc = [0.0]
    for a, b in zip(pts, pts[1:]):
        acc.append(acc[-1] + math.hypot(b[0] - a[0], (b[1] - a[1]) * BUN_W))
    return pts, acc


_BUN_PTS, _BUN_ACC = _bun_profile()


def bun_profile(f):
    """f in 0..1 along the loaf -> (x, cross-section scale)."""
    target = f * _BUN_ACC[-1]
    lo, hi = 0, len(_BUN_ACC) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if _BUN_ACC[mid] < target:
            lo = mid
        else:
            hi = mid
    span = _BUN_ACC[hi] - _BUN_ACC[lo] or 1.0
    t = (target - _BUN_ACC[lo]) / span
    a, b = _BUN_PTS[lo], _BUN_PTS[hi]
    return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t


def cleft(theta):
    """1 at the centre of the top split, falling to 0 on the lobes."""
    d = math.atan2(math.sin(theta - math.pi / 2), math.cos(theta - math.pi / 2))
    return math.exp(-((d / CLEFT_WIDTH) ** 2))


def bun_base(f, theta):
    x, s = bun_profile(f)
    co, si = math.cos(theta), math.sin(theta)
    y = BUN_W * math.copysign(abs(co) ** 0.85, co)
    z = BUN_H * math.copysign(abs(si) ** 0.85, si)
    if z < 0:
        z *= 0.72
    k = 1 - CLEFT_DEPTH * cleft(theta)
    return Vector((x, y * k * s, BUN_BASE_Z + (z * k - BUN_BASE_Z) * s))


def bun_point(f, theta):
    """Bun surface with bready lumps; returns (position, outward normal)."""
    p = bun_base(f, theta)
    e = 1e-3
    n = (bun_base(min(f + e, 1), theta) - bun_base(max(f - e, 0), theta)).cross(
        bun_base(f, theta + e) - bun_base(f, theta - e)
    )
    if n.length < 1e-9:
        n = Vector((math.copysign(1, p.x), 0, 0))
    n.normalize()
    if n.dot(Vector((0, p.y, p.z - BUN_BASE_Z))) < 0 and cleft(theta) < 0.5:
        n = -n
    lumps = noise.noise(p * 5.0) * 0.012 + noise.noise(p * 21.0) * 0.003
    return p + n * lumps * (1 - 0.7 * cleft(theta)), n


def build_bun(nu=112, nv=96):
    rings, clefts = [], []
    for i in range(1, nu):
        ring = []
        for j in range(nv):
            theta = 2 * math.pi * j / nv
            ring.append(bun_point(i / nu, theta)[0])
            clefts.append(cleft(theta))
        rings.append(ring)
    verts, faces = c.lofted_surface(bun_base(0, 0), rings, bun_base(1, 0))
    clefts = [0.0] + clefts + [0.0]
    obj = c.mesh_object("Bun", verts, faces, uvs=c.lofted_uvs(len(rings), nv))

    crust_deep = c.srgb(0.40, 0.17, 0.05)
    crust = c.srgb(0.60, 0.30, 0.09)
    side = c.srgb(0.78, 0.47, 0.18)
    scorch = c.srgb(0.16, 0.07, 0.03)
    bottom = c.srgb(0.87, 0.67, 0.40)
    crumb = c.srgb(0.96, 0.88, 0.70)
    colors = []
    for v, g in zip(obj.data.vertices, clefts):
        up = v.normal.z
        mottle = noise.noise(v.co * 9.0) * 0.5 + 0.5
        col = c.mix(bottom, side, c.smoothstep(-0.75, -0.1, up))
        col = c.mix(col, crust, c.smoothstep(-0.1, 0.5, up + (mottle - 0.5) * 0.3))
        col = c.mix(col, crust_deep, c.smoothstep(0.5, 1.0, up) * (0.5 + 0.5 * mottle))
        # the lip of the split sat on the grill: a dark toasted edge
        col = c.mix(col, scorch, 0.7 * c.smoothstep(0.06, 0.16, g) * (1 - c.smoothstep(0.2, 0.3, g)) * (0.5 + 0.5 * mottle))
        inside = c.smoothstep(0.22, 0.6, g)
        col = c.mix(col, crumb, inside)
        colors.append(col[:3] + (inside,))  # alpha = crumb mask for the material
    c.set_colors(obj, colors)
    obj.data.materials.append(bun_material())
    return obj


def bun_material():
    """Egg-washed crust with uneven oven browning and fine pores; open crumb inside the split."""
    g = sh.Graph(sh.principled("BunCrust", coat=0.3, coat_roughness=0.22, subsurface=0.1))
    col, crumb = g.vertex_color()
    # crust: darker patches where the oven caught it, pale flecks, scattered pores
    patches = g.step(g.noise(6, detail=5), 0.45, 0.8, 0, 0.34)
    crust = g.mix(patches, col, c.srgb(0.47, 0.23, 0.08))
    grain = g.noise(60, detail=3)
    crust = g.mix(g.step(grain, 0.4, 0.8, 0, 0.2), crust, c.srgb(0.93, 0.74, 0.42))
    pores = g.mul(g.step(g.cells(150), 0.0, 0.2, 1, 0), g.step(g.noise(38), 0.5, 0.68))
    crust = g.mix(g.mul(pores, 0.4), crust, c.srgb(0.30, 0.13, 0.04))
    # crumb: cream with shadowed air pockets
    holes = g.step(g.cells(46), 0.12, 0.42, 1, 0)
    inside = g.mix(g.mul(holes, 0.45), col, c.srgb(0.74, 0.60, 0.40))
    color = g.mix(crumb, crust, inside)

    crust_h = g.add(g.add(g.mul(g.noise(16), 0.5), g.mul(grain, 0.25)), g.mul(pores, -0.7))
    height = g.add(g.mul(crust_h, g.math("SUBTRACT", 1.0, crumb)), g.mul(g.mul(holes, -1.0), crumb))
    crust_r = g.add(g.add(0.36, g.mul(g.noise(22), 0.3)), g.mul(pores, 0.2))
    rough = g.math("ADD", crust_r, g.mul(crumb, 0.4), clamp=True)
    return g.finish(color, rough, height, bump_strength=0.5, bump_distance=0.012)


# ---------------------------------------------------------------- sausage
SAUS_L, SAUS_R, SAUS_Z, SAUS_BOW = 1.03, 0.105, 0.15, 0.03  # sticks well out of both ends


def sausage_axis_z(x):
    return SAUS_Z + SAUS_BOW * (x / SAUS_L) ** 2


def build_sausage(body=200, cap=10, nv=72):
    profile = []
    straight = SAUS_L - SAUS_R
    for a in range(1, cap + 1):
        alpha = (a / cap) * math.pi / 2
        profile.append((-straight - SAUS_R * math.cos(alpha), SAUS_R * math.sin(alpha)))
    for b in range(1, body):
        profile.append((-straight + 2 * straight * b / body, SAUS_R))
    profile += [(-x, r) for x, r in reversed(profile[:cap])]

    rings, thetas = [], []
    for x, r in profile:
        ring = []
        for j in range(nv):
            theta = 2 * math.pi * j / nv
            p = Vector((x, r * math.cos(theta), sausage_axis_z(x) + r * math.sin(theta)))
            # faint skin wrinkles
            ring.append(p * (1 + noise.noise(p * 14.0) * 0.006))
            thetas.append(theta)
        rings.append(ring)
    verts, faces = c.lofted_surface((-SAUS_L, 0, sausage_axis_z(SAUS_L)), rings, (SAUS_L, 0, sausage_axis_z(SAUS_L)))
    thetas = [0.0] + thetas + [0.0]

    skin = c.srgb(0.60, 0.15, 0.09)
    skin_dark = c.srgb(0.34, 0.08, 0.05)
    char = c.srgb(0.08, 0.035, 0.025)
    colors = []
    for p, theta in zip(verts, thetas):
        p = Vector(p)
        browning = noise.noise(p * 5.0) * 0.5 + 0.5 + noise.noise(p * 19.0) * 0.15
        col = c.mix(skin, skin_dark, c.smoothstep(0.3, 0.8, browning))
        col = c.mix(col, skin_dark, c.smoothstep(0.72, 0.9, abs(p.x)) * 0.6)
        # diagonal grill marks across the top
        stripe = ((p.x + (theta - math.pi / 2) * SAUS_R * 0.9) / 0.19) % 1.0
        mark = c.smoothstep(0.0, 0.06, stripe) * (1 - c.smoothstep(0.10, 0.16, stripe))
        seared = mark * c.smoothstep(0.2, 0.75, math.sin(theta))
        col = c.mix(col, char, seared * (0.8 + 0.2 * noise.noise(p * 30.0)))
        # blistered patches where the grill caught it between the bars
        blister = c.smoothstep(0.62, 0.8, noise.noise(p * 11.0) * 0.5 + 0.5)
        col = c.mix(col, char, 0.55 * blister)
        colors.append(col[:3] + (seared,))  # alpha = grill mask for the material
    obj = c.mesh_object("Sausage", verts, faces, colors, uvs=c.lofted_uvs(len(rings), nv))
    obj.data.materials.append(sausage_material())
    return obj


def sausage_material():
    """Natural casing: blotchy browning, fine flecks, lengthwise wrinkles, a wet sheen that
    breaks up where the grill dried it."""
    g = sh.Graph(sh.principled("SausageSkin", coat=0.4, coat_roughness=0.16, subsurface=0.08))
    col, grill = g.vertex_color()
    blotch = g.step(g.noise(9, detail=5), 0.35, 0.7, 0, 0.55)
    color = g.mix(blotch, col, c.srgb(0.36, 0.10, 0.05))
    flecks = g.step(g.noise(240, detail=2), 0.55, 0.8, 0, 0.18)
    color = g.mix(flecks, color, c.srgb(0.74, 0.36, 0.22))
    wrinkles = g.noise(30, detail=3, stretch=(0.12, 1, 1))
    height = g.add(g.add(g.mul(g.noise(20), 0.4), g.mul(wrinkles, 0.35)), g.mul(grill, -0.5))
    rough = g.math("ADD", g.add(0.26, g.mul(g.noise(15), 0.3)), g.mul(grill, 0.35), clamp=True)
    return g.finish(color, rough, height, bump_strength=0.4, bump_distance=0.008)


# ---------------------------------------------------------------- mustard
def build_mustard(steps=420, nv=10, radius=0.021, span=0.66, amp=0.07, wave=0.20, cap=6):
    path = []
    for i in range(steps + 1):
        x = -span + 2 * span * i / steps
        # a hand squeeze: the swing and rhythm wander
        wobble = 1 + 0.28 * noise.noise(Vector((x * 3.1, 7.7, 0)))
        y = amp * wobble * math.sin(2 * math.pi * x / wave + 0.7 * noise.noise(Vector((x * 2.0, 1.3, 5.0))))
        z = sausage_axis_z(x) + math.sqrt(SAUS_R ** 2 - y ** 2) + radius * 0.35
        path.append(Vector((x, y, z)))

    rings = []
    up = Vector((0, 0, 1))
    for i in range(1, steps):
        tangent = (path[i + 1] - path[i - 1]).normalized()
        sideways = tangent.cross(up).normalized()
        upward = sideways.cross(tangent)
        end = min(i, steps - i) / cap
        r = radius * (1 + 0.3 * noise.noise(Vector((path[i].x * 8.0, 0, 3.1))))
        if steps - i < steps * 0.04:
            r *= 1.25  # the little blob where the squeeze stops
        if end < 1:
            r *= math.sqrt(1 - (1 - end) ** 2)
        rings.append([
            path[i] + sideways * math.cos(a) * r * 1.15 + upward * math.sin(a) * r * 0.85
            for a in (2 * math.pi * j / nv for j in range(nv))
        ])
    verts, faces = c.lofted_surface(path[0], rings, path[-1])
    bright, deep = c.srgb(*SAUCE[0]), c.srgb(*SAUCE[1])
    colors = [c.mix(bright, deep, noise.noise(Vector(p) * 8.0) * 0.5 + 0.5) for p in verts]
    obj = c.mesh_object("Mustard", verts, faces, colors)
    obj.data.materials.append(c.vertex_color_material("Mustard", roughness=0.26, coat=0.5, coat_roughness=0.1))
    return obj


# ---------------------------------------------------------------- scatter helpers
class Scatter:
    """Accumulates many small lofted pieces into one mesh (one draw call on the web)."""

    def __init__(self):
        self.verts, self.faces, self.colors = [], [], []

    def add(self, start, rings, end, color):
        sv, sf = c.lofted_surface(start, rings, end)
        base = len(self.verts)
        self.verts.extend(sv)
        self.faces.extend(tuple(base + i for i in face) for face in sf)
        self.colors.extend([color] * len(sv))

    def to_object(self, name, material):
        obj = c.mesh_object(name, self.verts, self.faces, self.colors)
        obj.data.materials.append(material)
        return obj


# ---------------------------------------------------------------- sesame seeds
def build_seeds(count=110, rings_n=5, nv=8):
    scatter = Scatter()
    pale, toasted = c.srgb(0.93, 0.83, 0.62), c.srgb(0.80, 0.63, 0.38)
    for _ in range(count):
        f = random.uniform(0.10, 0.90)
        theta = math.pi / 2 + random.choice((-1, 1)) * random.uniform(0.58, 1.30)
        p, n = bun_point(f, theta)
        spin = random.uniform(0, math.tau)
        ref = Vector((1, 0, 0)) if abs(n.x) < 0.9 else Vector((0, 1, 0))
        a = n.cross(ref).normalized()
        b = n.cross(a)
        long_axis = a * math.cos(spin) + b * math.sin(spin)
        short_axis = n.cross(long_axis)
        length, width, height = (random.uniform(0.9, 1.15) * d for d in (0.017, 0.009, 0.005))

        def at(u, ang):
            # teardrop: fatter at one end
            r = math.sin(math.pi * u) * (1.15 - 0.4 * u)
            return (p + n * 0.0015 + long_axis * (u - 0.5) * 2 * length
                    + short_axis * math.cos(ang) * r * width
                    + n * max(math.sin(ang), -0.2) * r * height)

        rings = [[at(i / (rings_n + 1), math.tau * j / nv) for j in range(nv)] for i in range(1, rings_n + 1)]
        scatter.add(at(0, 0), rings, at(1, 0), c.mix(pale, toasted, random.random()))
    return scatter.to_object("Seeds", c.vertex_color_material("Sesame", roughness=0.55))


# ---------------------------------------------------------------- toppings
def build_toppings(onions=CRUMBS[2], chives=BITS[2]):
    """Crispy onion crumbs and chopped chives tucked along both seams of the sausage."""
    scatter = Scatter()

    def seam_point():
        x = random.uniform(-0.70, 0.70)
        ang = math.radians(random.uniform(28, 62))
        n = Vector((0, random.choice((-1, 1)) * math.cos(ang), math.sin(ang)))
        return Vector((x, 0, sausage_axis_z(x))) + n * (SAUS_R + 0.004), n

    fried, fried_dark = c.srgb(*CRUMBS[0]), c.srgb(*CRUMBS[1])
    for _ in range(onions):
        p, n = seam_point()
        size = random.uniform(0.008, 0.016)
        offset = Vector((random.uniform(0, 9), random.uniform(0, 9), random.uniform(0, 9)))
        squash = (random.uniform(0.8, 1.6), random.uniform(0.7, 1.2), random.uniform(0.5, 0.9))

        def crumb(u, ang):
            d = Vector((math.cos(math.pi * u), math.sin(math.pi * u) * math.cos(ang), math.sin(math.pi * u) * math.sin(ang)))
            r = size * (1 + 0.45 * noise.noise(d * 1.7 + offset))
            return p + n * size * 0.5 + Vector((d.x * squash[0], d.y * squash[1], d.z * squash[2])) * r

        rings = [[crumb(i / 5, math.tau * j / 7) for j in range(7)] for i in range(1, 5)]
        scatter.add(crumb(0, 0), rings, crumb(1, 0), c.mix(fried, fried_dark, random.random() ** 1.5))

    green, green_light = c.srgb(*BITS[0]), c.srgb(*BITS[1])
    for _ in range(chives):
        p, n = seam_point()
        axis = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-0.3, 0.3))).normalized()
        a = axis.cross(n).normalized()
        b = axis.cross(a)
        half, r = random.uniform(0.008, 0.014), random.uniform(0.0055, 0.0075)
        centre = p + n * r
        rings = [[centre + axis * h + (a * math.cos(t) + b * math.sin(t)) * r for t in (math.tau * j / 7 for j in range(7))]
                 for h in (-half, half)]
        scatter.add(centre - axis * half, rings, centre + axis * half, c.mix(green, green_light, random.random()))

    return scatter.to_object("Toppings", c.vertex_color_material("Toppings", roughness=0.5))


# ---------------------------------------------------------------- loaded toppings (signature)
def _strip(path, width, thick, nv=8):
    """Flat ribbon along a path -> (start, rings, end) for Scatter.add. Width tapers to the ends."""
    rings = []
    for i in range(1, len(path) - 1):
        tangent = (path[i + 1] - path[i - 1]).normalized()
        side = tangent.cross(Vector((0, 0, 1)))
        side = side.normalized() if side.length > 1e-4 else Vector((0, 1, 0))
        up = side.cross(tangent)
        taper = math.sin(math.pi * i / (len(path) - 1)) ** 0.5
        rings.append([path[i] + side * math.cos(a) * width * taper + up * math.sin(a) * thick
                      for a in (math.tau * j / nv for j in range(nv))])
    return path[0], rings, path[-1]


def build_loaded():
    """Roasted red peppers piled along the frank, leaves tucked down the sides, three
    spoonfuls of cream cheese on top, black and white sesame over the cheese."""
    scatter = Scatter()

    def top(x, y):
        return sausage_axis_z(x) + math.sqrt(max(SAUS_R ** 2 - y ** 2, 0.0))

    # roasted peppers: soft glossy strips lying every which way
    red, orange = c.srgb(0.78, 0.13, 0.06), c.srgb(0.90, 0.32, 0.07)
    for _ in range(26):
        cx, cy = random.uniform(-0.62, 0.62), random.uniform(-0.10, 0.10)
        yaw = random.uniform(-1.0, 1.0)
        length, lift = random.uniform(0.16, 0.30), random.uniform(0.012, 0.05)
        direction = Vector((math.cos(yaw), math.sin(yaw), 0))
        path = []
        for i in range(13):
            t = i / 12
            p = Vector((cx, cy, 0)) + direction * (t - 0.5) * length
            p.y = max(-0.15, min(0.15, p.y))
            p.z = top(p.x, p.y * 0.6) + lift + 0.02 * math.sin(math.pi * t) + 0.01 * noise.noise(p * 9.0)
            path.append(p)
        scatter.add(*_strip(path, random.uniform(0.030, 0.048), 0.013, nv=12), c.mix(red, orange, random.random() ** 2))

    # leaves: thin blades springing out from between frank and bun
    leaf, leaf_light, stem = c.srgb(0.16, 0.38, 0.10), c.srgb(0.42, 0.62, 0.18), c.srgb(0.62, 0.10, 0.16)
    for _ in range(26):
        x = random.uniform(-0.66, 0.66)
        side = random.choice((-1, 1))
        base = Vector((x, side * 0.10, sausage_axis_z(x) + 0.07))
        out = Vector((random.uniform(-0.5, 0.5), side * random.uniform(0.5, 1.0), random.uniform(0.25, 0.9))).normalized()
        length = random.uniform(0.12, 0.24)
        path = [base + out * length * t + Vector((0, 0, -0.05 * t * t)) for t in (i / 11 for i in range(12))]
        colour = stem if random.random() < 0.15 else c.mix(leaf, leaf_light, random.random())
        scatter.add(*_strip(path, random.uniform(0.03, 0.05), 0.005, nv=10), colour)

    # cream cheese: three soft spoonfuls, each with a pulled tip
    cheese = c.srgb(0.96, 0.95, 0.91)
    black, white = c.srgb(0.03, 0.03, 0.03), c.srgb(0.90, 0.84, 0.66)
    for k, x in enumerate((-0.36, -0.02, 0.33)):
        y = (-0.03, 0.035, -0.02)[k]
        centre = Vector((x, y, top(x, y) + 0.085))
        yaw = (0.5, 0.2, 0.6)[k]
        long_axis = Vector((math.cos(yaw), math.sin(yaw), 0.12)).normalized()
        across = long_axis.cross(Vector((0, 0, 1))).normalized()
        upward = across.cross(long_axis)
        radii = (0.15, 0.075, 0.07)
        offset = Vector((k * 3.1, 1.7, 0.4))

        def dollop(u, ang, grow=1.0):
            profile = math.sin(math.pi * u) ** 0.6 * (1.1 - 0.35 * u)  # fatter at one end, pulled at the other
            d = across * math.cos(ang) * radii[1] + upward * math.sin(ang) * radii[2]
            p = centre + long_axis * (u - 0.5) * 2 * radii[0] + d * profile * grow
            return p + (p - centre).normalized() * 0.012 * noise.noise(p * 14.0 + offset)

        rings = [[dollop(i / 15, math.tau * j / 16) for j in range(16)] for i in range(1, 15)]
        scatter.add(dollop(0, 0), rings, dollop(1, 0), cheese)

        for _ in range(46):  # sesame scattered over the top of the spoonful
            u, ang = random.uniform(0.15, 0.85), random.uniform(0.25, math.pi - 0.25)
            p = dollop(u, ang, 1.03)
            axis = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-0.3, 0.3))).normalized()
            n = (p - centre).normalized()
            wide = axis.cross(n).normalized()
            seed = [p + axis * 0.011 * (t - 0.5) * 2 for t in (0.0, 0.2, 0.5, 0.8, 1.0)]
            rings = [[seed[i] + (wide * math.cos(a) * 0.005 + n * math.sin(a) * 0.003) * math.sin(math.pi * i / 4)
                      for a in (math.tau * j / 6 for j in range(6))] for i in (1, 2, 3)]
            scatter.add(seed[0], rings, seed[-1], black if random.random() < 0.6 else white)

    return scatter.to_object("Toppings", c.vertex_color_material("Loaded", roughness=0.38, coat=0.15))


# ---------------------------------------------------------------- build
def main():
    args = c.script_args()
    samples = int(args[args.index("--samples") + 1]) if "--samples" in args else 160
    scene = c.reset_scene()

    bun, sausage = build_bun(), build_sausage()
    if VARIANT == "signature":
        mustard = None
        parts = [bun, sausage, build_loaded()]
    else:
        mustard = build_mustard()
        parts = [bun, sausage, mustard, build_seeds(), build_toppings()]

    if VARIANT != "signature":  # a menu still only: no bake, no GLB, no .blend
        c.studio(scene, target=(0, 0, 0.03), camera_dir=(-0.55, -1.0, 0.62), distance=5.8, floor_z=-0.21)
        c.configure_cycles(scene, 2000, 1250, samples=samples)
        c.render_still(scene, f"{NAME}-{VARIANT}")
        return

    # Toppings press real contact shadows into the baked bun and frank.
    bun_maps = sh.bake_pbr(bun, "hotdog_bun", size=(2048, 2048), detail_size=(1024, 1024))
    frank_maps = sh.bake_pbr(sausage, "hotdog_frank", size=(2048, 1024), detail_size=(1024, 512))
    baked = [(bun, sh.baked_material(bun.data.materials[0], *bun_maps)),
             (sausage, sh.baked_material(sausage.data.materials[0], *frank_maps))]
    with sh.BakedSwap(baked):
        c.export_glb(NAME, parts)

    c.studio(scene, target=(0, 0, 0.03), camera_dir=(-0.55, -1.0, 0.62), distance=5.8, floor_z=-0.21)
    c.configure_cycles(scene, 2000, 1250, samples=samples)
    c.save_blend(NAME)
    if "--no-render" not in args:
        c.render_still(scene, NAME)


main()
