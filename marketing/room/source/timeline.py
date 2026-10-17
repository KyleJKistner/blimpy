"""FLOAT / Room edit timeline. Pure data shared by render, finishing and score.

A day with FLOAT in 40 seconds: each vignette shows something an assistant on a
phone or a speaker cannot do because it cannot go and look. 24 fps, 120 BPM:
one beat is exactly 12 frames, one bar 48 frames; every cut lands on a beat.
Times are in frames unless a name ends in _s.
"""
FPS = 24
BPM = 120
BEAT = 12
BAR = 48
FRAMES = 960                       # 40.0 s

# id, name, first frame, end frame (exclusive), time of day, purpose
SHOTS = [
    ('S01', 'The ask', 0, 60, 'morning', 'Hook: a mirrored sphere in a sunlit room turns toward a spoken question.'),
    ('S02', 'Listening', 60, 84, 'morning', 'Product face: lens and amber ring answer "Let me look."'),
    ('S03', 'Search view', 84, 120, 'morning', "FLOAT's simulated camera view locks on the keys."),
    ('S04', 'Found', 120, 168, 'morning', 'Rack focus from FLOAT to the keys; spoken answer.'),
    ('S05', 'Spin-up', 168, 180, 'morning', 'Detail: guarded fan spins up into the drop.'),
    ('S06', 'Set off', 180, 192, 'morning', 'Detail: low three-quarter; the room curves across the envelope.'),
    ('S07', 'Meet FLOAT', 192, 288, 'morning', 'Drop: low tracking shot through the sun, title.'),
    ('S08', 'From anywhere', 288, 324, 'graphic', 'Simulated app: "Did I leave the stove on?" asked from outside.'),
    ('S09', 'Into the kitchen', 324, 360, 'midday', 'FLOAT crosses the house to go and look.'),
    ('S10', 'Live view', 360, 408, 'midday', 'Simulated live view: four knobs, all off.'),
    ('S11', 'Notices', 408, 480, 'golden', 'FLOAT notices the olive tree needs water.'),
    ('S12', 'Cooking', 480, 528, 'evening', 'Hands-free in the kitchen: "What\'s next?"'),
    ('S13', 'Next step', 528, 576, 'evening', 'Pod close-up over the pan; timer.'),
    ('S14', 'The call', 576, 648, 'evening', "Grandma's voice through FLOAT over a crayon drawing."),
    ('S15', 'Shift change', 648, 744, 'night', 'The day unit docks; a charged one lifts off.'),
    ('S16', 'Lift', 744, 792, 'night', 'Low angle as the fresh unit rises.'),
    ('S17', 'In the room', 792, 864, 'night', 'Thesis line.'),
    ('S18', 'End card', 864, 960, 'night', 'Brand, call to action and concept disclosure.'),
]
GRAPHIC_SHOTS = {'S08'}            # built entirely in finish.py; nothing to render

# Spoken lines. Start times are design targets; voice.py measures durations and
# writes assets/voice/timing.json for captions and FLOAT's indicator.
DIALOGUE = [
    dict(id='ask', who='person', start_s=0.30, text='Float, have you seen my keys?'),
    dict(id='look', who='float', start_s=2.55, text='Let me look.'),
    dict(id='found', who='float', start_s=5.10, text='Found them. Between the cushions.'),
    dict(id='stove', who='person', start_s=12.10, text='Did I leave the stove on?', phone=True),
    dict(id='stove_ok', who='float', start_s=15.25, text='All four burners are off.'),
    dict(id='plant', who='float', start_s=17.70, text='Your olive tree looks thirsty.'),
    dict(id='next', who='person', start_s=20.45, text="What's next?"),
    dict(id='garlic', who='float', start_s=21.50, text="Two cloves of garlic. I'll time the simmer."),
    dict(id='grandma', who='grandma', start_s=24.45, text='Did you draw that? It\'s beautiful!', via_float=True),
]

# Large kinetic copy. Times in seconds.
TITLES = [
    dict(shot='S07', at_s=8.50, lines=['Meet FLOAT.'], sub='A floating AI companion.'),
    dict(shot='S15', at_s=28.95, lines=['One rests.'], sub=None),
    dict(shot='S15', at_s=29.95, lines=['Another takes over.'], sub=None, add=True),
    dict(shot='S17', at_s=33.25, lines=['Not on a screen.'], sub=None),
    dict(shot='S17', at_s=34.25, lines=['In the room.'], sub=None, add=True),
]

# Small feature labels that make the montage legible with the sound off.
CHYRONS = [
    dict(start_s=3.5, end_s=7.0, text='FINDS WHAT YOU LOST'),
    dict(start_s=12.0, end_s=17.0, text="CHECKS IN WHILE YOU'RE OUT"),
    dict(start_s=17.0, end_s=20.0, text='NOTICES THE LITTLE THINGS'),
    dict(start_s=20.0, end_s=24.0, text='HANDS-FREE IN THE KITCHEN'),
    dict(start_s=24.0, end_s=27.0, text='BRINGS FAMILY INTO THE ROOM'),
]

# Simulated interface moments (all labelled as simulated on screen).
SEARCH_LOCK_F = 103                 # S03: brackets snap onto the keys
STOVE_LOCK_F = 378                  # S10: knobs read as off
APP = dict(question='Did I leave the stove on?', reply='Checking the kitchen…')
TIMER = dict(at_s=22.70, label='Simmer', minutes=9)
PLANT_NOTE = dict(at_s=18.0, title='Olive tree', body='Last watered 9 days ago')
CALL = dict(name='Grandma', label='Video call via FLOAT')
DISCLOSURE = 'CGI concept. Proposed experience, not prototype footage.'
END_CARD_S = 36.0


def shot(sid):
    return next(s for s in SHOTS if s[0] == sid)


def shot_at(frame):
    for s in SHOTS:
        if s[2] <= frame < s[3]:
            return s
    return SHOTS[-1]


def edl_rows():
    rows = []
    for sid, name, a, b, tod, purpose in SHOTS:
        rows.append(dict(shot=sid, name=name, first_frame=a, last_frame=b - 1, start_s=a / FPS, end_s=b / FPS,
                         beats=(b - a) / BEAT, time_of_day=tod, purpose=purpose))
    return rows
