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
# Performances (absolute time t, seconds)
# ----------------------------------------------------------------------------

P0 = Vector((-0.55, 0.40, 1.47))      # opening hover, in the sun
P1 = Vector((0.35, -0.10, 1.30))      # end of the glide
SOFA_HOVER = Vector((1.30, 0.38, 1.12))     # above the far cushion, facing the keys
WINDOW_HOVER = Vector((-2.40, 0.55, 1.50))


def hero_state(t):
    """Position, yaw, rotor state and LED level of the unit that finds the keys."""
    sp = SPEECH
    if t < 6.3:
        pos = P0.copy()
        yaw = -20 + 66 * ramp(t, 1.40, 2.95)
    elif t < 11.0:
        u = ramp(t, 6.3, 11.0)
        pos = lerp(P0, P1, u) + Vector((0, 0, .04 * math.sin(math.pi * u)))
        yaw = 46 + 19 * ramp(t, 6.3, 8.5)
    elif t < 13.0:
        u = (t - 11.0) / 2.0
        pos = lerp(P1, Vector((0.80, 0.06, 1.13)), smooth(u) * .85 + u * .15)
        yaw = 65 - 14 * smooth(u)
    elif t < 18.0:
        pos = SOFA_HOVER - Vector((0, 0, .04 * ramp(t, 13.0, 15.5)))
        yaw = 3 - 3 * ramp(t, 13.2, 14.6)
    else:
        pad = Vector((S.DOCK_PADS[1][0], S.DOCK_PADS[1][1], S.DOCKED_Z))
        start = Vector((pad.x - .05, 2.18, 1.31))
        u = ramp(t, 18.0, 19.95)
        pos = lerp(start, pad, u)
        yaw = 8 * (1 - u)
    docked = t >= 19.95
    dz, pitch, roll = bob(t, .3)
    damp = 1 - ramp(t, 19.4, 19.95)
    pos = pos + Vector((0, 0, dz * damp))
    spinning = 5.0 <= t < 19.95
    # Indicator: idle, heard you, speaking, charging.
    if docked:
        led = breathe(t, 1.2, 3.4, 2.6)
    elif t < 1.55:
        led = .5
    else:
        led = .5 + 4.5 * ramp(t, 1.55, 2.25) + .6 * math.sin(2 * math.pi * t / 1.3) * ramp(t, 1.55, 2.25)
        led += 7.0 * (sp.env('look', t) + sp.env('found', t))
    return dict(pos=pos, yaw=yaw, pitch=pitch * damp, roll=roll * damp, spinning=spinning, led=led)


def dock_a_state(t):
    """Unit on pad 0 that takes over: charging, then lifts off and patrols."""
    pad = Vector((S.DOCK_PADS[0][0], S.DOCK_PADS[0][1], S.DOCKED_Z))
    if t < 24.0:
        lift = ramp(t, 20.55, 24.0)
        pos = pad + Vector((.0, -.42 * lift ** 1.4, .62 * lift))
        yaw = 0 - 12 * lift
        dz, pitch, roll = bob(t, 1.7)
        k = ramp(t, 20.55, 21.4)
        pos += Vector((0, 0, dz * k))
        pitch, roll = pitch * k, roll * k
    elif t < 27.0:
        pos = WINDOW_HOVER.copy()
        yaw = 92 - 10 * ramp(t, 24.0, 27.0)
        dz, pitch, roll = bob(t, 1.7)
        pos += Vector((0, 0, dz))
    else:
        pos = Vector((-0.55, 0.45, 1.46))
        yaw = 38
        dz, pitch, roll = bob(t, 1.7)
        pos += Vector((0, 0, dz))
    spinning = t >= 20.35
    led = breathe(t, 1.2, 3.4, 2.6, 1.0) if t < 20.35 else 1.2 + 3.8 * ramp(t, 20.35, 20.9)
    return dict(pos=pos, yaw=yaw, pitch=pitch, roll=roll, spinning=spinning, led=led)


def dock_b_state(t):
    pos = Vector((S.DOCK_PADS[2][0], S.DOCK_PADS[2][1], S.DOCKED_Z))
    return dict(pos=pos, yaw=-4, pitch=0, roll=0, spinning=False, led=breathe(t, 1.2, 3.4, 2.6, 2.1))


def pad_levels(t):
    return [breathe(t, 1.0, 2.6, 2.6, 1.0) * (1 - ramp(t, 20.4, 20.9)) + .15,
            .15 + 2.2 * ramp(t, 19.95, 20.5) * breathe(t, .55, 1.0, 2.6),
            breathe(t, 1.0, 2.6, 2.6, 2.1)]


# ----------------------------------------------------------------------------
# Cameras: each returns (location, target, lens_mm, f_stop, focus_point, roll_deg)
# ----------------------------------------------------------------------------

def cam_S01(t, u):
    loc = lerp((2.25, -2.25, 1.34), (2.00, -1.98, 1.31), smooth(u) * .8 + u * .2)
    target = P0 + Vector((.62, .05, -.10))
    return loc, target, 34, 4.0, P0, 0


def cam_S02(t, u):
    h = hero_state(t)
    f = heading(h['yaw'])
    side = Vector((-f.y, f.x, 0))
    pod = local_to_world(h['pos'], h['yaw'], (0, 0, S.POD_Z))
    d = .50 - .09 * smooth(u)
    loc = pod + f * d + side * .07 + Vector((0, 0, -.012))
    target = pod + Vector((0, 0, .008)) + side * .012
    return loc, target, 85, 2.0, local_to_world(h['pos'], h['yaw'], (0, -.04, S.POD_Z)), -2 + 3 * u


