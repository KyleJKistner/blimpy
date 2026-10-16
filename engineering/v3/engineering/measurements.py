"""Validate real measurements before constructing a local thrust/power map.
No manufacturer-point extrapolation to low thrust; no fabricated measurements.
Run: python -m engineering.measurements path/to/measurements.csv
Required columns: assembly_id,direction,guarded,voltage_v,thrust_g,current_a
"""
from __future__ import annotations
from pathlib import Path
import csv, math, sys
import numpy as np
from scipy.interpolate import LinearNDInterpolator

REQUIRED={'assembly_id','direction','guarded','voltage_v','thrust_g','current_a'}

def read_points(path: str | Path) -> list[dict]:
    with Path(path).open(newline='') as f:
        reader=csv.DictReader(f)
        if not REQUIRED.issubset(reader.fieldnames or []):
            raise ValueError(f'Missing required fields: {sorted(REQUIRED-set(reader.fieldnames or []))}')
        rows=[]
        for line,r in enumerate(reader,2):
            for k in ['voltage_v','thrust_g','current_a']:
                r[k]=float(r[k])
                if not math.isfinite(r[k]) or r[k]<0:raise ValueError(f'Invalid {k} at line {line}')
            if r['voltage_v']<=0: raise ValueError('Supply must be positive')
            if r['direction'] not in ['forward','reverse']:raise ValueError('Direction must be forward or reverse')
            if r['guarded'] not in ['true','false']:raise ValueError('guarded must be true or false')
            rows.append(r)
    if not rows:raise ValueError('No physical measurements present; cannot construct map')
    return rows

class MeasuredMap:
    def __init__(self, rows: list[dict], assembly_id: str, direction: str, guarded: bool=True):
        rows=[r for r in rows if r['assembly_id']==assembly_id and r['direction']==direction
              and r['guarded']==str(guarded).lower()]
        if len(rows)<3:raise ValueError('At least three noncollinear measured points required')
        points=np.array([[r['voltage_v'],r['thrust_g']] for r in rows])
        if np.linalg.matrix_rank(points-points[0])<2:
            raise ValueError('Two-dimensional voltage/thrust coverage is required')
        watts=np.array([r['voltage_v']*r['current_a'] for r in rows])
        self.interpolator=LinearNDInterpolator(points,watts,fill_value=np.nan)

    def watts(self, voltage_v: float, thrust_g: float) -> float:
        y=float(self.interpolator(voltage_v,thrust_g))
        if not math.isfinite(y):raise ValueError('Requested condition outside measured convex hull')
        return y

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('Usage: python -m engineering.measurements FILE.csv')
    rows=read_points(sys.argv[1]);print(f'Validated {len(rows)} rows; inspect fixture/revision before use.')
