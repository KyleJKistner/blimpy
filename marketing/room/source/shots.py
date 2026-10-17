"""Per-shot cameras and performances for FLOAT / Room (runs inside Blender).

FLOAT's own motion is deliberately slow (about 0.35 m/s peak, 45 deg/s yaw):
energy comes from camera movement and the edit, not implied performance.
"""
import json
import math
from pathlib import Path

import bpy
from mathutils import Euler, Quaternion, Vector

import scene as S
import timeline as T

VOICE_TIMING = S.ROOT / 'assets' / 'voice' / 'timing.json'


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def smoother(x):
    x = clamp(x)
    return x * x * x * (x * (6 * x - 15) + 10)


def ramp(t, t0, t1):
    return smoother((t - t0) / (t1 - t0))


def lerp(a, b, u):
    return Vector(a).lerp(Vector(b), u)


def yaw_to(src, dst):
    d = Vector(dst) - Vector(src)
    return math.degrees(math.atan2(d.x, -d.y))


def heading(yaw_deg):
    y = math.radians(yaw_deg)
    return Vector((math.sin(y), -math.cos(y), 0))


def local_to_world(pos, yaw_deg, p):
    return Vector(pos) + Euler((0, 0, math.radians(yaw_deg))).to_matrix() @ Vector(p)


class Speech:
    """Speech envelopes for LED animation, from voice.py's timing file if present."""

    def __init__(self):
        self.lines = {}
        if VOICE_TIMING.exists():
            data = json.loads(VOICE_TIMING.read_text())
            for line in data['lines']:
                self.lines[line['id']] = line
        for d in T.DIALOGUE:
            self.lines.setdefault(d['id'], dict(id=d['id'], start_s=d['start_s'],
                                                duration_s=.075 * len(d['text']), envelope=None, fps=T.FPS))

    def env(self, line_id, t):
        ln = self.lines[line_id]
        u = t - ln['start_s']
        if u < 0 or u > ln['duration_s']:
            return 0.0
        e = ln.get('envelope')
        if e:
            i = u * ln.get('fps', T.FPS)
            k = int(i)
            if k + 1 >= len(e):
                return e[-1]
            return e[k] + (e[k + 1] - e[k]) * (i - k)
        return .55 + .45 * math.sin(u * 23) * math.sin(u * 7.3)

    def end(self, line_id):
        ln = self.lines[line_id]
        return ln['start_s'] + ln['duration_s']


SPEECH = None


def bob(t, phase=0.0):
    z = .007 * math.sin(2 * math.pi * .21 * t + phase) + .003 * math.sin(2 * math.pi * .47 * t + 2 * phase)
    pitch = .55 * math.sin(2 * math.pi * .17 * t + phase + 1)
    roll = .45 * math.sin(2 * math.pi * .13 * t + phase + 2)
    return z, pitch, roll


def breathe(t, lo, hi, period=2.6, phase=0.0):
    return lo + (hi - lo) * (.5 + .5 * math.sin(2 * math.pi * t / period + phase))


# ----------------------------------------------------------------------------
# Performances. Each shot sets every unit explicitly; t is absolute seconds.
# ----------------------------------------------------------------------------

P0 = Vector((-0.55, 0.40, 1.47))            # morning hover, in the sun
P1 = Vector((0.35, -0.10, 1.30))            # end of the title glide
SOFA_HOVER = Vector((1.30, 0.38, 1.12))     # above the far cushion, facing the keys
KITCHEN_HOVER = Vector((-0.30, -2.02, 1.47))
STOVE_VIEW = Vector((-0.80, -2.12, 1.33))
PLANT_HOVER = Vector((-2.30, 1.50, 1.62))
PLANT_AT = Vector((-2.98, 2.30, 1.55))
CALL_HOVER = Vector((-0.12, -0.62, 0.99))
WINDOW_HOVER = Vector((-2.40, 0.55, 1.50))
DOCK_LAND_T = 28.95                         # day unit settles on the middle pad
LIFT_T = 29.55                              # charged unit leaves pad 0


def unit(pos, yaw, t, phase=0.0, spinning=True, led=4.5, damp=1.0):
    dz, pitch, roll = bob(t, phase)
    return dict(pos=Vector(pos) + Vector((0, 0, dz * damp)), yaw=yaw, pitch=pitch * damp, roll=roll * damp,
                spinning=spinning, led=led)


