"""FLOAT / Momentum. A new 24-second, 140-BPM product concept film.
New 3D camera choreography, not a recut of previously rendered video.
All capabilities are proposed. Geometry inherited and refined from Presence.
"""
import os
os.environ.setdefault('VTK_DEFAULT_OPENGL_WINDOW','vtkEGLRenderWindow')
os.environ.setdefault('LP_NUM_THREADS','4')
os.environ.setdefault('OMP_NUM_THREADS','4')
import math,sys,time,json,subprocess,argparse
from pathlib import Path
import numpy as np
import cv2
import vtk
from vtk.util.numpy_support import vtk_to_numpy
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import core_scene as S

ROOT=Path(__file__).resolve().parents[1]
FPS=30; BPM=140; BEAT=60/BPM; DURATION=24.
CUT_BEATS=[0,1,2,4,8,12,14,18,22,25,28,32,34,38,42,48,56]
NAMES=['Lens ignition','Rotor cut-in','Foil sweep','Off-screen hero',
       'Low-angle flyby','Camera whip','Conversation orbit','Search dive',
       'Keys lock-on','Phone match','Dock rail slider','Contact detail',
       'Departure rise','Fleet handoff','Presence orbit','Brand resolve']
WHITE=(246,244,237); MUTED=(181,193,199); AMBER=(255,186,104); INK=(5,10,15)

def smooth(u):
 u=float(np.clip(u,0,1));return u*u*(3-2*u)
def ease(u):
 u=float(np.clip(u,0,1));return 1-(1-u)**3
def mix(a,b,u):return np.asarray(a)*(1-u)+np.asarray(b)*u

def segment(t):
 b=t/BEAT;i=int(np.clip(np.searchsorted(CUT_BEATS,b,side='right')-1,0,len(NAMES)-1))
 a,z=CUT_BEATS[i:i+2];return i,(b-a)/(z-a),a*BEAT,z*BEAT

def robot_pose(bot,p,yaw,t,active=True):
 S.pose(bot,p,yaw,t,active)
 # Narrow rotational planes: a visual motion cue, not an RPM or acoustic claim.

def cam_orbit(target,r,az,z):
 return np.asarray(target)+np.array([r*np.sin(np.radians(az)),-r*np.cos(np.radians(az)),z])

