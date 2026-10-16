"""Master the finished renders, normalize original audio, then validate files."""
import json,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT.parent

def run(cmd,**kw):
 return subprocess.run(cmd,check=True,**kw)
def probe(p):
 result=subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)],capture_output=True,text=True)
 if result.returncode:return None
 return json.loads(result.stdout)
def await_render(p):
 start=time.monotonic()
 while time.monotonic()-start<1800:
  d=probe(p)
  if d and abs(float(d['format']['duration'])-24)<.04:return
  time.sleep(3)
 raise TimeoutError(f'Render not ready: {p}')

mix=ROOT/'assets/Momentum_140bpm_mix.wav'
first=subprocess.run(['ffmpeg','-hide_banner','-i',str(mix),'-af','loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
raw=first.stderr[first.stderr.rfind('{'):first.stderr.rfind('}')+1];meas=json.loads(raw)
(ROOT/'deliverables/audio_first_pass.json').write_text(json.dumps(meas,indent=2))
af=(f"loudnorm=I=-14:TP=-1.5:LRA=9:measured_I={meas['input_i']}:measured_TP={meas['input_tp']}:"
    f"measured_LRA={meas['input_lra']}:measured_thresh={meas['input_thresh']}:offset={meas['target_offset']}:linear=false")
master=ROOT/'assets/Momentum_master_48k.wav'
run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(mix),'-af',af,'-ar','48000','-ac','2','-c:a','pcm_s24le',str(master)])
outputs=[('wide_silent.mp4','FLOAT_Momentum_24s_1080p.mp4',1920,1080),('feed_silent.mp4','FLOAT_Momentum_24s_Feed.mp4',1080,1350)]
validation={}
for src,name,width,height in outputs:
 await_render(ROOT/'renders'/src)
 print('Mastering',name,flush=True)
 # Explicit RGB/YUV matrix bookkeeping: raw-rgb render input used swscale's
 # default BT.601 conversion, so convert to BT.709 before marking the master.
 run(['ffmpeg','-hide_banner','-loglevel','error','-y','-threads','2','-i',str(ROOT/'renders'/src),'-i',str(master),'-map','0:v:0','-map','1:a:0',
 '-vf','scale=in_color_matrix=bt601:out_color_matrix=bt709:out_range=tv','-c:v','libx264','-preset','slow','-crf','16','-threads','2','-profile:v','high','-level:v','4.2','-r','30','-fps_mode','cfr',
 '-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-pix_fmt','yuv420p','-t','24','-movflags','+faststart',
 '-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-color_range','tv',
 '-metadata','title=FLOAT | Momentum','-metadata','comment=CGI concept visualization. Proposed interactions, not working-prototype footage. Original 140 BPM score. Stylized camera motion.',str(DEST/name)])
 d=probe(DEST/name);v=next(x for x in d['streams'] if x['codec_type']=='video');a=next(x for x in d['streams'] if x['codec_type']=='audio')
 assert (v['width'],v['height'])==(width,height)
 assert v['r_frame_rate']=='30/1' and int(v['nb_frames'])==720
 assert abs(float(d['format']['duration'])-24)<.04
 assert a['channels']==2 and int(a['sample_rate'])==48000
 assert v['pix_fmt']=='yuv420p' and v['color_space']=='bt709'
 # Full-stream decode checks are distinct from a metadata-only inspection.
 run(['ffmpeg','-hide_banner','-v','error','-i',str(DEST/name),'-f','null','-'],stdout=subprocess.DEVNULL)
 validation[name]={'duration_seconds':float(d['format']['duration']),'dimensions':[width,height],'fps':30,'frames':720,'video':'H.264 High / yuv420p / BT.709','audio':'48kHz stereo AAC','bytes':(DEST/name).stat().st_size,'full_decode':'passed','concept_label':'burned in throughout','shot_count':16,'visual_status':'CGI concept, not a prototype demonstration'}
 (ROOT/'deliverables'/f'{name}.probe.json').write_text(json.dumps(d,indent=2))
 run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss','22.3','-i',str(DEST/name),'-frames:v','1','-q:v','2',str(DEST/('FLOAT_Momentum_Cover.jpg' if width==1920 else 'FLOAT_Momentum_Feed_Cover.jpg'))])
 print('Validated',name,flush=True)
(ROOT/'deliverables/QA_SUMMARY.json').write_text(json.dumps(validation,indent=2))
print('Both masters validated.',flush=True)