def docked(i, t, phase):
    pad = Vector((S.DOCK_PADS[i][0], S.DOCK_PADS[i][1], S.DOCKED_Z))
    return dict(pos=pad, yaw=(0, 0, -4)[i], pitch=0, roll=0, spinning=False, led=breathe(t, 1.2, 3.4, 2.6, phase))


def speaking(t, *lines, base=4.5):
    return base + .5 * math.sin(2 * math.pi * t / 1.3) + 7.0 * sum(SPEECH.env(k, t) for k in lines)


def hero_state(sid, t):
    if sid == 'S01':
        wake = ramp(t, 1.2, 1.8)
        return unit(P0, -20 + 66 * ramp(t, 0.9, 2.3), t, .3, False, .5 + 4.5 * wake)
    if sid == 'S02':
        return unit(P0, 46, t, .3, False, speaking(t, 'look'))
    if sid == 'S03':
        u = ramp(t, 3.5, 5.0) * .85 + clamp((t - 3.5) / 1.5) * .15
        pos = lerp((0.35, -0.10, 1.30), (0.80, 0.06, 1.13), u)
        return unit(pos, yaw_to(pos, S.KEYS_AT), t, .3)
    if sid == 'S04':
        return unit(SOFA_HOVER - Vector((0, 0, .04 * ramp(t, 5.0, 6.5))), 3 - 3 * ramp(t, 5.2, 6.4), t, .3,
                    led=speaking(t, 'found'))
    if sid in ('S05', 'S06', 'S07'):
        u = ramp(t, 7.6, 12.0)
        pos = lerp(P0, P1, u) + Vector((0, 0, .04 * math.sin(math.pi * u)))
        st = unit(pos, 46 + 19 * ramp(t, 7.6, 9.6), t, .3)
        st['spinning'] = t >= 7.42
        return st
    if sid == 'S09':
        a, b = Vector((0.30, -1.15, 1.42)), Vector((-0.62, -2.02, 1.34))
        return unit(lerp(a, b, ramp(t, 13.2, 15.3)), yaw_to(a, b), t, .3)
    if sid == 'S10':
        pos = STOVE_VIEW + Vector((.02 * (t - 15.0), 0, -.01 * (t - 15.0)))
        return unit(pos, yaw_to(pos, S.KNOBS[1].lerp(S.KNOBS[2], .5)), t, .3)
    if sid == 'S11':
        pos = PLANT_HOVER + Vector((-.05, .04, 0)) * ramp(t, 17.0, 20.0)
        return unit(pos, yaw_to(pos, PLANT_AT), t, .3, led=speaking(t, 'plant'))
    if sid == 'S12':
        return unit(KITCHEN_HOVER, -30 + 65 * ramp(t, 20.55, 21.9), t, .3, led=speaking(t, 'next', 'garlic'))
    if sid == 'S13':
        pos = Vector((-0.45, -2.25, 1.40))
        return unit(pos, yaw_to(pos, S.PAN_AT), t, .3, led=speaking(t, 'garlic'))
    if sid == 'S14':
        return unit(CALL_HOVER, 108, t, .3, led=speaking(t, 'grandma', base=3.5))
    if sid == 'S15':
        pad = Vector((S.DOCK_PADS[1][0], S.DOCK_PADS[1][1], S.DOCKED_Z))
        start = Vector((pad.x - .05, 2.18, 1.31))
        u = ramp(t, 27.0, DOCK_LAND_T)
        if t >= DOCK_LAND_T:
            return docked(1, t, 0.0)
        return unit(lerp(start, pad, u), 8 * (1 - u), t, .3, led=4.5, damp=1 - ramp(t, 28.4, DOCK_LAND_T))
    return docked(1, t, 0.0)


def dock_a_state(sid, t):
    if t < LIFT_T - .2 or sid not in ('S15', 'S16', 'S17', 'S18'):
        st = docked(0, t, 1.0)
        st['spinning'] = t >= LIFT_T - .2 and sid == 'S15'
        return st
    if sid in ('S15', 'S16'):
        pad = Vector((S.DOCK_PADS[0][0], S.DOCK_PADS[0][1], S.DOCKED_Z))
        lift = ramp(t, LIFT_T, 33.0)
        k = ramp(t, LIFT_T, LIFT_T + .85)
        return unit(pad + Vector((0, -.42 * lift ** 1.4, .62 * lift)), -12 * lift, t, 1.7,
                    led=1.2 + 3.8 * ramp(t, LIFT_T - .2, LIFT_T + .35), damp=k)
    if sid == 'S17':
        return unit(WINDOW_HOVER, 92 - 10 * ramp(t, 33.0, 36.0), t, 1.7)
    return unit((-0.55, 0.45, 1.46), 38, t, 1.7)


