"""FLOAT / Presence: original CGI concept teaser. Not prototype footage.
Procedural geometry and soundtrack. Needs VTK, numpy, Pillow, scipy and ffmpeg.
No fonts are distributed. Set FLOAT_FONT_DIR for a locally licensed Inter install.
"""
import os
os.environ.setdefault('VTK_DEFAULT_OPENGL_WINDOW','vtkEGLRenderWindow')
os.environ.setdefault('OMP_NUM_THREADS','4')
import sys, math, time, argparse, subprocess, json, wave
from pathlib import Path
from collections import defaultdict
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import vtk
from vtk.util.numpy_support import vtk_to_numpy,numpy_to_vtk
ROOT=Path(__file__).resolve().parents[1]
for q in ['previews','renders','assets','deliverables']: (ROOT/q).mkdir(exist_ok=True)
W,H=1920,1080; FPS=24; DUR=30
C={'foil':(.58,.61,.61),'seam':(.41,.44,.44),'ink':(.078,.093,.105),'rubber':(.023,.026,.028),'silver':(.63,.68,.70),'lens':(.014,.025,.029),'gold':(.76,.47,.19),'light':(.98,.96,.91),'wood':(.27,.12,.052),'stone':(.22,.21,.19),'dark':(.025,.030,.035)}

def smooth(x):
 x=np.clip(x,0,1);return x*x*(3-2*x)
def mix(a,b,u):return np.array(a)*(1-u)+np.array(b)*u

def transform(poly,pos=(0,0,0),scale=(1,1,1),rot=(0,0,0)):
 tr=vtk.vtkTransform();tr.Translate(*pos);tr.RotateZ(rot[2]);tr.RotateY(rot[1]);tr.RotateX(rot[0]);tr.Scale(*scale)
 f=vtk.vtkTransformPolyDataFilter();f.SetInputData(poly);f.SetTransform(tr);f.Update();p=vtk.vtkPolyData();p.ShallowCopy(f.GetOutput());return p

