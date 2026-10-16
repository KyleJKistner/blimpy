"""Procedural 3D marketing concept film; no real-prototype footage.
Uses the installed VTK/EGL renderer, Pillow, NumPy and ffmpeg. No external assets.
All dimensions are illustrative; features shown are proposed.
"""
import os
os.environ.setdefault('VTK_DEFAULT_OPENGL_WINDOW','vtkEGLRenderWindow')
import math, json, time, argparse, subprocess, wave
from pathlib import Path
from collections import defaultdict
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import vtk
from vtk.util.numpy_support import vtk_to_numpy, numpy_to_vtk

ROOT=Path('/mnt/data/float_film'); (ROOT/'render').mkdir(exist_ok=True)
W,H=1920,1080; RW,RH=1440,810; FPS=24; DURATION=28
C={
 'cream':(.83,.83,.78),'envelope':(.80,.84,.82),'seam':(.59,.68,.65),
 'dark':(.047,.085,.091),'rubber':(.085,.12,.12),'lens':(.007,.037,.049),
 'teal':(.08,.68,.58),'glow':(.22,.92,.76),'bronze':(.66,.43,.19),
 'wood':(.54,.36,.22),'walnut':(.25,.15,.10),'linen':(.74,.67,.56),
 'wall':(.88,.86,.81),'floor':(.73,.71,.66),'rug':(.61,.65,.62),
 'ink':(.10,.15,.15),'white':(.95,.95,.90),'skin':(.65,.50,.37),
 'shirt':(.16,.29,.29),'pants':(.35,.36,.31),'clay':(.65,.42,.29),
 'leaf':(.16,.30,.22),'screen':(.025,.08,.09),'blue':(.34,.49,.52),
}

def smooth(x):
 x=np.clip(x,0,1); return x*x*(3-2*x)
def mix(a,b,t): return np.asarray(a)*(1-t)+np.asarray(b)*t

def poly_transform(poly, pos=(0,0,0), scale=(1,1,1), rot=(0,0,0)):
 tr=vtk.vtkTransform(); tr.Translate(*pos); tr.RotateZ(rot[2]); tr.RotateY(rot[1]); tr.RotateX(rot[0]);tr.Scale(*scale)
 fl=vtk.vtkTransformPolyDataFilter();fl.SetInputData(poly);fl.SetTransform(tr);fl.Update();out=vtk.vtkPolyData();out.ShallowCopy(fl.GetOutput());return out