def dock_b_state(sid, t):
    return docked(2, t, 2.1)


def pad_levels(t):
    return [breathe(t, 1.0, 2.6, 2.6, 1.0) * (1 - ramp(t, LIFT_T - .15, LIFT_T + .35)) + .15,
            .15 + 2.2 * ramp(t, DOCK_LAND_T, DOCK_LAND_T + .55) * breathe(t, .55, 1.0, 2.6),
            breathe(t, 1.0, 2.6, 2.6, 2.1)]


POV_SHOTS = {'S03', 'S10'}
FLAME_SHOTS = {'S12', 'S13'}


# ----------------------------------------------------------------------------
# Cameras: each returns (location, target, lens_mm, f_stop, focus_point, roll_deg)
# ----------------------------------------------------------------------------

def pod_of(h):
    return local_to_world(h['pos'], h['yaw'], (0, -.04, S.POD_Z))


def cam_S01(t, u):
    loc = lerp((2.25, -2.25, 1.34), (2.00, -1.98, 1.31), smooth(u) * .8 + u * .2)
    return loc, P0 + Vector((.62, .05, -.10)), 34, 4.0, P0, 0


def cam_S02(t, u):
    h = hero_state('S02', t)
    f = heading(h['yaw'])
    side = Vector((-f.y, f.x, 0))
    pod = local_to_world(h['pos'], h['yaw'], (0, 0, S.POD_Z))
    loc = pod + f * (.50 - .09 * smooth(u)) + side * .07 + Vector((0, 0, -.012))
    return loc, pod + Vector((0, 0, .008)) + side * .012, 85, 2.0, pod_of(h), -2 + 3 * u


def cam_S03(t, u):
    h = hero_state('S03', t)
    lens = local_to_world(h['pos'], h['yaw'], (0, -.045, S.POD_Z))
    target = S.KEYS_AT + Vector((-.06 + .05 * smooth(u), .03, .05))
    return lens, target, 18, 11.0, S.KEYS_AT, 1.5 * math.sin(t * 2.1)


def cam_S04(t, u):
    h = hero_state('S04', t)
    loc = lerp((1.30, -.82, .530), (1.30, -.76, .528), smooth(u))
    rack = ramp(t, 5.10, 5.65)
    focus = lerp(pod_of(h), S.KEYS_AT + Vector((0, 0, .01)), rack)
    return loc, Vector((1.31, .10, .53)), 22, 1.8, focus, 0


def cam_S05(t, u):
    h = hero_state('S05', t)
    c = Vector(S.FANS['right'][0])
    fan = local_to_world(h['pos'], h['yaw'], c)
    loc = local_to_world(h['pos'], h['yaw'], c + Vector((.16 - .03 * u, -.17 + .02 * u, -.06 + .02 * u)))
    target = local_to_world(h['pos'], h['yaw'], c + Vector((-.045, 0, .025)))
    return loc, target, 50, 2.8, fan, 4 - 6 * u


def cam_S06(t, u):
    h = hero_state('S06', t)
    a = math.radians(-8 * smooth(u))
    off = Vector((.95 * math.cos(a) + .55 * math.sin(a), -.55 * math.cos(a) + .95 * math.sin(a), -.42 + .06 * u))
    loc = local_to_world(h['pos'], h['yaw'], off)
    return loc, h['pos'] + Vector((0, 0, -.14)), 50, 2.8, h['pos'] + Vector((0, 0, -.2)), -4 + 7 * u


def cam_S07(t, u):
    h = hero_state('S07', t)
    loc = lerp((.85, -1.62, .58), (-.38, -1.38, .74), smooth(u) * .7 + u * .3)
    return loc, h['pos'] + Vector((.08, 0, -.05)), 27, 4.0, h['pos'], 3 - 5 * u


def cam_S09(t, u):
    h = hero_state('S09', t)
    loc = lerp((.78, -2.30, 1.05), (.58, -2.26, 1.09), smooth(u))
    target = h['pos'].lerp(Vector((-1.4, -2.7, 1.05)), .28)
    return loc, target, 24, 2.8, h['pos'], 2 - 3 * u


