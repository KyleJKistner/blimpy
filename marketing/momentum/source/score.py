"""Original 140-BPM score and synchronized sound design for FLOAT / Momentum.
No sampled music, borrowed recordings or synthesized third-party voice.
Deterministic generation; stereo stems are provided for editing.
"""
from pathlib import Path
import json,wave
import numpy as np
from scipy.signal import butter,sosfilt
from scipy.io import wavfile
ROOT=Path(__file__).resolve().parents[1]
SR=48000;DUR=24;B=60/140;N=round(DUR*SR)
rng=np.random.default_rng(240016)
stems={k:np.zeros((N,2),np.float64) for k in ['drums','bass','music','effects']}

def add(bus,sig,start,amp=1.,pan=0.):
 i=round(start*SR);skip=max(0,-i);i=max(0,i);j=min(N,i+len(sig)-skip)
 if j<=i:return
 sig=np.asarray(sig[skip:skip+j-i])*amp
 if sig.ndim==2:stems[bus][i:j]+=sig;return
 p=np.clip(pan,-1,1)
 stems[bus][i:j,0]+=sig*np.sqrt((1-p)/2)
 stems[bus][i:j,1]+=sig*np.sqrt((1+p)/2)

def hz(m):return 440*2**((m-69)/12)
def filtered_noise(n,lo,hi):
 raw=rng.normal(0,1,n);sos=butter(2,[lo,hi],btype='bandpass',fs=SR,output='sos');return sosfilt(sos,raw)
def note(start,dur,m,amp=.1,kind='pluck',pan=0,bus='music'):
 t=np.arange(round(dur*SR))/SR;f=hz(m)
 if kind=='pluck':
  x=np.sin(2*np.pi*f*t+.75*np.exp(-t*8)*np.sin(2*np.pi*f*2*t))
  x+=.18*np.sin(2*np.pi*f*2.003*t)*np.exp(-t*10)+.065*np.sin(2*np.pi*f*3.004*t)*np.exp(-t*6)
  e=np.minimum(t/.004,1)*np.exp(-t*5.0)*np.clip((dur-t)/.14,0,1)
 elif kind=='bass':
  x=.78*np.sin(2*np.pi*f*t)+.28*np.sin(2*np.pi*f*2*t)+.10*np.sin(2*np.pi*f*3*t)+.045*np.sin(2*np.pi*f*5*t)
  x=np.tanh(x*1.45)*.75
  e=np.minimum(t/.007,1)*np.minimum((dur-t)/.065,1)*(.63+.37*np.exp(-t*6))
 elif kind=='pad':
  x=np.zeros(len(t))
  for det,aa in [(-.0031,.23),(0,.5),(.0027,.23)]:
   x+=aa*(np.sin(2*np.pi*f*(1+det)*t)+.14*np.sin(2*np.pi*f*2*(1+det)*t))
  e=np.minimum(t/.5,1)*np.clip((dur-t)/.8,0,1)
 elif kind=='stab':
  x=np.zeros(len(t))
  for det in [-.004,0,.004]:
   for k in range(1,7):x+=np.sin(2*np.pi*f*k*(1+det)*t)/(k*3)
  e=np.minimum(t/.007,1)*np.exp(-t*8)*np.clip((dur-t)/.08,0,1)
 else:raise ValueError(kind)
 sig=x*e;add(bus,sig,start,amp,pan)
 if kind=='pluck':
  add(bus,sig,start+B*.75,amp*.25,-pan)
  add(bus,sig,start+B*1.5,amp*.10,pan)

def kick(st,amp=.5):
 t=np.arange(round(.36*SR))/SR;f=46+106*np.exp(-t*42);ph=2*np.pi*np.cumsum(f)/SR
 x=np.sin(ph)*np.exp(-t*13)+filtered_noise(len(t),1600,6500)*np.exp(-t*330)*.16
 x*=np.minimum(t/.0008,1)*np.clip((.36-t)/.045,0,1)
 add('drums',np.tanh(x*1.2),st,amp)
