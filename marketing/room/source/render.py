"""Render FLOAT / Room frames with Blender Cycles.

    blender -b --python source/render.py -- --quality preview --shots S01,S05
    blender -b --python source/render.py -- --quality final --format wide --gpu

Frames are written as renders/<format>/<quality>/f_0000.png using global frame
numbers. Existing frames are skipped, so an interrupted render resumes.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scene as S       # noqa: E402
import shots            # noqa: E402
import timeline as T    # noqa: E402

QUALITY = {
    # width (wide), samples, motion blur, volumetric haze
    'preview': dict(width=640, samples=24, blur=False, haze=False),
    'animatic': dict(width=480, samples=10, blur=False, haze=False),
    'draft': dict(width=960, samples=40, blur=True, haze=False),
    'final': dict(width=1920, samples=160, blur=True, haze=True),
}
# End-card background is defocused and darkened under type; it needs fewer samples.
LOW_SAMPLE_SHOTS = {'S12': .5}
# Sun-beam haze only where the beams read on screen (it is the costliest effect).
HAZE_SHOTS = {'S01', 'S05', 'S11', 'S12'}


def parse():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument('--quality', choices=QUALITY, default='preview')
    p.add_argument('--format', choices=['wide', 'feed'], default='wide')
    p.add_argument('--shots', default='all', help='comma-separated shot ids or "all"')
    p.add_argument('--frames', default='', help='explicit global frames, e.g. 10,250,300; overrides --every')
    p.add_argument('--every', type=int, default=0, help='render every Nth frame of each shot (0 = middle frame only for preview)')
    p.add_argument('--samples', type=int, default=0)
    p.add_argument('--gpu', action='store_true')
    p.add_argument('--out', default='')
    p.add_argument('--haze', choices=['auto', 'on', 'off'], default='auto')
    p.add_argument('--track-only', action='store_true', help='write screen-space tracks for overlays, no rendering')
    p.add_argument('--shard', default='0/1', help='i/n: render only frames where frame %% n == i (multi-machine)')
    return p.parse_args(argv)


def track_points(H):
    hero = H['units'][0]['root']
    return {
        'keys': lambda: S.KEYS_AT,
        'hero_pod': lambda: hero.matrix_world @ Vector((0, -.04, S.POD_Z)),
        'hero': lambda: hero.matrix_world.translation.copy(),
    }


def write_tracks(H, cam, sid, f0, f1, path):
    sc = bpy.context.scene
    data = json.loads(path.read_text()) if path.exists() else {}
    pts = track_points(H)
    for f in range(f0, f1):
        sc.frame_set(f)
        row = {}
        for name, fn in pts.items():
            x, y, z = world_to_camera_view(sc, cam, fn())
            row[name] = [round(x, 5), round(1 - y, 5), round(z, 4)]
        data[str(f)] = row
    path.write_text(json.dumps(data))


def main():
    a = parse()
    q = dict(QUALITY[a.quality])
    haze = q['haze'] if a.haze == 'auto' else a.haze == 'on'
    w = q['width']
    h = w * 9 // 16
    if a.format == 'feed':
        w, h = round(q['width'] * 1080 / 1920 / 2) * 2, round(q['width'] * 1350 / 1920 / 2) * 2
    H = S.build(volumetric=haze)
    samples = a.samples or q['samples']
    S.configure_render(w, h, samples, gpu=a.gpu, motion_blur=q['blur'], deep=a.quality == 'final')
    cam = bpy.data.objects.new('camera', bpy.data.cameras.new('camera'))
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    cam.data.sensor_fit = 'HORIZONTAL' if a.format == 'wide' else 'VERTICAL'
    cam.data.sensor_width = 36
    cam.data.sensor_height = 36
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_blades = 7
    cam.data.dof.aperture_rotation = 0.3
    cam.data.clip_start = .01
    cam.data.clip_end = 60
    out = Path(a.out) if a.out else S.ROOT / 'renders' / a.format / a.quality
    out.mkdir(parents=True, exist_ok=True)
    wanted = None if a.shots == 'all' else set(a.shots.split(','))
    explicit = [int(x) for x in a.frames.split(',') if x] if a.frames else None
    sc = bpy.context.scene
    total = 0
    t_start = time.monotonic()
    for sid, name, f0, f1, _ in T.SHOTS:
        if wanted and sid not in wanted:
            continue
        if explicit is not None:
            frames = [f for f in explicit if f0 <= f < f1]
        elif a.every:
            frames = list(range(f0, f1, a.every))
        elif a.quality == 'preview':
            frames = [(f0 + f1) // 2]
        else:
            frames = list(range(f0, f1))
        si, sn = (int(x) for x in a.shard.split('/'))
        frames = [f for f in frames if f % sn == si and not (out / f'f_{f:04d}.png').exists()]
        if a.track_only:
            shots.bake(H, cam, sid, a.format)
            write_tracks(H, cam, sid, f0, f1, S.ROOT / 'renders' / a.format / 'tracks.json')
            print('TRACKED', sid, flush=True)
            continue
        if not frames:
            continue
        shots.bake(H, cam, sid, a.format)
        write_tracks(H, cam, sid, f0, f1, S.ROOT / 'renders' / a.format / 'tracks.json')
        sc.cycles.samples = max(16, int(samples * LOW_SAMPLE_SHOTS.get(sid, 1)))
        if H['haze'] is not None:
            H['haze'].hide_render = sid not in HAZE_SHOTS
        for f in frames:
            sc.frame_set(f)
            sc.render.filepath = str(out / f'f_{f:04d}.png')
            t0 = time.monotonic()
            bpy.ops.render.render(write_still=True)
            total += 1
            print(f'RENDERED {sid} {name} frame {f} {time.monotonic() - t0:.1f}s '
                  f'(total {total}, {time.monotonic() - t_start:.0f}s)', flush=True)


if __name__ == '__main__':
    main()
