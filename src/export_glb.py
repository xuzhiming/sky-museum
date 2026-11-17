import bpy, os
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
bpy.ops.wm.open_mainfile(filepath=os.path.join(root, 'model.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(root, 'model.glb'), export_format='GLB', export_yup=True, export_apply=True,
                          export_image_format='AUTO', export_materials='EXPORT', export_extras=False, export_lights=False, export_cameras=False)
print('exported', os.path.getsize(os.path.join(root, 'model.glb')))
