"""Master the completed renders and record technical validation."""
import json,subprocess,time,zipfile,shutil
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];DEST=ROOT.parent

def probe(path):
 p=subprocess.run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(path)],capture_output=True,text=True)
 return json.loads(p.stdout) if p.returncode==0 else None

def wait_complete(path,duration):
 while True:
  d=probe(path)
  if d and abs(float(d['format']['duration'])-duration)<.05:return d
  time.sleep(3)

vf="curves=all='0/0 0.125/0.09 0.25/0.235 0.5/0.52 0.75/0.79 1/1',unsharp=5:5:0.25:5:5:0,noise=alls=1:allf=t+u,format=yuv420p"
report={}
for name,src,dur in [('FLOAT_Presence_30s_1080p.mp4','main_silent.mp4',30),('FLOAT_Presence_15s_Square.mp4','social_silent.mp4',15)]:
 p=ROOT/'renders'/src;wait_complete(p,dur);out=DEST/name
 af='volume=-1.7dB'
 if dur==15:af+=',atrim=0:15,afade=t=out:st=14.2:d=0.8'
 cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-threads','2','-i',str(p),'-i',str(ROOT/'assets/score_original.wav'),'-vf',vf,'-af',af,'-t',str(dur),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','slow','-crf','16','-threads','2','-c:a','aac','-b:a','192k','-ar','48000','-pix_fmt','yuv420p','-movflags','+faststart','-metadata','title=FLOAT — Presence','-metadata','comment=CGI concept visualization. Proposed experience; not a working prototype. Original synthesized score.','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709',str(out)]
 subprocess.run(cmd,check=True)
 report[name]=probe(out);print('MASTERED',str(out),flush=True)
# Covers are actual frames from these visual treatments, not product photography.
for src,name in [('shot_04.8.jpg','FLOAT_Presence_Cover.jpg'),('social_3.5.jpg','FLOAT_Presence_Square_Cover.jpg')]:
 im=Image.open(ROOT/'previews'/src);import numpy as np
 lut=np.interp(np.arange(256),[0,32,64,128,192,255],[0,23,60,133,202,255]).astype('uint8').tolist();im.point(lut*3).save(DEST/name,quality=96)
(ROOT/'deliverables/technical_validation.json').write_text(json.dumps(report,indent=2))
# No installed font files are shared.
with zipfile.ZipFile(DEST/'FLOAT_Presence_Source.zip','w',zipfile.ZIP_DEFLATED,6) as z:
 for fn in ['launch_film.py','social_cut.py','export_model.py','finalize.py','README.md','PHOTOREAL_FILM_BRIEF.md','SOCIAL_CAPTION.txt']:
  z.write(ROOT/'source'/fn,'FLOAT_Presence/source/'+fn)
 for fn in ['score_original.wav','FLOAT_concept_model.glb']:
  z.write(ROOT/'assets'/fn,'FLOAT_Presence/assets/'+fn)
 for fn in ['shot_01.7.jpg','shot_04.8.jpg','shot_09.8.jpg','shot_14.3.jpg','shot_20.1.jpg','shot_24.8.jpg','social_3.5.jpg']:
  z.write(ROOT/'previews'/fn,'FLOAT_Presence/previews/'+fn)
 z.write(ROOT/'deliverables/technical_validation.json','FLOAT_Presence/technical_validation.json')
print('PACKAGED',flush=True)
