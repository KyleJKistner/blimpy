"""FLOAT / Room edit timeline. Pure data shared by render, finishing and score.

24 fps, 120 BPM: one beat is exactly 12 frames, one bar 48 frames. Every cut
lands on a beat. Times are in frames unless a name ends in _s.
"""
FPS = 24
BPM = 120
BEAT = 12
BAR = 48
FRAMES = 720                       # 30.0 s

# id, name, first frame, end frame (exclusive), purpose
SHOTS = [
    ('S01', 'The ask', 0, 72, 'Hook: a mirrored sphere in a sunlit room turns toward a spoken question.'),
    ('S02', 'Listening', 72, 120, 'Product face: lens and amber ring answer "Let me look."'),
    ('S03', 'Spin-up', 120, 144, 'Detail: guarded fan spins up on the beat.'),
    ('S04', 'Set off', 144, 168, 'Detail: low three-quarter as FLOAT sets off; the room curves across the envelope.'),
    ('S05', 'Meet FLOAT', 168, 264, 'Drop: low tracking shot through the sun, title.'),
    ('S06', 'Point of view', 264, 312, "Use case: FLOAT's simulated camera view finds the keys."),
    ('S07', 'Found', 312, 384, 'Payoff: rack focus to the keys; spoken answer.'),
    ('S08', 'On your phone', 384, 432, 'Payoff: simulated phone notification.'),
    ('S09', 'Shift change', 432, 528, 'Differentiator: one unit docks, another lifts off.'),
    ('S10', 'Lift', 528, 576, 'Energy: low angle as the fresh unit rises.'),
    ('S11', 'In the room', 576, 648, 'Thesis line over a backlit beauty shot.'),
    ('S12', 'End card', 648, 720, 'Brand, call to action and concept disclosure.'),
]

# Spoken lines. Start times are design targets; voice.py measures actual
# durations and writes assets/voice/timing.json for captions and the LED.
DIALOGUE = [
    dict(id='ask', who='person', start_s=0.40, text='Float, have you seen my keys?'),
    dict(id='look', who='float', start_s=3.25, text='Let me look.'),
    dict(id='found', who='float', start_s=13.55, text='Found them. They slipped between the cushions.'),
]

# On-screen copy (not dialogue captions). Times in seconds.
TITLES = [
    dict(shot='S05', at_s=7.50, lines=['Meet FLOAT.'], sub='A floating AI companion.'),
    dict(shot='S09', at_s=19.95, lines=['One rests.'], sub=None),
    dict(shot='S09', at_s=20.95, lines=['Another takes over.'], sub=None, add=True),
    dict(shot='S11', at_s=24.25, lines=['Not on a screen.'], sub=None),
    dict(shot='S11', at_s=25.25, lines=['In the room.'], sub=None, add=True),
]

NOTIFICATION = dict(at_s=16.25, app='FLOAT', title='Keys found', body='Sofa, between the seat cushions.')
DISCLOSURE = 'CGI concept. Proposed experience, not prototype footage.'


def shot_at(frame):
    for s in SHOTS:
        if s[2] <= frame < s[3]:
            return s
    return SHOTS[-1]


def edl_rows():
    rows = []
    for sid, name, a, b, purpose in SHOTS:
        rows.append(dict(shot=sid, name=name, first_frame=a, last_frame=b - 1, start_s=a / FPS, end_s=b / FPS,
                         beats=(b - a) / BEAT, purpose=purpose))
    return rows
