"""Render start/end-frame plates for generated live-action inserts (Blender).

    blender -b --python source/plates.py -- [--gpu] [--samples 128]

Each plate is a frame of the CG film (same set, product, light and lens) that an
image-to-video model animates, so generated shots cut cleanly against the CG.
See SEEDANCE_PACK.md for the matching prompts. Output: plates/stills/*.png
"""
import argparse
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scene as S       # noqa: E402
import shots            # noqa: E402
import timeline as T    # noqa: E402

# name: (shot whose performance to use, frame, camera override or None, hide keys)
PLATES = {
    'P1_ask_start': ('S01', 0, ((2.55, -2.55, 1.32), (-.05, .45, 1.27), 30, 4.0), False),
    'P2_pickup_start': ('S04', 165, None, False),
    'P2_pickup_end': ('S04', 165, None, True),
    'P3_thanks_start': ('S04', 160, ((.48, -.62, 1.50), (1.22, .30, 1.08), 32, 2.8), False),
    'P4_cook_start': ('S12', 500, ((.35, -1.55, 1.55), (-.75, -2.70, 1.00), 32, 2.8), False),
    'P5_call_start': ('S14', 600, ((.95, -.05, 1.05), (-.10, -.70, .55), 30, 2.8), False),
}


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument('--gpu', action='store_true')
    p.add_argument('--samples', type=int, default=96)
    p.add_argument('--width', type=int, default=1920)
    p.add_argument('--only', default='')
    a = p.parse_args(argv)
    H = S.build(volumetric=False)
    S.configure_render(a.width, a.width * 9 // 16, a.samples, gpu=a.gpu, motion_blur=False)
    cam = bpy.data.objects.new('camera', bpy.data.cameras.new('camera'))
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    cam.data.sensor_fit = 'HORIZONTAL'
    cam.data.sensor_width = 36
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_blades = 7
    out = S.ROOT / 'plates' / 'stills'
    out.mkdir(parents=True, exist_ok=True)
    keys = [H['keys']] + list(H['keys'].children_recursive)
    for name, (sid, frame, override, hide_keys) in PLATES.items():
        if a.only and name not in a.only.split(','):
            continue
        shots.bake(H, cam, sid)
        S.set_time_of_day(H, T.shot(sid)[4])
        sc = bpy.context.scene
        sc.frame_set(frame)
        if override:
            loc, target, lens, fstop = override
            cam.animation_data_clear()
            cam.data.animation_data_clear()
            cam.location = loc
            cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
            cam.data.lens = lens
            cam.data.dof.aperture_fstop = fstop
            hero = H['units'][0]['root']
            cam.data.dof.focus_distance = (hero.matrix_world.translation - Vector(loc)).length
        for o in keys:
            o.hide_render = hide_keys
        sc.render.filepath = str(out / f'{name}.png')
        bpy.ops.render.render(write_still=True)
        print('PLATE', name, flush=True)


if __name__ == '__main__':
    main()
