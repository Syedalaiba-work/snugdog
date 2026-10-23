"""Skeleton, skinning and the reusable pose library for the SNUGDOG mascot.

Poses are written in armature space, which matches the model's axes:
X = forward (nose), Y = the dog's left, Z = up. So for any bone in its rest frame:
    turn Z +  -> swings toward the dog's left     turn Y +  -> tips forward/down
    turn X +  -> rolls (left side rises)
"""
import math

import bpy
from mathutils import Matrix, Vector

import anatomy as an
import common as c


def _activate(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def build_armature(name):
    data = bpy.data.armatures.new(name)
    arm = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(arm)
    _activate(arm)
    bpy.ops.object.mode_set(mode="EDIT")
    for bone, (head, tail, _) in an.BONES.items():
        eb = data.edit_bones.new(bone)
        eb.head, eb.tail = head, tail
    for bone, (_, _, parent) in an.BONES.items():
        if parent:
            data.edit_bones[bone].parent = data.edit_bones[parent]
    bpy.ops.object.mode_set(mode="OBJECT")
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"
    return arm


def bind(skin, arm):
    """Skin with automatic (bone heat) weights; envelope weights if the solver fails."""
    def weighted():
        names = {b.name for b in arm.data.bones}
        return any(g.group < len(skin.vertex_groups) and skin.vertex_groups[g.group].name in names and g.weight > 0
                   for v in skin.data.vertices for g in v.groups)

    for mode in ("ARMATURE_AUTO", "ARMATURE_ENVELOPE"):
        bpy.ops.object.select_all(action="DESELECT")
        skin.select_set(True)
        arm.select_set(True)
        bpy.context.view_layer.objects.active = arm
        bpy.ops.object.parent_set(type=mode)
        if weighted():
            print(f"[snugdog] {skin.name} skinned with {mode}")
            break
    _weight_ears(skin)


def _weight_ears(skin):
    """Ears are thin flaps; give them clean weights by distance from the root
    instead of trusting bone heat through the skull."""
    marker = skin.vertex_groups.get("is_ear")
    if marker is None:
        return
    root_z, up = an.EAR_ROOT.z, an.EAR_DIRECTION
    groups = {g.index: g for g in skin.vertex_groups}
    for v in skin.data.vertices:
        if not any(g.group == marker.index and g.weight > 0.5 for g in v.groups):
            continue
        for g in list(v.groups):
            groups[g.group].remove([v.index])
        tag = "L" if v.co.y > 0 else "R"
        along = (v.co.z - root_z) * up  # distance from the root toward the tip
        tip = c.smoothstep(0.36, 0.62, along)
        head = 0.8 * c.smoothstep(0.18, -0.04, along)
        skin.vertex_groups["Head"].add([v.index], head, "REPLACE")
        skin.vertex_groups[f"Ear_{tag}"].add([v.index], (1 - head) * (1 - tip), "REPLACE")
        skin.vertex_groups[f"Ear_{tag}_2"].add([v.index], (1 - head) * tip, "REPLACE")
    skin.vertex_groups.remove(marker)


def attach(obj, arm, bone="Head"):
    """Rigid part that rides a bone and keeps its own transform (eyes can look, lids can blink)."""
    world = obj.matrix_world.copy()
    obj.parent = arm
    obj.parent_type = "BONE"
    obj.parent_bone = bone
    bpy.context.view_layer.update()
    obj.matrix_world = world


# ---------------------------------------------------------------- posing
def reset(arm):
    for pb in arm.pose.bones:
        pb.matrix_basis.identity()
    bpy.context.view_layer.update()


def turn(arm, bone, axis, degrees):
    pb = arm.pose.bones[bone]
    pivot = Matrix.Translation(pb.head)
    pb.matrix = pivot @ Matrix.Rotation(math.radians(degrees), 4, axis) @ pivot.inverted() @ pb.matrix
    bpy.context.view_layer.update()


def shift(arm, bone, offset):
    pb = arm.pose.bones[bone]
    pb.matrix = Matrix.Translation(Vector(offset)) @ pb.matrix
    bpy.context.view_layer.update()


def _both(bone, axis, degrees):
    """Same swing for the left and right bone (X/Z rotations are mirrored)."""
    sign = 1 if axis == "Y" else -1
    return [("turn", f"{bone}L" if bone.endswith(("_F", "_B")) else f"{bone}_L", axis, degrees),
            ("turn", f"{bone}R" if bone.endswith(("_F", "_B")) else f"{bone}_R", axis, degrees * sign)]


# Each pose is an ordered list of steps. Order matters: children before parents, and for
# one bone roll (X) and pitch (Y) before yaw (Z). That way every turn acts in the bone's
# own rest frame: a head tilt stays a tilt however far the neck has turned.
POSES = {
    "01_HeroStanding": [  # one paw lifted, caught mid-thought
        ("turn", "Head", "X", -8), ("turn", "Head", "Y", 4), ("turn", "Head", "Z", 14),
        ("turn", "Neck", "Y", -4), ("turn", "Neck", "Z", 8),
        ("turn", "Paw_FL", "Y", 48), ("turn", "Leg_FL", "Y", -40),
        ("turn", "Ear_L", "X", 6), ("turn", "Ear_R", "X", -4),
        ("turn", "Tail_2", "Y", -6), ("turn", "Tail", "Y", -8),
        ("turn", "Chest", "Z", 3),
    ],
    "02_Curious": [
        ("turn", "Head", "X", 20), ("turn", "Head", "Y", 2), ("turn", "Head", "Z", 12),
        ("turn", "Neck", "Y", -3), ("turn", "Neck", "Z", 8),
        ("turn", "Ear_L", "X", 14), ("turn", "Ear_R", "X", 8),
        ("turn", "Tail_2", "Z", 10), ("turn", "Tail", "Y", 6),
    ],
    "03_Walking": [
        ("turn", "Head", "Y", -4), ("turn", "Head", "Z", 8),
        ("turn", "Neck", "Y", 6), ("turn", "Neck", "Z", 5),
        ("turn", "Paw_FL", "Y", 16), ("turn", "Leg_FL", "Y", -26),
        ("turn", "Paw_FR", "Y", -24), ("turn", "Leg_FR", "Y", 20),
        ("turn", "Paw_BR", "Y", 10), ("turn", "Leg_BR", "Y", -20),
        ("turn", "Paw_BL", "Y", -18), ("turn", "Leg_BL", "Y", 20),
        ("turn", "Tail_2", "Y", 6), ("turn", "Tail", "Y", 10),
        ("turn", "Chest", "Z", 4), ("turn", "Body", "Z", -3),
        ("shift", "Root", (0, 0, -0.02)),
    ],
    "04_Sitting": [
        ("turn", "Head", "X", -5), ("turn", "Head", "Y", 10), ("turn", "Head", "Z", 12),
        ("turn", "Neck", "Y", 12), ("turn", "Neck", "Z", 8),
        *_both("Leg_F", "Y", 22),
        *_both("Paw_B", "Y", 30), *_both("Leg_B", "Y", -42),
        ("turn", "Tail_2", "Z", 12), ("turn", "Tail", "Y", 30),
        ("turn", "Root", "Y", -22), ("shift", "Root", (0, 0, -0.62)),
    ],
    "05_LookingBack": [
        ("turn", "Head", "X", 6), ("turn", "Head", "Z", 46),
        ("turn", "Neck", "Y", -6), ("turn", "Neck", "Z", 48),
        ("turn", "Ear_L", "X", 8),
        ("turn", "Chest", "Z", 12), ("turn", "Body", "Z", 9),
        ("turn", "Tail", "Z", -10), ("turn", "Tail", "Y", -6),
    ],
}


def apply_pose(arm, name):
    reset(arm)
    for kind, bone, *rest in POSES[name]:
        if kind == "turn":
            turn(arm, bone, *rest)
        else:
            shift(arm, bone, *rest)


def store_poses(arm):
    """Bake every pose into its own action on a muted NLA track; the glTF exporter
    turns each track into a named clip the web can cross-fade between."""
    arm.animation_data_create()
    for name in POSES:
        apply_pose(arm, name)
        action = bpy.data.actions.new(f"Pose_{name}")
        arm.animation_data.action = action
        for pb in arm.pose.bones:
            for frame in (1, 2):
                pb.keyframe_insert("rotation_quaternion", frame=frame)
                pb.keyframe_insert("location", frame=frame)
        track = arm.animation_data.nla_tracks.new()
        track.name = f"Pose_{name}"
        track.strips.new(action.name, 1, action)
        track.mute = True
        arm.animation_data.action = None
    reset(arm)


def set_tracks_muted(arm, muted):
    for track in arm.animation_data.nla_tracks:
        track.mute = muted