class KineticFilm(S.Film):
 def __init__(self,w=1920,h=1080):
  super().__init__(w,h)
  self.portrait=h>w
  # Clear satin envelope rather than the previous latitude-band surface.
  self.r.SetBackground(.003,.008,.013);self.r.SetBackground2(.026,.040,.054)
  self.lights[0].SetColor(1,.84,.65)
  self.lights[1].SetColor(.62,.82,1)
  # Studio practicals provide a stable world reference for fast camera motion.
  g=S.Group()
  for x in [-1.55,1.55]:
   g.add(S.box((x,.82,1.2),(.012,.014,2.35),.1),(.23,.43,.58),.1,.26,2.2)
  self.stage=g.build()[0];self.r.AddViewProp(self.stage)
  self.stage.SetVisibility(False)
  self.focus_point=None
  self._last=None
 def update(self,t):
  i,u,a,b=segment(t);q=smooth(u);v=.18*u+.82*q
  self.shot=i;self.scene=i;self.shot_u=u;self.dof=0;self.focus_point=None
  self.env.SetVisibility(i in [7,8,9]);self.keys.SetVisibility(i in [7,8,9]);self.keyshadow.SetVisibility(i in [7,8,9]);self.dock.SetVisibility(i in [10,11,12,13]);self.studio.SetVisibility(False);self.stage.SetVisibility(i in [4,6,14])
  for j,b0 in enumerate(self.bots):b0['root'].SetVisibility(j==0 or i in [10,11,12,13])
  for shadow in self.shadows:shadow.SetVisibility(False)
  self.lights[0].SetIntensity(1.05 if i in [7,8,9,10,11,12,13] else .67)
  self.lights[1].SetIntensity(.68 if i in [7,8,9,10,11,12,13] else .48)
  self.lights[2].SetIntensity(.24)
  pos=np.array([0,0,1.12]);yaw=0.;angle=34;roll=0
  # Fast camera movement, not a claim of high-speed balloon maneuverability.
  if i==0:
   pos=np.array([0,0,1.10]);target=np.array([0,-.039,.73]);cam=mix((.12,-.32,.779),(.027,-.235,.748),ease(u));angle=30;roll=-12*(1-v);self.dof=.12
  elif i==1:
   pos=np.array([0,0,1.10]);target=np.array([-.156,0,.782]);cam=mix((-.37,-.28,.74),(-.20,-.25,.83),v);angle=31;roll=18-30*v;self.dof=.10
  elif i==2:
   pos=np.array([0,0,1.10]);yaw=4*v;target=np.array([.14,0,1.20]);cam=mix((.68,-.63,1.28),(.29,-.60,1.11),v);angle=31;roll=-7+12*v
  elif i==3:
   pos=np.array([.19,0,1.14+.018*u]);yaw=-6+9*v
   target=np.array([-.23,0,1.08]);cam=cam_orbit(target,1.28+1.18*ease(u),-20+36*v,.12+.15*v)
   angle=32;roll=5*(1-ease(u))
  elif i==4:
   pos=np.array([-.07+.17*v,-.035*v,1.23+.012*np.sin(t)]);yaw=-10+15*v
   target=pos+np.array([0,0,-.12]);cam=cam_orbit(target,1.31+0.24*v,-55+90*v,-.49+.22*v);angle=37;roll=-9+14*v
  elif i==5:
   pos=np.array([0,0,1.1]);yaw=-3+6*v;target=pos+np.array([0,-.025,-.37]);cam=cam_orbit(target,.35,-28+58*v,.09-.05*v);angle=35;roll=6-10*v;self.dof=.10
  elif i==6:
   pos=np.array([.09,0,1.15+.014*np.sin(t)]);yaw=-6+14*v
   target=np.array([-.22,0,1.06]);cam=cam_orbit(target,2.02,-15+38*v,.12+.12*np.sin(u*np.pi));angle=33;roll=-3+6*v
  elif i==7:
   pos=mix((-.18,.64,1.56),(.13,.50,1.47),v);yaw=12+12*v
   target=mix((.04,.30,1.14),(.10,.17,1.05),v);cam=mix((1.09,-.91,2.47),(.80,-1.53,1.52),v);angle=41;roll=9*(1-v);self.dof=.06
  elif i==8:
   pos=np.array([.14,.50,1.47]);yaw=24;target=self.keypos
   cam=mix((.52,-.64,1.23),(.31,-.47,1.105),v);angle=36;roll=-6+6*v;self.dof=.18;self.focus_point=self.keypos
  elif i==9:
   pos=np.array([.14,.50,1.47]);yaw=24;target=np.array([.12,.17,1.08]);cam=mix((.93,-1.54,1.50),(.77,-1.47,1.36),v);angle=39;roll=0;self.dof=.06
  elif i in [10,11,12,13]:
   # Shared physical trajectory continuous across its four camera cuts.
   arrival=smooth((t-12)/1.9);dep=smooth((t-14.57)/2.65)
   p0=mix((-.8,-.32,1.57),(-.8,.10,1.24),arrival)
   p1=mix((0,.10,1.24),(.13,-.71,1.57),dep)
   p2=np.array([.8,.10,1.24])
   for bo,pp,yy,act in [(self.bots[0],p0,6,arrival<.999),(self.bots[1],p1,-12*dep,dep>.001),(self.bots[2],p2,-6,False)]:robot_pose(bo,pp,yy,t,act)
   for sh,pp in zip(self.shadows,[p0,p1,p2]):sh.SetVisibility(True);sh.SetPosition(pp[0],pp[1],.725);sh.SetScale(.40,.4,1)
   if i==10:
    target=np.array([-.1,.08,1.34]);cam=mix((-1.70,-3.02,1.27),(-.85,-2.99,1.67),v);angle=35;roll=-3+3*v
   elif i==11:
    target=np.array([-.8,.10,.825]);cam=mix((-.53,-.24,.92),(-.66,-.26,.87),v);angle=34;roll=7-9*v;self.dof=.12;self.focus_point=target
   elif i==12:
    target=p1+np.array([-.08,0,-.18]);cam=mix((.56,-1.68,.98),(1.04,-1.90,1.48),v);angle=39;roll=-5+9*v
   else:
    target=np.array([.01,-.12,1.39]);cam=mix((1.65,-3.28,2.55),(.62,-3.19,1.98),v);angle=34;roll=3*(1-v)
  elif i==14:
   pos=np.array([.13,0,1.18+.016*np.sin(t)]);yaw=-7+12*v
   target=np.array([-.17,0,1.11]);cam=cam_orbit(target,2.22,-39+68*v,.06+.35*np.sin(u*np.pi));angle=32;roll=-5+9*v
  else:
   pos=np.array([.25,0,1.15+.008*np.sin(t)]);yaw=-7+6*v
   target=np.array([-.21,0,1.11]);cam=cam_orbit(target,2.4+0.1*v,17-15*v,.17-.05*v);angle=32
  if i not in [10,11,12,13]:
   robot_pose(self.bots[0],pos,yaw,t,True)
   if i in [3,4,6,14,15]:
    sh=self.shadows[0];sh.SetVisibility(True);sh.SetPosition(pos[0],pos[1],.006);sh.SetScale(.58,.52,1)
   elif i in [7,8,9]:
    sh=self.shadows[0];sh.SetVisibility(True);sh.SetPosition(pos[0],pos[1],.778);sh.SetScale(.56,.47,1)
  # Independent 4:5 cameras. Not a centre crop of landscape typography.
  if self.portrait:
   if i in [3,6,14,15]:
    target=pos+np.array([0,0,-.07]);az={3:-18+32*v,6:-18+32*v,14:-36+64*v,15:14-12*v}[i]
    cam=cam_orbit(target,2.22 if i!=15 else 2.52,az,.18);angle=37
   elif i==4:
    target=pos+np.array([0,0,-.06]);cam=cam_orbit(target,2.,-48+80*v,-.34+.15*v);angle=39
   elif i==7:
    target=np.array([.11,.22,1.13]);cam=mix((.55,-1.70,2.27),(.46,-2.18,1.57),v);angle=42
   elif i==9:
    target=np.array([.14,.22,1.11]);cam=np.array([.38,-2.38,1.59]);angle=42
   elif i in [10,13]:
    target=np.array([0,-.03,1.40]);cam=mix((.90,-4.60,2.26),(.15,-4.44,1.99),v);angle=42
   elif i==12:
    target=p1+np.array([0,0,-.06]);cam=mix((.46,-2.53,1.14),(.94,-2.72,1.80),v);angle=42
  self.cam.SetPosition(*cam);self.cam.SetFocalPoint(*target);self.cam.SetViewUp(0,0,1);self.cam.SetViewAngle(angle);self.cam.Roll(roll);self.cam.SetClippingRange(.005,40);self.target=np.array(target)
 def project_native(self,p):
  self.r.SetWorldPoint(*p,1);self.r.WorldToDisplay();x,y,z=self.r.GetDisplayPoint();return np.array([x,self.h-y])
 def raw(self,t):
  self.update(t);self.win.Render();self.w2i.Modified();self.w2i.Update()
  arr=vtk_to_numpy(self.w2i.GetOutput().GetPointData().GetScalars()).reshape(self.h,self.w,3)[::-1].copy()
  if self.dof:
   self.z2i.Modified();self.z2i.Update();z=vtk_to_numpy(self.z2i.GetOutput().GetPointData().GetScalars()).reshape(self.h,self.w)[::-1]
   near,far=self.cam.GetClippingRange();dist=near*far/(far-z*(far-near))
   point=self.target if self.focus_point is None else self.focus_point
   focus=np.linalg.norm(np.asarray(self.cam.GetPosition())-point)
   alpha=np.clip(np.abs(dist-focus)/(focus*.7)-.17,0,.7)[...,None]
   blur=cv2.GaussianBlur(arr,(0,0),2.6*self.w/1920)
   arr=(arr*(1-alpha)+blur*alpha).astype(np.uint8)
  return arr
 def frame(self,t,blur=True,overlay=True):
  i,u,a,b=segment(t)
  # Temporal integration for deliberately fast camera moves. No smoothing across cuts.
  times=[t]
  if blur and i in [0,1,2,3,4,5,7,10,11,12,14]:
   dt=1/(FPS*4);times=[max(a+1e-5,t-dt),min(b-1e-5,t+dt)]
  acc=None
  for tt in times:
   ar=self.raw(tt).astype(np.float32)
   acc=ar if acc is None else acc+ar
  ar=np.clip(acc/len(times),0,255).astype(np.uint8)
  # Subtle highlight bloom; preserve black levels and camera-pod readability.
  bright=np.maximum(ar.astype(np.float32)-165,0)
  bloom=cv2.GaussianBlur(bright,(0,0),7*self.w/1920)
  ar=np.clip(ar+bloom*.085,0,255).astype(np.uint8)
  self.update(t)
  return compose(Image.fromarray(ar),t,self) if overlay else Image.fromarray(ar)