def cam_S10(t, u):
    h = hero_state('S10', t)
    lens = local_to_world(h['pos'], h['yaw'], (0, -.045, S.POD_Z))
    target = Vector((-.82, -2.60, .86)) + Vector((.03 * math.sin(t * 1.3), 0, .01 * math.sin(t * 2.0)))
    return lens, target, 20, 11.0, S.KNOBS[1], 1.2 * math.sin(t * 1.7)


def cam_S11(t, u):
    h = hero_state('S11', t)
    loc = lerp((-3.08, .52, 1.38), (-3.00, .63, 1.42), smooth(u))
    return loc, h['pos'].lerp(PLANT_AT, .45), 28, 3.2, h['pos'], 0


def cam_S12(t, u):
    h = hero_state('S12', t)
    loc = lerp((.95, -.95, 1.32), (.80, -1.02, 1.30), smooth(u))
    return loc, Vector((-.55, -2.45, 1.12)), 30, 3.2, h['pos'], 0


def cam_S13(t, u):
    h = hero_state('S13', t)
    loc = lerp((-1.35, -2.95, 1.12), (-1.30, -2.90, 1.12), smooth(u))
    return loc, pod_of(h) + Vector((0, 0, .06)), 35, 2.0, pod_of(h), 0


def cam_S14(t, u):
    h = hero_state('S14', t)
    loc = lerp((.78, -.30, .64), (.72, -.33, .62), smooth(u))
    return loc, Vector((-.12, -.62, .68)), 24, 2.8, pod_of(h), 0


def cam_S15(t, u):
    loc = lerp((.55, .92, 1.16), (1.12, .98, 1.14), smooth(u) * .6 + u * .4)
    return loc, Vector((.85, 2.62, 1.02)), 27, 5.0, Vector((.9, 2.64, 1.05)), 0


def cam_S16(t, u):
    a = dock_a_state('S16', t)
    loc = lerp((.52, 1.62, .78), (.48, 1.52, .86), u)
    return loc, a['pos'] + Vector((.05, 0, .05)), 22, 3.5, a['pos'], -6 + 4 * u


def cam_S17(t, u):
    a = dock_a_state('S17', t)
    az = math.radians(-58 + 22 * smooth(u))
    loc = a['pos'] + Vector((math.cos(az) * 1.95, math.sin(az) * 1.95, -.08 + .05 * u))
    right = Vector((-math.sin(az), math.cos(az), 0))      # camera-right; keeps FLOAT on the left third
    return loc, a['pos'] + right * .42 + Vector((0, 0, .02)), 40, 2.4, a['pos'], 0


def cam_S18(t, u):
    loc = lerp((2.70, -2.55, 1.62), (3.05, -2.85, 1.72), smooth(u))
    return loc, Vector((-.75, .75, 1.10)), 26, 5.6, Vector((-.55, .45, 1.46)), 0


CAMERAS = {sid: globals()[f'cam_{sid}'] for sid, *_ in T.SHOTS if sid not in T.GRAPHIC_SHOTS}
# Portrait (4:5) reframing: longer lens to hold subject scale, horizontal/vertical shift.
FEED = {
    'S01': dict(lens=1.25, shift_x=-.14), 'S02': dict(lens=1.15, shift_x=0), 'S03': dict(lens=1.0, shift_x=0),
    'S04': dict(lens=1.15, shift_x=.04), 'S05': dict(lens=1.1, shift_x=0), 'S06': dict(lens=1.1, shift_x=.05),
    'S07': dict(lens=1.25, shift_x=.05), 'S09': dict(lens=1.2, shift_x=-.05), 'S10': dict(lens=1.0, shift_x=0),
    'S11': dict(lens=1.2, shift_x=.04), 'S12': dict(lens=1.25, shift_x=-.08), 'S13': dict(lens=1.1, shift_x=.05),
    'S14': dict(lens=1.15, shift_x=-.05), 'S15': dict(lens=1.0, shift_x=0), 'S16': dict(lens=1.1, shift_x=0),
    'S17': dict(lens=1.05, shift_x=-.04, shift_y=-.13), 'S18': dict(lens=1.2, shift_x=-.12),
}


# ----------------------------------------------------------------------------
# Baking
# ----------------------------------------------------------------------------

def unit_objects(unit):
    return [unit['root']] + list(unit['root'].children_recursive)


def clear_animation(H, cam):
    for o in bpy.data.objects:
        o.animation_data_clear()
        o.hide_render = False
    for m in bpy.data.materials:
        if m.node_tree:
            m.node_tree.animation_data_clear()
    cam.data.animation_data_clear()