def snare(st,amp=.22):
 t=np.arange(round(.22*SR))/SR;n=filtered_noise(len(t),1100,11500)
 env=np.exp(-t*22)*(1-np.exp(-t*600))
 x=n*env+.55*np.sin(2*np.pi*183*t)*np.exp(-t*30)+.12*np.sin(2*np.pi*310*t)*np.exp(-t*45)
 # Two small flam transients give the clap texture.
 for dl in [.006,.014]:
  k=round(dl*SR);x[k:]+=n[:-k]*np.exp(-(t[:-k])*90)*.2
 add('drums',x,st,amp)
def hat(st,amp=.06,opened=False,pan=.0):
 dur=.18 if opened else .06;t=np.arange(round(dur*SR))/SR
 n=filtered_noise(len(t),6500,18000);x=n*np.exp(-t*(28 if opened else 100))*np.minimum(t/.0005,1)
 add('drums',x,st,amp,pan)
def whoosh(st,dur=.35,amp=.11,pan_direction=1):
 t=np.arange(round(dur*SR))/SR;u=t/dur
 x=filtered_noise(len(t),450,9200)*np.sin(np.pi*u)**2
 # A smooth rising/descending tonal air component, not a loud rotor recording.
 x+=.08*np.sin(2*np.pi*(430*t+1750*t*t/dur))*np.sin(np.pi*u)**3
 p=pan_direction*(u*1.8-.9);stereo=np.column_stack((x*np.sqrt((1-p)/2),x*np.sqrt((1+p)/2)))
 add('effects',stereo,st,amp)
def impact(st,amp=.25):
 t=np.arange(round(.72*SR))/SR;ph=2*np.pi*np.cumsum(39+35*np.exp(-t*22))/SR
 x=np.sin(ph)*np.exp(-t*7)*np.minimum(t/.002,1)+.2*filtered_noise(len(t),300,6500)*np.exp(-t*22)
 add('effects',x,st,amp)
def click(st,amp=.12):
 t=np.arange(round(.08*SR))/SR;x=filtered_noise(len(t),900,13500)*np.exp(-t*100)+.4*np.sin(2*np.pi*920*t)*np.exp(-t*120)
 add('effects',x,st,amp)

# C# minor; a small rising opening leads to the first complete product reveal.
chords=[[49,56,61,64],[45,52,57,61],[52,59,64,68],[47,54,59,63]]
for j,m in enumerate([73,80,76,85]):note(j*B,1.0,m,.08,'pluck',-.5+j*.3)
for j,m in enumerate(chords[0]):note(0,2.4,m,.032,'pad',-.6+j*.4)
for bar in range(1,12):
 st=bar*4*B;ch=chords[(bar-1)%4]
 for j,m in enumerate(ch):note(st,4*B+.50,m,.040 if bar<7 else .047,'pad',-.65+j*.43)
 # Tight syncopated, mostly mono bass. Deliberately more present than prior score.
 root=ch[0]-12
 for off,ln,vel in [(0,.72,.27),(.875,.38,.18),(1.5,.42,.23),(2.0,.70,.27),(2.875,.38,.19),(3.5,.40,.22)]:
  note(st+off*B,ln*B,root+(12 if off==3.5 else 0),vel,'bass',0,'bass')
 arp=[ch[2]+12,ch[1]+12,ch[3]+12,ch[2]+12,ch[1]+24,ch[3]+12,ch[2]+12,ch[1]+12]
 for j,m in enumerate(arp):note(st+j*.5*B,.95,m,.048 if bar<7 else .062,'pluck',(-.50,.50)[j%2])
 if bar in [1,3,7,9,11]:
  for j,m in enumerate(ch):note(st,.56,m+12,.038,'stab',-.4+j*.27)