def sphere(pos=(0,0,0),r=1,scale=(1,1,1),res=64):
 s=vtk.vtkSphereSource();s.SetRadius(r);s.SetThetaResolution(res);s.SetPhiResolution(res//2);s.Update();return transform(s.GetOutput(),pos,scale)
def box(pos,dims,rough=.16,rot=(0,0,0)):
 s=vtk.vtkSuperquadricSource();s.SetThetaResolution(48);s.SetPhiResolution(32);s.SetPhiRoundness(rough);s.SetThetaRoundness(rough);s.Update();return transform(s.GetOutput(),pos,dims,rot)
def cyl(a,b,r,res=24):
 a=np.array(a,float);b=np.array(b,float);d=b-a;ln=np.linalg.norm(d);d/=ln
 s=vtk.vtkCylinderSource();s.SetRadius(r);s.SetHeight(ln);s.SetResolution(res);s.CappingOn();s.Update()
 tr=vtk.vtkTransform();tr.Translate(*((a+b)*.5));ax=np.cross((0,1,0),d)
 if np.linalg.norm(ax)>1e-9:tr.RotateWXYZ(np.degrees(np.arccos(np.clip(d[1],-1,1))),*(ax/np.linalg.norm(ax)))
 elif d[1]<0:tr.RotateX(180)
 f=vtk.vtkTransformPolyDataFilter();f.SetInputData(s.GetOutput());f.SetTransform(tr);f.Update();p=vtk.vtkPolyData();p.ShallowCopy(f.GetOutput());return p

def tube(points,r=.001,closed=False,sides=8):
 pts=vtk.vtkPoints();pts.SetData(numpy_to_vtk(np.array(points,np.float32),deep=True));p=vtk.vtkPolyData();p.SetPoints(pts)
 ln=vtk.vtkPolyLine();ln.GetPointIds().SetNumberOfIds(len(points)+int(closed))
 for i in range(len(points)):ln.GetPointIds().SetId(i,i)
 if closed:ln.GetPointIds().SetId(len(points),0)
 ls=vtk.vtkCellArray();ls.InsertNextCell(ln);p.SetLines(ls);t=vtk.vtkTubeFilter();t.SetInputData(p);t.SetRadius(r);t.SetNumberOfSides(sides);t.CappingOn();t.Update();out=vtk.vtkPolyData();out.ShallowCopy(t.GetOutput());return out

def ring(c,r,axis=(0,0,1),th=.001,n=72):
 a=np.array(axis,float);a/=np.linalg.norm(a);ref=(0,0,1) if abs(a[2])<.8 else (1,0,0);u=np.cross(a,ref);u/=np.linalg.norm(u);v=np.cross(a,u)
 return tube([np.array(c)+r*(np.cos(t)*u+np.sin(t)*v) for t in np.linspace(0,2*np.pi,n,endpoint=False)],th,True)

_WOOD_TEX=None

def wood_texture():
 global _WOOD_TEX
 if _WOOD_TEX is None:
  from scipy.ndimage import gaussian_filter
  n=1024;yy,xx=np.mgrid[0:n,0:n]/n;rng=np.random.default_rng(901)
  warp=yy+0.013*np.sin(xx*13)+0.008*np.sin(xx*4+yy*11)
  grain=.60*np.sin(2*np.pi*(warp*73))+.22*np.sin(2*np.pi*(warp*187))+.18*np.sin(2*np.pi*(warp*317))
  broad=gaussian_filter(rng.normal(0,1,(n,n)),(18,75));broad/=max(broad.std(),1e-6)
  tone=np.clip(.63+.06*grain+.045*broad+rng.normal(0,.008,(n,n)),.35,.87)
  rgb=np.clip(tone[:,:,None]*np.array([.59,.40,.26])[None,None,:]*255,0,255).astype(np.uint8)
  vi=vtk.vtkImageData();vi.SetDimensions(n,n,1);vi.GetPointData().SetScalars(numpy_to_vtk(rgb.reshape(-1,3),deep=True));tx=vtk.vtkTexture();tx.SetInputData(vi);tx.SetColorModeToDirectScalars();tx.InterpolateOn();tx.MipmapOn();tx.RepeatOn();tx.UseSRGBColorSpaceOn();_WOOD_TEX=tx
 return _WOOD_TEX

class Group:
 def __init__(self):self.geo=defaultdict(list)
 def add(self,p,mat='ink',metal=0.,rough=.5,emit=0,alpha=1.):self.geo[(mat,metal,rough,emit,alpha)].append(p)
 def build(self):
  root=vtk.vtkAssembly();actors=[]
  for (mat,metal,rough,emit,alpha),ps in self.geo.items():
   ap=vtk.vtkAppendPolyData()
   for p in ps:ap.AddInputData(p)
   ap.Update();norm=vtk.vtkPolyDataNormals();norm.SetInputConnection(ap.GetOutputPort());norm.SplittingOff();norm.Update()
   m=vtk.vtkPolyDataMapper();m.SetInputConnection(norm.GetOutputPort());a=vtk.vtkActor();a.SetMapper(m);p=a.GetProperty();col=C.get(mat,mat if isinstance(mat,tuple) else C['ink']);p.SetColor(*col);p.SetInterpolationToPBR();p.SetMetallic(metal);p.SetRoughness(rough);p.SetOpacity(alpha)
   if metal>.3:p.SetCoatStrength(.06);p.SetCoatRoughness(.2)
   if emit:p.SetEmissiveFactor(*[v*emit for v in col])
   if mat=='wood':
    poly=vtk.vtkPolyData();poly.DeepCopy(norm.GetOutput());vv=vtk_to_numpy(poly.GetPoints().GetData());uv=np.column_stack((vv[:,0]/2.6+.5,(vv[:,1]+.2)/1.6)).astype(np.float32)
    ar=numpy_to_vtk(uv,deep=True);ar.SetName('UV');poly.GetPointData().SetTCoords(ar);m.SetInputData(poly);p.SetColor(1,1,1);p.SetBaseColorTexture(wood_texture())
   root.AddPart(a);actors.append(a)
  return root,actors

def blade(center,axis,az):
 c=np.array(center);a=np.array(axis,float);ref=np.array([0,0,1]) if abs(a[2])<.8 else np.array([1,0,0]);u=np.cross(a,ref);u/=np.linalg.norm(u);v=np.cross(a,u);pts=[];cells=vtk.vtkCellArray()
 for i,t in enumerate(np.linspace(.005,.046,18)):
  ang=az+.22*(t/.046);d=np.cos(ang)*u+np.sin(ang)*v;side=-np.sin(ang)*u+np.cos(ang)*v;width=.002+.010*np.sin(np.pi*(t-.002)/.052)**.65
  for s in [-1,1]:pts.append(c+d*t+side*s*width*.5+a*s*.0018*(1-t/.06))
 for i in range(17):
  cell=vtk.vtkQuad()
  for j,k in enumerate([2*i,2*i+1,2*i+3,2*i+2]):cell.GetPointIds().SetId(j,k)
  cells.InsertNextCell(cell)
 p=vtk.vtkPolyData();q=vtk.vtkPoints();q.SetData(numpy_to_vtk(np.array(pts,np.float32),deep=True));p.SetPoints(q);p.SetPolys(cells);return p

def robot():
 g=Group();r=.31;s=vtk.vtkSphereSource();s.SetRadius(r);s.SetThetaResolution(192);s.SetPhiResolution(128);s.Update();p=vtk.vtkPolyData();p.DeepCopy(s.GetOutput());pts=vtk_to_numpy(p.GetPoints().GetData());az=np.arctan2(pts[:,1],pts[:,0]);lat=np.arccos(np.clip(pts[:,2]/r,-1,1));fac=1-.0030*np.cos(12*az)**12*np.maximum(np.sin(lat),0)**1.4+.00008*np.sin(92*lat+6*az);pts*=fac[:,None];p.GetPoints().Modified();g.add(p,'foil',.48,.39)
 for j in range(12):
  aa=j*2*np.pi/12;pp=[((r+.0002)*math.sin(t)*math.cos(aa),(r+.0002)*math.sin(t)*math.sin(aa),(r+.0002)*math.cos(t)) for t in np.linspace(.055,np.pi-.055,130)];g.add(tube(pp,.00047,sides=8),'seam',.68,.40)
 g.add(sphere((0,0,-.310),.013,(1,1,.2)),'rubber',0,.5)
 # Structural stays and low-mass suspended camera pod.
 for x,y in [(-.083,-.035),(.083,-.035),(0,.079)]:g.add(cyl((x,y,-math.sqrt(r*r-x*x-y*y)),(x*.37,y*.37,-.35),.00085,12),'ink',.6,.28)
 g.add(box((0,0,-.376),(.10,.070,.054),.32),'ink',.55,.30)
 g.add(box((0,.0325,-.376),(.088,.005,.042),.25),'silver',.75,.31)
 for rad,ya,yb,mat,met,rough in [(.0195,-.034,-.039,'rubber',.1,.31),(.018,-.039,-.042,'silver',.95,.22),(.0164,-.042,-.044,'ink',.75,.15),(.0128,-.044,-.0458,'lens',.95,.075)]:
  g.add(cyl((0,ya,-.370),(0,yb,-.370),rad,72),mat,met,rough)
 g.add(ring((0,-.0431,-.370),.0174,(0,1,0),.0006),'gold',.6,.2,.45)
 g.add(ring((0,-.0460,-.370),.0109,(0,1,0),.00015),(.12,.19,.21),.8,.08)
 for xx in [-.0062,.0041]:g.add(sphere((xx,-.0461,-.365),.0013,(1,.23,.60),24),'light',.4,.08,.2)
 for i in range(9):
  for j in range(2):g.add(sphere((-.033+i*.008,-.0351,-.393+j*.0026),.00075,(1,.25,1),12),'rubber')
 g.add(sphere((.035,-.035,-.368),.0017,(1,.35,1),16),'gold',.3,.20,2.5)
 root,actors=g.build();fans=[]
 configs=[((-.156,0,-.318),(0,1,0)),((.156,0,-.318),(0,1,0)),((0,.116,-.317),(1,0,0)),((0,.025,-.431),(0,0,1))]
 for c,ax in configs:
  c=np.array(c);a=np.array(ax,float);gg=Group();gg.add(cyl((0,.012,-.356),c,.0011,12),'ink',.6,.28)
  for off in [-.007,.007]:gg.add(ring(c+off*a,.052,ax,.0014),'ink',.50,.25)
  ref=(0,0,1) if abs(a[2])<.8 else (1,0,0);u=np.cross(a,ref);u/=np.linalg.norm(u);v=np.cross(a,u)
  for angle in np.linspace(0,2*np.pi,10,endpoint=False):
   edge=.052*(np.cos(angle)*u+np.sin(angle)*v);gg.add(cyl(c+edge-.007*a,c+edge+.007*a,.00065,6),'silver',.65,.28)
   gg.add(cyl(c+.008*a,c+edge+.008*a,.00037,6),'ink',.4,.35)
  gg.add(cyl(c-.004*a,c+.004*a,.0045,32),'silver',.7,.25);guard,_=gg.build();root.AddPart(guard)
  rr=Group()
  for az in [0,np.pi]:rr.add(blade(c,ax,az),'ink',.5,.34)
  rotor,_=rr.build();root.AddPart(rotor);fans.append((rotor,c,a))
 return dict(root=root,fans=fans,actors=actors)

def pose(bot,pos,yaw,t,active=True):
 bot['root'].SetPosition(*pos);bot['root'].SetOrientation(0,0,yaw)
 for a,c,ax in bot['fans']:
  tr=vtk.vtkTransform();tr.Translate(*c);tr.RotateWXYZ(t*2261 if active else 31,*ax);tr.Translate(*(-c));a.SetUserTransform(tr)

def gaussian_shadow(center,rx,ry,alpha=.30):
 n=256;y,x=np.mgrid[-1:1:complex(n),-1:1:complex(n)];im=np.zeros((n,n,4),np.uint8);im[:,:,:3]=[3,5,7];im[:,:,3]=(np.exp(-4*(x*x+y*y))*alpha*255).astype(np.uint8)
 vi=vtk.vtkImageData();vi.SetDimensions(n,n,1);vi.GetPointData().SetScalars(numpy_to_vtk(im.reshape(-1,4),deep=True));tex=vtk.vtkTexture();tex.SetInputData(vi);tex.InterpolateOn()
 pl=vtk.vtkPlaneSource();pl.SetOrigin(-rx,-ry,0);pl.SetPoint1(rx,-ry,0);pl.SetPoint2(-rx,ry,0);pl.Update();mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(pl.GetOutputPort());ac=vtk.vtkActor();ac.SetMapper(mapper);ac.SetTexture(tex);ac.GetProperty().SetLighting(False);ac.SetPosition(*center);return ac

def keys():
 g=Group();loc=np.array([.14,-.07,.786]);g.add(ring(loc,.018,(0,0,1),.0015),'silver',.95,.18)
 for az,ln in [(-.8,.064),(.35,.052)]:
  d=np.array([np.sin(az),-np.cos(az),0]);p=loc+d*.028;g.add(box(p,(.023,.026,.0025),.2,(0,0,-az*180/np.pi)),'gold',.88,.19);a=p+d*.01;b=a+d*ln;g.add(cyl(a,b,.003,12),'gold',.85,.2)
  for q in [.023,.030,.045]:
   per=np.array([-d[1],d[0],0]);v=a+d*q;g.add(cyl(v,v+.006*per,.0019,10),'gold',.85,.2)
 g.add(box((.174,-.037,.791),(.033,.061,.009),.35,(0,0,-20)),'rubber',.1,.40)
 g.add(ring((.174,-.038,.796),.007,(0,0,1),.0005),'silver',.7,.3)
 return g.build()[0],loc

class Film:
 def __init__(self,w=1920,h=1080):
  self.w,self.h=w,h;r=vtk.vtkRenderer();self.r=r;r.SetBackground(.008,.014,.020);r.SetBackground2(.040,.048,.056);r.GradientBackgroundOn();r.AutomaticLightCreationOff();r.SetUseFXAA(True)
  win=vtk.vtkRenderWindow();win.SetOffScreenRendering(True);win.SetSize(w,h);win.SetMultiSamples(0);win.AddRenderer(r);self.win=win
  # Linear HDR studio map: narrow rim strips, a broad warm softbox, dim fill.
  eh,ew=256,512;yy,xx=np.mgrid[0:eh,0:ew];env=np.empty((eh,ew,3),np.float32);env[:]=(.016,.024,.031)
  def softrect(cx,cy,sx,sy,power,col):
   w=np.exp(-((xx-cx)/sx)**8-((yy-cy)/sy)**8);env[:]+=w[:,:,None]*np.array(col)*power
  softrect(77,51,27,68,3.8,(1,.92,.82));softrect(300,65,9,81,5.5,(.75,.87,1));softrect(194,13,65,11,1.6,(1,.96,.90))
  vi=vtk.vtkImageData();vi.SetDimensions(ew,eh,1);vi.GetPointData().SetScalars(numpy_to_vtk(env.reshape(-1,3),deep=True));tx=vtk.vtkTexture();tx.SetInputData(vi);tx.SetColorModeToDirectScalars();tx.InterpolateOn();tx.MipmapOn();r.UseImageBasedLightingOn();r.SetEnvironmentTexture(tx);r.SetEnvironmentUp(0,0,1);r.SetEnvironmentRight(1,0,0)
  self.lights=[]
  for p,f,inten,col in [((-2.3,-3.5,4.2),(0,0,1),2.0,(1,.85,.67)),((2.0,.4,3.2),(0,0,1),2.5,(.62,.79,1)),((0,-3,1.5),(0,0,1),.35,(1,.96,.91))]:
   l=vtk.vtkLight();l.SetLightTypeToSceneLight();l.SetPosition(*p);l.SetFocalPoint(*f);l.SetIntensity(inten);l.SetColor(*col);l.SetSpecularColor(0,0,0);r.AddLight(l);self.lights.append(l)
  steps=vtk.vtkRenderStepsPass();ss=vtk.vtkSSAOPass();ss.SetDelegatePass(steps);ss.SetRadius(.055);ss.SetBias(.0007);ss.SetKernelSize(48);ss.BlurOn()
  tone=vtk.vtkToneMappingPass();tone.SetToneMappingType(vtk.vtkToneMappingPass.GenericFilmic);tone.SetGenericFilmicDefaultPresets();tone.SetExposure(.95);tone.SetDelegatePass(ss);r.SetPass(tone)
  self.cam=r.GetActiveCamera();self.cam.ParallelProjectionOff();self.cam.SetViewUp(0,0,1);self.cam.SetViewAngle(30);self.cam.SetClippingRange(.004,60)
  self.bots=[robot() for _ in range(3)]
  for bot in self.bots:r.AddViewProp(bot['root'])
  # Studio: quiet dark ground, no toy furniture or stick-figure humans.
  studio=Group();studio.add(box((0,0,-.09),(40,40,.15),.01),(.018,.024,.030),.25,.5);self.studio=studio.build()[0];r.AddViewProp(self.studio)
  # Designed interior set: walnut tabletop, plaster wall, slatted light and furnishings.
  envg=Group();envg.add(box((0,.6,.733),(2.5,1.45,.08),.12),'wood',.03,.48)
  for x in [-.94,.94]:envg.add(box((x,.72,.34),(.055,.73,.70),.1),'ink',.3,.34)
  envg.add(box((0,1.7,1.75),(20,.11,6),.05),(.15,.17,.17),0,.85)
  envg.add(box((0,0,-.065),(14,14,.1),.03),(.13,.11,.088),.02,.7)
  # Long, raking warm window-light strips as physical set panels.
  for i in range(6):
   envg.add(box((-2.0+i*.42,1.635,1.60),(.16,.008,2.8),.05,(0,0,0)),(.19,.17,.13),.0,.85,.05)
  envg.add(box((-.66,.33,.787),(.30,.245,.022),.10,(0,0,11)),'ink',.2,.35)
  envg.add(box((-.66,.33,.798),(.292,.231,.012),.09,(0,0,11)),(.63,.59,.49),0,.75)
  envg.add(box((-.66,.33,.807),(.30,.245,.005),.06,(0,0,11)),'ink',.1,.4)
  envg.add(cyl((-.75,.35,.814),(-.57,.386,.814),.0025),'gold',.75,.21)
  # Ceramic cup with dark coffee and a small handle.
  envg.add(cyl((.55,.44,.775),(.55,.44,.876),.037,64),(.67,.62,.50),.03,.3)
  envg.add(cyl((.55,.44,.8765),(.55,.44,.878),.031,64),(.025,.012,.006),.15,.16)
  envg.add(ring((.587,.44,.825),.023,(0,1,0),.006),(.67,.62,.50),.03,.3)
  self.env=envg.build()[0];r.AddViewProp(self.env);self.keys,self.keypos=keys();r.AddViewProp(self.keys)
  self.keyshadow=gaussian_shadow((.14,-.07,.777),.11,.105,.8);r.AddViewProp(self.keyshadow)
  # Shared dock: physically long enough for three approximately62cm bodies.
  dg=Group();dg.add(box((0,.1,.67),(2.5,.64,.10),.18),'wood',.1,.38);dg.add(box((0,.1,.741),(2.35,.28,.046),.18),'ink',.65,.28)
  dg.add(box((0,.10,.762),(2.22,.24,.004),.14),(.055,.062,.071),.60,.2)
  for x in [-1.05,1.05]:dg.add(box((x,.1,.29),(.045,.47,.70),.12),'ink',.2,.4)
  for x in [-.8,0,.8]:
   dg.add(cyl((x,.1,.765),(x,.1,.795),.06,64),'rubber',.2,.4)
   dg.add(ring((x,.1,.797),.046,(0,0,1),.0015),'gold',.4,.2,1.3)
   for dx in [-.014,.014]:dg.add(cyl((x+dx,.1,.80),(x+dx,.1,.804),.003,16),'gold',.9,.2)
  self.dock=dg.build()[0];r.AddViewProp(self.dock)
  self.shadows=[]
  for _ in range(3):
   ac=gaussian_shadow((0,0,.003),.6,.5,.52);r.AddViewProp(ac);self.shadows.append(ac)
  self.w2i=vtk.vtkWindowToImageFilter();self.w2i.SetInput(win);self.w2i.SetInputBufferTypeToRGB();self.w2i.ReadFrontBufferOff();self.w2i.ShouldRerenderOff()
  self.z2i=vtk.vtkWindowToImageFilter();self.z2i.SetInput(win);self.z2i.SetInputBufferTypeToZBuffer();self.z2i.ReadFrontBufferOff();self.z2i.ShouldRerenderOff()
 def project(self,p):
  self.r.SetWorldPoint(*p,1);self.r.WorldToDisplay();q=self.r.GetDisplayPoint();return np.array([q[0]*W/self.w,(self.h-q[1])*H/self.h])
 def update(self,t):
  self.scene=0 if t<3 else 1 if t<7 else 2 if t<12 else 3 if t<16 else 4 if t<23 else 5 if t<27 else 6
  s=self.scene;bb=.004*np.sin(t*1.2);self.env.SetVisibility(s in [2,3]);self.keys.SetVisibility(s in [2,3]);self.keyshadow.SetVisibility(s in [2,3]);self.studio.SetVisibility(False);self.dock.SetVisibility(s==4)
  for i,b in enumerate(self.bots):b['root'].SetVisibility(i==0 or s==4)
  for shadow in self.shadows:shadow.SetVisibility(False)
  self.lights[0].SetIntensity(.45 if s not in [2,3] else 1.35);self.lights[1].SetIntensity(.35 if s not in [2,3] else .60);self.lights[2].SetIntensity(.15)
  self.cam.SetViewAngle(29);self.dof=0
  if s==0:
   u=t/3;q=smooth(u);pos=(0,0,1.05);pose(self.bots[0],pos,-6+10*q,t)
   cam=mix((.205,-.485,.76),(.09,-.420,.72),q);target=(-.045,-.001,.727);self.cam.SetViewAngle(29);self.dof=.075
  elif s==1:
   u=(t-3)/4;q=smooth(u);pos=(.18,0,1.06+bb);pose(self.bots[0],pos,-9+16*q,t)
   cam=mix((1.09,-2.75,1.53),(.67,-2.30,1.38),q);target=(-.15,0,1.09);self.dof=0
   self.shadows[0].SetVisibility(True);self.shadows[0].SetPosition(pos[0],0,.005)
  elif s==2:
   u=(t-7)/5;q=smooth(u);pos=mix((-.41,.68,1.57),(.13,.53,1.43),q);pos[2]+=bb;pose(self.bots[0],pos,7+17*q,t)
   cam=mix((1.26,-1.72,1.35),(.98,-1.46,1.23),q);target=(-.04,.13,1.10);self.cam.SetViewAngle(38);self.dof=.12
   self.shadows[0].SetVisibility(True);self.shadows[0].SetPosition(pos[0],pos[1],.778);self.shadows[0].SetScale(.72,.62,1)
  elif s==3:
   u=(t-12)/4;q=smooth(u);pos=(.14,.50,1.43+bb);pose(self.bots[0],pos,28,t)
   cam=mix((.55,-.78,1.37),(.39,-.63,1.29),q);target=(.10,-.005,.895);self.cam.SetViewAngle(30);self.dof=.21
  elif s==4:
   u=(t-16)/7;arr=smooth(u/.40);dep=smooth((u-.44)/.48)
   p0=mix((-.8,-.43,1.62),(-.8,.10,1.24),arr);p1=mix((0,.10,1.24),(.05,-.74,1.55),dep);p2=(.8,.10,1.24)
   pose(self.bots[0],p0,5,t,arr<.999);pose(self.bots[1],p1,-17*dep,t,dep>.001);pose(self.bots[2],p2,-6,t,False)
   cam=mix((1.18,-3.18,1.95),(.94,-3.03,1.81),smooth(u));target=(0,.02,1.42);self.cam.SetViewAngle(32)
   for sh,p in zip(self.shadows,[p0,p1,p2]):sh.SetVisibility(True);sh.SetPosition(p[0],p[1],.725);sh.SetScale(.40,.4,1)
  else:
   u=(t-23)/7;q=smooth(u);pos=(.25,0,1.07+bb);pose(self.bots[0],pos,24-39*q,t)
   cam=mix((.57,-2.4,1.4),(.12,-2.23,1.30),q);target=(-.19,0,1.11);self.shadows[0].SetVisibility(True);self.shadows[0].SetPosition(.25,0,.005);self.shadows[0].SetScale(1,1,1)
  self.cam.SetPosition(*cam);self.cam.SetFocalPoint(*target);self.cam.SetClippingRange(.008,35);self.cam.SetViewUp(0,0,1);self.target=np.array(target)
 def frame(self,t,overlay=True):
  self.update(t);self.win.Render();self.w2i.Modified();self.w2i.Update();arr=vtk_to_numpy(self.w2i.GetOutput().GetPointData().GetScalars()).reshape(self.h,self.w,3)[::-1].copy();im=Image.fromarray(arr)
  if self.dof:
   self.z2i.Modified();self.z2i.Update();z=vtk_to_numpy(self.z2i.GetOutput().GetPointData().GetScalars()).reshape(self.h,self.w)[::-1].copy();near,far=self.cam.GetClippingRange();dist=near*far/(far-z*(far-near));focus=np.linalg.norm(np.array(self.cam.GetPosition())-self.target)
   if self.scene==0:focus=np.linalg.norm(np.array(self.cam.GetPosition())-np.array([0,-.045,1.05-.370]))
   if self.scene==3:focus=np.linalg.norm(np.array(self.cam.GetPosition())-self.keypos)
   # A depth-aware lens blur with foreground preserved, no fictitious optical performance claim.
   amount=np.clip(np.abs(dist-focus)/(focus*.55)-.15,0,1);mask=Image.fromarray((amount*180).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.1));blur=im.filter(ImageFilter.GaussianBlur(4.2*self.w/1920));im=Image.composite(blur,im,mask)
  if (self.w,self.h)!=(W,H):im=im.resize((W,H),Image.Resampling.LANCZOS)
  return compose(im,t,self) if overlay else im

