"""Collect verified masters' preview frames and editable, font-free sources."""
import json,time,zipfile,subprocess,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];DEST=ROOT.parent
for _ in range(240):
 if (ROOT/'deliverables/QA_SUMMARY.json').exists():break
 time.sleep(2)
else:raise TimeoutError('Master verification did not finish')
times=[.2,.64,1.22,2.58,4.4,5.58,6.85,8.58,10.03,11.35,12.9,14.18,15.4,17.22,19.31,22.35]
for typ,name,cell in [('wide','FLOAT_Momentum_24s_1080p.mp4',(480,270)),('feed','FLOAT_Momentum_24s_Feed.mp4',(270,338))]:
 # Extract exact selected frames in one full decode, then assemble a QC sheet.
 select='+'.join(f'eq(n\\,{round(t*30)})' for t in times)
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(DEST/name),'-vf',f"select={select},scale={cell[0]}:{cell[1]}",'-fps_mode','vfr','-q:v','3',str(ROOT/'previews'/f'final_{typ}_%02d.jpg')],check=True)
 cw,ch=cell;board=Image.new('RGB',(cw*4,(ch+23)*4),(15,18,22));d=ImageDraw.Draw(board)
 files=sorted((ROOT/'previews').glob(f'final_{typ}_[0-9][0-9].jpg'));assert len(files)==16
 for i,f in enumerate(files):
  x,y=(i%4)*cw,(i//4)*(ch+23);board.paste(Image.open(f),(x,y));d.text((x+8,y+ch+5),f'{i+1:02d} / {times[i]:05.2f}s',fill=(220,224,229))
 board.save(ROOT/'previews'/f'final_{typ}_sheet.jpg',quality=94)
# Two masters and the covers exist before links are exposed.
files=[DEST/'FLOAT_Momentum_24s_1080p.mp4',DEST/'FLOAT_Momentum_24s_Feed.mp4',DEST/'FLOAT_Momentum_Cover.jpg',DEST/'FLOAT_Momentum_Feed_Cover.jpg']
assert all(p.is_file() and p.stat().st_size>0 for p in files)
manifest={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files}
(ROOT/'deliverables/file_manifest.json').write_text(json.dumps(manifest,indent=2))
pack=DEST/'FLOAT_Momentum_Source.zip'
with zipfile.ZipFile(pack,'w',zipfile.ZIP_DEFLATED,6) as z:
 z.write(ROOT/'README.md','FLOAT_Momentum/README.md')
 for folder in ['source','assets','deliverables']:
  for p in sorted((ROOT/folder).iterdir()):
   if not p.is_file() or p.suffix in ['.log','.gltf'] or p.name=='Momentum_140bpm_mix.wav':continue
   if p.suffix.lower() in ['.ttf','.otf','.woff','.woff2','.ttc']:raise RuntimeError('Font files may not be bundled')
   z.write(p,'FLOAT_Momentum/'+str(p.relative_to(ROOT)))
 for name in ['final_wide_sheet.jpg','final_feed_sheet.jpg']:
  p=ROOT/'previews'/name;z.write(p,'FLOAT_Momentum/previews/'+name)
 for p in [DEST/'FLOAT_Momentum_Cover.jpg',DEST/'FLOAT_Momentum_Feed_Cover.jpg']:
  z.write(p,'FLOAT_Momentum/previews/'+p.name)
 assert not any(n.lower().endswith(('.ttf','.otf','.woff','.woff2','.ttc')) for n in z.namelist())
print('Packaged:',pack,'bytes:',pack.stat().st_size,flush=True)
print((ROOT/'deliverables/QA_SUMMARY.json').read_text(),flush=True)