# Drum groove. Short strategic gaps emphasize the found-object and dock details.
kicks=[]
for bar in range(1,12):
 origin=bar*4
 for off in [0,1.5,2.75]:
  beat=origin+off
  if 22<=beat<24:continue
  st=beat*B;kick(st,.43 if bar<7 else .50);kicks.append(st)
 for off in [1,3]:
  beat=origin+off
  if 22<=beat<24:continue
  snare(beat*B,.19 if bar<7 else .235)
 for j in range(8):
  beat=origin+j*.5
  if 22<=beat<23.5:continue
  hat(beat*B,.042 if j%2==0 else .065,opened=(j==7),pan=(-.38,.38)[j%2])
 if bar in [3,6,7,10,11]:
  for off in [3.25,3.75]:hat((origin+off)*B,.04,pan=.55 if off>3.5 else -.55)

# Synchronized sound design. Precise cuts rather than a wash under the whole film.
for j,beat in enumerate([1,2,4,8,12,14,18,22,25,28,32,34,38,42,48]):
 dur=.18 if beat in [1,2] else .32
 whoosh(beat*B-dur*.66,dur,.055 if beat in [1,2,12,14] else .09,(-1)**j)
for beat in [4,8,28,34,42,48]:impact(beat*B,.19 if beat!=48 else .27)
for beat in [0,1,2]:click(beat*B,.10)
# Key acquisition and mobile response are deliberately audible design cues.
for start in [22.2*B,25.3*B]:
 note(start,.7,85,.115,'pluck',-.14,'effects');note(start+.075,.8,92,.085,'pluck',.14,'effects')
# Dock contact: one restrained tactile click, then a bright confirmation.
click(32.7*B,.19);note(33.0*B,.8,80,.072,'pluck',-.1,'effects')
# The ending opens out instead of maintaining 16th notes beneath the CTA.
for j,m in enumerate([49,56,61,64,68]):note(48*B,3.43,m,.055,'pad',-.7+j*.35)
for j,m in enumerate([73,76,80,85]):note(48*B+j*B*.5,2.5,m,.083,'pluck',-.45+j*.30)
note(48*B,2.5,37,.22,'bass',0,'bass');kick(48*B,.42);kicks.append(48*B)

# Sidechain-like breathing driven by the actual kick positions.
clock=np.arange(N)/SR;duck=np.ones(N)
for st in kicks:
 i=round(st*SR);ln=min(N-i,round(.36*SR))
 if ln>0:duck[i:i+ln]*=1-.52*np.exp(-np.arange(ln)/SR*13)
stems['bass']*=duck[:,None];stems['music']*=np.sqrt(duck[:,None])
# Stereo room tails, applied to music/FX only to preserve drum attack.
for bus in ['music','effects']:
 dry=stems[bus].copy()
 for delay,decay in [(.047,.14),(.079,.12),(.137,.095),(.193,.07),(.277,.04)]:
  k=round(delay*SR);stems[bus][k:,0]+=dry[:-k,1]*decay;stems[bus][k:,1]+=dry[:-k,0]*decay
fade=np.minimum(clock/.006,1)*np.clip((DUR-clock)/.60,0,1)
for bus in stems:stems[bus]*=fade[:,None]
mix=sum(stems.values());mix-=mix.mean(axis=0)
# Gentle shared peak safety. Final integrated loudness is set in mastering.
peak=np.max(np.abs(mix));gain=min(1,.89/peak)
for bus,arr in stems.items():
 wavfile.write(ROOT/'assets'/f'{bus}_140bpm.wav',SR,(arr*gain).astype(np.float32))
wavfile.write(ROOT/'assets'/'Momentum_140bpm_mix.wav',SR,(mix*gain).astype(np.float32))
(ROOT/'assets'/'music_metadata.json').write_text(json.dumps({'bpm':140,'key':'C# minor','duration_s':24,'sample_rate':SR,'seed':240016,'original_synthesis':True,'stems':list(stems),'raw_peak_before_gain':float(peak),'gain':float(gain),'synchronized_cut_beats':[0,1,2,4,8,12,14,18,22,25,28,32,34,38,42,48,56]},indent=2))
print('Original score and four stems written. Raw mix peak:',peak,'gain:',gain)