FONTS={}
def font(n,weight='Medium'):
 n=max(8,int(round(n)));k=(n,weight)
 if k not in FONTS:FONTS[k]=S.font(n,weight)
 return FONTS[k]

def compose(im,t,f):
 w,h=im.size;port=f.portrait;s=w/1920 if not port else w/1080
 i,u,a,b=segment(t);local=t-a;W=w;H=h
 L=Image.new('RGBA',(w,h));d=ImageDraw.Draw(L)
 margin=78*s if not port else 52*s
 # Controlled tonal field for text, plus light top/footer gradients.
 yy=np.arange(h)[:,None];xx=np.arange(w)[None,:]
 bottom=np.clip((yy-h*.70)/(h*.30),0,1)*145
 top=np.clip(1-yy/(h*.19),0,1)*70
 alpha=np.broadcast_to(np.maximum(bottom,top),(h,w)).copy()
 if i in [3,6,14,15] and not port:
  alpha=np.maximum(alpha,np.broadcast_to(np.clip(1-xx/(w*.63),0,1)*166,(h,w)))
 rgba=np.zeros((h,w,4),np.uint8);rgba[:,:,:3]=INK;rgba[:,:,3]=alpha.astype(np.uint8);L.alpha_composite(Image.fromarray(rgba));d=ImageDraw.Draw(L)
 def text(x,y,st,n,col=WHITE,weight='Medium',a=255,anchor=None):
  d.text((round(x),round(y)),st,font=font(n*s,weight),fill=(*col,int(np.clip(a,0,255))),anchor=anchor)
 def track(x,y,st,n=13,spacing=2.2,col=MUTED,opacity=220):
  ff=font(n*s,'Medium')
  for ch in st:
   d.text((x,y),ch,font=ff,fill=(*col,int(opacity)));x+=d.textlength(ch,font=ff)+spacing*s
 def block(lines,x,y,n=86,leading=1.02,col=WHITE,weight='Bold',reveal=.13):
  # Fast eased settle, not endlessly floating type.
  op=255*smooth(local/.12);dy=24*s*(1-ease(local/reveal));dx=-10*s*(1-ease(local/reveal))
  for j,st in enumerate(lines):text(x+dx,y+dy+j*n*s*leading,st,n,col,weight,op)
 def brackets(p,ww,hh,opacity=255):
  x,y=f.project_native(p);ll=18*s
  for sx,sy in [(-1,-1),(-1,1),(1,-1),(1,1)]:
   ex=x+sx*ww/2;ey=y+sy*hh/2;d.line((ex-sx*ll,ey,ex,ey,ex,ey-sy*ll),fill=(*AMBER,int(opacity)),width=max(1,round(2*s)))
  return x,y
 # Small, consistent signposting. No simulated performance metrics.
 track(margin,42*s if not port else 42*s,'F L O A T',15 if not port else 17,1.2,WHITE,240)
 if not port:track(w-349*s,44*s,'A FLOATING AI COMPANION',11,1.2,MUTED,195)
 footer='CGI CONCEPT  /  PROPOSED EXPERIENCE'
 track(margin,h-(44*s if not port else 48*s),footer,10 if not port else 12,1.1,MUTED,205)
 # Thin editorial progress track, not a fabricated battery indicator.
 d.line((margin,h-17*s,w-margin,h-17*s),fill=(76,88,98,100),width=max(1,round(s)))
 d.line((margin,h-17*s,margin+(w-2*margin)*(t/DURATION),h-17*s),fill=(*AMBER,190),width=max(1,round(s)))
 left=margin;ty=310*s if not port else 142*s
 if i<3:
  # Each macro has a single compact, stable word.
  label=['WAKE.','MOVE.','FLOAT.'][i]
  text(margin,h-(167*s if not port else 248*s),label,60 if not port else 80,WHITE,'Bold')
  track(margin,h-(83*s if not port else 144*s),'A NEW KIND OF PRESENCE',12 if not port else 15,2,AMBER)
 elif i==3:
  block(['AI.','OFF SCREEN.'],left,ty,94 if not port else 100)
  if not port:track(left,ty+234*s,'MEET FLOAT',16,3,AMBER)
  else:track(left,h-190*s,'MEET YOUR FLOATING AI COMPANION',14,1.2,AMBER)
 elif i==4:
  block(['MEET FLOAT.'],left,h-(232*s if not port else 340*s),85 if not port else 91)
  track(left,h-(120*s if not port else 215*s),'A LITTLE CLOSER TO YOUR WORLD.',14 if not port else 15,1.7,AMBER)
 elif i==5:
  block(['SEES.'],left,h-(233*s if not port else 330*s),88 if not port else 100)
 elif i==6:
  block(['LISTENS.','ANSWERS.'],left,ty,86 if not port else 95)
  base=(ty+231*s) if not port else h-185*s
  for j in range(43):
   amp=(.15+.85*abs(math.sin(2.1*j+t*8)))*(.2+.8*math.sin(math.pi*j/43))
   ht=(8+32*amp)*s;x=left+j*7*s
   d.line((x,base-ht/2,x,base+ht/2),fill=(*AMBER,240),width=max(2,round(3*s)))
  track(left,base+46*s,'CONVERSATION, IN YOUR SPACE.',13 if not port else 15,1.5,MUTED)
 elif i==7:
  label='“Where are my keys?”'
  if port:
   block(['“Where are','my keys?”'],left,160*s,69)
  else:block([label],left,138*s,66)
  track(left,h-(109*s if not port else 155*s),'ANOTHER POINT OF VIEW.',14 if not port else 16,2,AMBER)
  if u>.65:brackets(f.keypos,93*s,62*s,255*smooth((u-.65)/.17))
 elif i==8:
  block(['FOUND.'],left,h-(245*s if not port else 315*s),91 if not port else 103)
  x,y=brackets(f.keypos,230*s,155*s)
  # No detector confidence is invented.
  track(min(w-150*s,x+134*s),max(115*s,y-64*s),'KEYS',13 if not port else 15,2,AMBER)
 elif i==9:
  if not port:
   block(['RIGHT HERE.'],left,176*s,78)
   text(left,278*s,'And on your phone.',27,MUTED,'Regular')
   x0,y0,ww,hh=w-690*s,h-402*s,610*s,247*s
  else:
   block(['RIGHT HERE.'],left,148*s,77)
   text(left,253*s,'And on your phone.',27,MUTED,'Regular')
   x0,y0,ww,hh=left,h-403*s,w-2*left,247*s
  sc=ease(local/.26);y0+=35*s*(1-sc)
  d.rounded_rectangle((x0,y0,x0+ww,y0+hh),radius=21*s,fill=(12,23,31,240),outline=(117,140,152,155),width=max(1,round(s)))
  d.ellipse((x0+25*s,y0+29*s,x0+38*s,y0+42*s),fill=(*AMBER,255));track(x0+52*s,y0+22*s,'FLOAT  ·  YOUR PHONE',13,1.5,MUTED)
  text(x0+25*s,y0+65*s,'Keys found.',34,WHITE,'Bold')
  text(x0+25*s,y0+119*s,'On the table. Beside the notebook.',20,MUTED,'Regular')
  track(x0+25*s,y0+191*s,'SIMULATED NOTIFICATION',11,1.3,MUTED,175)
 elif i==10:
  block(['BACK TO BASE.'],left,129*s if not port else 159*s,70 if not port else 76)
  track(left,h-(115*s if not port else 215*s),'A SHARED DOCK. A ROTATING FLEET.',13 if not port else 14,1.5,AMBER)
 elif i==11:
  block(['DOCK.'],left,h-(233*s if not port else 345*s),91 if not port else 104)
 elif i==12:
  block(['NEXT UP.'],left,132*s if not port else 159*s,88 if not port else 95)
 elif i==13:
  block(['ONE RETURNS.','ONE TAKES OVER.'],left,122*s if not port else 161*s,66 if not port else 66)
  track(left,h-(113*s if not port else 207*s),'THE COMPANION CONTINUES.',13 if not port else 16,1.9,AMBER)
 elif i==14:
  block(['LESS SCREEN.','MORE WORLD.'],left,ty,82 if not port else 88)
  track(left,h-(130*s if not port else 183*s),'A NEW KIND OF PRESENCE.',14 if not port else 16,2,AMBER)
 else:
  if not port:
   block(['FLOAT.'],left,289*s,156,reveal=.18)
   text(left,484*s,'A floating AI companion.',33,MUTED,'Regular')
   yy=590*s;nn=17
  else:
   block(['FLOAT.'],left,135*s,175,reveal=.18)
   text(left,345*s,'A floating AI companion.',34,MUTED,'Regular')
   yy=h-262*s;nn=19
  if local>.22:
   track(left,yy,'FOLLOW THE BUILD',nn,3,AMBER)
   d.line((left,yy+44*s,left+245*s,yy+44*s),fill=(*AMBER,220),width=max(1,round(2*s)))
  text(left,yy+76*s,'Early concept. Not prototype footage.',17 if not port else 21,MUTED,'Regular',230)
 out=Image.alpha_composite(im.convert('RGBA'),L).convert('RGB')
 # Brief closing fade only; opening is immediate.
 if t>DURATION-.26:out=Image.blend(Image.new('RGB',(w,h),INK),out,float(smooth((DURATION-t)/.26)))
 return out


