"""
plan3d_renderer.py
--------------------
Builds an interactive, colorful 3D scene (Plotly Mesh3d) from the same JSON
layout used by the 2D blueprint - desks with monitors, chairs, an oval/round/
rectangular meeting table with chairs, sofas, plants, reception desk,
restroom fixtures, storage, and cabin partitions. The user can freely
rotate/zoom/pan it in the browser.
"""

import numpy as np
import plotly.graph_objects as go

from mesh3d_utils import MeshBuffer, box_polygon, regular_polygon
from color_theme import lighten

DESK_TOP_Z = (0.75, 0.78)
CHAIR_SEAT_Z = (0.45, 0.5)
CHAIR_BACK_Z = (0.5, 1.0)
TABLE_Z = (0.72, 0.78)
SOFA_SEAT_Z = (0.0, 1.1)
SOFA_BACK_Z = (1.1, 2.0)
WALL_HEIGHT = 8.0
WALL_THICKNESS = 0.3


def _add_desk(buf, x, y, w, h, colors):
    buf.add_box(x, y, DESK_TOP_Z[0], w, h, DESK_TOP_Z[1], colors["workstation"])
    # legs
    leg = 0.12
    for lx, ly in [(x, y), (x + w - leg, y), (x, y + h - leg), (x + w - leg, y + h - leg)]:
        buf.add_box(lx, ly, 0, leg, leg, DESK_TOP_Z[0], lighten(colors["workstation"], 0.55))
    mon_w, mon_h = w * 0.45, h * 0.12
    buf.add_box(x + (w - mon_w) / 2, y + h * 0.15, DESK_TOP_Z[1], mon_w, mon_h, DESK_TOP_Z[1] + 0.4,
                colors["monitor"])
    seat_r = min(w, h) * 0.24
    cx, cy = x + w / 2, y + h + seat_r + 0.15
    buf.add_cylinder(cx, cy, CHAIR_SEAT_Z[0], seat_r, seat_r, CHAIR_SEAT_Z[1], colors["chair"], n=10)
    buf.add_box(cx - seat_r * 0.8, cy + seat_r * 0.55, CHAIR_SEAT_Z[1], seat_r * 1.6, seat_r * 0.35,
                CHAIR_BACK_Z[1], colors["chair"])


def _add_workstation_cluster(buf, x, y, w, h, rows, cols, colors):
    rows = max(1, int(rows))
    cols = max(1, int(cols))
    desk_w = w / cols
    desk_h = (h / rows) * 0.6
    row_gap = (h / rows) * 0.4
    for r in range(rows):
        for c in range(cols):
            dx = x + c * desk_w + desk_w * 0.1
            dy = y + r * (desk_h + row_gap) + row_gap * 0.3
            _add_desk(buf, dx, dy, desk_w * 0.8, desk_h, colors)
        if r % 2 == 1:
            _add_plant(buf, x + w + 0.6, y + r * (desk_h + row_gap) + desk_h / 2, colors)


def _add_plant(buf, x, y, colors, scale=1.0):
    r = 0.35 * scale
    buf.add_cylinder(x, y, 0, r * 0.35, r * 0.35, 1.1 * scale, colors["plant_pot"], n=10)
    buf.add_cylinder(x, y, 1.0 * scale, r * 1.15, r * 1.15, 1.7 * scale, colors["plant_leaf"], n=12)
    buf.add_cylinder(x, y, 1.55 * scale, r * 0.75, r * 0.75, 2.15 * scale, colors["plant_leaf"], n=10)


def _add_meeting_table(buf, x, y, w, h, shape, seats, colors):
    cx, cy = x + w / 2, y + h / 2
    if shape == "round":
        r = min(w, h) / 2 * 0.8
        poly = regular_polygon(cx, cy, r, r, n=24)
    elif shape == "rectangle":
        poly = box_polygon(x + w * 0.15, y + h * 0.15, w * 0.7, h * 0.7)
    else:
        poly = regular_polygon(cx, cy, w * 0.35, h * 0.42, n=28)
    buf.add_prism(poly, TABLE_Z[0], TABLE_Z[1], colors["meeting_table"])
    # single central leg/base
    buf.add_cylinder(cx, cy, 0, min(w, h) * 0.06, min(w, h) * 0.06, TABLE_Z[0], lighten(colors["meeting_table"], 0.3))

    seats = max(2, int(seats))
    chair_r = min(w, h) * 0.09
    for i in range(seats):
        angle = 2 * np.pi * i / seats
        rx, ry = w * 0.45, h * 0.5
        chx, chy = cx + rx * np.cos(angle), cy + ry * np.sin(angle)
        buf.add_cylinder(chx, chy, CHAIR_SEAT_Z[0], chair_r, chair_r, CHAIR_SEAT_Z[1], colors["meeting_chair"], n=10)
        back_dx, back_dy = np.cos(angle) * chair_r * 0.8, np.sin(angle) * chair_r * 0.8
        buf.add_box(chx + back_dx - chair_r * 0.6, chy + back_dy - chair_r * 0.6, CHAIR_SEAT_Z[1],
                    chair_r * 1.2, chair_r * 1.2, CHAIR_BACK_Z[1], colors["meeting_chair"])


