from pathlib import Path
import json
import vtk
import launch_film as L
bot=L.robot()
r=vtk.vtkRenderer();r.AddViewProp(bot['root'])
w=vtk.vtkRenderWindow();w.SetOffScreenRendering(1);w.SetSize(32,32);w.AddRenderer(r)
e=vtk.vtkGLTFExporter();e.SetRenderWindow(w);e.InlineDataOn();e.SaveNormalOn();e.SetFileName(str(L.ROOT/'assets/FLOAT_concept_model.gltf'));e.Write()
p=L.ROOT/'assets/FLOAT_concept_model.gltf'
d=json.loads(p.read_text());d['asset']['copyright']='FLOAT concept model; illustrative only, not manufacturing CAD or proof of function.';p.write_text(json.dumps(d,separators=(',',':')))
try:
 import trimesh
 m=trimesh.load(p,force='scene');m.export(L.ROOT/'assets/FLOAT_concept_model.glb')
 print('Exported portable GLB',flush=True)
except Exception as exc: print('Embedded glTF export available; GLB conversion not performed:',str(exc),flush=True)