def render(args):
 w,h=(1080,1350) if args.format=='feed' else (1920,1080)
 if args.preview:w,h=(648,810) if args.format=='feed' else (1152,648)
 f=KineticFilm(w,h)
 if args.preview:
  times=[.20,.64,1.22,2.58,4.40,5.58,6.85,8.58,10.03,11.35,12.9,14.18,15.4,17.22,19.31,22.35]
  for t in times:
   st=time.monotonic();im=f.frame(t,blur=False);out=ROOT/'previews'/f'{args.format}_{t:05.2f}.jpg';im.save(out,quality=93);print('preview',args.format,t,round(time.monotonic()-st,2),flush=True)
  f.win.Finalize();return
 start,end=args.start,args.end
 out=ROOT/'renders'/args.output
 cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-threads','2','-f','rawvideo','-pix_fmt','rgb24','-s',f'{w}x{h}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','16','-threads','2','-profile:v','high','-level:v','4.2','-pix_fmt','yuv420p','-movflags','+faststart',str(out)]
 p=subprocess.Popen(cmd,stdin=subprocess.PIPE);st=time.monotonic()
 try:
  for frame in range(round(start*FPS),round(end*FPS)):
   im=f.frame(frame/FPS,blur=not args.no_blur)
   p.stdin.write(np.asarray(im).tobytes())
   if frame%30==0:print(f'{args.format}: frame {frame}, elapsed {time.monotonic()-st:.1f}s',flush=True)
  p.stdin.close()
  if p.wait()!=0:raise RuntimeError('ffmpeg failed')
 finally:
  if p.poll() is None:p.kill()
  f.win.Finalize()

if __name__=='__main__':
 pa=argparse.ArgumentParser();pa.add_argument('--preview',action='store_true');pa.add_argument('--format',choices=['wide','feed'],default='wide');pa.add_argument('--start',type=float,default=0);pa.add_argument('--end',type=float,default=DURATION);pa.add_argument('--output',default='wide_silent.mp4');pa.add_argument('--no-blur',action='store_true');ar=pa.parse_args();render(ar)