def _add_sofa(buf, x, y, w, h, seats, colors):
    seats = max(1, int(seats))
    buf.add_box(x, y, SOFA_SEAT_Z[0], w, h, SOFA_SEAT_Z[1], colors["lounge"])
    buf.add_box(x, y, SOFA_SEAT_Z[1], w, h * 0.2, SOFA_BACK_Z[1], lighten(colors["lounge"], 0.15))
    arm_w = w * 0.06
    buf.add_box(x, y, SOFA_SEAT_Z[0], arm_w, h, SOFA_BACK_Z[1] * 0.75, lighten(colors["lounge"], 0.15))
    buf.add_box(x + w - arm_w, y, SOFA_SEAT_Z[0], arm_w, h, SOFA_BACK_Z[1] * 0.75, lighten(colors["lounge"], 0.15))


def _add_reception(buf, x, y, w, h, colors):
    buf.add_box(x, y, 0, w, h, 1.1, colors["reception"])
    buf.add_box(x + w * 0.1, y + h * 0.1, 1.1, w * 0.8, h * 0.15, 1.6, lighten(colors["reception"], 0.3))
    buf.add_cylinder(x + w / 2, max(y - 0.6, 0.1), CHAIR_SEAT_Z[0], 0.35, 0.35, CHAIR_SEAT_Z[1], colors["chair"])


def _add_restroom(buf, x, y, w, h, colors):
    base = colors["restroom"]
    buf.add_cylinder(x + w * 0.25, y + h * 0.22, 0, w * 0.16, h * 0.16, 0.85, lighten(base, 0.4), n=14)
    buf.add_box(x + w * 0.15, y + h * 0.34, 0.6, w * 0.2, h * 0.08, 1.2, lighten(base, 0.4))
    buf.add_box(x + w * 0.55, y + h * 0.55, 0, w * 0.25, h * 0.2, 0.9, lighten(base, 0.5))


def _add_storage(buf, x, y, w, h, colors):
    buf.add_box(x, y, 0, w, h, 6.0, colors["storage"])
    for i in range(1, 4):
        buf.add_box(x - 0.02, y - 0.02, i * 1.5, w + 0.04, h + 0.04, i * 1.5 + 0.05, lighten(colors["storage"], 0.35))


def _add_cabin(buf, x, y, w, h, colors):
    t = 0.15
    wall_col = lighten(colors["cabin"], 0.6)
    buf.add_box(x, y, 0, w, t, WALL_HEIGHT * 0.6, wall_col)
    buf.add_box(x, y, 0, t, h, WALL_HEIGHT * 0.6, wall_col)
    buf.add_box(x, y + h - t, 0, w, t, WALL_HEIGHT * 0.6, wall_col)
    buf.add_box(x + w - t, y, 0, t, h, WALL_HEIGHT * 0.6, wall_col)
    _add_desk(buf, x + w * 0.2, y + h * 0.2, w * 0.55, h * 0.35, colors)


ZONE_BUILDERS = {
    "workstation_cluster": lambda buf, z, c: _add_workstation_cluster(
        buf, z["x"], z["y"], z["width"], z["height"], z.get("rows", 2), z.get("cols", 4), c),
    "meeting_room": lambda buf, z, c: _add_meeting_table(
        buf, z["x"], z["y"], z["width"], z["height"], z.get("table_shape", "oval"), z.get("seats", 8), c),
    "lounge": lambda buf, z, c: _add_sofa(buf, z["x"], z["y"], z["width"], z["height"], z.get("seats", 3), c),
    "reception": lambda buf, z, c: _add_reception(buf, z["x"], z["y"], z["width"], z["height"], c),
    "restroom": lambda buf, z, c: _add_restroom(buf, z["x"], z["y"], z["width"], z["height"], c),
    "storage": lambda buf, z, c: _add_storage(buf, z["x"], z["y"], z["width"], z["height"], c),
    "pantry": lambda buf, z, c: _add_storage(buf, z["x"], z["y"], z["width"], z["height"], c),
    "cabin": lambda buf, z, c: _add_cabin(buf, z["x"], z["y"], z["width"], z["height"], c),
}


def render_3d_plan(layout: dict, colors: dict):
    room = layout["room"]
    width, height = float(room["width"]), float(room["height"])

    buf = MeshBuffer()
    buf.add_box(0, 0, -0.05, width, height, 0, colors["floor"])

    wt = WALL_THICKNESS
    buf.add_box(-wt, -wt, 0, width + 2 * wt, wt, WALL_HEIGHT, colors["wall"])
    buf.add_box(-wt, height, 0, width + 2 * wt, wt, WALL_HEIGHT, colors["wall"])
    buf.add_box(-wt, 0, 0, wt, height, WALL_HEIGHT, colors["wall"])
    buf.add_box(width, 0, 0, wt, height, WALL_HEIGHT, colors["wall"])

    for zone in layout.get("zones", []):
        builder = ZONE_BUILDERS.get(zone.get("type"))
        zx = max(0.0, min(float(zone.get("x", 0)), width))
        zy = max(0.0, min(float(zone.get("y", 0)), height))
        zw = max(0.5, min(float(zone.get("width", 1)), width - zx))
        zh = max(0.5, min(float(zone.get("height", 1)), height - zy))
        clipped = {**zone, "x": zx, "y": zy, "width": zw, "height": zh}
        if builder:
            try:
                builder(buf, clipped, colors)
            except Exception:
                buf.add_box(zx, zy, 0, zw, zh, 0.4, "#cccccc")

    fig = go.Figure(data=buf.traces())
    fig.update_layout(
        scene=dict(
            aspectmode="data",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            camera=dict(eye=dict(x=1.35, y=-1.35, z=1.1)),
            bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=650,
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    return fig
