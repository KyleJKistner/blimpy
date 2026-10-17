"""Mux, loudness-normalize and validate FLOAT / Room deliverables.

    python source/master.py --format wide --quality final

Inputs: renders/<format>_<quality>_silent.mp4 (finish.py) and
assets/audio/premaster_mix.wav (score.py). Outputs go to deliverables/:
the MP4, an SRT caption file, a cover JPEG, a 12-shot contact sheet and a QA
record. Audio is mastered to -14 LUFS integrated, -1 dBTP (two-pass loudnorm).
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import timeline as T  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DELIV = ROOT / 'deliverables'


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)


def probe(p):
    r = run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(p)], capture_output=True, text=True)
    return json.loads(r.stdout)


def loudness(path):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(path), '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                       capture_output=True, text=True)
    out = r.stderr[r.stderr.rfind('Summary:'):]
    vals = {}
    for line in out.splitlines():
        line = line.strip()
        if line.startswith('I:'):
            vals['integrated_lufs'] = float(line.split()[1])
        elif line.startswith('LRA:'):
            vals['lra_lu'] = float(line.split()[1])
        elif line.startswith('Peak:'):
            vals['true_peak_dbtp'] = float(line.split()[1])
    return vals


def master_audio(src, dst):
    first = run(['ffmpeg', '-hide_banner', '-i', str(src), '-af', 'loudnorm=I=-14:TP=-1.0:LRA=11:print_format=json',
                 '-f', 'null', '-'], capture_output=True, text=True)
    raw = first.stderr[first.stderr.rfind('{'):first.stderr.rfind('}') + 1]
    m = json.loads(raw)
    af = (f"loudnorm=I=-14:TP=-1.0:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    run(['ffmpeg', '-v', 'error', '-y', '-i', str(src), '-af', af, '-ar', '48000', '-ac', '2', '-c:a', 'pcm_s24le', str(dst)])
    return m


def srt(path):
    timing = json.loads((ROOT / 'assets' / 'voice' / 'timing.json').read_text())

    def ts(x):
        ms = int(round(x * 1000))
        return f'{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}'
    rows = []
    for i, ln in enumerate(timing['lines'], 1):
        who = 'FLOAT: ' if ln['who'] == 'float' else ''
        rows.append(f"{i}\n{ts(ln['start_s'])} --> {ts(ln['start_s'] + ln['duration_s'] + .4)}\n{who}{ln['text']}\n")
    path.write_text('\n'.join(rows))


def contact_sheet(video, dst, w, h):
    mids = [(a + b) // 2 for _, _, a, b, _ in T.SHOTS]
    sel = '+'.join(f'eq(n\\,{f})' for f in mids)
    tmp = DELIV / '_sheet'
    tmp.mkdir(exist_ok=True)
    run(['ffmpeg', '-v', 'error', '-y', '-i', str(video), '-vf', f'select={sel},scale={w}:{h}', '-fps_mode', 'vfr',
         '-q:v', '3', str(tmp / 's_%02d.jpg')])
    files = sorted(tmp.glob('s_*.jpg'))
    cols = 4
    rows = (len(files) + cols - 1) // cols
    board = Image.new('RGB', (w * cols, (h + 26) * rows), (14, 15, 17))
    d = ImageDraw.Draw(board)
    for i, f in enumerate(files):
        x, y = (i % cols) * w, (i // cols) * (h + 26)
        board.paste(Image.open(f), (x, y))
        sid, name, a, b, _ = T.SHOTS[i]
        d.text((x + 8, y + h + 6), f'{sid} {name}  {a / T.FPS:05.2f}-{b / T.FPS:05.2f}s', fill=(225, 225, 228))
        f.unlink()
    tmp.rmdir()
    board.save(dst, quality=92)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--format', choices=['wide', 'feed'], default='wide')
    p.add_argument('--quality', default='final')
    p.add_argument('--music', default='', help='optional replacement pre-master mix WAV')
    a = p.parse_args()
    DELIV.mkdir(exist_ok=True)
    silent = ROOT / 'renders' / f'{a.format}_{a.quality}_silent.mp4'
    mix = Path(a.music) if a.music else ROOT / 'assets' / 'audio' / 'premaster_mix.wav'
    mastered = ROOT / 'assets' / 'audio' / 'master_48k.wav'
    meas = master_audio(mix, mastered)
    suffix = '' if a.quality == 'final' else f'_{a.quality}'
    name = f"FLOAT_Room_30s_{'16x9' if a.format == 'wide' else '4x5'}{suffix}.mp4"
    out = DELIV / name
    W, H = (1920, 1080) if a.format == 'wide' else (1080, 1350)
    run(['ffmpeg', '-v', 'error', '-y', '-i', str(silent), '-i', str(mastered), '-map', '0:v:0', '-map', '1:a:0',
         '-vf', f'scale={W}:{H}:flags=lanczos,format=yuv420p', '-c:v', 'libx264', '-preset', 'slow', '-crf', '15',
         '-profile:v', 'high', '-level:v', '4.2', '-r', str(T.FPS), '-g', str(T.FPS * 2), '-bf', '2',
         '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-color_range', 'tv',
         '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-ac', '2', '-t', f'{T.FRAMES / T.FPS:.3f}',
         '-movflags', '+faststart', '-metadata', 'title=FLOAT | Room',
         '-metadata', 'comment=CGI concept visualization of a proposed product. Not footage of a working prototype. '
                      'Original synthesized score; synthetic stock TTS voices.', str(out)])
    d = probe(out)
    v = next(s for s in d['streams'] if s['codec_type'] == 'video')
    au = next(s for s in d['streams'] if s['codec_type'] == 'audio')
    checks = {
        'dimensions': (v['width'], v['height']) == (W, H),
        'fps_24': v['r_frame_rate'] == f'{T.FPS}/1',
        'frames_720': int(v.get('nb_frames', 0)) == T.FRAMES,
        'duration_30s': abs(float(d['format']['duration']) - T.FRAMES / T.FPS) < .05,
        'yuv420p_bt709': v['pix_fmt'] == 'yuv420p' and v.get('color_space') == 'bt709',
        'audio_48k_stereo': int(au['sample_rate']) == 48000 and au['channels'] == 2,
    }
    run(['ffmpeg', '-v', 'error', '-i', str(out), '-f', 'null', '-'], stdout=subprocess.DEVNULL)
    checks['full_decode'] = True
    loud = loudness(out)
    checks['loudness_within_1lu'] = abs(loud.get('integrated_lufs', 0) + 14) <= 1.0
    checks['true_peak_below_-0.5'] = loud.get('true_peak_dbtp', 0) <= -.5
    srt(DELIV / f"FLOAT_Room_30s_captions{suffix}.srt")
    cover = DELIV / out.name.replace('.mp4', '_cover.jpg')
    run(['ffmpeg', '-v', 'error', '-y', '-ss', '9.0', '-i', str(out), '-frames:v', '1', '-q:v', '2', str(cover)])
    sw, sh = (480, 270) if a.format == 'wide' else (270, 338)
    contact_sheet(out, DELIV / out.name.replace('.mp4', '_sheet.jpg'), sw, sh)
    qa = dict(file=out.name, bytes=out.stat().st_size, width=W, height=H, fps=T.FPS, frames=int(v.get('nb_frames', 0)),
              duration_s=float(d['format']['duration']), video=f"{v['codec_name']} {v.get('profile')} {v['pix_fmt']}",
              audio=f"{au['codec_name']} {au['sample_rate']} Hz {au['channels']} ch", loudnorm_first_pass=meas,
              measured=loud, checks=checks, concept_label='burned in on every frame before the end card; end card carries full disclosure',
              status='CGI concept visualization, not prototype footage')
    (DELIV / out.name.replace('.mp4', '_qa.json')).write_text(json.dumps(qa, indent=1))
    print(json.dumps(qa['checks'], indent=1), loud, flush=True)
    if not all(checks.values()):
        raise SystemExit('QA failed: ' + ', '.join(k for k, ok in checks.items() if not ok))


if __name__ == '__main__':
    main()
