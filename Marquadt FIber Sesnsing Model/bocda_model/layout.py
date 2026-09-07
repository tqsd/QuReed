"""Presentation-only positions and orthogonal wire routing for the native board."""
from __future__ import annotations
from copy import deepcopy
from heapq import heappop, heappush

WIDTH, HEIGHT = 1380, 840
BLOCK_WIDTH, BLOCK_HEIGHT = 112, 86
POSITIONS = {
    "fm": (28, 170), "laser": (28, 340), "splitter": (160, 340),
    "probe_rf": (292, 50), "probe_eom": (292, 170),
    "pc": (424, 170), "isolator": (556, 170),
    "pump_eom": (292, 340), "edfa": (424, 340), "circulator": (556, 340),
    "fiber1": (688, 340), "fiber2": (820, 340),
    "fiber3": (952, 340), "fiber4": (1084, 340), "termination": (1216, 340),
    "pump_reference": (292, 480), "pd": (556, 600),
    "lia": (820, 600), "scan": (1084, 600), "lo": (424, 700),
}


def tidy_scheme(scheme):
    """Change locations only. Unknown/custom nodes and every physical value survive."""
    from .project import uid
    locations = {uid(key): list(value) for key, value in POSITIONS.items()}
    result = deepcopy(scheme)
    for node in result["devices"]:
        if node["uuid"] in locations:
            node["location"] = locations[node["uuid"]]
    return result


def segment_blocked(a, b, rectangles):
    """Whether an axis-aligned segment enters any rectangle interior."""
    for left, top, right, bottom in rectangles:
        if a[0] == b[0]:
            if left < a[0] < right and max(min(a[1], b[1]), top) < min(max(a[1], b[1]), bottom):
                return True
        elif a[1] == b[1]:
            if top < a[1] < bottom and max(min(a[0], b[0]), left) < min(max(a[0], b[0]), right):
                return True
        else:
            raise ValueError("Wire segments must be orthogonal")
    return False


def route_wire(start, end, rectangles, start_side, end_side, occupied=()):
    """Shortest rectilinear route with bend/overlap penalties and side-aware escape.

    Only the short endpoint stubs enter their own blocks. All interior segments
    avoid padded rectangles. Overlapping user-dragged blocks may leave no route;
    that case falls back to a visible ordinary elbow without changing topology.
    """
    start, end = tuple(start), tuple(end)
    a = (start[0] + (14 if start_side == "right" else -14), start[1])
    b = (end[0] + (14 if end_side == "right" else -14), end[1])
    padded = [(l-6, t-6, r+6, d+6) for l,t,r,d in rectangles]
    xs = sorted({a[0], b[0], 8., float(WIDTH-8),
                 *[v for l,t,r,d in rectangles for v in (l-8, r+8)]})
    ys = sorted({a[1], b[1], 30., float(HEIGHT-12),
                 *[v for l,t,r,d in rectangles for v in (t-12, d+12)]})
    occupied_segments = [(p,q) for points in occupied for p,q in zip(points,points[1:])]
    valid = {(i,j) for i,x in enumerate(xs) for j,y in enumerate(ys)
             if not any(l<x<r and t<y<d for l,t,r,d in padded)}
    origin, target = (xs.index(a[0]),ys.index(a[1])), (xs.index(b[0]),ys.index(b[1]))
    queue = [(0., 0., origin, -1)]
    best = {(origin,-1): 0.}
    previous = {}
    answer = None
    while queue:
        _, cost, point, direction = heappop(queue)
        state = (point,direction)
        if cost != best.get(state): continue
        if point == target:
            answer = state
            break
        i,j = point
        p = (xs[i],ys[j])
        for ni,nj,axis in ((i-1,j,0),(i+1,j,0),(i,j-1,1),(i,j+1,1)):
            other = (ni,nj)
            if other not in valid: continue
            q = (xs[ni],ys[nj])
            if segment_blocked(p,q,padded): continue
            distance = abs(p[0]-q[0])+abs(p[1]-q[1])
            penalty = 22. if direction not in (-1,axis) else 0.
            for u,v in occupied_segments:
                if p[axis^1] == q[axis^1] == u[axis^1] == v[axis^1]:
                    overlap = max(0.,min(max(p[axis],q[axis]),max(u[axis],v[axis]))-
                                      max(min(p[axis],q[axis]),min(u[axis],v[axis])))
                    penalty += 3.*overlap
            score = cost+distance+penalty
            nxt = (other,axis)
            if score < best.get(nxt,float("inf")):
                best[nxt],previous[nxt] = score,state
                heuristic = abs(q[0]-b[0])+abs(q[1]-b[1])
                heappush(queue,(score+heuristic,score,other,axis))
    if answer is None:
        mid = (a[0]+b[0])/2
        return [start,a,(mid,a[1]),(mid,b[1]),b,end]
    points = []
    while True:
        point,_ = answer
        points.append((xs[point[0]],ys[point[1]]))
        if answer not in previous: break
        answer = previous[answer]
    points = [start]+list(reversed(points))+[end]
    compact = []
    for point in points:
        if compact and point == compact[-1]: continue
        while len(compact)>1 and ((compact[-2][0]==compact[-1][0]==point[0]) or
                                  (compact[-2][1]==compact[-1][1]==point[1])):
            compact.pop()
        compact.append(point)
    return compact
