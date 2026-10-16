"""Master revision: replace the handoff shot after typography QA, without double grading."""
import json, subprocess, time, zipfile
from pathlib import Path
from PIL import Image
import numpy as np
ROOT=Path(__file__).resolve().parents[1]; DEST=ROOT.parent
VF="curves=all='0/0 0.125/0.09 0.25/0.235 0.5/0.52 0.75/0.79 1/1',unsharp=5:5:0.25:5:5:0,noise=alls=1:allf=t+u,format=yuv420p"
def probe(p):
 r=subprocess.run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(p)],capture_output=True,text=True)
 return json.loads(r.stdout) if r.returncode==0 else None
COMMON=['-c:v','libx264','-preset','slow','-crf','16','-threads','2','-c:a','aac','-b:a','192k','-ar','48000','-pix_fmt','yuv420p','-movflags','+faststart','-metadata','title=FLOAT — Presence','-metadata','comment=CGI concept visualization. Proposed experience; not a working prototype. Original synthesized score.','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709']
fc=f"[0:v]split=2[a][b];[a]trim=end=16,setpts=PTS-STARTPTS[p1];[1:v]setpts=PTS-STARTPTS[p2];[b]trim=start=23,setpts=PTS-STARTPTS[p3];[p1][p2][p3]concat=n=3:v=1:a=0,{VF}[v]"
out=DEST/'FLOAT_Presence_30s_1080p.mp4'
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-filter_complex_threads','2','-i',str(ROOT/'renders/main_silent.mp4'),'-i',str(ROOT/'renders/handoff_fixed.mp4'),'-i',str(ROOT/'assets/score_original.wav'),'-filter_complex',fc,'-map','[v]','-map','2:a:0','-af','volume=-1.7dB','-t','30']+COMMON+[str(out)],check=True)
print('Landscape mastered',flush=True)
while True:
 d=probe(ROOT/'renders/social_silent.mp4')
 if d and abs(float(d['format']['duration'])-15)<.02:break
 time.sleep(2)
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-threads','2','-i',str(ROOT/'renders/social_silent.mp4'),'-i',str(ROOT/'assets/score_original.wav'),'-vf',VF,'-af','volume=-1.7dB,atrim=0:15,afade=t=out:st=14.2:d=0.8','-map','0:v:0','-map','1:a:0','-t','15']+COMMON+[str(DEST/'FLOAT_Presence_15s_Square.mp4')],check=True)
print('Square mastered',flush=True)
report={};qa={}
for name,dur,width,height in [('FLOAT_Presence_30s_1080p.mp4',30,1920,1080),('FLOAT_Presence_15s_Square.mp4',15,1080,1080)]:
 d=probe(DEST/name);report[name]=d;v=next(s for s in d['streams'] if s['codec_type']=='video');a=next(s for s in d['streams'] if s['codec_type']=='audio')
 assert v['width']==width and v['height']==height and int(v['nb_frames'])==24*dur
 assert v['r_frame_rate']=='24/1' and abs(float(d['format']['duration'])-dur)<.03
 assert a['channels']==2 and int(a['sample_rate'])==48000
 qa[name]={'duration_s':dur,'width':width,'height':height,'frames':int(v['nb_frames']),'fps':24,'audio':'48kHz stereo AAC','size_bytes':(DEST/name).stat().st_size,'technical_checks':'passed','visual_status':'CGI concept, not prototype footage'}
(ROOT/'deliverables/technical_validation.json').write_text(json.dumps(report,indent=2))
(ROOT/'deliverables/QA_SUMMARY.json').write_text(json.dumps(qa,indent=2))
for src,ss,fn in [('handoff_fixed.mp4','4.1','shot_20.1.jpg'),('social_silent.mp4','10.1','social_10.1.jpg')]:
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',ss,'-i',str(ROOT/'renders'/src),'-frames:v','1',str(ROOT/'previews'/fn)],check=True)
with zipfile.ZipFile(DEST/'FLOAT_Presence_Source.zip','w',zipfile.ZIP_DEFLATED,6) as z:
 for fn in ['launch_film.py','social_cut.py','export_model.py','finalize.py','master_revision.py','README.md','requirements.txt','PHOTOREAL_FILM_BRIEF.md','SOCIAL_CAPTION.txt']:
  z.write(ROOT/'source'/fn,'FLOAT_Presence/source/'+fn)
 for fn in ['score_original.wav','FLOAT_concept_model.glb']:
  z.write(ROOT/'assets'/fn,'FLOAT_Presence/assets/'+fn)
 for fn in ['shot_01.7.jpg','shot_04.8.jpg','shot_09.8.jpg','shot_14.3.jpg','shot_20.1.jpg','shot_24.8.jpg','social_3.5.jpg','social_10.1.jpg']:
  z.write(ROOT/'previews'/fn,'FLOAT_Presence/previews/'+fn)
 for fn in ['technical_validation.json','QA_SUMMARY.json']:
  z.write(ROOT/'deliverables'/fn,'FLOAT_Presence/'+fn)
 assert not any(x.lower().endswith(('.ttf','.otf','.woff','.woff2')) for x in z.namelist())
print('Validated and packaged',flush=True)
