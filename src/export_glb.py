"""model.blend -> model.glb (full detail, LOD0) and model_lod1.glb (web LOD: facade detail groups D_* dropped)"""
import bpy, os, sys
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
def export(path):
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', export_yup=True, export_apply=True,
                              export_image_format='AUTO', export_materials='EXPORT', export_extras=False, export_lights=False, export_cameras=False)
    print('exported', os.path.basename(path), os.path.getsize(path))
bpy.ops.wm.open_mainfile(filepath=os.path.join(root, 'model.blend'))
export(os.path.join(root, 'model.glb'))
for ob in [o for o in bpy.data.objects if o.name.startswith('D_')]: bpy.data.objects.remove(ob)
export(os.path.join(root, 'model_lod1.glb'))
