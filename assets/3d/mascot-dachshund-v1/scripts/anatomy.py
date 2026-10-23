"""SNUGDOG dachshund anatomy: every measurement that defines the character lives here.

Units: 1 = 10 cm. Nose points +X, +Z is up, the dog's left side is +Y, paws rest on Z = 0.
The character is an adult: long back, deep chest, long muzzle, small eyes, low ears.
Proportions are pushed slightly (longer body, a touch more head) for brand silhouette.
"""
from mathutils import Vector

V = Vector

# (centre, side radius, vertical radius) along each limb
BODY = [
    (V((-1.98, 0, 1.52)), 0.14, 0.16),
    (V((-1.72, 0, 1.53)), 0.40, 0.42),
    (V((-1.30, 0, 1.50)), 0.50, 0.52),  # hips
    (V((-0.60, 0, 1.50)), 0.46, 0.45),  # loin: the tuck-up
    (V((0.10, 0, 1.44)), 0.52, 0.54),
    (V((0.80, 0, 1.38)), 0.58, 0.66),  # ribcage
    (V((1.30, 0, 1.38)), 0.57, 0.69),  # deepest chest
    (V((1.66, 0, 1.48)), 0.46, 0.56),
    (V((1.92, 0, 1.58)), 0.26, 0.32),
]
NECK = [
    (V((1.40, 0, 1.72)), 0.44, 0.44),
    (V((1.82, 0, 2.18)), 0.37, 0.37),
    (V((2.10, 0, 2.56)), 0.33, 0.33),
]
MUZZLE = [
    (V((2.44, 0, 2.66)), 0.31, 0.29),
    (V((2.80, 0, 2.60)), 0.27, 0.255),
    (V((3.12, 0, 2.55)), 0.225, 0.215),
    (V((3.32, 0, 2.52)), 0.185, 0.18),
]
TAIL = [
    (V((-1.84, 0, 1.70)), 0.15, 0.15),
    (V((-2.30, 0, 1.86)), 0.11, 0.11),
    (V((-2.80, 0, 2.16)), 0.07, 0.07),
    (V((-3.16, 0, 2.52)), 0.035, 0.035),
]


def front_leg(side):
    y = 0.37 * side
    return [
        (V((1.20, y, 1.06)), 0.20, 0.20),
        (V((1.22, y, 0.60)), 0.16, 0.16),
        (V((1.26, y, 0.20)), 0.14, 0.14),
    ]


def hind_leg(side):
    y = 0.38 * side
    return [
        (V((-1.42, y, 0.90)), 0.18, 0.18),
        (V((-1.70, y, 0.52)), 0.135, 0.135),
        (V((-1.60, y, 0.20)), 0.12, 0.12),
    ]


# (centre, radii) volumes that round out the form
HEAD = (V((2.26, 0, 2.77)), V((0.54, 0.47, 0.46)))
PROSTERNUM = (V((1.66, 0, 1.30)), V((0.26, 0.28, 0.30)))
JAW = (V((2.74, 0, 2.44)), V((0.40, 0.21, 0.13)))


def paired(side):
    """Left/right volumes: shoulder, thigh, paws, cheek, brow."""
    s = side
    return {
        "shoulder": (V((1.20, 0.37 * s, 1.26)), V((0.30, 0.21, 0.40))),
        "thigh": (V((-1.30, 0.36 * s, 1.20)), V((0.42, 0.22, 0.50))),
        "paw_front": (V((1.37, 0.38 * s, 0.13)), V((0.27, 0.18, 0.13))),
        "paw_hind": (V((-1.48, 0.38 * s, 0.13)), V((0.26, 0.17, 0.13))),
        "cheek": (V((2.38, 0.26 * s, 2.62)), V((0.27, 0.19, 0.23))),
        "brow": (V((2.52, 0.22 * s, 3.00)), V((0.17, 0.15, 0.10))),
    }


EYE_RADIUS = 0.105


def eye_centre(side):
    return V((2.56, 0.235 * side, 2.86))


def eye_forward(side):
    """Eyes sit on the front corners of the skull and look forward and slightly out."""
    return V((0.80, 0.56 * side, 0.20)).normalized()


NOSE = (V((3.44, 0, 2.545)), V((0.095, 0.125, 0.088)))

# Ear: hangs from high on the skull, a long rounded leaf lying against the cheek.
EAR_ROOT = V((2.04, 0.40, 3.02))
EAR_LENGTH, EAR_WIDTH, EAR_THICKNESS = 0.98, 0.31, 0.04

# ---------------------------------------------------------------- skeleton
# name: (head, tail, parent). Names follow the model hierarchy in the brief.
BONES = {
    "Root": (V((-1.30, 0, 1.50)), V((-1.30, 0, 1.90)), None),
    "Body": (V((-1.30, 0, 1.50)), V((-0.10, 0, 1.46)), "Root"),
    "Chest": (V((-0.10, 0, 1.46)), V((1.35, 0, 1.55)), "Body"),
    "Neck": (V((1.35, 0, 1.55)), V((2.08, 0, 2.50)), "Chest"),
    "Head": (V((2.08, 0, 2.50)), V((2.50, 0, 2.90)), "Neck"),
    "Muzzle": (V((2.50, 0, 2.62)), V((3.34, 0, 2.52)), "Head"),
    "Tail": (V((-1.84, 0, 1.70)), V((-2.30, 0, 1.86)), "Root"),
    "Tail_2": (V((-2.30, 0, 1.86)), V((-2.80, 0, 2.16)), "Tail"),
    "Tail_3": (V((-2.80, 0, 2.16)), V((-3.16, 0, 2.52)), "Tail_2"),
}
for _name, _side in (("L", 1), ("R", -1)):
    yf, yh, ye = 0.37 * _side, 0.38 * _side, 0.37 * _side
    BONES[f"Leg_F{_name}"] = (V((1.20, yf, 1.10)), V((1.24, yf, 0.34)), "Chest")
    BONES[f"Paw_F{_name}"] = (V((1.24, yf, 0.34)), V((1.50, yf, 0.06)), f"Leg_F{_name}")
    BONES[f"Leg_B{_name}"] = (V((-1.32, yh, 1.25)), V((-1.68, yh, 0.50)), "Root")
    BONES[f"Paw_B{_name}"] = (V((-1.68, yh, 0.50)), V((-1.50, yh, 0.06)), f"Leg_B{_name}")
    BONES[f"Ear_{_name}"] = (V((2.02, ye, 2.96)), V((2.06, 0.50 * _side, 2.50)), "Head")
    BONES[f"Ear_{_name}_2"] = (V((2.06, 0.50 * _side, 2.50)), V((2.10, 0.52 * _side, 2.02)), f"Ear_{_name}")
