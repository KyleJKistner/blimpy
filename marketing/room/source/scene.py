"""FLOAT / Room: set, product model and render configuration (Blender 4.5 LTS).

Everything is built procedurally from this file plus the PNGs written by
textures.py. The FLOAT model follows the concept lock used by earlier films:
~62 cm twelve-gore metallized envelope, small camera/audio pod, four guarded
fans (left/right forward, rear lateral, bottom vertical), amber indicator and a
three-bay shared dock. It is an illustration, not manufacturing CAD.
"""
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]
TEX = ROOT / 'assets' / 'textures'

R_ENV = 0.31                      # envelope radius, m
POD_Z = -0.352                    # pod centre below envelope centre
FANS = {                          # centre, thrust axis (local frame; -Y is forward)
    'left': ((-0.20, 0.0, -0.335), (0, 1, 0)),
    'right': ((0.20, 0.0, -0.335), (0, 1, 0)),
    'rear': ((0.0, 0.20, -0.335), (1, 0, 0)),
    'bottom': ((0.0, 0.0, -0.432), (0, 0, 1)),
}
DOCK_PADS = [(0.15, 2.64), (0.90, 2.64), (1.65, 2.64)]
DOCK_TOP = 0.62
DOCKED_Z = DOCK_TOP + 0.018 + 0.432 + 0.020   # bottom duct resting on a pad
KEYS_AT = Vector((1.30, -0.35, 0.446))        # in the gap between the sofa seat cushions


# ----------------------------------------------------------------------------
# Materials
# ----------------------------------------------------------------------------

def _image(name, non_color=False):
    img = bpy.data.images.get(name + '.png') or bpy.data.images.load(str(TEX / f'{name}.png'))
    if non_color:
        img.colorspace_settings.name = 'Non-Color'
    return img


def material(name, color=(.5, .5, .5), rough=.5, metal=0., **kw):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    for key, val in kw.items():
        sock = b.inputs[key]
        sock.default_value = (*val, 1) if isinstance(val, tuple) and len(val) == 3 else val
    return m


def textured(name, color_tex, scale, rough=.5, rough_tex=None, bump_tex=None, bump=.2,
             tint=(1, 1, 1), sat=1.0, box=True, **kw):
    """Box-projected image material in object space, `scale` metres per tile."""
    m = material(name, rough=rough, **kw)
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    coord = nt.nodes.new('ShaderNodeTexCoord')
    mapping = nt.nodes.new('ShaderNodeMapping')
    mapping.inputs['Scale'].default_value = (1 / scale, 1 / scale, 1 / scale)
    nt.links.new(coord.outputs['Object'], mapping.inputs['Vector'])

    def tex(img_name, non_color):
        t = nt.nodes.new('ShaderNodeTexImage')
        t.image = _image(img_name, non_color)
        if box:
            t.projection = 'BOX'
            t.projection_blend = .25
        nt.links.new(mapping.outputs['Vector'], t.inputs['Vector'])
        return t

    c = tex(color_tex, False)
    hsv = nt.nodes.new('ShaderNodeHueSaturation')
    hsv.inputs['Saturation'].default_value = sat
    nt.links.new(c.outputs['Color'], hsv.inputs['Color'])
    mul = nt.nodes.new('ShaderNodeMix')
    mul.data_type = 'RGBA'
    mul.blend_type = 'MULTIPLY'
    mul.inputs['Factor'].default_value = 1
    mul.inputs['B'].default_value = (*tint, 1)
    nt.links.new(hsv.outputs['Color'], mul.inputs['A'])
    nt.links.new(mul.outputs['Result'], b.inputs['Base Color'])
    if rough_tex:
        nt.links.new(tex(rough_tex, True).outputs['Color'], b.inputs['Roughness'])
    if bump_tex:
        bn = nt.nodes.new('ShaderNodeBump')
        bn.inputs['Strength'].default_value = bump
        bn.inputs['Distance'].default_value = .002
        nt.links.new(tex(bump_tex, True).outputs['Color'], bn.inputs['Height'])
        nt.links.new(bn.outputs['Normal'], b.inputs['Normal'])
    return m