def sphere(pos,r=1,scale=None,res=40):
 s=vtk.vtkSphereSource();s.SetRadius(r);s.SetThetaResolution(res);s.SetPhiResolution(max(16,res//2));s.Update()
 return poly_transform(s.GetOutput(),pos,scale or(1,1,1))
def box(pos,dims,roundness=.12,rot=(0,0,0)):
 # Superquadrics give the furniture and electronics consistent softly rounded edges.
 q=vtk.vtkSuperquadricSource();q.SetThetaResolution(40);q.SetPhiResolution(32);q.SetPhiRoundness(roundness);q.SetThetaRoundness(roundness);q.SetToroidal(False);q.Update()
 return poly_transform(q.GetOutput(),pos,dims,rot)
def cylinder_between(a,b,r,res=24):
 a=np.asarray(a,dtype=float);b=np.asarray(b,dtype=float);d=b-a;l=np.linalg.norm(d)
 s=vtk.vtkCylinderSource();s.SetRadius(r);s.SetHeight(l);s.SetResolution(res);s.CappingOn();s.Update()
 tr=vtk.vtkTransform();tr.Translate(*((a+b)/2));u=np.array([0.,1.,0.]);axis=np.cross(u,d/l);norm=np.linalg.norm(axis)
 if norm>1e-8:tr.RotateWXYZ(math.degrees(math.acos(np.clip(np.dot(u,d/l),-1,1))),*(axis/norm))
 elif d[1]<0:tr.RotateX(180)
 f=vtk.vtkTransformPolyDataFilter();f.SetInputConnection(s.GetOutputPort());f.SetTransform(tr);f.Update();p=vtk.vtkPolyData();p.ShallowCopy(f.GetOutput());return p

def tube(points,r=.002,closed=False,sides=8):
 pts=vtk.vtkPoints(); pts.SetData(numpy_to_vtk(np.asarray(points,dtype=np.float32),deep=True))
 line=vtk.vtkPolyLine();line.GetPointIds().SetNumberOfIds(len(points)+(1 if closed else 0))
 for i in range(len(points)):line.GetPointIds().SetId(i,i)
 if closed:line.GetPointIds().SetId(len(points),0)
 lines=vtk.vtkCellArray();lines.InsertNextCell(line);p=vtk.vtkPolyData();p.SetPoints(pts);p.SetLines(lines)
 t=vtk.vtkTubeFilter();t.SetInputData(p);t.SetRadius(r);t.SetNumberOfSides(sides);t.CappingOn();t.Update();o=vtk.vtkPolyData();o.ShallowCopy(t.GetOutput());return o

def ring(center,r,axis=(0,0,1),thickness=.003,n=64):
 a=np.asarray(axis,dtype=float);a/=np.linalg.norm(a);ref=np.array([0,0,1]) if abs(a[2])<.9 else np.array([0,1,0]);u=np.cross(a,ref);u/=np.linalg.norm(u);v=np.cross(a,u)
 return tube([np.asarray(center)+r*(np.cos(t)*u+np.sin(t)*v) for t in np.linspace(0,2*np.pi,n,endpoint=False)],thickness,True)

class Group:
 def __init__(self):self.geometry=defaultdict(list)
 def add(self,p,mat='white',metal=0.,rough=.7,emit=0.,opacity=1.):self.geometry[(mat,metal,rough,emit,opacity)].append(p)
 def build(self):
  group=vtk.vtkAssembly();actors=[]
  for (mat,metal,rough,emit,opacity),polys in self.geometry.items():
   ap=vtk.vtkAppendPolyData()
   for p in polys:ap.AddInputData(p)
   ap.Update();m=vtk.vtkPolyDataMapper();m.SetInputConnection(ap.GetOutputPort());a=vtk.vtkActor();a.SetMapper(m)
   prop=a.GetProperty();prop.SetColor(*C.get(mat,mat if isinstance(mat,tuple) else C['white']));prop.SetInterpolationToPBR();prop.SetMetallic(metal);prop.SetRoughness(rough);prop.SetOpacity(opacity)
   if emit:prop.SetEmissiveFactor(*[x*emit for x in C.get(mat,C['teal'])])
   group.AddPart(a);actors.append(a)
  return group,actors

def make_robot(idx=0):
 g=Group(); r=.31
 # A lightly scalloped, tensioned envelope with visible twelve-gore construction.
 s=vtk.vtkSphereSource();s.SetRadius(r);s.SetThetaResolution(120);s.SetPhiResolution(64);s.Update();p=vtk.vtkPolyData();p.DeepCopy(s.GetOutput())
 pts=vtk_to_numpy(p.GetPoints().GetData());az=np.arctan2(pts[:,1],pts[:,0]);lat=np.arccos(np.clip(pts[:,2]/r,-1,1));fac=1-.0022*(np.cos(12*az)**2)*(np.sin(lat)**2);pts[:]*=fac[:,None];p.GetPoints().Modified()
 g.add(p,'envelope',.25,.42)
 for j in range(12):
  az=j*2*math.pi/12
  points=[(.3102*math.sin(t)*math.cos(az),.3102*math.sin(t)*math.sin(az),.3102*math.cos(t)) for t in np.linspace(.045,math.pi-.045,85)]
  g.add(tube(points,.00095,sides=8),'seam',.2,.55)
 # Suspension and very small camera / audio gondola, not a rigid robot covering.
 for x,y in [(-.095,-.028),(.095,-.028),(0,.09)]:
  g.add(cylinder_between((x,y,-math.sqrt(r*r-x*x-y*y)),(x*.42,y*.42,-.358),.0011,12),'dark',.2)
 camg=Group()
 camg.add(box((0,0,-.38),(.114,.077,.071),.36),'dark',.15,.38)
 # Camera axis faces -Y.
 camg.add(cylinder_between((0,-.044,-.375),(0,-.054,-.375),.024),'rubber',.3,.35)
 camg.add(cylinder_between((0,-.054,-.375),(0,-.055,-.375),.016),'lens',.5,.15)
 camg.add(ring((0,-.0558,-.375),.020,(0,1,0),.0015),'teal',.1,.45,1)
 camg.add(sphere((-.005,-.057,-.369),.003,res=12),'white',.1,.2,.5)
 for x in np.linspace(-.028,.028,6):
  camg.add(cylinder_between((x,-.0378,-.404),(x,-.039,-.404),.0013,8),'rubber')
 # Four small shrouded props: two longitudinal, one lateral, one vertical.
 configs=[((-.185,0,-.302),(0,1,0)),((.185,0,-.302),(0,1,0)),((0,.123,-.317),(1,0,0)),((0,.039,-.433),(0,0,1))]
 rotors=[]
 root,bodyactors=g.build()
 camroot,_=camg.build();root.AddPart(camroot)
 for k,(center,axis) in enumerate(configs):
  c=np.asarray(center);a=np.asarray(axis,float);ref=np.array([0,0,1]) if abs(a[2])<.9 else np.array([0,1,0]);u=np.cross(a,ref);u=u/np.linalg.norm(u);v=np.cross(a,u)
  guard=Group(); guard.add(cylinder_between((0,.012,-.355),c,.0017,12),'dark',.1,.55)
  for off in [-.007,.007]:guard.add(ring(c+a*off,.052,axis,.0019,48),'rubber',.1,.5)
  for angle in np.linspace(0,2*np.pi,8,endpoint=False):
   edge=.052*(np.cos(angle)*u+np.sin(angle)*v)
   guard.add(cylinder_between(c+edge-a*.007,c+edge+a*.007,.001,8),'rubber')
   guard.add(cylinder_between(c+a*.009,c+edge+a*.009,.00055,6),'seam',.05)
  guard.add(sphere(c,.007,res=16),'dark',.3,.3)
  guardA,_=guard.build();root.AddPart(guardA)
  rg=Group()
  for angle in [0,2*np.pi/3,4*np.pi/3]:
   # Three slender blades in the rotor plane.
   direction=np.cos(angle)*u+np.sin(angle)*v
   rg.add(cylinder_between(c+.01*direction,c+.047*direction,.0045,10),'dark',.2,.5)
  ra,_=rg.build();root.AddPart(ra);rotors.append((ra,c,a))
 return {'root':root,'rotors':rotors,'actors':bodyactors,'idx':idx,'camera':camroot}

def pose_robot(robot,pos,yaw,t,active=True,pitch=0):
 root=robot['root'];root.SetPosition(*pos);root.SetOrientation(0,0,yaw)
 ct=vtk.vtkTransform();ct.Translate(0,0,-.375);ct.RotateX(pitch);ct.Translate(0,0,.375);robot['camera'].SetUserTransform(ct)
 for ra,c,axis in robot['rotors']:
  tr=vtk.vtkTransform();tr.Translate(*c);tr.RotateWXYZ((t*1330 if active else 0)%360,*axis);tr.Translate(*(-c));ra.SetUserTransform(tr)

# Room and decor.
def plant(g,loc,scale=1):
 x,y,z=loc
 g.add(box((x,y,z+.12*scale),(.22*scale,.22*scale,.24*scale),.6),'clay',0,.85)
 for j in range(8):
  az=j*2.4; height=(.28+.045*j)*scale; tip=(x+.19*scale*math.cos(az),y+.15*scale*math.sin(az),z+.21*scale+height)
  g.add(cylinder_between((x,y,z+.22*scale),tip,.006*scale,8),'leaf')
  g.add(sphere(tip,1,(.11*scale,.045*scale,.06*scale),res=20),'leaf')

def make_room():
 g=Group()
 g.add(box((0,0,-.09),(11,10,.18),.02),'floor')
 g.add(box((0,3.35,1.8),(11,.16,3.6),.03),'wall')
 g.add(box((-4.5,.0,1.8),(.12,6.7,3.6),.03),'wall')
 # Large daylight window and mullions.
 g.add(box((-4.415,.05,1.92),(.015,4.7,2.25),.03),(.82,.89,.86),0,.9,.6)
 for y in [-2.30,-.75,.8,2.4]:g.add(box((-4.39,y,1.92),(.06,.035,2.3),.05),'white')
 for z in [.79,3.055]:g.add(box((-4.39,.05,z),(.06,4.75,.04),.05),'white')
 # Some understated flooring joints.
 for x in np.arange(-4,5,.7):g.add(box((x,0,.004),(.003,9,.001),.1),(.68,.66,.60))
 # Wool rug.
 g.add(box((.8,.15,.009),(4.4,2.8,.018),.11),'rug')
 # Sofa, seat and cushions.
 for x in [.80,3.55]:
  for y in [1.35,2.10]:g.add(cylinder_between((x,y,.02),(x,y,.24),.035),'walnut')
 g.add(box((2.2,1.80,.38),(3.0,1.14,.32),.25),'linen')
 g.add(box((2.2,2.23,.80),(3.0,.28,.90),.25),'linen')
 for x in [.69,3.71]:g.add(box((x,1.80,.64),(.27,1.17,.64),.28),'linen')
 for x in [1.30,2.18,3.04]:g.add(box((x,1.62,.57),(.84,.82,.18),.24),(.81,.75,.65))
 g.add(box((1.14,2.01,.91),(.58,.19,.59),.35,(0,-9,-7)),'blue')
 g.add(box((3.20,2.04,.90),(.54,.19,.53),.35,(0,12,9)),(.71,.48,.31))
 # Coffee table.
 g.add(cylinder_between((1.82,.13,.025),(1.82,.13,.42),.20,48),'walnut')
 g.add(cylinder_between((1.82,.13,.42),(1.82,.13,.49),.65,96),'wood',0,.42)
 # Notebook on tabletop.
 g.add(box((1.73,.26,.506),(.30,.22,.027),.10,(0,0,8)),'ink')
 g.add(box((1.73,.26,.514),(.28,.205,.014),.10,(0,0,8)),'cream')
 g.add(box((1.73,.26,.524),(.30,.22,.008),.08,(0,0,8)),'ink')
 g.add(cylinder_between((1.80,.29,.536),(1.92,.31,.536),.003,12),'bronze',.5,.3)
 # Ceramic cup.
 g.add(cylinder_between((2.18,.25,.495),(2.18,.25,.58),.034,32),'cream')
 g.add(ring((2.215,.25,.55),.022,(0,1,0),.005,24),'cream')
 # Dock credenza: 3 real-scale balloons occupy a long strip.
 g.add(box((-.94,2.53,.46),(2.78,.66,.80),.10),'wood',0,.54)
 for x in [-2.04,.14]:
  for y in [2.33,2.74]:g.add(cylinder_between((x,y,.01),(x,y,.12),.025,12),'walnut')
 g.add(box((-.94,2.53,.876),(2.81,.68,.055),.13),'cream')
 for x in [-1.43,-.48]:g.add(box((x,2.191,.47),(.008,.004,.66),.1),'walnut')
 g.add(box((-.94,2.48,.916),(2.46,.34,.048),.25),'dark',.1,.45)
 docks=[]
 for i,x in enumerate([-1.76,-.94,-.12]):
  g.add(cylinder_between((x,2.48,.938),(x,2.48,.971),.073,40),'rubber')
  g.add(ring((x,2.48,.974),.061,(0,0,1),.003,48),'teal',.1,.3,1)
  docks.append((x,2.441,1.407))
 # Art above console.
 g.add(box((-1,3.247,2.3),(1.50,.055,.82),.025),'wood')
 g.add(box((-1,3.209,2.3),(1.43,.017,.75),.025),'cream')
 g.add(sphere((-1.18,3.193,2.31),1,(.21,.01,.27),32),'clay')
 g.add(box((-.74,3.19,2.31),(.13,.019,.44),.15),'leaf')
 # Desk and laptop.
 for x in [-3.62,-2.45]:
  for y in [.77,1.34]:g.add(cylinder_between((x,y,.01),(x,y,.77),.027,12),'walnut')
 g.add(box((-3.03,1.07,.79),(1.45,.81,.065),.10),'wood')
 g.add(box((-2.94,.93,.834),(.43,.29,.018),.14),'rubber',.4,.3)
 g.add(box((-2.94,1.07,.98),(.43,.016,.30),.13,(12,0,0)),'dark',.4,.3)
 g.add(box((-2.94,1.054,.985),(.397,.006,.26),.12,(12,0,0)),'screen',.15,.3,.8)
 # Screen tiny glyph bars.
 for j,w in enumerate([.25,.18,.23,.11]):g.add(box((-2.96,1.045,1.05-j*.036),(w,.005,.009),.1),'teal',0,.6,.8)
 plant(g,(-3.5,1.16,.83),.48);plant(g,(4.1,2.8,.0),1.4)
 # Floor lamp.
 g.add(cylinder_between((3.98,1.42,.01),(3.98,1.42,.06),.17,40),'dark')
 g.add(cylinder_between((3.98,1.42,.06),(3.98,1.42,1.75),.012,20),'bronze',.5,.4)
 g.add(sphere((3.98,1.42,1.82),1,(.25,.25,.14),32),'cream',0,.8,.2)
 return g.build()[0],docks

def make_keys():
 g=Group(); pos=np.array([1.62,-.09,.514])
 g.add(ring(pos,.025,(0,0,1),.003,40),'bronze',.75,.25)
 for j,(angle,ln) in enumerate([(-.6,.079),(.22,.072)]):
  direction=np.array([math.sin(angle),-math.cos(angle),0]);start=pos+direction*.024;end=start+direction*ln
  g.add(cylinder_between(start,end,.006,12),'bronze',.65,.3)
  for q in [.055,.072]:
   cen=start+direction*q;per=np.array([-direction[1],direction[0],0]);g.add(cylinder_between(cen,cen+per*.011,.004,10),'bronze',.65,.3)
 # Key fob.
 g.add(box((1.663,-.054,.521),(.025,.055,.012),.5,(0,0,-30)),'dark',.15,.4)
 return g.build()[0],pos

def make_person():
 root=vtk.vtkAssembly();body=Group()
 body.add(box((0,0,1.22),(.39,.235,.52),.48),'shirt')
 body.add(sphere((0,0,1.62),1,(.095,.085,.124),40),'skin')
 body.add(cylinder_between((0,0,1.43),(0,0,1.54),.047,20),'skin')
 body.add(box((0,0,.92),(.32,.20,.17),.4),'pants')
 # Short, simple hairstyle; character deliberately stylized and faceless.
 body.add(sphere((0,.015,1.707),1,(.098,.087,.057),32),'dark')
 root.AddPart(body.build()[0]);limbs=[]
 for side in [-1,1]:
  for limb in ['leg','arm']:
   gg=Group()
   if limb=='leg':
    gg.add(cylinder_between((side*.10,0,0),(side*.10,0,-.73),.073,20),'pants')
    gg.add(box((side*.10,-.055,-.77),(.15,.26,.10),.45),'white')
    pivot=(0,0,.86)
   else:
    gg.add(cylinder_between((side*.235,0,0),(side*.245,0,-.42),.049,20),'shirt')
    gg.add(sphere((side*.245,0,-.47),1,(.038,.037,.063),24),'skin');pivot=(0,0,1.40)
   a=gg.build()[0];a.SetPosition(*pivot);root.AddPart(a);limbs.append((a,side,limb))
 return root,limbs

class Film:
 def __init__(self):
  self.renderer=vtk.vtkRenderer();r=self.renderer;r.SetBackground(.86,.87,.82);r.SetBackground2(.91,.93,.89);r.GradientBackgroundOn()
  self.win=vtk.vtkRenderWindow();self.win.SetOffScreenRendering(1);self.win.SetSize(RW,RH);self.win.SetMultiSamples(0);self.win.AddRenderer(r)
  # A generated linear-HDR light environment: broad overhead softboxes, not external imagery.
  eh,ew=128,256; yy,xx=np.mgrid[0:eh,0:ew];env=np.zeros((eh,ew,3),np.float32)
  env[:]=(.30,.34,.33)
  for cx,cy,sx,sy,power,color in [(50,25,24,17,2.7,(1,.94,.85)),(195,40,37,24,1.9,(.82,.94,1)),(112,85,70,20,.30,(.85,.85,.78))]:
   w=np.exp(-.5*((xx-cx)/sx)**2-.5*((yy-cy)/sy)**2)*power;env+=w[:,:,None]*np.array(color)
  image=vtk.vtkImageData();image.SetDimensions(ew,eh,1);image.GetPointData().SetScalars(numpy_to_vtk(env.reshape(-1,3),deep=True))
  texture=vtk.vtkTexture();texture.SetInputData(image);texture.InterpolateOn();texture.MipmapOn();r.UseImageBasedLightingOn();r.SetEnvironmentTexture(texture)
  r.SetEnvironmentUp(0,0,1);r.SetEnvironmentRight(1,0,0)
  for p,f,inten,col in [((-3,-2,6),(0,1,0),1.8,(1,.95,.86)),((4,-1,4),(0,1,1),.8,(.86,.94,1)),((0,3,4),(0,0,1),.5,(1,1,1))]:
   light=vtk.vtkLight();light.SetPosition(*p);light.SetFocalPoint(*f);light.SetLightTypeToSceneLight();light.SetIntensity(inten);light.SetColor(*col);r.AddLight(light)
  r.AutomaticLightCreationOff()
  steps=vtk.vtkRenderStepsPass();ao=vtk.vtkSSAOPass();ao.SetRadius(.18);ao.SetBias(.006);ao.SetKernelSize(24);ao.BlurOn();ao.SetDelegatePass(steps)
  tone=vtk.vtkToneMappingPass();tone.SetToneMappingType(vtk.vtkToneMappingPass.GenericFilmic);tone.SetGenericFilmicDefaultPresets();tone.SetExposure(1.05);tone.SetDelegatePass(ao);r.SetPass(tone)
  r.SetUseFXAA(True)
  self.room,self.docks=make_room();r.AddViewProp(self.room)
  self.keys,self.keypos=make_keys();r.AddViewProp(self.keys)
  self.person,self.limbs=make_person();r.AddViewProp(self.person)
  self.robots=[make_robot(i) for i in range(3)]
  for bot in self.robots:r.AddViewProp(bot['root'])
  self.studio=Group();self.studio.add(box((0,0,-.055),(30,30,.1),.02),(.86,.88,.84));self.studio=self.studio.build()[0];r.AddViewProp(self.studio)
  # Broad, subtle contact shadows represented as layered transparent planes.
  self.shadows=[]
  for i in range(4):
   g=Group()
   for j in range(6):g.add(sphere((0,0,.007+j*.0002),1,(.22+j*.035,.15+j*.025,.0001),32),'dark',0,1,0,.016)
   a=g.build()[0];r.AddViewProp(a);self.shadows.append(a)
  self.camera=r.GetActiveCamera();self.camera.SetViewUp(0,0,1);self.camera.ParallelProjectionOn();self.camera.SetClippingRange(.03,70)
  self.w2i=vtk.vtkWindowToImageFilter();self.w2i.SetInput(self.win);self.w2i.SetInputBufferTypeToRGB();self.w2i.ReadFrontBufferOff()
  self.last_scene=None
 def projected(self,p):
  r=self.renderer;r.SetWorldPoint(*p,1);r.WorldToDisplay();v=r.GetDisplayPoint();return (v[0]*W/RW,(RH-v[1])*H/RH)
 def update(self,t):
  # Continuous movements within five edited shots.
  scene=0 if t<5 else 1 if t<10.5 else 2 if t<16.7 else 3 if t<23 else 4
  self.scene=scene;self.person.SetVisibility(scene==1);self.room.SetVisibility(scene!=4);self.keys.SetVisibility(scene!=4);self.studio.SetVisibility(scene==4)
  for i,bot in enumerate(self.robots):bot['root'].SetVisibility(scene==3 or i==0)
  for i,s in enumerate(self.shadows):s.SetVisibility(False)
  bob=.006*math.sin(t*2.1)
  if scene==0:
   u=t/5;pos=(-.35,1.04,1.51+bob);yaw=-7+10*u
   cam=mix((1.40,-2.55,2.12),(1.18,-2.42,1.95),smooth(u));target=(-.72,1.03,1.41);scale=.87
   pose_robot(self.robots[0],pos,yaw,t)
  elif scene==1:
   u=(t-5)/5.5;q=smooth(u);person=mix((-2.12,-.12,0),(-.56,-.68,0),q);bot=mix((-3.13,-.06,1.44),(-1.62,-.66,1.45),q);bot[2]+=bob
   self.person.SetPosition(*person);self.person.SetOrientation(0,0,70)
   for limb,side,kind in self.limbs:limb.SetOrientation(math.sin(t*6)*side*(16 if kind=='leg' else -17)*math.sin(math.pi*u),0,0)
   pose_robot(self.robots[0],bot,62,t)
   cam=mix((5.0,-7.3,3.55),(4.6,-7.0,3.35),u);target=(-.9,.35,1.02);scale=1.73
   for idx,p in enumerate([bot,person]):self.shadows[idx].SetVisibility(True);self.shadows[idx].SetPosition(p[0],p[1],0)
  elif scene==2:
   u=(t-10.5)/6.2;q=smooth(min(u*1.6,1));bot=mix((.38,.04,1.39),(.92,-.33,1.22),q);bot[2]+=bob
   pose_robot(self.robots[0],bot,103+6*q,t,pitch=23*q)
   cam=mix((4.6,-4.6,3.55),(4.35,-4.35,3.30),u);target=(1.35,.10,1.02);scale=1.06
   self.shadows[0].SetVisibility(True);self.shadows[0].SetPosition(bot[0],bot[1],0)
  elif scene==3:
   u=(t-16.7)/6.3
   d0=np.array(self.docks[0]);d1=np.array(self.docks[1]);d2=np.array(self.docks[2])
   arr=smooth(min(u/.49,1));bot=mix(d0+np.array([-.15,-.78,.39]),d0,arr);bot[2]+=(1-arr)*bob
   dep=smooth(np.clip((u-.49)/.48,0,1));second=mix(d1,d1+np.array([.22,-.87,.35]),dep);second[2]+=dep*bob
   pose_robot(self.robots[0],bot,0,t,arr<.99);pose_robot(self.robots[1],second,0-20*dep,t,dep>.01);pose_robot(self.robots[2],d2,0,t,False)
   cam=mix((1.45,-2.7,2.55),(1.23,-2.52,2.48),u);target=(-.95,2.30,1.32);scale=1.04
  else:
   u=(t-23)/5;bot=(.50,0,1.08+bob);pose_robot(self.robots[0],bot,-9+14*u,t)
   cam=mix((1.8,-4.0,1.65),(1.5,-3.9,1.57),smooth(u));target=(-.05,0,1.00);scale=.83
   self.shadows[0].SetVisibility(True);self.shadows[0].SetPosition(.5,0,0)
  self.camera.SetPosition(*cam);self.camera.SetFocalPoint(*target);self.camera.SetParallelScale(scale);self.camera.SetClippingRange(.05,60)
  for shadow in self.shadows: shadow.SetVisibility(False)
  self.current_robot=pos if scene==0 else bot
 def frame(self,t):
  self.update(t);self.win.Render();self.w2i.Modified();self.w2i.Update();arr=vtk_to_numpy(self.w2i.GetOutput().GetPointData().GetScalars()).reshape(RH,RW,3)[::-1].copy()
  im=Image.fromarray(arr).resize((W,H),Image.Resampling.LANCZOS)
  return overlay(im,t,self)

FONTP=Path('/usr/share/fonts/opentype/inter')
FONTS={}
def font(size,weight='Regular'):
 key=(size,weight)
 if key not in FONTS:FONTS[key]=ImageFont.truetype(str(FONTP/f'InterDisplay-{weight}.otf'),size)
 return FONTS[key]
INK=(22,46,47);MUTED=(66,85,83);TEAL=(15,128,112);PAPER=(244,245,237)
def text(draw,xy,s,size=32,fill=INK,weight='Regular',alpha=255,anchor=None):
 draw.text(xy,s,font=font(size,weight),fill=(*fill,alpha),anchor=anchor,stroke_width=0)
def track(draw,xy,s,size=20,spacing=3,fill=INK,alpha=255):
 x,y=xy;f=font(size,'Medium')
 for char in s:
  draw.text((x,y),char,font=f,fill=(*fill,alpha));x+=draw.textlength(char,font=f)+spacing
 return x

def opacity(t,start,dur=.6,end=None):
 v=smooth((t-start)/dur)
 if end is not None:v*=smooth((end-t)/dur)
 return int(v*255)

def overlay(im,t,film):
 # The text is designed at output resolution for readable, clean typography.
 lay=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(lay)
 scene=film.scene
 # Consistent quiet brand and explicit concept status.
 for i in range(3):d.ellipse((69+i*11,67,74+i*11,72),fill=(*TEAL,230))
 track(d,(116,56),'FLOAT',24,5)
 text(d,(285,60),' /  CONCEPT 01',18,MUTED,'Medium')
 d.rounded_rectangle((1515,53,1850,95),radius=21,fill=(*PAPER,216),outline=(161,173,163,160),width=1)
 track(d,(1537,65),'CONCEPT VISUALIZATION',13,1.3,fill=MUTED)
 # Soft footer separation, persistent honesty label.
 grad=Image.new('RGBA',(W,105),(0,0,0,0));ga=np.zeros((105,W,4),np.uint8);ga[:,:,:3]=PAPER;ga[:,:,3]=(np.linspace(0,220,105)[:,None]);grad=Image.fromarray(ga);lay.alpha_composite(grad,(0,H-105));d=ImageDraw.Draw(lay)
 text(d,(70,1020),'Proposed experience. Not footage of a working prototype.',18,MUTED,'Regular')
 text(d,(1850,1020),f'0{scene+1} / 05',18,MUTED,'Medium',anchor='ra')
 if scene==0:
  a=opacity(t,.3,.8,end=5)
  # Left-side copy on a very light, broad gradient; scene remains visible.
  g=np.zeros((740,830,4),np.uint8);g[:,:,:3]=PAPER;g[:,:,3]=(np.linspace(150,0,830)[None,:]).astype('uint8');panel=Image.fromarray(g);lay.alpha_composite(panel,(0,150));d=ImageDraw.Draw(lay)
  track(d,(77,292),'MEET YOUR FLOATING COMPANION',15,2.1,TEAL,a)
  text(d,(70,336),'An AI companion.',66,INK,'Medium',a)
  text(d,(70,414),'Beyond the screen.',66,INK,'Medium',a)
  text(d,(75,515),'A buoyant, room-to-room presence.',25,MUTED,'Regular',a)
  # Physical scale cue: no microscopic drone implied.
  p=film.projected(np.array(film.current_robot)+np.array([.32,0,.22]));x,y=p
  if x<W-200:
   d.line((x,y,x+56,y-35),fill=(*MUTED,a),width=2);text(d,(x+65,y-55),'≈ 60 cm',22,MUTED,'Medium',a)
 elif scene==1:
  a=opacity(t,5.3,.5,end=10.5)
  d.rounded_rectangle((58,757,900,954),22,fill=(*PAPER,int(.92*a)))
  track(d,(81,780),'01  /  FOLLOW',15,2,TEAL,a)
  text(d,(77,813),'It comes with you.',56,INK,'Medium',a)
  text(d,(80,887),'Designed to follow, listen and respond.',24,MUTED,'Regular',a)
  a2=opacity(t,6.0,.4,end=8.7)
  if a2:
   p=np.array(film.person.GetPosition())+np.array([.12,-.1,1.78]);x,y=film.projected(p);x=np.clip(x,300,1300);y=max(y-85,130)
   d.rounded_rectangle((x-60,y,x+240,y+66),radius=25,fill=(*PAPER,int(.95*a2)))
   text(d,(x-35,y+17),'“Come with me.”',25,INK,'Medium',a2)
 elif scene==2:
  a=opacity(t,10.8,.5,end=16.7)
  if t<13.2:
   text(d,(73,171),'“Where are my keys?”',56,INK,'Medium',a)
   text(d,(77,247),'A new point of view.',25,MUTED,'Regular',a)
  else:
   a2=opacity(t,13.2,.4,end=16.7)
   d.rounded_rectangle((61,760,939,954),22,fill=(*PAPER,int(.94*a2)))
   track(d,(82,782),'02  /  FIND',15,2,TEAL,a2)
   text(d,(78,815),'See together. Find together.',46,INK,'Medium',a2)
   text(d,(82,885),'“On the table, beside the notebook.”',24,MUTED,'Regular',a2)
   x,y=film.projected(film.keypos);rr=25+5*math.sin(t*4)
   d.ellipse((x-rr,y-rr,x+rr,y+rr),outline=(*TEAL,a2),width=3)
   for dx,dy in [(-1,-1),(-1,1),(1,-1),(1,1)]:
    xx=x+dx*40;yy=y+dy*30;d.line((xx-dx*12,yy,xx,yy,xx,yy-dy*10),fill=(*TEAL,a2),width=3)
   # An explicitly simulated phone-notification concept card.
   cx,cy=1433,212
   d.rounded_rectangle((cx,cy,cx+407,cy+174),radius=24,fill=(*PAPER,int(.96*a2)),outline=(*MUTED,int(.25*a2)),width=1)
   d.ellipse((cx+24,cy+23,cx+43,cy+42),fill=(*TEAL,a2));text(d,(cx+57,cy+22),'FLOAT  ·  PHONE PREVIEW',15,MUTED,'Medium',a2)
   text(d,(cx+24,cy+61),'Keys found',32,INK,'Medium',a2)
   text(d,(cx+24,cy+110),'Beside the notebook.',21,MUTED,'Regular',a2)
 elif scene==3:
  a=opacity(t,17,.5,end=23)
  d.rounded_rectangle((60,761,1130,958),22,fill=(*PAPER,int(.94*a)))
  track(d,(83,780),'03  /  RECHARGE & HAND OVER',15,2,TEAL,a)
  text(d,(78,814),'One returns. Another takes over.',48,INK,'Medium',a)
  text(d,(82,886),'A shared dock for a rotating fleet.',25,MUTED,'Regular',a)
  if t>19.8:
   a2=opacity(t,19.8,.5,end=23)
   for i,label in [(0,'RECHARGING'),(2,'READY')]:
    p=film.projected(np.array(film.docks[i])+np.array([0,0,-.55]));x,y=p
    d.rounded_rectangle((x-86,y-20,x+86,y+17),18,fill=(*PAPER,int(.95*a2)))
    track(d,(x-68,y-10),label,12,1.1,TEAL,a2)
 else:
  a=opacity(t,23.3,.65)
  track(d,(78,281),'FLOAT',24,6,TEAL,a)
  text(d,(70,343),'Less screen.',83,INK,'Medium',a)
  text(d,(70,434),'More presence.',83,INK,'Medium',a)
  text(d,(77,555),'A floating AI companion.',29,MUTED,'Regular',a)
  text(d,(77,624),'Early hardware concept',19,MUTED,'Medium',a)
 # Fine editorial progress rule.
 d.line((70,990,1850,990),fill=(110,130,123,55),width=1)
 d.line((70,990,70+1780*min(t/DURATION,1),990),fill=(*TEAL,130),width=2)
 out=Image.alpha_composite(im.convert('RGBA'),lay).convert('RGB')
 # 4-frame dip to a warm white at shot boundaries; real animated scenes between edits.
 fade=1.0
 for cut in [5,10.5,16.7,23]:
  dist=abs(t-cut)
  if dist<.105:fade=min(fade,dist/.105)
 if t<.22:fade=min(fade,float(smooth(t/.22)))
 if fade<1:out=Image.blend(Image.new('RGB',(W,H),PAPER),out,fade)
 return out

def make_audio():
 sr=48000;n=int((DURATION+.1)*sr);stereo=np.zeros((n,2),np.float64);rng=np.random.default_rng(20261015)
 def note(start,dur,freq,level=.03,pan=0,kind='pad'):
  count=int(dur*sr);tt=np.arange(count)/sr
  if kind=='pad':
   signal=np.sin(2*np.pi*freq*tt)+.20*np.sin(2*np.pi*freq*2*tt+.2)+.06*np.sin(2*np.pi*freq*3*tt)
   env=np.minimum(tt/.7,1)*np.minimum((dur-tt)/1.1,1);signal*=np.maximum(env,0)
  else:
   signal=(np.sin(2*np.pi*freq*tt)+.25*np.sin(2*np.pi*freq*2.003*tt))*np.exp(-tt/1.05)*np.minimum(tt/.014,1)
  signal*=level;i=int(start*sr);j=min(i+count,n);signal=signal[:j-i];stereo[i:j,0]+=signal*math.sqrt((1-pan)/2);stereo[i:j,1]+=signal*math.sqrt((1+pan)/2)
 chords=[[130.81,196,246.94,329.63],[110,164.81,220,261.63],[87.31,130.81,174.61,220],[98,146.83,196,246.94]]
 for k in range(8):
  start=k*3.5;ch=chords[k%4]
  for j,f in enumerate(ch):note(start,4.2,f,.025,(-.6+j*.4))
  for j in range(4):note(start+.42+j*.69,1.8,ch[(j+k)%4]*2,.029,(-.5+j*.33),'bell')
 for t in [4.96,13.25,20.2,23.1]:
  note(t,1.3,659.255,.035,-.2,'bell');note(t+.14,1.4,987.767,.028,.25,'bell')
 # Short restrained air transitions.
 for start in [4.8,10.3,16.5,22.8]:
  dur=.45;num=int(dur*sr);raw=rng.normal(0,1,num);sm=np.convolve(raw,np.ones(31)/31,'same');env=np.sin(np.linspace(0,np.pi,num))**2;sig=sm*env*.020;idx=int(start*sr);stereo[idx:idx+num]+=sig[:,None]
 times=np.arange(n)/sr;env=np.minimum(times/1.0,1)*np.clip((DURATION-times)/1.5,0,1);stereo*=env[:,None]
 stereo=np.tanh(stereo*1.5);peak=np.max(abs(stereo));stereo*=.55/max(peak,.001)
 pcm=(stereo[:int(DURATION*sr)]*32767).astype('<i2')
 with wave.open(str(ROOT/'render/score.wav'),'wb') as f:f.setnchannels(2);f.setsampwidth(2);f.setframerate(sr);f.writeframes(pcm.tobytes())

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--previews',action='store_true');ap.add_argument('--start',type=int,default=0);ap.add_argument('--end',type=int,default=int(FPS*DURATION));args=ap.parse_args()
 film=Film()
 if args.previews:
  for t in [2.4,7.6,14.4,20.6,25.8]:
   tt=time.monotonic();im=film.frame(t);im.save(ROOT/'render'/f'preview_{t:04.1f}.jpg',quality=94);print('preview',t,round(time.monotonic()-tt,3),flush=True)
 else:
  make_audio();out=ROOT/'render/silent.mp4'
  cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(out)]
  proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
  start=time.monotonic()
  try:
   for i in range(args.start,args.end):
    im=film.frame(i/FPS);proc.stdin.write(np.asarray(im).tobytes())
    if i%48==0:print(f'frame {i}/{args.end} wall={time.monotonic()-start:.1f}s',flush=True)
   proc.stdin.close();ret=proc.wait()
   if ret:raise RuntimeError('ffmpeg encoding failed')
  except BaseException:
   proc.kill();raise
  final=ROOT/'FLOAT_concept_film.mp4'
  subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(out),'-i',str(ROOT/'render/score.wav'),'-c:v','copy','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',str(final)],check=True)
  print('FINAL',final,flush=True)