def cam_S03(t, u):
    h = hero_state(t)
    fan = local_to_world(h['pos'], h['yaw'], S.FANS['right'][0])
    loc = local_to_world(h['pos'], h['yaw'], Vector(S.FANS['right'][0]) + Vector((.16 - .03 * u, -.17 + .02 * u, -.06 + .02 * u)))
    target = local_to_world(h['pos'], h['yaw'], Vector(S.FANS['right'][0]) + Vector((-.045, 0, .025)))
    return loc, target, 50, 2.8, fan, 4 - 6 * u


def cam_S04(t, u):
    # Low three-quarter profile as FLOAT sets off: envelope edge, pod and fans.
    h = hero_state(t)
    a = math.radians(-8 * smooth(u))
    off = Vector((.95 * math.cos(a) + .55 * math.sin(a), -.55 * math.cos(a) + .95 * math.sin(a), -.42 + .06 * u))
    loc = local_to_world(h['pos'], h['yaw'], off)
    target = h['pos'] + Vector((0, 0, -.14))
    return loc, target, 50, 2.8, h['pos'] + Vector((0, 0, -.2)), -4 + 7 * u


def cam_S05(t, u):
    h = hero_state(t)
    loc = lerp((.85, -1.62, .58), (-.38, -1.38, .74), smooth(u) * .7 + u * .3)
    target = h['pos'] + Vector((.08, 0, -.05))
    return loc, target, 27, 4.0, h['pos'], 3 - 5 * u


def cam_S06(t, u):
    h = hero_state(t)
    lens = local_to_world(h['pos'], h['yaw'], (0, -.045, S.POD_Z))
    target = S.KEYS_AT + Vector((-.06 + .05 * smooth(u), .03, .05))
    return lens, target, 18, 11.0, S.KEYS_AT, 1.5 * math.sin(t * 2.1)


def cam_S07(t, u):
    h = hero_state(t)
    loc = lerp((1.30, -.82, .530), (1.30, -.76, .528), smooth(u))
    target = Vector((1.31, .10, .53))
    # Hold on FLOAT, then rack to the keys on "Found them".
    rack = ramp(t, 13.55, 14.10)
    focus = lerp(local_to_world(h['pos'], h['yaw'], (0, -.04, S.POD_Z)), S.KEYS_AT + Vector((0, 0, .01)), rack)
    return loc, target, 22, 1.8, focus, 0


def cam_S08(t, u):
    h = hero_state(t)
    loc = lerp((.45, -1.05, 1.18), (.62, -.92, 1.16), smooth(u))
    target = h['pos'] + Vector((-.05, -.45, -.10))
    return loc, target, 35, 3.2, h['pos'], 0


def cam_S09(t, u):
    loc = lerp((.55, .92, 1.16), (1.12, .98, 1.14), smooth(u) * .6 + u * .4)
    target = Vector((.85, 2.62, 1.02))
    return loc, target, 27, 5.0, Vector((.9, 2.64, 1.05)), 0


def cam_S10(t, u):
    a = dock_a_state(t)
    loc = lerp((.52, 1.62, .78), (.48, 1.52, .86), u)
    target = a['pos'] + Vector((.05, 0, .05))
    return loc, target, 22, 3.5, a['pos'], -6 + 4 * u


def cam_S11(t, u):
    a = dock_a_state(t)
    az = math.radians(-58 + 22 * smooth(u))
    r = 1.95
    loc = a['pos'] + Vector((math.cos(az) * r, math.sin(az) * r, -.08 + .05 * u))
    right = Vector((-math.sin(az), math.cos(az), 0))      # camera-right; keeps FLOAT on the left third
    target = a['pos'] + right * .42 + Vector((0, 0, .02))
    return loc, target, 40, 2.4, a['pos'], 0


def cam_S12(t, u):
    loc = lerp((2.70, -2.55, 1.62), (3.05, -2.85, 1.72), smooth(u))
    target = Vector((-.75, .75, 1.10))
    return loc, target, 26, 5.6, Vector((-.55, .45, 1.46)), 0


CAMERAS = {f'S{i:02d}': globals()[f'cam_S{i:02d}'] for i in range(1, 13)}
# Portrait (4:5) reframing: longer lens to hold subject scale, horizontal shift.
FEED = {
    'S01': dict(lens=1.25, shift_x=-.14), 'S02': dict(lens=1.15, shift_x=.0), 'S03': dict(lens=1.1, shift_x=0),
    'S04': dict(lens=1.1, shift_x=.05), 'S05': dict(lens=1.25, shift_x=.05), 'S06': dict(lens=1.0, shift_x=0),
    'S07': dict(lens=1.15, shift_x=.04), 'S08': dict(lens=1.35, shift_x=-.12), 'S09': dict(lens=1.0, shift_x=0),
    'S10': dict(lens=1.1, shift_x=0), 'S11': dict(lens=1.05, shift_x=-.04, shift_y=-.13), 'S12': dict(lens=1.2, shift_x=-.12),
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
    _, _, a, b, _ = next(s for s in T.SHOTS if s[0] == sid)
    clear_animation(H, cam)
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
            st = states[unit['tag']](t)
            phase = 0.0
            if unit['tag'] == 'hero' and sid == 'S03':
                # Visible spin-up: blades accelerate under motion blur, then read as a disc.
                w = 140 * ramp(t, 5.0, 5.40)
                spin_phase += math.radians(w)
                phase = spin_phase
                st['spinning'] = t >= 5.42
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
    # The POV shot is seen from inside the hero's pod.
    if sid == 'S06':
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