FONTP=Path(os.getenv('FLOAT_FONT_DIR','/usr/share/fonts/opentype/inter'));FONTS={}
def font(size,weight='Regular'):
 key=(size,weight)
 if key not in FONTS:FONTS[key]=ImageFont.truetype(str(FONTP/f'InterDisplay-{weight}.otf'),size)
 return FONTS[key]
WHITE=(241,239,232);GRAY=(166,175,180);GOLD=(229,185,118)
def txt(d,xy,s,size=48,color=WHITE,weight='Regular',a=255,anchor=None):d.text(xy,s,font=font(size,weight),fill=(*color,int(a)),anchor=anchor)
def tracking(d,xy,s,size=16,spacing=4,color=WHITE,a=255):
 x,y=xy
 for ch in s:d.text((x,y),ch,font=font(size,'Medium'),fill=(*color,int(a)));x+=d.textlength(ch,font=font(size,'Medium'))+spacing
 return x

def alp(t,start,end,fade=.45):return float(smooth((t-start)/fade)*smooth((end-t)/.3))

def bracket(d,x,y,w,h,a,col=GOLD):
 for sx,sy in [(-1,-1),(-1,1),(1,-1),(1,1)]:
  xx=x+sx*w/2;yy=y+sy*h/2;d.line((xx-sx*14,yy,xx,yy,xx,yy-sy*14),fill=(*col,int(a)),width=2)