def emissive(name, color, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes['Principled BSDF'])
    e = nt.nodes.new('ShaderNodeEmission')
    e.inputs['Color'].default_value = (*color, 1)
    e.inputs['Strength'].default_value = strength
    nt.links.new(e.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
    return m


def foil_material(name):
    """Metallized film: near-mirror metal, faint micro-crinkle, slight warm cast."""
    m = material(name, (.93, .925, .91), .055, 1.0)
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    n = nt.nodes.new('ShaderNodeTexNoise')
    n.inputs['Scale'].default_value = 34
    n.inputs['Detail'].default_value = 3
    n.inputs['Roughness'].default_value = .45
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = .035
    bump.inputs['Distance'].default_value = .0015
    nt.links.new(n.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def prop_blur_material(name):
    """Rotor at speed under a 180-degree shutter: a faint, hub-weighted disc."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    out = nt.nodes['Material Output']
    nt.nodes.remove(nt.nodes['Principled BSDF'])
    dark = nt.nodes.new('ShaderNodeBsdfPrincipled')
    dark.inputs['Base Color'].default_value = (.02, .022, .025, 1)
    dark.inputs['Roughness'].default_value = .4
    clear = nt.nodes.new('ShaderNodeBsdfTransparent')
    coord = nt.nodes.new('ShaderNodeTexCoord')
    grad = nt.nodes.new('ShaderNodeTexGradient')
    grad.gradient_type = 'SPHERICAL'
    mapping = nt.nodes.new('ShaderNodeMapping')
    mapping.inputs['Scale'].default_value = (20, 20, 20)       # disc radius 0.05 m -> 1
    nt.links.new(coord.outputs['Object'], mapping.inputs['Vector'])
    nt.links.new(mapping.outputs['Vector'], grad.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = .0
    ramp.color_ramp.elements[0].color = (.0, .0, .0, 1)
    ramp.color_ramp.elements[1].position = .9
    ramp.color_ramp.elements[1].color = (.42, .42, .42, 1)
    nt.links.new(grad.outputs['Fac'], ramp.inputs['Fac'])
    mix = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(ramp.outputs['Color'], mix.inputs['Fac'])
    nt.links.new(clear.outputs[0], mix.inputs[1])
    nt.links.new(dark.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m


def window_glass_material():
    """Faint reflections for camera rays; transparent for light and shadows."""
    m = bpy.data.materials.new('window_glass')
    m.use_nodes = True
    nt = m.node_tree
    out = nt.nodes['Material Output']
    nt.nodes.remove(nt.nodes['Principled BSDF'])
    lp = nt.nodes.new('ShaderNodeLightPath')
    fres = nt.nodes.new('ShaderNodeFresnel')
    fres.inputs['IOR'].default_value = 1.5
    gl = nt.nodes.new('ShaderNodeBsdfGlossy')
    gl.inputs['Roughness'].default_value = .02
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    m1 = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(fres.outputs[0], m1.inputs['Fac'])
    nt.links.new(tr.outputs[0], m1.inputs[1])
    nt.links.new(gl.outputs[0], m1.inputs[2])
    camera_only = nt.nodes.new('ShaderNodeMath')
    camera_only.operation = 'SUBTRACT'
    camera_only.inputs[0].default_value = 1
    nt.links.new(lp.outputs['Is Camera Ray'], camera_only.inputs[1])
    m2 = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(camera_only.outputs[0], m2.inputs['Fac'])
    nt.links.new(m1.outputs[0], m2.inputs[1])
    nt.links.new(tr.outputs[0], m2.inputs[2])
    nt.links.new(m2.outputs[0], out.inputs['Surface'])
    return m


def build_materials():
    M = {}
    M['oak'] = textured('oak', 'oak_color', 3.6, rough_tex='oak_rough', bump_tex='oak_bump', bump=.25,
                        sat=.72, tint=(1.0, .97, .93), box=False)
    M['plaster'] = textured('plaster', 'plaster_color', 2.0, rough=.92, bump_tex='plaster_bump', bump=.12, tint=(1.12, 1.14, 1.19))
    M['ceiling'] = material('ceiling', (.90, .89, .86), .95)
    M['walnut'] = textured('walnut', 'walnut_color', 1.4, rough_tex='walnut_rough', sat=.9,
                           **{'Coat Weight': .25, 'Coat Roughness': .18})
    M['boucle'] = textured('boucle', 'boucle_color', .12, rough=.95, bump_tex='boucle_bump', bump=1.0,
                           **{'Sheen Weight': .5, 'Sheen Roughness': .4})
    M['rug'] = textured('rug', 'rug_color', 2.4, rough=.95, bump_tex='rug_bump', bump=.6, box=False)
    M['knit'] = textured('knit', 'knit_color', .25, rough=.9, bump_tex='knit_bump', bump=.7,
                         **{'Sheen Weight': .4})
    M['steel'] = material('black_steel', (.018, .018, .02), .38, .85)
    M['trim'] = material('trim', (.83, .81, .77), .6)
    M['ceramic'] = material('ceramic', (.86, .83, .76), .32, **{'Coat Weight': .4, 'Coat Roughness': .1})
    M['clay'] = material('clay', (.42, .26, .18), .8)
    M['stone'] = material('travertine', (.74, .68, .58), .55)
    M['brass'] = material('brass', (.80, .58, .32), .22, 1.0)
    M['leather'] = material('leather', (.42, .20, .09), .45, **{'Coat Weight': .2, 'Coat Roughness': .3})
    M['paper'] = material('paper', (.86, .84, .80), .85)
    M['leaf'] = material('olive_leaf', (.21, .25, .14), .55, **{'Subsurface Weight': .0})
    M['bark'] = material('bark', (.20, .16, .12), .9)
    M['linen'] = material('linen_shade', (.92, .88, .80), .9, **{'Transmission Weight': .0})
    M['books'] = [material(f'book_{i}', c, .7) for i, c in enumerate(
        [(.55, .16, .09), (.12, .18, .22), (.80, .74, .62), (.25, .30, .22), (.62, .46, .26), (.10, .10, .11)])]
    M['glass'] = window_glass_material()
    art = textured('art', 'artwork', 1.0, rough=.8, box=False)
    M['art'] = art
    # FLOAT palette.
    M['graphite'] = material('graphite', (.028, .030, .033), .34, .15, **{'Coat Weight': .35, 'Coat Roughness': .22})
    M['graphite_matte'] = material('graphite_matte', (.035, .037, .040), .55, .1)
    M['carbon'] = material('carbon', (.02, .021, .023), .3, .4)
    M['seam'] = material('seam', (.86, .855, .84), .22, 1.0)
    M['valve'] = material('valve', (.82, .82, .80), .4)
    M['lens_glass'] = material('lens_glass', (.0, .0, .0), .02, **{'Coat Weight': 1.0, 'Coat Roughness': .0})
    M['lens_inner'] = material('lens_inner', (.03, .06, .09), .08, .9)
    M['grille'] = material('grille', (.05, .052, .056), .45, .6)
    M['contact'] = material('contact', (.85, .62, .35), .25, 1.0)
    M['prop'] = material('prop', (.03, .03, .033), .35)
    M['prop_blur'] = prop_blur_material('prop_blur')
    M['pad'] = material('pad', (.03, .032, .036), .5)
    M['outside'] = emissive('outside_view', (1, 1, 1), 1.0)
    # Kitchen and evening props.
    M['cabinet'] = material('cabinet', (.105, .19, .16), .42, **{'Coat Weight': .25, 'Coat Roughness': .25})
    M['counter'] = material('counter', (.86, .85, .82), .22, **{'Coat Weight': .3, 'Coat Roughness': .1})
    M['tile'] = textured('tile', 'zellige_color', .8, rough=.12, bump_tex='zellige_bump', bump=.35, box=False,
                         **{'Coat Weight': .6, 'Coat Roughness': .05})
    M['stainless'] = material('stainless', (.72, .71, .69), .28, 1.0)
    M['iron'] = material('cast_iron', (.035, .034, .033), .55, .6)
    M['oil'] = material('oil', (.30, .19, .05), .05, **{'Coat Weight': .8})
    M['garlic'] = material('garlic', (.93, .89, .82), .55, **{'Subsurface Weight': .2})
    M['board'] = textured('board', 'walnut_color', 1.0, rough=.5, tint=(1.9, 1.75, 1.55))
    M['knob_mark'] = material('knob_mark', (.9, .9, .88), .4)
    M['drawing'] = textured('drawing', 'drawing', 1.0, rough=.85, box=False)
    M['recipe'] = textured('recipe', 'recipe', 1.0, rough=.85, box=False)
    M['crayons'] = [material(f'crayon_{i}', c, .5) for i, c in enumerate(
        [(.75, .12, .10), (.12, .25, .65), (.85, .65, .08), (.15, .45, .2)])]
    M['flame'] = emissive('flame', (.25, .48, 1.0), 0.0)
    M['strip'] = emissive('led_strip', (1.0, .78, .55), 0.0)
    M['shade_glow'] = emissive('shade_glow', (1.0, .80, .58), 0.0)
    return M


# ----------------------------------------------------------------------------
# Geometry helpers
# ----------------------------------------------------------------------------

def link(obj, coll=None):
    (coll or bpy.context.scene.collection).objects.link(obj)
    return obj


def mesh_object(name, bm, mat, coll=None, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        me.shade_smooth()
    me.materials.append(mat)
    return link(bpy.data.objects.new(name, me), coll)


def box(name, size, loc, mat, bevel=0.0, seg=3, rot=(0, 0, 0), coll=None, subsurf=0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    o = mesh_object(name, bm, mat, coll, smooth=bool(bevel or subsurf))
    o.location = loc
    o.rotation_euler = rot
    if bevel:
        mod = o.modifiers.new('bevel', 'BEVEL')
        mod.width = bevel
        mod.segments = seg
        mod.limit_method = 'NONE'
        mod.harden_normals = False
    if subsurf:
        s = o.modifiers.new('sub', 'SUBSURF')
        s.levels = subsurf
        s.render_levels = subsurf
    return o


def cylinder(name, r, depth, loc, mat, seg=48, rot=(0, 0, 0), coll=None, bevel=0.0, cap=True):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=cap, segments=seg, radius1=r, radius2=r, depth=depth)
    o = mesh_object(name, bm, mat, coll)
    o.location = loc
    o.rotation_euler = rot
    if bevel:
        mod = o.modifiers.new('bevel', 'BEVEL')
        mod.width = bevel
        mod.segments = 3
        mod.limit_method = 'ANGLE'
    return o


def sphere(name, r, loc, mat, seg=48, rings=24, scale=(1, 1, 1), coll=None):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r)
    bmesh.ops.scale(bm, vec=Vector(scale), verts=bm.verts)
    o = mesh_object(name, bm, mat, coll)
    o.location = loc
    return o


def tube(name, points, r, mat, coll=None, closed=False, res=6):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = r
    cu.bevel_resolution = res // 2
    cu.use_fill_caps = True
    sp = cu.splines.new('POLY')
    sp.points.add(len(points) - 1)
    for p, q in zip(sp.points, points):
        p.co = (*q, 1)
    sp.use_cyclic_u = closed
    o = link(bpy.data.objects.new(name, cu), coll)
    cu.materials.append(mat)
    return o


def ring_points(c, radius, axis, n=96):
    a = Vector(axis).normalized()
    ref = Vector((0, 0, 1)) if abs(a.z) < .8 else Vector((1, 0, 0))
    u = a.cross(ref).normalized()
    v = a.cross(u)
    return [tuple(Vector(c) + radius * (math.cos(t) * u + math.sin(t) * v))
            for t in [2 * math.pi * i / n for i in range(n)]]


def axis_rotation(axis):
    """Euler that maps local +Z onto `axis`."""
    return Vector((0, 0, 1)).rotation_difference(Vector(axis).normalized()).to_euler()


def parent(child, par):
    child.parent = par
    return child


# ----------------------------------------------------------------------------
# FLOAT
# ----------------------------------------------------------------------------

def envelope_bmesh(gores=12, per_gore=12, rings=96, pinch=.0075):
    """Twelve pillowed gores: radius drawn in slightly at each welded seam."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=gores * per_gore, v_segments=rings, radius=R_ENV)
    for v in bm.verts:
        p = v.co.normalized()
        colat = math.acos(max(-1, min(1, p.z)))
        lon = math.atan2(p.y, p.x) % (2 * math.pi)
        u = (lon / (2 * math.pi / gores)) % 1.0
        pillow = math.sin(math.pi * u) ** .45
        squeeze = 1 - pinch * (1 - pillow) * math.sin(colat) ** 1.5
        v.co = p * R_ENV * squeeze
    return bm


def make_float(tag, M, coll):
    """Return dict of handles for one FLOAT unit; root is an Empty at envelope centre."""
    root = bpy.data.objects.new(f'FLOAT_{tag}', None)
    link(root, coll)
    root.empty_display_size = .35
    led = emissive(f'led_{tag}', (1.0, .52, .16), 0.0)
    env = mesh_object(f'envelope_{tag}', envelope_bmesh(), M['foil'], coll)
    parent(env, root)
    sub = env.modifiers.new('sub', 'SUBSURF')
    sub.levels = 0
    sub.render_levels = 1
    # Welded seams follow the pinched meridians.
    for j in range(12):
        lon = j * 2 * math.pi / 12
        pts = []
        for i in range(1, 140):
            colat = math.pi * i / 140
            rr = R_ENV * (1 - .0075 * math.sin(colat) ** 1.5) + .0004
            pts.append((rr * math.sin(colat) * math.cos(lon), rr * math.sin(colat) * math.sin(lon), rr * math.cos(colat)))
        parent(tube(f'seam_{tag}_{j}', pts, .0011, M['seam'], coll, res=4), root)
    parent(cylinder(f'valve_{tag}', .028, .004, (0, 0, R_ENV - .0005), M['valve'], 48, coll=coll, bevel=.0015), root)
    parent(cylinder(f'valve_nub_{tag}', .009, .008, (0, 0, R_ENV + .004), M['valve'], 32, coll=coll, bevel=.002), root)
    parent(cylinder(f'load_patch_{tag}', .05, .004, (0, 0, -R_ENV + .0008), M['graphite_matte'], 48, coll=coll, bevel=.0015), root)
    parent(cylinder(f'neck_{tag}', .016, .03, (0, 0, -.322), M['graphite'], 32, coll=coll), root)
    # Camera/audio pod: a soft pill, lens forward (-Y).
    pod = box(f'pod_{tag}', (.122, .074, .054), (0, 0, POD_Z), M['graphite'], bevel=.022, seg=8, coll=coll)
    parent(pod, root)
    fy = -.037
    parent(cylinder(f'lens_bezel_{tag}', .0205, .006, (0, fy - .001, POD_Z), M['graphite_matte'], 64,
                    rot=(math.pi / 2, 0, 0), coll=coll, bevel=.001), root)
    parent(sphere(f'lens_glass_{tag}', .0158, (0, fy - .0035, POD_Z), M['lens_glass'], 64, 32, (1, .42, 1), coll), root)
    parent(cylinder(f'lens_inner_{tag}', .0085, .002, (0, fy - .0072, POD_Z), M['lens_inner'], 48,
                    rot=(math.pi / 2, 0, 0), coll=coll), root)
    ring = tube(f'led_ring_{tag}', ring_points((0, fy - .0043, POD_Z), .0186, (0, 1, 0), 96), .00075, led, coll, closed=True)
    parent(ring, root)
    # Microphone pinholes and a speaker slot grille.
    for i, x in enumerate([-.032, .032]):
        parent(cylinder(f'mic_{tag}_{i}', .0012, .002, (x, -.012, POD_Z + .027), M['carbon'], 16, coll=coll), root)
    for k in range(7):
        parent(box(f'spk_{tag}_{k}', (.026, .0016, .0012), (-.0 , .012 + k * .0032 - .01, POD_Z - .0272), M['carbon'], coll=coll), root)
    # Fans: ducted guards with fine wire grilles; rotor disc or stopped blades.
    blur, blades = [], []
    for key, (c, axis) in FANS.items():
        c = Vector(c)
        a = Vector(axis)
        rot = axis_rotation(axis)
        duct = cylinder(f'duct_{tag}_{key}', .057, .040, c, M['graphite'], 72, rot=rot, coll=coll, cap=False)
        so = duct.modifiers.new('solid', 'SOLIDIFY')
        so.thickness = .0042
        so.offset = 1
        bv = duct.modifiers.new('bevel', 'BEVEL')
        bv.width = .0009
        bv.segments = 2
        parent(duct, root)
        for side in (-1, 1):
            face = c + a * side * .0198
            for rr in (.012, .019, .026, .033, .040, .047, .054):
                parent(tube(f'grille_{tag}_{key}_{side}_{rr}', ring_points(face, rr, axis, 64), .00032, M['grille'], coll, closed=True, res=2), root)
            ref = Vector((0, 0, 1)) if abs(a.z) < .8 else Vector((1, 0, 0))
            u = a.cross(ref).normalized()
            v = a.cross(u)
            for s in range(6):
                t = s * math.pi / 3 + .26
                d = math.cos(t) * u + math.sin(t) * v
                parent(tube(f'spoke_{tag}_{key}_{side}_{s}', [tuple(face + d * .006), tuple(face + d * .056)], .00036, M['grille'], coll, res=2), root)
        parent(cylinder(f'hub_{tag}_{key}', .0055, .012, c, M['carbon'], 24, rot=rot, coll=coll), root)
        disc = cylinder(f'rotor_blur_{tag}_{key}', .05, .0006, c, M['prop_blur'], 64, rot=rot, coll=coll)
        disc.visible_shadow = False
        parent(disc, root)
        blur.append(disc)
        bl = bmesh.new()
        prof = [(.006, .004), (.02, .0085), (.035, .0075), (.048, .0045), (.0495, .0)]
        verts_l = [bl.verts.new((x, w, 0)) for x, w in prof]
        verts_r = [bl.verts.new((x, -w * .55, 0)) for x, w in prof]
        for i in range(len(prof) - 1):
            bl.faces.new((verts_l[i], verts_l[i + 1], verts_r[i + 1], verts_r[i]))
        bmesh.ops.mirror(bl, geom=bl.verts[:] + bl.faces[:], axis='X', merge_dist=0)
        blade = mesh_object(f'blades_{tag}_{key}', bl, M['prop'], coll)
        blade.location = c
        blade.rotation_euler = rot
        sol = blade.modifiers.new('solid', 'SOLIDIFY')
        sol.thickness = .0012
        parent(blade, root)
        blades.append(blade)
        # Arm from pod to duct.
        start = Vector((0, 0, POD_Z)) + (c - Vector((0, 0, POD_Z))).normalized() * .03
        end = c - (c - Vector((0, 0, POD_Z))).normalized() * .057
        parent(tube(f'arm_{tag}_{key}', [tuple(start), tuple(end)], .0032, M['carbon'], coll, res=6), root)
    return dict(root=root, led=led, blur=blur, blades=blades, tag=tag)


def set_rotors(unit, spinning, frame=None):
    for o in unit['blur']:
        o.hide_render = not spinning
        if frame is not None:
            o.keyframe_insert('hide_render', frame=frame)
    for o in unit['blades']:
        o.hide_render = spinning
        if frame is not None:
            o.keyframe_insert('hide_render', frame=frame)


# ----------------------------------------------------------------------------
# Set
# ----------------------------------------------------------------------------

X0, X1, Y0, Y1, ZC = -3.6, 3.6, -3.2, 3.0, 2.9
WIN = dict(y0=-2.3, y1=2.3, z0=.12, z1=2.62)


def build_room(M, coll):
    t = .12
    floor = box('floor', (X1 - X0, Y1 - Y0, .04), ((X0 + X1) / 2, (Y0 + Y1) / 2, -.02), M['oak'], coll=coll)
    box('ceiling', (X1 - X0 + .3, Y1 - Y0 + .3, t), ((X0 + X1) / 2, (Y0 + Y1) / 2, ZC + t / 2), M['ceiling'], coll=coll)
    box('wall_back', (X1 - X0 + .3, t, ZC), ((X0 + X1) / 2, Y1 + t / 2, ZC / 2), M['plaster'], coll=coll)
    box('wall_front', (X1 - X0 + .3, t, ZC), ((X0 + X1) / 2, Y0 - t / 2, ZC / 2), M['plaster'], coll=coll)
    box('wall_right', (t, Y1 - Y0, ZC), (X1 + t / 2, (Y0 + Y1) / 2, ZC / 2), M['plaster'], coll=coll)
    # Left wall with a wide steel-framed window.
    xw = X0 - t / 2
    box('wall_left_a', (t, WIN['y0'] - Y0, ZC), (xw, (Y0 + WIN['y0']) / 2, ZC / 2), M['plaster'], coll=coll)
    box('wall_left_b', (t, Y1 - WIN['y1'], ZC), (xw, (WIN['y1'] + Y1) / 2, ZC / 2), M['plaster'], coll=coll)
    box('wall_left_sill', (t, WIN['y1'] - WIN['y0'], WIN['z0']), (xw, 0, WIN['z0'] / 2), M['plaster'], coll=coll)
    box('wall_left_head', (t, WIN['y1'] - WIN['y0'], ZC - WIN['z1']), (xw, 0, (WIN['z1'] + ZC) / 2), M['plaster'], coll=coll)
    for y in [WIN['y0'], -1.15, 0, 1.15, WIN['y1']]:
        box(f'mullion_{y}', (.07, .045, WIN['z1'] - WIN['z0']), (X0 - .03, y, (WIN['z0'] + WIN['z1']) / 2), M['steel'], coll=coll)
    for z in [WIN['z0'], 2.02, WIN['z1']]:
        box(f'transom_{z}', (.07, WIN['y1'] - WIN['y0'], .045), (X0 - .03, 0, z), M['steel'], coll=coll)
    glass = box('window_glass', (.006, WIN['y1'] - WIN['y0'], WIN['z1'] - WIN['z0']), (X0 - .04, 0, (WIN['z0'] + WIN['z1']) / 2), M['glass'], coll=coll)
    glass.visible_shadow = False
    # Bright, defocused exterior visible only to camera and reflections.
    out = bpy.data.meshes.new('outside')
    out.from_pydata([(0, -9, -1), (0, 9, -1), (0, 9, 6), (0, -9, 6)], [], [(0, 1, 2, 3)])
    uv = out.uv_layers.new()
    for li, co in zip(range(4), [(0, 0), (1, 0), (1, 1), (0, 1)]):
        uv.data[li].uv = co
    o = link(bpy.data.objects.new('outside', out), coll)
    o.location = (X0 - 6, 0, 0)
    m = M['outside']
    nt = m.node_tree
    tx = nt.nodes.new('ShaderNodeTexImage')
    tx.image = _image('outside')
    tint = nt.nodes.new('ShaderNodeMix')
    tint.name = 'view_tint'
    tint.data_type = 'RGBA'
    tint.blend_type = 'MULTIPLY'
    tint.inputs['Factor'].default_value = 1
    tint.inputs['B'].default_value = (1, 1, 1, 1)
    nt.links.new(tx.outputs['Color'], tint.inputs['A'])
    nt.links.new(tint.outputs['Result'], nt.nodes['Emission'].inputs['Color'])
    nt.nodes['Emission'].inputs['Strength'].default_value = 7.0
    o.data.materials.append(m)
    o.visible_diffuse = False
    o.visible_shadow = False
    o.visible_volume_scatter = False
    # Skirting boards.
    sk = .09
    box('skirt_back', (X1 - X0, .015, sk), ((X0 + X1) / 2, Y1 - .008, sk / 2), M['trim'], coll=coll)
    box('skirt_right', (.015, Y1 - Y0, sk), (X1 - .008, (Y0 + Y1) / 2, sk / 2), M['trim'], coll=coll)
    box('skirt_front', (X1 - X0, .015, sk), ((X0 + X1) / 2, Y0 + .008, sk / 2), M['trim'], coll=coll)


def build_sofa(M, coll, cx=1.55, cy=-.35, length=2.3):
    """Low bouclé sofa facing the window (-X)."""
    d, seat_h = .98, .42
    x_front = cx - d / 2
    box('sofa_base', (d, length, .26), (cx, cy, .19), M['boucle'], bevel=.04, seg=4, coll=coll)
    box('sofa_back', (.24, length, .48), (cx + d / 2 - .12, cy, .54), M['boucle'], bevel=.08, seg=5, coll=coll)
    for s in (-1, 1):
        box(f'sofa_arm_{s}', (d, .22, .36), (cx, cy + s * (length / 2 - .11), .48), M['boucle'], bevel=.08, seg=5, coll=coll)
    n = 2
    w = (length - .44) / n
    for i in range(n):
        y = cy - (length - .44) / 2 + w * (i + .5)
        box(f'seat_cushion_{i}', (d - .26, w - .012, .14), (x_front + (d - .26) / 2 + .02, y, seat_h - .045), M['boucle'],
            bevel=.05, seg=5, coll=coll)
        box(f'back_cushion_{i}', (.20, w - .03, .40), (cx + d / 2 - .30, y, .66), M['boucle'], bevel=.08, seg=5,
            rot=(0, math.radians(-9), 0), coll=coll)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cylinder(f'sofa_leg_{sx}{sy}', .018, .06, (cx + sx * (d / 2 - .07), cy + sy * (length / 2 - .07), .03), M['walnut'], 16, coll=coll)
    # Knit throw folded over the near arm.
    box('throw', (.62, .30, .035), (cx - .06, cy - length / 2 + .2, .675), M['knit'], bevel=.016, seg=4, coll=coll,
        rot=(math.radians(4), 0, math.radians(2)))
    box('throw_fall', (.62, .035, .30), (cx - .06, cy - length / 2 + .055, .53), M['knit'], bevel=.014, seg=4, coll=coll)


def build_keys(M, coll):
    """Three brass keys and a tan leather tag on a ring, wedged in the cushion gap."""
    root = bpy.data.objects.new('KEYS', None)
    link(root, coll)
    root.location = KEYS_AT
    root.rotation_euler = (math.radians(-18), math.radians(10), math.radians(28))
    parent(tube('key_ring', ring_points((0, 0, 0), .015, (0, 0, 1), 48), .0013, M['brass'], coll, closed=True), root)
    for i, az in enumerate([-.75, -.15, .5]):
        d = Vector((math.cos(az), math.sin(az), 0))
        side = Vector((-d.y, d.x, 0))
        head = d * .029 + Vector((0, 0, .0012 * i))
        parent(cylinder(f'key_head_{i}', .0125, .0024, tuple(head), M['brass'], 32, coll=coll, bevel=.0007), root)
        ln = .05 - .006 * i
        blade_c = d * (.042 + ln / 2) + Vector((0, 0, .0012 * i))
        parent(box(f'key_blade_{i}', (ln, .0085, .0019), tuple(blade_c), M['brass'], bevel=.0006, seg=1, coll=coll,
                   rot=(0, 0, az)), root)
        for k in range(4):
            notch = blade_c + d * (ln * (k / 4 - .3)) + side * .0047
            parent(box(f'key_bit_{i}_{k}', (.003, .002, .0019), tuple(notch), M['brass'], coll=coll, rot=(0, 0, az)), root)
    tag_d = Vector((math.cos(2.3), math.sin(2.3), 0))
    parent(box('key_tag', (.062, .026, .0035), tuple(tag_d * .045), M['leather'], bevel=.004, seg=3, coll=coll,
               rot=(0, 0, 2.3)), root)
    return root


def build_coffee_table(M, coll, c=(.05, -.45)):
    cylinder('table_top', .48, .045, (c[0], c[1], .375), M['stone'], 96, coll=coll, bevel=.008)
    cylinder('table_base', .16, .35, (c[0], c[1], .175), M['stone'], 64, coll=coll, bevel=.01)
    for i, (dx, dy, w, h, m) in enumerate([(-.12, .1, .24, .035, 0), (-.12, .1, .22, .028, 2), (-.13, .1, .2, .03, 1)]):
        box(f'book_t_{i}', (w, w * .72, h), (c[0] + dx, c[1] + dy, .3975 + .0175 + sum([.035, .028, .03][:i])), M['books'][m],
            bevel=.002, seg=1, coll=coll, rot=(0, 0, math.radians(8 * i - 6)))
    cylinder('vase', .055, .26, (c[0] - .32, c[1] + .28, .53), M['ceramic'], 48, coll=coll, bevel=.01)
    cylinder('mug', .042, .095, (c[0] - .05, c[1] + .30, .445), M['ceramic'], 48, coll=coll, bevel=.004)


def build_rug(M, coll):
    box('rug', (2.6, 2.0, .012), (.35, -.45, .006), M['rug'], bevel=.004, seg=2, coll=coll)


def build_dock(M, coll):
    """Walnut sideboard on the back wall carrying the three-bay shared dock."""
    x0, x1 = -.35, 2.15
    cx, L = (x0 + x1) / 2, x1 - x0
    box('sideboard', (L, .5, .5), (cx, 2.75, .37), M['walnut'], bevel=.006, seg=2, coll=coll)
    box('sideboard_top', (L + .02, .52, .03), (cx, 2.74, .605), M['walnut'], bevel=.004, seg=2, coll=coll)
    for i in range(1, 4):
        box(f'sideboard_gap_{i}', (.004, .005, .46), (x0 + L * i / 4, 2.497, .37), M['graphite_matte'], coll=coll)
    for sx in (x0 + .06, x1 - .06):
        for sy in (2.55, 2.95):
            cylinder(f'sb_leg_{sx}_{sy}', .015, .12, (sx, sy, .06), M['steel'], 16, coll=coll)
    box('dock_rail', (L - .16, .26, .016), (cx, DOCK_PADS[0][1] + .02, DOCK_TOP + .008), M['graphite'], bevel=.006, seg=3, coll=coll)
    pads = []
    for i, (px, py) in enumerate(DOCK_PADS):
        cylinder(f'pad_{i}', .072, .012, (px, py, DOCK_TOP + .012), M['pad'], 64, coll=coll, bevel=.003)
        glow = emissive(f'pad_glow_{i}', (1.0, .55, .2), 0.0)
        tube(f'pad_ring_{i}', ring_points((px, py, DOCK_TOP + .0185), .062, (0, 0, 1), 96), .0011, glow, coll, closed=True)
        for dx in (-.02, .02):
            cylinder(f'pad_contact_{i}_{dx}', .004, .003, (px + dx, py - .035, DOCK_TOP + .019), M['contact'], 16, coll=coll)
        pads.append(glow)
    return pads


def build_shelf(M, coll):
    """Low bookshelf and art on the right wall; populates reflections and wides."""
    box('shelf', (.38, 1.8, .7), (X1 - .19, 1.3, .35), M['walnut'], bevel=.004, seg=2, coll=coll)
    import random
    rnd = random.Random(4)
    y = .5
    while y < 2.05:
        w = rnd.uniform(.025, .05)
        h = rnd.uniform(.18, .26)
        box(f'book_s_{y:.3f}', (rnd.uniform(.15, .2), w, h), (X1 - .2, y, .7 + h / 2), rnd.choice(M['books']),
            bevel=.002, seg=1, coll=coll, rot=(rnd.uniform(-.03, .03), 0, 0))
        y += w + .004
    cylinder('shelf_bowl', .12, .06, (X1 - .2, .75, .73), M['clay'], 48, coll=coll, bevel=.02)
    frame = box('art_frame', (.03, .86, 1.08), (X1 - .016, 1.3, 1.62), M['walnut'], bevel=.004, seg=2, coll=coll)
    art = bpy.data.meshes.new('art_canvas')
    art.from_pydata([(0, -.4, -.5), (0, .4, -.5), (0, .4, .5), (0, -.4, .5)], [], [(0, 3, 2, 1)])
    o = link(bpy.data.objects.new('art_canvas', art), coll)
    o.location = (X1 - .033, 1.3, 1.62)
    o.data.materials.append(M['art'])
    o.rotation_euler = (0, 0, 0)


def build_plant(M, coll, base=(-3.0, 2.35)):
    """Olive tree in a clay pot by the window."""
    import random
    rnd = random.Random(9)
    bx, by = base
    cylinder('pot', .24, .46, (bx, by, .23), M['clay'], 64, coll=coll, bevel=.02)
    cylinder('soil', .22, .01, (bx, by, .445), M['bark'], 48, coll=coll)
    trunk = [(bx, by, .44), (bx + .03, by - .02, .9), (bx - .02, by + .03, 1.4), (bx + .05, by, 1.7)]
    tube('trunk', trunk, .022, M['bark'], coll, res=6)
    leaf = bmesh.new()
    lv = [leaf.verts.new(p) for p in [(0, 0, 0), (.035, .007, 0), (.075, 0, 0), (.035, -.007, 0)]]
    leaf.faces.new(lv)
    lm = bpy.data.meshes.new('leaf_mesh')
    leaf.to_mesh(lm)
    leaf.free()
    lm.materials.append(M['leaf'])
    bm = bmesh.new()
    branch_tips = []
    for k in range(9):
        a = rnd.uniform(0, 2 * math.pi)
        z0 = rnd.uniform(1.1, 1.65)
        start = Vector((bx + .02, by, z0))
        end = start + Vector((math.cos(a) * rnd.uniform(.25, .45), math.sin(a) * rnd.uniform(.2, .4), rnd.uniform(.15, .45)))
        mid = (start + end) / 2 + Vector((0, 0, .06))
        tube(f'branch_o_{k}', [tuple(start), tuple(mid), tuple(end)], .007, M['bark'], coll, res=4)
        branch_tips.append((start, end))
    for start, end in branch_tips:
        for i in range(150):
            t = rnd.uniform(.25, 1.0)
            p = start.lerp(end, t) + Vector((rnd.gauss(0, .07), rnd.gauss(0, .07), rnd.gauss(0, .06)))
            mat = Matrix.Translation(p) @ Matrix.Rotation(rnd.uniform(0, 6.28), 4, 'Z') @ \
                Matrix.Rotation(rnd.uniform(-.9, .3), 4, 'Y') @ Matrix.Rotation(rnd.uniform(-.6, .6), 4, 'X')
            s = rnd.uniform(.8, 1.25)
            vs = [bm.verts.new(mat @ (Vector(v) * s)) for v in [(0, 0, 0), (.035, .007, 0), (.075, 0, 0), (.035, -.007, 0)]]
            bm.faces.new(vs)
    o = mesh_object('olive_leaves', bm, M['leaf'], coll, smooth=False)
    return o


def uv_plane(name, w, h, loc, rot, mat, coll):
    me = bpy.data.meshes.new(name)
    me.from_pydata([(-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new()
    for li, co in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]):
        uv.data[li].uv = co
    me.materials.append(mat)
    o = link(bpy.data.objects.new(name, me), coll)
    o.location = loc
    o.rotation_euler = rot
    return o


KITCHEN = dict(x0=-3.30, x1=.95, front=-2.56, top=.91)
RANGE_X = (-1.20, -.44)
KNOBS = [Vector((x, KITCHEN['front'] + .018, .845)) for x in (-1.08, -.93, -.71, -.56)]
BURNERS = [(-1.0, -2.76), (-.64, -2.76), (-1.0, -3.0), (-.64, -3.0)]
PAN_AT = Vector((-1.0, -2.76, .995))


def build_kitchen(M, coll):
    """Kitchen run on the front wall: green cabinets, stone top, range, tile, shelves."""
    k = KITCHEN
    depth = Y0 - k['front']                        # negative
    cy = (Y0 + k['front']) / 2
    for x0, x1 in [(k['x0'], RANGE_X[0]), (RANGE_X[1], k['x1'])]:
        box(f'base_{x0}', (x1 - x0 - .004, -depth - .02, .78), ((x0 + x1) / 2, cy - .01, .48), M['cabinet'], bevel=.003, seg=2, coll=coll)
        box(f'toe_{x0}', (x1 - x0, -depth - .08, .09), ((x0 + x1) / 2, cy - .04, .045), M['graphite_matte'], coll=coll)
        n = max(1, round((x1 - x0) / .6))
        for i in range(n):
            xa = x0 + (x1 - x0) * i / n
            xb = x0 + (x1 - x0) * (i + 1) / n
            box(f'door_gap_{x0}_{i}', (.004, .004, .74), (xb - .002, k['front'] - .002, .48), M['graphite_matte'], coll=coll)
            box(f'pull_{x0}_{i}', (.12, .012, .012), ((xa + xb) / 2, k['front'] + .012, .80), M['brass'], bevel=.004, seg=2, coll=coll)
        box(f'top_{x0}', (x1 - x0, -depth + .02, .04), ((x0 + x1) / 2, cy + .01, k['top'] - .02), M['counter'], bevel=.004, seg=2, coll=coll)
    # Range: stainless body, oven door, knobs at OFF, cast-iron grates.
    rx = (RANGE_X[0] + RANGE_X[1]) / 2
    rw = RANGE_X[1] - RANGE_X[0]
    box('range_body', (rw, -depth, .90), (rx, cy, .45), M['stainless'], bevel=.006, seg=2, coll=coll)
    box('oven_door', (rw - .06, .02, .5), (rx, k['front'] + .005, .38), M['stainless'], bevel=.01, seg=3, coll=coll)
    box('oven_glass', (rw - .2, .004, .22), (rx, k['front'] + .016, .42), M['lens_glass'], bevel=.006, seg=2, coll=coll)
    cylinder('oven_handle', .011, rw - .16, (rx, k['front'] + .055, .66), M['stainless'], 24, rot=(0, math.pi / 2, 0), coll=coll)
    box('cooktop', (rw, -depth, .02), (rx, cy, .915), M['iron'], bevel=.004, seg=2, coll=coll)
    for i, kp in enumerate(KNOBS):
        cylinder(f'knob_{i}', .021, .028, tuple(kp), M['graphite'], 32, rot=(math.pi / 2, 0, 0), coll=coll, bevel=.004)
        box(f'knob_mark_{i}', (.003, .004, .014), (kp.x, kp.y + .015, kp.z + .009), M['knob_mark'], coll=coll)
    flames = []
    for i, (bx, by) in enumerate(BURNERS):
        cylinder(f'burner_{i}', .045, .02, (bx, by, .935), M['iron'], 32, coll=coll, bevel=.004)
        cylinder(f'burner_cap_{i}', .032, .008, (bx, by, .948), M['iron'], 32, coll=coll, bevel=.002)
        if i == 0:
            flames.append(tube('flame_ring', ring_points((bx, by, .942), .05, (0, 0, 1), 72), .0045, M['flame'], coll, closed=True))
    for gx in (-1.0, -.64):
        for gy in (-2.76, -3.0):
            for d in (-.08, -.03, .03, .08):
                box(f'grate_{gx}_{gy}_{d}', (.2, .008, .012), (gx, gy + d, .966), M['iron'], coll=coll)
                box(f'grate_x_{gx}_{gy}_{d}', (.008, .2, .012), (gx + d, gy, .966), M['iron'], coll=coll)
    # Skillet on the front-left burner, with oil.
    pan = cylinder('skillet', .125, .045, (PAN_AT.x, PAN_AT.y, PAN_AT.z), M['iron'], 64, coll=coll, cap=False)
    so = pan.modifiers.new('solid', 'SOLIDIFY')
    so.thickness = .005
    cylinder('skillet_base', .125, .006, (PAN_AT.x, PAN_AT.y, PAN_AT.z - .02), M['iron'], 64, coll=coll)
    cylinder('skillet_oil', .118, .002, (PAN_AT.x, PAN_AT.y, PAN_AT.z - .015), M['oil'], 64, coll=coll)
    box('skillet_handle', (.20, .025, .014), (PAN_AT.x + .22, PAN_AT.y + .02, PAN_AT.z + .012), M['iron'], bevel=.005, seg=2,
        coll=coll, rot=(0, math.radians(-8), math.radians(6)))
    # Board, garlic, knife; recipe book on a stand.
    box('board', (.42, .26, .022), (.05, -2.86, k['top'] + .011), M['board'], bevel=.006, seg=3, coll=coll, rot=(0, 0, .08))
    for i, (gx, gy) in enumerate([(-.04, -2.84), (.08, -2.9)]):
        g = sphere(f'garlic_{i}', .028, (gx, gy, k['top'] + .05), M['garlic'], 32, 16, (1, 1, .82), coll)
        g.modifiers.new('sub', 'SUBSURF').levels = 1
        tube(f'garlic_stem_{i}', [(gx, gy, k['top'] + .07), (gx + .004, gy, k['top'] + .085)], .003, M['garlic'], coll, res=4)
    for i, (cx, cy2) in enumerate([(.16, -2.80), (.19, -2.83), (.14, -2.85)]):
        sphere(f'clove_{i}', .009, (cx, cy2, k['top'] + .028), M['garlic'], 16, 8, (1.6, 1, .9), coll)
    box('knife_blade', (.17, .028, .002), (.15, -2.95, k['top'] + .025), M['stainless'], bevel=.001, seg=1, coll=coll, rot=(0, 0, -.12))
    box('knife_handle', (.1, .022, .016), (.01, -2.932, k['top'] + .03), M['graphite'], bevel=.006, seg=2, coll=coll, rot=(0, 0, -.12))
    box('stand', (.20, .03, .26), (.62, -3.05, k['top'] + .13), M['walnut'], bevel=.004, seg=2, coll=coll, rot=(math.radians(-18), 0, 0))
    for side in (-1, 1):
        uv_plane(f'recipe_{side}', .145, .2, (.62 + side * .075, -3.025, k['top'] + .15), (math.radians(108), 0, side * .12), M['recipe'], coll)
    # Backsplash, open shelves with an under-shelf light.
    uv_plane('backsplash', k['x1'] - k['x0'], .54, ((k['x0'] + k['x1']) / 2, Y0 + .002, k['top'] + .27),
             (math.radians(90), 0, 0), M['tile'], coll)
    for z in (1.47, 1.86):
        box(f'shelf_k_{z}', (3.4, .26, .035), (-1.25, Y0 + .13, z), M['walnut'], bevel=.004, seg=2, coll=coll)
    strip = box('led_strip', (3.3, .02, .006), (-1.25, Y0 + .2, 1.449), M['strip'], coll=coll)
    strip.visible_shadow = False
    import random
    rnd = random.Random(12)
    x = -2.85
    while x < .3:
        kind = rnd.random()
        if kind < .45:
            for j in range(rnd.randint(3, 6)):
                cylinder(f'plate_{x:.2f}_{j}', .11, .012, (x + .11, Y0 + .14, 1.497 + j * .013), M['ceramic'], 48, coll=coll, bevel=.003)
            x += .27
        elif kind < .8:
            h = rnd.uniform(.12, .22)
            cylinder(f'jar_{x:.2f}', .055, h, (x + .06, Y0 + .12, 1.4875 + h / 2), rnd.choice([M['ceramic'], M['clay']]), 32, coll=coll, bevel=.008)
            x += .16
        else:
            cylinder(f'bowl_{x:.2f}', .09, .07, (x + .09, Y0 + .13, 1.522), M['clay'], 48, coll=coll, bevel=.02)
            x += .22
    light = bpy.data.lights.new('kitchen_strip', 'AREA')
    light.shape = 'RECTANGLE'
    light.size, light.size_y = 3.3, .08
    light.color = (1.0, .76, .52)
    light.energy = 0
    lo = link(bpy.data.objects.new('kitchen_strip', light), coll)
    lo.location = (-1.25, Y0 + .2, 1.44)
    return dict(flame=M['flame'], strip=(light, 150.0), knobs=KNOBS)


def build_drawing(M, coll):
    """A child's crayon drawing and crayons on the coffee table."""
    uv_plane('drawing', .297, .21, (.06, -.66, .3986), (0, 0, math.radians(-10)), M['drawing'], coll)
    for i, (x, y, a) in enumerate([(.30, -.60, .4), (.27, -.67, 1.2), (.33, -.72, 2.3), (.24, -.55, 2.9)]):
        c = cylinder(f'crayon_{i}', .0045, .085, (x, y, .4035), M['crayons'][i], 12, rot=(math.pi / 2, 0, a), coll=coll)
        c.modifiers.new('bevel', 'BEVEL').width = .001


def build_lamps(M, coll):
    """Evening practicals: a floor lamp by the sofa and a small lamp on the bookshelf."""
    lights = []
    for name, (x, y, z_base, pole, r, h) in {'floor_lamp': (3.18, -1.55, 0, 1.42, .20, .30),
                                             'shelf_lamp': (X1 - .2, 2.12, .70, .22, .11, .16)}.items():
        cylinder(f'{name}_base', r * .55, .03, (x, y, z_base + .015), M['stone'], 48, coll=coll, bevel=.006)
        cylinder(f'{name}_pole', .008, pole, (x, y, z_base + pole / 2), M['brass'], 16, coll=coll)
        shade = cylinder(f'{name}_shade', r, h, (x, y, z_base + pole + h * .3), M['shade_glow'], 64, coll=coll, cap=False)
        shade.modifiers.new('solid', 'SOLIDIFY').thickness = .003
        lamp = bpy.data.lights.new(name, 'POINT')
        lamp.color = (1.0, .74, .48)
        lamp.shadow_soft_size = r * .5
        lamp.energy = 0
        lo = link(bpy.data.objects.new(name, lamp), coll)
        lo.location = (x, y, z_base + pole + h * .25)
        lights.append((lamp, 70.0 if name == 'floor_lamp' else 25.0))
    return lights


TIME_OF_DAY = {
    # sun elevation/azimuth (deg), sun energy, sun colour, sky mix (0 sky, 1 flat), flat colour, world strength,
    # window view tint and strength, bounce energy, practicals (0-1), exposure
    'morning': dict(elev=26, az=30, sun=5.0, col=(1.0, .90, .80), flat=0, sky=.65, view=(1, 1, 1), view_k=7.0,
                    bounce=60, practical=0, exposure=0.0),
    'midday': dict(elev=46, az=18, sun=5.5, col=(1.0, .97, .92), flat=0, sky=.85, view=(1, 1, 1), view_k=8.0,
                   bounce=45, practical=0, exposure=0.0),
    'golden': dict(elev=17, az=33, sun=6.5, col=(1.0, .80, .60), flat=0, sky=.55, view=(1, 1, 1), view_k=7.0,
                   bounce=70, practical=0, exposure=0.0),
    'evening': dict(elev=-4, az=33, sun=0.0, col=(1, 1, 1), flat=1, sky=.55, flat_col=(.10, .15, .32),
                    view=(.30, .42, .75), view_k=1.4, bounce=0, practical=1.0, exposure=.35),
    'night': dict(elev=-20, az=33, sun=0.0, col=(1, 1, 1), flat=1, sky=.35, flat_col=(.025, .035, .08),
                  view=(.06, .09, .19), view_k=1.0, bounce=0, practical=.85, exposure=.45),
}


def set_time_of_day(H, tod):
    p = TIME_OF_DAY['golden' if tod == 'graphic' else tod]
    L = H['lighting']
    sun, so = L['sun'], L['sun_obj']
    sun.energy = p['sun']
    sun.color = p['col']
    so.hide_render = p['sun'] <= 0
    d = Vector((math.cos(math.radians(p['az'])), math.sin(math.radians(p['az'])), -math.tan(math.radians(max(p['elev'], 1))))).normalized()
    so.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    L['sky_node'].sun_elevation = math.radians(max(p['elev'], 0))
    L['sky_mix'].inputs['Factor'].default_value = p['flat']
    L['sky_mix'].inputs['B'].default_value = (*p.get('flat_col', (0, 0, 0)), 1)
    L['background'].inputs['Strength'].default_value = p['sky']
    L['view_emission'].default_value = p['view_k']
    L['view_tint'].inputs['B'].default_value = (*p['view'], 1)
    L['bounce'].energy = p['bounce']
    L['bounce_obj'].hide_render = p['bounce'] <= 0
    for light, base in H['practicals']:
        light.energy = base * p['practical']
    H['M']['strip'].node_tree.nodes['Emission'].inputs['Strength'].default_value = 6.0 * p['practical']
    H['M']['shade_glow'].node_tree.nodes['Emission'].inputs['Strength'].default_value = 3.5 * p['practical']
    bpy.context.scene.view_settings.exposure = p['exposure']


# ----------------------------------------------------------------------------
# Lighting and render configuration
# ----------------------------------------------------------------------------

def build_lighting(coll, sun_elev=17, sun_az=33, volumetric=False):
    sc = bpy.context.scene
    w = bpy.data.worlds.new('world')
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    sky = nt.nodes.new('ShaderNodeTexSky')
    sky.sky_type = 'NISHITA'
    sky.sun_disc = False
    sky.sun_elevation = math.radians(sun_elev)
    sky.sun_rotation = math.radians(180 + sun_az)
    sky.air_density = 1.2
    sky.dust_density = 2.5
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.inputs['Factor'].default_value = 0
    nt.links.new(sky.outputs[0], mix.inputs['A'])
    nt.links.new(mix.outputs['Result'], nt.nodes['Background'].inputs[0])
    nt.nodes['Background'].inputs['Strength'].default_value = .55
    # Sun travelling into the room from the window wall (-X), low and warm.
    sun = bpy.data.lights.new('sun', 'SUN')
    sun.energy = 6.5
    sun.angle = math.radians(1.2)
    sun.color = (1.0, .80, .60)
    so = link(bpy.data.objects.new('sun', sun), coll)
    d = Vector((math.cos(math.radians(sun_az)), math.sin(math.radians(sun_az)), -math.tan(math.radians(sun_elev)))).normalized()
    so.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    # Window portal guides sky sampling through the opening.
    portal = bpy.data.lights.new('window_portal', 'AREA')
    portal.shape = 'RECTANGLE'
    portal.size = WIN['z1'] - WIN['z0']         # local X maps to world Z below
    portal.size_y = WIN['y1'] - WIN['y0']
    if hasattr(portal, 'cycles') and hasattr(portal.cycles, 'is_portal'):
        portal.cycles.is_portal = True
    po = link(bpy.data.objects.new('window_portal', portal), coll)
    po.location = (X0 - .02, 0, (WIN['z0'] + WIN['z1']) / 2)
    po.rotation_euler = (0, math.radians(-90), 0)   # emit into the room (+X)
    # Soft bounce from the sunlit floor patch and a dim ceiling fill.
    bounce = bpy.data.lights.new('bounce', 'AREA')
    bounce.shape = 'RECTANGLE'
    bounce.size, bounce.size_y = 3.0, 2.0
    bounce.energy = 70
    bounce.color = (1.0, .82, .66)
    bo = link(bpy.data.objects.new('bounce', bounce), coll)
    bo.location = (-.8, -.2, .05)
    bo.rotation_euler = (0, 0, 0)
    bo.rotation_euler = Vector((0, 0, 1)).to_track_quat('-Z', 'Y').to_euler()
    bo.visible_camera = False
    bounce.use_shadow = True
    if volumetric:
        vol = bpy.data.materials.new('room_haze')
        vol.use_nodes = True
        vnt = vol.node_tree
        vnt.nodes.remove(vnt.nodes['Principled BSDF'])
        pv = vnt.nodes.new('ShaderNodeVolumePrincipled')
        pv.inputs['Density'].default_value = .012
        pv.inputs['Anisotropy'].default_value = .55
        vnt.links.new(pv.outputs[0], vnt.nodes['Material Output'].inputs['Volume'])
        haze = box('haze', (X1 - X0 - .05, Y1 - Y0 - .05, ZC - .05), ((X0 + X1) / 2, (Y0 + Y1) / 2, ZC / 2), vol, coll=coll)
        haze.visible_shadow = False
    else:
        haze = None
    handles = dict(sun=sun, sun_obj=so, sky_node=sky, sky_mix=mix, background=nt.nodes['Background'],
                   bounce=bounce, bounce_obj=bo)
    return handles, haze


def configure_render(width, height, samples, gpu=False, motion_blur=True, fps=24, film_grade='AgX - Medium High Contrast',
                     deep=False):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.render.fps = fps
    sc.render.resolution_x, sc.render.resolution_y = width, height
    sc.render.resolution_percentage = 100
    sc.render.use_persistent_data = True
    c = sc.cycles
    if gpu:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        for backend in ('OPTIX', 'CUDA', 'HIP', 'METAL', 'ONEAPI'):
            try:
                prefs.compute_device_type = backend
                prefs.refresh_devices()
                devs = [d for d in prefs.devices if d.type == backend]
                if devs:
                    for d in prefs.devices:
                        d.use = d.type == backend
                    c.device = 'GPU'
                    print('Cycles device:', backend, [d.name for d in devs], flush=True)
                    break
            except TypeError:
                continue
        else:
            raise RuntimeError('No GPU compute device found; rerun without --gpu')
    else:
        c.device = 'CPU'
    c.samples = samples
    c.use_adaptive_sampling = True
    c.adaptive_threshold = .02 if samples >= 128 else .04
    c.use_denoising = True
    c.denoiser = 'OPENIMAGEDENOISE'
    c.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
    c.denoising_prefilter = 'ACCURATE'
    c.max_bounces = 8
    c.diffuse_bounces = 3 if samples >= 128 else 2
    c.glossy_bounces = 5
    c.transmission_bounces = 4
    c.transparent_max_bounces = 8
    c.volume_bounces = 0
    c.volume_step_rate = 4.0
    c.caustics_reflective = False
    c.caustics_refractive = False
    c.sample_clamp_indirect = 6
    c.blur_glossy = .6
    sc.render.use_motion_blur = motion_blur
    sc.render.motion_blur_shutter = .5
    sc.view_settings.view_transform = 'AgX'
    try:
        sc.view_settings.look = film_grade
    except TypeError:
        pass
    sc.view_settings.exposure = 0.0
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGB'
    sc.render.image_settings.color_depth = '16' if deep else '8'       # 16-bit for finals: grading headroom
    sc.render.image_settings.compression = 35
    sc.render.dither_intensity = 1.0
    sc.render.film_transparent = False


def build(volumetric=False):
    """Create the full set and three FLOAT units; return handles."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    M = build_materials()
    M['foil'] = foil_material('foil')
    coll = sc.collection
    build_room(M, coll)
    build_rug(M, coll)
    build_sofa(M, coll)
    build_coffee_table(M, coll)
    pads = build_dock(M, coll)
    build_shelf(M, coll)
    build_plant(M, coll)
    keys = build_keys(M, coll)
    kitchen = build_kitchen(M, coll)
    build_drawing(M, coll)
    lamps = build_lamps(M, coll)
    lighting, haze = build_lighting(coll, volumetric=volumetric)
    lighting['view_emission'] = M['outside'].node_tree.nodes['Emission'].inputs['Strength']
    lighting['view_tint'] = M['outside'].node_tree.nodes['view_tint']
    units = [make_float(t, M, coll) for t in ('hero', 'dock_a', 'dock_b')]
    H = dict(M=M, units=units, pads=pads, keys=keys, lighting=lighting, haze=haze, kitchen=kitchen,
             practicals=lamps + [kitchen['strip']])
    set_time_of_day(H, 'golden')
    return H