def look(cam, loc, target, roll_deg, prev):
    d = Vector(target) - Vector(loc)
    q = d.to_track_quat('-Z', 'Y') @ Quaternion((0, 0, 1), math.radians(roll_deg))
    e = q.to_euler('XYZ', prev) if prev is not None else q.to_euler('XYZ')
    cam.location = loc
    cam.rotation_euler = e
    return e


def pose_unit(unit, st, f, blade_phase):
    r = unit['root']
    r.location = st['pos']
    r.rotation_euler = (math.radians(st['pitch']), math.radians(st['roll']), math.radians(st['yaw']))
    r.keyframe_insert('location', frame=f)
    r.keyframe_insert('rotation_euler', frame=f)
    inp = unit['led'].node_tree.nodes['Emission'].inputs['Strength']
    inp.default_value = st['led']
    inp.keyframe_insert('default_value', frame=f)
    for o in unit['blur']:
        o.hide_render = not st['spinning']
        o.keyframe_insert('hide_render', frame=f)
    for k, o in enumerate(unit['blades']):
        o.hide_render = st['spinning']
        o.keyframe_insert('hide_render', frame=f)
        o.rotation_mode = 'QUATERNION'
        base = Vector((0, 0, 1)).rotation_difference(Vector(list(S.FANS.values())[k][1]))
        o.rotation_quaternion = base @ Quaternion((0, 0, 1), blade_phase + k * 1.1)
        o.keyframe_insert('rotation_quaternion', frame=f)


def bake(H, cam, sid, fmt='wide'):
    """Insert per-frame keys for shot `sid` (plus one frame of handles each side)."""
    global SPEECH
    SPEECH = Speech()
    _, _, a, b, _, _ = T.shot(sid)
    clear_animation(H, cam)
    H['kitchen']['flame'].node_tree.nodes['Emission'].inputs['Strength'].default_value = 9.0 if sid in FLAME_SHOTS else 0.0
    hero, da, db = H['units']
    states = {'hero': hero_state, 'dock_a': dock_a_state, 'dock_b': dock_b_state}
    cfun = CAMERAS[sid]
    feed = FEED[sid] if fmt == 'feed' else dict(lens=1.0, shift_x=0)
    shift_y = feed.get('shift_y', 0.0)
    prev = None
    spin_phase = 0.0
    for f in range(a - 1, b + 1):
        t = f / T.FPS
        u = clamp((f - a) / max(1, b - a - 1))
        for unit in H['units']:
            st = states[unit['tag']](sid, t)
            phase = 0.0
            if unit['tag'] == 'hero' and sid == 'S05':
                # Visible spin-up: blades accelerate under motion blur, then read as a disc.
                w = 140 * ramp(t, 7.0, 7.38)
                spin_phase += math.radians(w)
                phase = spin_phase
                st['spinning'] = t >= 7.42
            pose_unit(unit, st, f, phase)
        for inp, lvl in zip([p.node_tree.nodes['Emission'].inputs['Strength'] for p in H['pads']], pad_levels(t)):
            inp.default_value = lvl
            inp.keyframe_insert('default_value', frame=f)
        loc, target, lens, fstop, focus, roll = cfun(t, u)
        prev = look(cam, loc, target, roll, prev)
        cam.keyframe_insert('location', frame=f)
        cam.keyframe_insert('rotation_euler', frame=f)
        cam.data.lens = lens * feed['lens']
        cam.data.shift_x = feed['shift_x']
        cam.data.shift_y = shift_y
        cam.data.dof.focus_distance = max(.05, (Vector(focus) - Vector(loc)).length)
        cam.data.dof.aperture_fstop = fstop
        for path in ('lens', 'shift_x', 'shift_y'):
            cam.data.keyframe_insert(path, frame=f)
        cam.data.dof.keyframe_insert('focus_distance', frame=f)
        cam.data.dof.keyframe_insert('aperture_fstop', frame=f)
    # Point-of-view shots are seen from inside the hero's pod.
    if sid in POV_SHOTS:
        for o in unit_objects(hero)[1:]:
            o.animation_data_clear()
            o.hide_render = True
    for obj in [o for o in bpy.data.objects] + [cam.data] + [m.node_tree for m in bpy.data.materials if m.node_tree]:
        ad = getattr(obj, 'animation_data', None)
        if ad and ad.action:
            for fc in ad.action.fcurves:
                for kp in fc.keyframe_points:
                    if kp.interpolation != 'CONSTANT' and 'hide' not in fc.data_path:
                        kp.interpolation = 'LINEAR'
    return a, b