def compose(im,t,film):
 s=film.scene;layer=Image.new('RGBA',(W,H));d=ImageDraw.Draw(layer)
 # Bottom, top and left exposure gradients keep typographic contrast without UI slabs.
 if s in [0,1,5,6]:
  g=np.zeros((H,1050,4),np.uint8);g[:,:,:3]=(6,12,18);g[:,:,3]=(np.linspace(140,0,1050)[None,:]).astype(np.uint8);layer.alpha_composite(Image.fromarray(g),(0,0));d=ImageDraw.Draw(layer)
 g=np.zeros((145,W,4),np.uint8);g[:,:,:3]=(6,10,14);g[:,:,3]=np.linspace(0,150,145)[:,None].astype(np.uint8);layer.alpha_composite(Image.fromarray(g),(0,H-145));d=ImageDraw.Draw(layer)
 tracking(d,(75,56),'FLOAT',20,5,WHITE,210)
 tracking(d,(1480,57),'A NEW KIND OF PRESENCE',12,1.8,GRAY,200)
 txt(d,(77,1020),'CONCEPT FILM  /  PROPOSED EXPERIENCE',15,GRAY,'Medium',190)
 # No feature speed, battery, safety, availability or acoustic claims.
 if s==0:
  a=alp(t,.22,3)*255;y=int(350+18*(1-smooth((t-.22)/.8)))
  txt(d,(73,y),'What if your AI',76,WHITE,'Medium',a);txt(d,(73,y+91),'came with you?',76,WHITE,'Medium',a)
  tracking(d,(80,y+220),'BEYOND THE SCREEN',16,2.8,GOLD,a)
 elif s==1:
  a=alp(t,3.24,7)*255
  tracking(d,(80,328),'INTRODUCING',17,3.5,GOLD,a)
  txt(d,(68,368),'FLOAT.',132,WHITE,'Medium',a)
  txt(d,(79,539),'A floating AI companion.',31,GRAY,'Regular',a)
  tracking(d,(80,603),'HELIUM-SUPPORTED  /  CONNECTED',14,1.8,GRAY,a)
  a2=alp(t,4.5,7)*220
  txt(d,(1620,851),'~62 cm',21,GRAY,'Regular',a2)
 elif s==2:
  a=alp(t,7.2,12)*255
  txt(d,(77,147),'“Where are my keys?”',58,WHITE,'Medium',a)
  tracking(d,(82,226),'IMAGINE ANOTHER POINT OF VIEW',14,2,GOLD,a)
  if t>9.5:
   a2=alp(t,9.5,12)*255;x,y=film.project(film.keypos);bracket(d,x,y,105,65,a2)
   d.line((x+57,y,x+155,y-35),fill=(*GOLD,int(a2)),width=2);tracking(d,(x+168,y-51),'LOCATED',13,1.8,GOLD,a2)
 elif s==3:
  a=alp(t,12.15,16)*255
  txt(d,(80,161),'“Right here.”',72,WHITE,'Medium',a)
  txt(d,(83,250),'Beside your notebook.',27,GRAY,'Regular',a)
  x,y=film.project(film.keypos);bracket(d,x,y,230,180,a*.9)
  # Designed notification, expressly a simulated experience.
  a2=alp(t,13,16)*255
  x0,y0=1255,612;ww,hh=585,253
  d.rounded_rectangle((x0,y0,x0+ww,y0+hh),radius=26,fill=(16,25,32,int(a2*.97)),outline=(112,130,139,int(a2*.50)),width=1)
  d.ellipse((x0+26,y0+29,x0+42,y0+45),fill=(*GOLD,int(a2)))
  tracking(d,(x0+61,y0+25),'FLOAT  ·  YOUR PHONE',14,1.8,GRAY,a2)
  txt(d,(x0+27,y0+69),'Keys found.',36,WHITE,'Medium',a2)
  txt(d,(x0+28,y0+124),'On the table. Beside the notebook.',21,GRAY,'Regular',a2)
  d.line((x0+28,y0+171,x0+ww-28,y0+171),fill=(104,124,134,int(a2*.3)),width=1)
  tracking(d,(x0+28,y0+193),'SIMULATED NOTIFICATION',11,1.4,GRAY,a2)
 elif s==4:
  a=alp(t,16.3,23)*255
  txt(d,(76,133),'One returns. Another takes over.',62,WHITE,'Medium',a)
  tracking(d,(82,220),'A SHARED DOCK. A ROTATING FLEET.',14,2,GOLD,a)
  if t>19.1:
   a2=alp(t,19.1,23)*230
   for pt,lab in [((-.8,.1,.56),'RECHARGING'),((.8,.1,.56),'READY')]:
    x,y=film.project(pt);tracking(d,(x-60,y),lab,12,1.6,GOLD,a2)
 elif s==5:
  a=alp(t,23.3,27)*255
  txt(d,(74,341),'Less screen.',85,WHITE,'Medium',a);txt(d,(74,441),'More presence.',85,WHITE,'Medium',a)
  txt(d,(81,584),'A companion for the world you live in.',26,GRAY,'Regular',a)
 else:
  a=alp(t,27.15,30,.5)*255
  txt(d,(69,305),'FLOAT.',132,WHITE,'Medium',a)
  txt(d,(79,477),'Help bring it to life.',41,WHITE,'Regular',a)
  tracking(d,(83,559),'FOLLOW THE BUILD',18,3,GOLD,a)
  txt(d,(81,658),'Early hardware concept.',22,GRAY,'Regular',a)
  txt(d,(81,696),'Not a working prototype.',22,GRAY,'Regular',a)
 out=Image.alpha_composite(im.convert('RGBA'),layer).convert('RGB')
 # Motivated hard cuts, with only the opening and ending fading from/to black.
 fade=min(float(smooth(t/.28)),float(smooth((DUR-t)/.55)))
 if fade<.999:out=Image.blend(Image.new('RGB',(W,H),(6,10,14)),out,fade)
 return out

