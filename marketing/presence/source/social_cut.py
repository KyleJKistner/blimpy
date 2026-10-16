"""Independently reframed 15-second square edit, not a crop of the landscape titles."""
import argparse,subprocess,time
import numpy as np
from PIL import Image,ImageDraw
import launch_film as L
L.W=L.H=1080
W=H=1080;FPS=24;DUR=15

def source_time(t):
 if t<2:return .58+t*1.10
 if t<5:return 3.2+(t-2)/3*3.5
 if t<8:return 8.4+(t-5)/3*3.15
 if t<12:return 16.15+(t-8)/4*6.7
 return 27.1+(t-12)/3*2.85

class Social(L.Film):
 def update(self,t):
  super().update(t);st=self.social_time
  if st<2:
   u=st/2;cam=L.mix((.14,-.72,.82),(.06,-.60,.76),L.smooth(u));tar=(0,0,.78);angle=35
  elif st<5:
   u=(st-2)/3;cam=L.mix((.53,-2.52,1.43),(.30,-2.26,1.37),u);tar=(.18,0,1.09);angle=34
  elif st<8:
   u=(st-5)/3;cam=L.mix((.89,-1.53,1.61),(.61,-1.4,1.52),u);tar=(.04,.20,1.17);angle=42
  elif st<12:
   u=(st-8)/4;cam=L.mix((.62,-4.10,2.02),(.44,-3.96,1.91),u);tar=(0,.08,1.21);angle=35
  else:
   u=(st-12)/3;cam=L.mix((.41,-2.42,1.3),(.11,-2.27,1.23),u);tar=(.25,0,1.10);angle=38
  self.cam.SetPosition(*cam);self.cam.SetFocalPoint(*tar);self.cam.SetViewAngle(angle);self.target=np.array(tar)

def compose(im,t,film):
 st=film.social_time;ly=Image.new('RGBA',(W,H));d=ImageDraw.Draw(ly)
 # Native square layout: large mobile-readable headline, protected margins.
 for y0,hh,v in [(0,370,np.linspace(168,0,370)),(865,215,np.linspace(0,185,215))]:
  a=np.zeros((hh,W,4),np.uint8);a[:,:,:3]=(5,10,15);a[:,:,3]=v[:,None].astype(np.uint8);ly.alpha_composite(Image.fromarray(a),(0,y0))
 d=ImageDraw.Draw(ly)
 L.tracking(d,(54,45),'FLOAT',20,5,L.WHITE,230)
 L.tracking(d,(810,49),'CONCEPT FILM',11,1.1,L.GRAY,220)
 if st<2:
  a=L.alp(st,-.50,2,.22)*255
  L.txt(d,(51,161),'Your AI.',72,L.WHITE,'Medium',a)
  L.txt(d,(51,245),'In real life?',72,L.WHITE,'Medium',a)
 elif st<5:
  a=L.alp(st,2.1,5,.22)*255
  L.txt(d,(48,143),'Meet FLOAT.',88,L.WHITE,'Medium',a)
  L.txt(d,(56,258),'A floating AI companion.',30,L.GRAY,'Regular',a)
  L.tracking(d,(56,937),'HELIUM-SUPPORTED  /  CONNECTED',13,1.5,L.GOLD,a)
 elif st<8:
  a=L.alp(st,5.12,8,.22)*255
  L.txt(d,(51,150),'“Where are',64,L.WHITE,'Medium',a)
  L.txt(d,(51,226),'my keys?”',64,L.WHITE,'Medium',a)
  if st>6.05:
   aa=L.alp(st,6.05,8,.22)*255;x,y=film.project(film.keypos);L.bracket(d,x,y,108,70,aa)
   L.txt(d,(55,915),'Another point of view.',32,L.WHITE,'Medium',aa)
 elif st<12:
  a=L.alp(st,8.12,12,.22)*255
  L.txt(d,(51,125),'One returns.',54,L.WHITE,'Medium',a)
  L.txt(d,(51,189),'Another takes over.',54,L.WHITE,'Medium',a)
  L.tracking(d,(55,917),'A SHARED DOCK. A ROTATING FLEET.',13,1.3,L.GOLD,a)
 else:
  a=L.alp(st,12.10,15,.26)*255
  L.txt(d,(51,151),'Less screen.',66,L.WHITE,'Medium',a)
  L.txt(d,(51,230),'More presence.',66,L.WHITE,'Medium',a)
  L.tracking(d,(55,897),'FOLLOW THE BUILD',18,2.8,L.GOLD,a)
  L.txt(d,(56,952),'Early concept. Not a working prototype.',21,L.GRAY,'Regular',a)
 L.txt(d,(55,1030),'CONCEPT VISUALIZATION · PROPOSED EXPERIENCE',14,L.GRAY,'Medium',210)
 out=Image.alpha_composite(im.convert('RGBA'),ly).convert('RGB');fade=float(L.smooth((15-st)/.4))
 return Image.blend(Image.new('RGB',(W,H),(5,10,15)),out,fade) if fade<1 else out
L.compose=compose
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--preview',action='store_true');args=p.parse_args();film=Social(1080,1080)
 if args.preview:
  for st in [1,3.5,6.7,10.1,13.7]:
   film.social_time=st;film.frame(source_time(st)).save(L.ROOT/'previews'/f'social_{st}.jpg',quality=95)
 else:
  proc=subprocess.Popen(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1080x1080','-r','24','-i','-','-an','-c:v','libx264','-preset','fast','-crf','17','-threads','2','-pix_fmt','yuv420p',str(L.ROOT/'renders/social_silent.mp4')],stdin=subprocess.PIPE)
  start=time.monotonic()
  try:
   for i in range(FPS*DUR):
    film.social_time=i/FPS;im=film.frame(source_time(i/FPS));proc.stdin.write(np.asarray(im).tobytes())
    if i%24==0:print('frame',i,'elapsed',round(time.monotonic()-start,1),flush=True)
   proc.stdin.close()
   if proc.wait():raise RuntimeError('Encoder failed')
  except BaseException:proc.kill();raise
