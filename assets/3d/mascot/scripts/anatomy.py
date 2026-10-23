"""SNUGDOG terrier anatomy: every measurement that defines the character lives here.

Units: 1 = 10 cm. Nose points +X, +Z is up, the dog's left side is +Y, paws rest on Z = 0.
The character is a charcoal Scottish-terrier type built from the client's reference:
compact body, big head, long bearded muzzle, heavy brows, upright pointed ears, wide
expressive eyes, short upright tail, red collar. The fur does a lot of the silhouette,
so these volumes are the dog under the coat.
"""
from mathutils import Vector

V = Vector

# (centre, side radius, vertical radius) along each limb
BODY = [
    (V((-1.28, 0, 1.56)), 0.16, 0.18),
    (V((-1.05, 0, 1.56)), 0.44, 0.46),
    (V((-0.60, 0, 1.52)), 0.52, 0.54),
    (V((0.10, 0, 1.50)), 0.55, 0.58),
    (V((0.60, 0, 1.50)), 0.56, 0.62),
    (V((0.95, 0, 1.58)), 0.46, 0.52),
    (V((1.15, 0, 1.68)), 0.26, 0.32),
]
NECK = [
    (V((0.80, 0, 1.85)), 0.44, 0.44),
    (V((1.05, 0, 2.25)), 0.42, 0.42),
    (V((1.25, 0, 2.60)), 0.42, 0.42),
]
MUZZLE = [
    (V((1.80, 0, 2.74)), 0.37, 0.33),
    (V((2.15, 0, 2.66)), 0.34, 0.31),
    (V((2.45, 0, 2.60)), 0.31, 0.28),
    (V((2.62, 0, 2.57)), 0.26, 0.24),
]
TAIL = [
    (V((-1.15, 0, 1.85)), 0.18, 0.18),
    (V((-1.30, 0, 2.30)), 0.14, 0.14),
    (V((-1.36, 0, 2.70)), 0.08, 0.08),
    (V((-1.38, 0, 2.95)), 0.04, 0.04),
]


def front_leg(side):
    y = 0.36 * side
    return [
        (V((0.72, y, 1.10)), 0.22, 0.22),
        (V((0.75, y, 0.60)), 0.20, 0.20),
        (V((0.78, y, 0.22)), 0.18, 0.18),
    ]


def hind_leg(side):
    y = 0.38 * side
    return [
        (V((-0.92, y, 0.90)), 0.20, 0.20),
        (V((-1.12, y, 0.52)), 0.17, 0.17),
        (V((-1.02, y, 0.22)), 0.16, 0.16),
    ]


# (centre, radii) volumes that round out the form
HEAD = (V((1.42, 0, 2.92)), V((0.62, 0.58, 0.56)))
PROSTERNUM = (V((1.00, 0, 1.30)), V((0.30, 0.32, 0.34)))
JAW = (V((2.20, 0, 2.42)), V((0.50, 0.30, 0.20)))  # the chin under the beard


def paired(side):
    """Left/right volumes: shoulder, thigh, paws, cheek, brow."""
    s = side
    return {
        "shoulder": (V((0.72, 0.36 * s, 1.28)), V((0.30, 0.24, 0.40))),
        "thigh": (V((-0.82, 0.36 * s, 1.20)), V((0.42, 0.25, 0.50))),
        "paw_front": (V((0.90, 0.38 * s, 0.15)), V((0.30, 0.22, 0.15))),
        "paw_hind": (V((-0.90, 0.38 * s, 0.15)), V((0.28, 0.21, 0.15))),
        "cheek": (V((1.80, 0.30 * s, 2.70)), V((0.30, 0.24, 0.28))),
        "brow": (V((1.92, 0.24 * s, 3.27)), V((0.20, 0.20, 0.13))),
    }


# Eyes: large, close-set and forward-facing, with visible whites so the gaze reads.
EYE_RADIUS = 0.165
EYE_PROTRUDE = 0.40  # share of the eyeball that clears the skull
PUPIL_DEG, IRIS_DEG = 13.0, 30.0
GAZE = V((0.0, 0.30, -0.06))  # a sideways glance toward the dog's left


def eye_centre(side):
    return V((1.95, 0.215 * side, 3.03))


def eye_socket(side):
    """Direction the eye sits in the skull (used to seat it)."""
    return V((0.96, 0.16 * side, 0.12)).normalized()


def eye_forward(side):
    """Direction the eye looks: the socket direction plus the shared glance."""
    return (V((0.96, 0.0, 0.12)) + GAZE).normalized()  # both eyes share one line of sight


NOSE = (V((2.75, 0, 2.68)), V((0.16, 0.21, 0.14)))

# Ear: upright and pointed, set high on the skull.
EAR_ROOT = V((1.20, 0.34, 3.32))
EAR_LENGTH, EAR_WIDTH, EAR_THICKNESS = 0.74, 0.23, 0.05
EAR_DIRECTION = 1  # +1 stands up, -1 hangs down

# Collar: (centre, axis along the neck, radius)
COLLAR = (V((0.98, 0, 2.12)), V((0.45, 0, 0.89)), 0.52)

# ---------------------------------------------------------------- skeleton
# name: (head, tail, parent)
BONES = {
    "Root": (V((-0.85, 0, 1.52)), V((-0.85, 0, 1.90)), None),
    "Body": (V((-0.85, 0, 1.52)), V((-0.10, 0, 1.50)), "Root"),
    "Chest": (V((-0.10, 0, 1.50)), V((0.85, 0, 1.62)), "Body"),
    "Neck": (V((0.85, 0, 1.72)), V((1.25, 0, 2.55)), "Chest"),
    "Head": (V((1.25, 0, 2.55)), V((1.55, 0, 3.10)), "Neck"),
    "Muzzle": (V((1.80, 0, 2.72)), V((2.62, 0, 2.57)), "Head"),
    "Tail": (V((-1.15, 0, 1.85)), V((-1.30, 0, 2.30)), "Root"),
    "Tail_2": (V((-1.30, 0, 2.30)), V((-1.36, 0, 2.70)), "Tail"),
    "Tail_3": (V((-1.36, 0, 2.70)), V((-1.38, 0, 2.95)), "Tail_2"),
}
for _name, _side in (("L", 1), ("R", -1)):
    yf, yh = 0.36 * _side, 0.38 * _side
    BONES[f"Leg_F{_name}"] = (V((0.72, yf, 1.15)), V((0.76, yf, 0.42)), "Chest")
    BONES[f"Paw_F{_name}"] = (V((0.76, yf, 0.42)), V((0.98, yf, 0.06)), f"Leg_F{_name}")
    BONES[f"Leg_B{_name}"] = (V((-0.84, yh, 1.25)), V((-1.12, yh, 0.52)), "Root")
    BONES[f"Paw_B{_name}"] = (V((-1.12, yh, 0.52)), V((-0.95, yh, 0.06)), f"Leg_B{_name}")
    BONES[f"Ear_{_name}"] = (V((1.20, 0.34 * _side, 3.32)), V((1.20, 0.40 * _side, 3.70)), "Head")
    BONES[f"Ear_{_name}_2"] = (V((1.20, 0.40 * _side, 3.70)), V((1.20, 0.47 * _side, 4.06)), f"Ear_{_name}")