def music():
 from scipy.signal import butter,sosfilt
 sr=48000;n=int(DUR*sr);out=np.zeros((n,2),np.float64);rng=np.random.default_rng(72125)
 def add(sig,start,amp=1,pan=0):
  i=int(start*sr);j=min(n,i+len(sig))
  if i<0 or j<=i:return
  sig=sig[:j-i]*amp;out[i:j,0]+=sig*np.sqrt((1-pan)/2);out[i:j,1]+=sig*np.sqrt((1+pan)/2)
 def note(start,dur,mid,amp=.08,kind='pluck',pan=0):
  tt=np.arange(int(dur*sr))/sr;f=440*2**((mid-69)/12)
  if kind=='pad':
   x=(np.sin(2*np.pi*f*tt+.003*np.sin(2*np.pi*.4*tt))+ .38*np.sin(2*np.pi*f*1.0015*tt)+.18*np.sin(2*np.pi*f*2*tt));env=np.minimum(tt/.85,1)*np.clip((dur-tt)/1.4,0,1)
  elif kind=='bass':x=np.sin(2*np.pi*f*tt)+.1*np.sin(2*np.pi*f*2*tt);env=(1-np.exp(-tt*30))*np.exp(-tt*1.8)*np.clip((dur-tt)/.15,0,1)
  else:x=np.sin(2*np.pi*f*tt+.8*np.exp(-tt*3)*np.sin(2*np.pi*f*2*tt))+.17*np.sin(2*np.pi*f*3.002*tt)*np.exp(-tt*3);env=np.minimum(tt/.008,1)*np.exp(-tt*2.7)*np.clip((dur-tt)/.12,0,1)
  sig=x*env;add(sig,start,amp,pan)
  if kind=='pluck':
   for delay,decay in [(.3125,.29),(.625,.13),(.9375,.05)]:add(sig,start+delay,amp*decay,-pan)
 # Original 96bpm composition, four harmonic colors, not a library music cue.
 beat=.625;chords=[[50,57,61,64,69],[47,54,57,61,66],[42,49,56,57,61],[49,56,59,63,66]]
 for bar in range(12):
  st=bar*2.5;ch=chords[(bar//2)%4]
  for j,m in enumerate(ch):note(st,3.5,m,.021,'pad',-.65+j*.325)
  note(st,2.0,ch[0]-12,.14 if 3<=st<27 else .07,'bass')
  if st>=2.5:
   for j in range(8):note(st+j*.3125,1.5,ch[[1,3,4,2,3,1,4,2][j]]+12,.03 if st<16 else .04,'pluck',(-.55,.55)[j%2])
 # Rounded heartbeat kick, dry tactile clicks, and sparse high-passed shakers.
 for st in np.arange(3,27,.625):
  tt=np.arange(int(.18*sr))/sr;freq=43+68*np.exp(-tt*29);phase=2*np.pi*np.cumsum(freq)/sr;sig=np.sin(phase)*np.exp(-tt*23)*np.minimum(tt/.002,1);add(sig,float(st),.095)
 for st in np.arange(3.3125,26.9,.625):
  tt=np.arange(int(.08*sr))/sr;raw=rng.normal(0,1,len(tt));raw=sosfilt(butter(2,3200,fs=sr,btype='highpass',output='sos'),raw);sig=raw*np.exp(-tt*80)*np.minimum(tt/.002,1);add(sig,float(st),.013, .4 if int(st*2)%2 else -.4)
 # Designed sound effects: airy cuts, camera confirmation, magnetic dock contact.
 for st in [2.74,6.77,11.74,15.72,22.73,26.75]:
  ln=.42;tt=np.arange(int(ln*sr))/sr;raw=rng.normal(0,1,len(tt));raw=sosfilt(butter(2,[400,3100],fs=sr,btype='bandpass',output='sos'),raw);env=np.sin(np.pi*tt/ln)**2;add(raw*env,st,.036,-.2)
 for st in [9.65,13.08,19.14]:
  note(st,.75,85,.065,'pluck',-.12);note(st+.085,.8,92,.045,'pluck',.12)
 for st in [18.7,19.2]:
  tt=np.arange(int(.11*sr))/sr;sig=(rng.normal(0,1,len(tt))*.20+np.sin(2*np.pi*920*tt))*np.exp(-tt*65);add(sig,st,.065)
 for j,m in enumerate([78,81,85]):note(27.23+j*.17,1.65,m,.056,'pluck',-.25+j*.25)
 # A restrained stereo room tail.
 dry=out.copy()
 for delay,decay in [(.079,.12),(.113,.095),(.181,.07),(.271,.045)]:
  k=int(delay*sr);out[k:,0]+=dry[:-k,1]*decay;out[k:,1]+=dry[:-k,0]*decay
 tt=np.arange(n)/sr;out*=np.minimum(tt/.65,1)[:,None]*np.clip((DUR-tt)/.8,0,1)[:,None];out=np.tanh(out*1.2);out*=.78/max(abs(out).max(),.01)
 with wave.open(str(ROOT/'assets/score_original.wav'),'wb') as f:f.setnchannels(2);f.setsampwidth(2);f.setframerate(sr);f.writeframes((out*32767).astype('<i2').tobytes())

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--preview',action='store_true');p.add_argument('--audio',action='store_true');p.add_argument('--start',type=float,default=0);p.add_argument('--end',type=float,default=DUR);p.add_argument('--width',type=int,default=1920);p.add_argument('--output',default='silent.mp4');args=p.parse_args()
 if args.audio:music();sys.exit(0)
 film=Film(args.width,round(args.width*9/16))
 if args.preview:
  for t in [1.7,4.8,9.8,14.3,20.1,24.8,28.3]:
   st=time.monotonic();im=film.frame(t);im.save(ROOT/'previews'/f'shot_{t:04.1f}.jpg',quality=95);print('preview',t,round(time.monotonic()-st,2),flush=True)
 else:
  cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-threads','2','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','17','-threads','2','-pix_fmt','yuv420p','-movflags','+faststart',str(ROOT/'renders'/args.output)]
  proc=subprocess.Popen(cmd,stdin=subprocess.PIPE);start=time.monotonic()
  try:
   for i in range(round(args.start*FPS),round(args.end*FPS)):
    im=film.frame(i/FPS);proc.stdin.write(np.array(im).tobytes())
    if i%24==0:print('frame',i,'elapsed',round(time.monotonic()-start,1),flush=True)
   proc.stdin.close()
   if proc.wait():raise RuntimeError('Encoder failed')
  except BaseException:proc.kill();raise
