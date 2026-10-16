"""Kerala geography for the parchment map, shared by the texture painter (plain Python)
and the Blender scene. Points are (lat, lon); `xy` projects them to Blender metres.

Map scale: 50 m of map per real kilometre, with Colachel at the origin, so the
Colachel diorama (about 1.1 km across) sits on the map at the southern tip.
Coordinates are approximate, traced from modern maps; good enough for a stylised map.
"""
import math

MAP_SCALE = 50.0                 # Blender metres per real km
ORIGIN = (8.17, 77.25)           # Colachel
KM_PER_DEG_LAT = 110.6
KM_PER_DEG_LON = 109.6           # at about 10 degrees N

# The diorama tile (Blender metres) and the depth of the map sheet under it.
TILE = (-700.0, 400.0, -700.0, 420.0)    # x0, x1, y0, y1
MAP_Z = -40.0

# The parchment sheet (Blender metres): x0, x1, y0, y1
SHEET = (-16000.0, 7000.0, -3000.0, 25500.0)

# The 3D map world (map_world.py): x0, x1, y0, y1 in Blender metres
MAP_REGION = (-14000.0, 8000.0, -6000.0, 16000.0)


def xy(lat, lon):
    return ((lon - ORIGIN[1]) * KM_PER_DEG_LON * MAP_SCALE,
            (lat - ORIGIN[0]) * KM_PER_DEG_LAT * MAP_SCALE)


# West coast, north to south, round the tip and up the east coast.
COAST = [
    (12.95, 74.82), (12.60, 74.95), (12.50, 74.99), (12.10, 75.20), (11.87, 75.35), (11.50, 75.60),
    (11.25, 75.77), (10.90, 75.88), (10.77, 75.92), (10.50, 76.02), (10.22, 76.18), (9.97, 76.24),
    (9.70, 76.30), (9.49, 76.32), (9.17, 76.43), (8.88, 76.59), (8.73, 76.70), (8.48, 76.92),
    (8.38, 76.99), (8.24, 77.17), (8.17, 77.25), (8.10, 77.40), (8.08, 77.55), (8.15, 77.70),
    (8.30, 77.90), (8.50, 78.05), (8.80, 78.15), (9.10, 78.40), (9.30, 78.90),
]
# Closes the land polygon well outside the sheet (north-east corner).
LAND_CLOSE = [(9.30, 80.0), (13.5, 80.0), (13.5, 74.82)]

# Western Ghats crest, south to north; the third value scales the height (Palakkad gap is low).
GHATS = [
    (8.28, 77.48, 0.5), (8.55, 77.25, 0.9), (8.75, 77.15, 1.0), (9.10, 77.15, 0.9), (9.45, 77.15, 1.0),
    (9.80, 77.10, 1.1), (10.15, 77.05, 1.3), (10.45, 76.90, 1.0), (10.65, 76.72, 0.35), (10.80, 76.65, 0.3),
    (10.95, 76.70, 0.8), (11.30, 76.65, 1.2), (11.55, 76.20, 1.0), (11.80, 75.95, 0.9), (12.10, 75.75, 0.9),
    (12.50, 75.55, 0.8), (12.95, 75.45, 0.8),
]

# Rivers from the hills to the sea: (name, source, mouth)
RIVERS = [
    ("Neyyar", (8.55, 77.15), (8.32, 77.05)),
    ("Kallada", (8.95, 77.15), (8.95, 76.56)),
    ("Achankovil", (9.10, 77.15), (9.22, 76.44)),
    ("Pamba", (9.40, 77.10), (9.36, 76.38)),
    ("Periyar", (10.00, 77.05), (10.15, 76.20)),
    ("Chalakudy", (10.30, 76.85), (10.20, 76.19)),
    ("Bharathapuzha", (10.80, 76.68), (10.78, 75.93)),
    ("Chaliyar", (11.40, 76.30), (11.17, 75.80)),
    ("Valapattanam", (12.00, 75.75), (11.95, 75.30)),
    ("Thamirabarani", (8.62, 77.30), (8.65, 78.12)),
]

# Backwater lakes: (centre lat, lon, half-length km, half-width km, angle deg)
LAKES = [
    # Vembanad is built as a long backwater in map_world.py
    # Ashtamudi is built as the long Kollam backwater in map_world.py
]


def coast_xy():
    return [xy(a, b) for a, b in COAST]


def land_polygon_xy():
    return [xy(a, b) for a, b in COAST + LAND_CLOSE]


def point_in_poly(x, y, poly):
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi:
            inside = not inside
        j = i
    return inside


def dist_to_polyline(x, y, pts):
    """Distance from (x, y) to a polyline, and the index of the nearest segment."""
    best, best_i = 1e18, 0
    for i in range(len(pts) - 1):
        ax, ay = pts[i]
        bx, by = pts[i + 1]
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy + 1e-12)))
        d = math.hypot(x - (ax + t * dx), y - (ay + t * dy))
        if d < best:
            best, best_i = d, i
    return best, best_i


