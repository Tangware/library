import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Euler, Matrix, Vector

FRAMES = 72
FPS = 24
MM = 0.001
REACH = 3.0
HEIGHT = 0.5
FROM_GLTF = Euler((-math.pi / 2, 0, 0)).to_matrix().to_4x4()

given = sys.argv[sys.argv.index("--") + 1 :]
built, written = Path(given[0]), Path(given[1])
final = "--final" in given
manifest = json.loads((built / "manifest.json").read_text())
parts = {part["id"]: part["mesh"] for part in manifest["parts"]}

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 16 if final else 4
scene.render.resolution_x, scene.render.resolution_y = (960, 540) if final else (480, 270)
scene.render.fps = FPS
scene.frame_start, scene.frame_end = 1, FRAMES
scene.world = bpy.data.worlds.new("studio")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.8, 0.8, 0.8, 1)


def placed(mesh: str, matrix: list[float]) -> list[bpy.types.Object]:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(built / mesh))
    new = [each for each in bpy.data.objects if each not in before]
    rows = [matrix[start : start + 4] for start in range(0, 16, 4)]
    at = Matrix(rows)
    at.translation = at.translation * MM
    for each in new:
        each.matrix_world = at @ Matrix.Scale(MM, 4) @ FROM_GLTF
    return new


shown = []
for assembly in manifest["assemblies"]:
    for instance in assembly["instances"]:
        shown += placed(parts[instance["part"]], instance["matrix"])
    for hardware in assembly["hardware"]:
        shown += placed(hardware["mesh"], hardware["matrix"])

corners = [each.matrix_world @ Vector(corner) for each in shown for corner in each.bound_box]
low = Vector(min(c[n] for c in corners) for n in range(3))
high = Vector(max(c[n] for c in corners) for n in range(3))
middle = (low + high) / 2
size = (high - low).length

target = bpy.data.objects.new("turntable", None)
target.location = middle
scene.collection.objects.link(target)
camera = bpy.data.objects.new("camera", bpy.data.cameras.new("camera"))
camera.location = middle + Vector((0, -REACH * size, HEIGHT * size))
camera.rotation_euler = Vector((0, REACH, -HEIGHT)).to_track_quat("-Z", "Y").to_euler()
camera.parent = target
camera.matrix_parent_inverse = target.matrix_world.inverted()
scene.collection.objects.link(camera)
scene.camera = camera
sun = bpy.data.objects.new("key", bpy.data.lights.new("key", "SUN"))
sun.rotation_euler = (math.radians(50), 0, math.radians(30))
sun.data.energy = 3
scene.collection.objects.link(sun)

bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"
target.rotation_euler = (0, 0, 0)
target.keyframe_insert("rotation_euler", frame=1)
target.rotation_euler = (0, 0, 2 * math.pi)
target.keyframe_insert("rotation_euler", frame=FRAMES + 1)

name = Path(__file__).stem
if final:
    scene.render.filepath = str(written / f"{name}-final" / "####")
    scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(animation=True)
    print(f"final frames {FRAMES} fps {FPS}")
else:
    written.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=str(written / f"{name}.glb"), export_cameras=True, export_lights=True
    )
    scene.render.filepath = str(written / name / "0001")
    scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