def ghats_height(x, y, noise=lambda x, y: 0.0):
    """Exaggerated height of the Western Ghats at (x, y) in Blender metres (0 off the hills)."""
    crest = [xy(a, b) for a, b, _ in GHATS]
    d, i = dist_to_polyline(x, y, crest)
    k = GHATS[i][2]
    width = 1500.0
    h = 650.0 * k * math.exp(-(d / width) ** 2) * (0.75 + 0.5 * noise(x, y))
    return h


def coast_detailed(step=60.0):
    """The coast resampled every `step` m with a gentle, repeatable wobble (bays and
    headlands), so the painted sea and the 3D land share exactly the same shoreline."""
    pts = coast_xy()
    out, s_total = [], 0.0
    for i in range(len(pts) - 1):
        (ax, ay), (bx, by) = pts[i], pts[i + 1]
        seg = math.hypot(bx - ax, by - ay)
        nx, ny = -(by - ay) / seg, (bx - ax) / seg
        n = max(1, int(seg / step))
        for k in range(n):
            t = k / n
            s = s_total + seg * t
            wob = 90 * math.sin(s / 900.0) + 45 * math.sin(s / 260.0 + 1.3) + 18 * math.sin(s / 75.0 + 0.4)
            out.append((ax + (bx - ax) * t + nx * wob, ay + (by - ay) * t + ny * wob))
        s_total += seg
    out.append(pts[-1])
    return out


def land_polygon_detailed(step=60.0):
    return coast_detailed(step) + [xy(a, b) for a, b in LAND_CLOSE]


# ------------------------------------------------------------------ Ceylon (S19)
# Ceylon (Sri Lanka) at its real place and size on the same projection, so the map can glide
# from the Kerala tip across the Gulf of Mannar to it. Outline traced from modern maps,
# clockwise from the Jaffna peninsula (lat, lon). Approximate, like the Kerala coast.
CEYLON_COAST = [
    (9.78, 80.00), (9.62, 79.93), (9.40, 80.05), (9.20, 79.98), (9.05, 79.93), (8.95, 79.90),
    (8.80, 79.93), (8.60, 79.93), (8.38, 79.86), (8.20, 79.76), (8.02, 79.82), (7.75, 79.80),
    (7.50, 79.81), (7.21, 79.83), (6.93, 79.84), (6.60, 79.95), (6.40, 80.00), (6.13, 80.10),
    (6.03, 80.22), (5.96, 80.45), (5.92, 80.59), (6.02, 80.80), (6.12, 81.10), (6.35, 81.45),
    (6.65, 81.75), (6.95, 81.85), (7.30, 81.86), (7.70, 81.72), (8.10, 81.48), (8.57, 81.23),
    (8.80, 81.08), (9.10, 80.92), (9.35, 80.75), (9.60, 80.55), (9.83, 80.25),
]
# The central highlands: (lat, lon, height factor). Pidurutalagala, Adam's Peak, the Knuckles,
# the Horton Plains / Haputale scarp.
CEYLON_HILLS = [(6.97, 80.77, 1.0), (6.81, 80.50, 0.85), (7.40, 80.80, 0.7), (6.80, 80.90, 0.8),
                (7.15, 80.55, 0.6)]
COLOMBO = (6.935, 79.845)        # the Dutch fort at Colombo, seat of the governor of Ceylon

# The faceted sea is extended beyond MAP_REGION (as a second mesh on the same lattice, so the
# approved S07-S18 sea is untouched) to cover the S19 camera: x0, x1, y0, y1 in Blender metres.
SEA_EXT = (-14000.0, 33000.0, -16500.0, 10000.0)


def ceylon_xy():
    return [xy(a, b) for a, b in CEYLON_COAST]


def outline_detailed(pts, step=60.0, amp=1.0, closed=True):
    """Any outline resampled every `step` m with the same gentle wobble as coast_detailed."""
    pts = list(pts) + ([pts[0]] if closed else [])
    out, s_total = [], 0.0
    for i in range(len(pts) - 1):
        (ax, ay), (bx, by) = pts[i], pts[i + 1]
        seg = math.hypot(bx - ax, by - ay)
        nx, ny = -(by - ay) / seg, (bx - ax) / seg
        n = max(1, int(seg / step))
        for k in range(n):
            t = k / n
            s = s_total + seg * t
            wob = amp * (90 * math.sin(s / 900.0) + 45 * math.sin(s / 260.0 + 1.3) + 18 * math.sin(s / 75.0 + 0.4))
            out.append((ax + (bx - ax) * t + nx * wob, ay + (by - ay) * t + ny * wob))
        s_total += seg
    if not closed:
        out.append(pts[-1])
    return out
