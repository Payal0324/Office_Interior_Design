"""
floorplan_renderer.py
----------------------
Turns the JSON layout produced by the Groq LLM into a 2-D architectural-style
floor plan drawing: colored zone backgrounds, filled furniture (desks,
monitors, chairs, an oval/round/rectangular meeting table, sofas, plants,
restroom fixtures, storage, cabins) with black outlines for a crisp
blueprint-meets-color look. Colors come from color_theme.py so the palette
matches the 3D view.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

from color_theme import DEFAULT_COLORS, lighten

LINE_COLOR = "black"
WALL_WIDTH = 4


def _draw_room_shell(ax, width, height, colors):
    ax.add_patch(patches.Rectangle((0, 0), width, height, fill=True,
                                    facecolor=colors["floor"], edgecolor="none", zorder=0))
    ax.add_patch(patches.Rectangle((0, 0), width, height, fill=False,
                                    edgecolor=LINE_COLOR, linewidth=WALL_WIDTH, zorder=5))


def _draw_zone_bg(ax, x, y, w, h, color):
    ax.add_patch(patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.3",
                                         linewidth=0, facecolor=lighten(color, 0.82), zorder=0.5))


def _draw_desk(ax, x, y, w, h, colors):
    ax.add_patch(patches.Rectangle((x, y), w, h, facecolor=colors["workstation"],
                                    edgecolor=LINE_COLOR, linewidth=1.2, zorder=2))
    mon_w, mon_h = w * 0.5, h * 0.35
    ax.add_patch(patches.Rectangle((x + (w - mon_w) / 2, y + h * 0.15), mon_w, mon_h,
                                    facecolor=colors["monitor"], edgecolor=LINE_COLOR, linewidth=1, zorder=3))
    kb_w, kb_h = w * 0.6, h * 0.15
    ax.add_patch(patches.Rectangle((x + (w - kb_w) / 2, y + h * 0.6), kb_w, kb_h,
                                    facecolor=lighten(colors["monitor"], 0.5), edgecolor=LINE_COLOR,
                                    linewidth=1, zorder=3))
    chair_r = w * 0.22
    ax.add_patch(patches.Circle((x + w / 2, y + h + chair_r + 0.15), chair_r,
                                 facecolor=colors["chair"], edgecolor=LINE_COLOR, linewidth=1, zorder=2))


def _draw_workstation_cluster(ax, x, y, w, h, rows, cols, colors):
    rows = max(1, int(rows))
    cols = max(1, int(cols))
    _draw_zone_bg(ax, x - 0.4, y - 0.4, w + 1.4, h + 0.8, colors["workstation"])
    desk_w = w / cols
    desk_h = (h / rows) * 0.6
    row_gap = (h / rows) * 0.4
    for r in range(rows):
        for c in range(cols):
            dx = x + c * desk_w + desk_w * 0.1
            dy = y + r * (desk_h + row_gap) + row_gap * 0.3
            _draw_desk(ax, dx, dy, desk_w * 0.8, desk_h, colors)
        if r % 2 == 1:
            _draw_plant(ax, x + w + 0.6, y + r * (desk_h + row_gap) + desk_h / 2, colors)


def _draw_plant(ax, x, y, colors, r=0.35):
    for i in range(6):
        angle = i * (np.pi / 3)
        px, py = x + r * np.cos(angle), y + r * np.sin(angle)
        ax.add_patch(patches.Circle((px, py), r * 0.55, facecolor=colors["plant_leaf"],
                                     edgecolor=LINE_COLOR, linewidth=0.8, zorder=3))
    ax.add_patch(patches.Circle((x, y), r * 0.25, facecolor=colors["plant_pot"],
                                 edgecolor=LINE_COLOR, linewidth=0.8, zorder=4))


def _draw_meeting_table(ax, x, y, w, h, shape, seats, colors):
    _draw_zone_bg(ax, x, y, w, h, colors["meeting_table"])
    cx, cy = x + w / 2, y + h / 2
    if shape == "round":
        r = min(w, h) / 2 * 0.8
        ax.add_patch(patches.Circle((cx, cy), r, facecolor=colors["meeting_table"],
                                     edgecolor=LINE_COLOR, linewidth=1.5, zorder=2))
    elif shape == "rectangle":
        ax.add_patch(patches.Rectangle((x + w * 0.15, y + h * 0.15), w * 0.7, h * 0.7,
                                        facecolor=colors["meeting_table"], edgecolor=LINE_COLOR,
                                        linewidth=1.5, zorder=2))
    else:  # oval
        ax.add_patch(patches.Ellipse((cx, cy), w * 0.7, h * 0.85, facecolor=colors["meeting_table"],
                                      edgecolor=LINE_COLOR, linewidth=1.5, zorder=2))

    chair_r = min(w, h) * 0.09
    seats = max(2, int(seats))
    for i in range(seats):
        angle = 2 * np.pi * i / seats
        rx, ry = w * 0.45, h * 0.5
        chx, chy = cx + rx * np.cos(angle), cy + ry * np.sin(angle)
        ax.add_patch(patches.Circle((chx, chy), chair_r, facecolor=colors["meeting_chair"],
                                     edgecolor=LINE_COLOR, linewidth=1, zorder=2))


def _draw_sofa(ax, x, y, w, h, seats, colors):
    _draw_zone_bg(ax, x - 0.4, y - 0.4, w + 0.8, h + 0.8, colors["lounge"])
    ax.add_patch(patches.Rectangle((x, y), w, h, facecolor=colors["lounge"],
                                    edgecolor=LINE_COLOR, linewidth=1.2, zorder=2))
    seats = max(1, int(seats))
    seat_w = w / seats
    for i in range(1, seats):
        ax.plot([x + i * seat_w, x + i * seat_w], [y, y + h], color=LINE_COLOR, linewidth=0.8, zorder=3)


def _draw_reception_desk(ax, x, y, w, h, colors):
    _draw_zone_bg(ax, x - 0.4, y - 0.4, w + 0.8, h + 1.2, colors["reception"])
    ax.add_patch(patches.Rectangle((x, y), w, h, facecolor=colors["reception"],
                                    edgecolor=LINE_COLOR, linewidth=1.2, zorder=2))
    ax.add_patch(patches.Circle((x + w / 2, max(y - 0.6, 0.1)), 0.35,
                                 facecolor=colors["chair"], edgecolor=LINE_COLOR, linewidth=1, zorder=2))


def _draw_restroom(ax, x, y, w, h, colors):
    _draw_zone_bg(ax, x, y, w, h, colors["restroom"])
    ax.add_patch(patches.Rectangle((x, y), w, h, fill=False, edgecolor=LINE_COLOR, linewidth=1.2, zorder=2))
    ax.add_patch(patches.Ellipse((x + w * 0.3, y + h * 0.25), w * 0.35, h * 0.3,
                                  facecolor=lighten(colors["restroom"], 0.4), edgecolor=LINE_COLOR,
                                  linewidth=1, zorder=3))
    ax.add_patch(patches.Rectangle((x + w * 0.55, y + h * 0.55), w * 0.3, h * 0.3,
                                    facecolor=lighten(colors["restroom"], 0.5), edgecolor=LINE_COLOR,
                                    linewidth=1, zorder=3))


def _draw_storage(ax, x, y, w, h, colors):
    _draw_zone_bg(ax, x, y, w, h, colors["storage"])
    ax.add_patch(patches.Rectangle((x, y), w, h, facecolor=lighten(colors["storage"], 0.6),
                                    edgecolor=LINE_COLOR, linewidth=1.2, zorder=2))
    step = h / 4
    for i in range(1, 4):
        ax.plot([x, x + w], [y + i * step, y + i * step], color=LINE_COLOR, linewidth=0.8, zorder=3)


def _draw_cabin(ax, x, y, w, h, colors):
    _draw_zone_bg(ax, x, y, w, h, colors["cabin"])
    ax.add_patch(patches.Rectangle((x, y), w, h, fill=False, edgecolor=LINE_COLOR, linewidth=1.5, zorder=2))
    _draw_desk(ax, x + w * 0.2, y + h * 0.2, w * 0.6, h * 0.4, colors)


def _draw_door(ax, x, y, wall, width=3, colors=None):
    color = colors["floor"] if colors else "white"
    if wall in ("top", "bottom"):
        ax.plot([x, x + width], [y, y], color=color, linewidth=6, zorder=6)
    else:
        ax.plot([x, x], [y, y + width], color=color, linewidth=6, zorder=6)


def _draw_window(ax, x1, y1, x2, y2):
    ax.plot([x1, x2], [y1, y2], color="black", linewidth=6, zorder=6)
    ax.plot([x1, x2], [y1, y2], color="#BEE3F8", linewidth=3, zorder=7)


ZONE_DRAWERS = {
    "reception": lambda ax, z, c: _draw_reception_desk(ax, z["x"], z["y"], z["width"], z["height"], c),
    "workstation_cluster": lambda ax, z, c: _draw_workstation_cluster(
        ax, z["x"], z["y"], z["width"], z["height"], z.get("rows", 2), z.get("cols", 4), c),
    "meeting_room": lambda ax, z, c: _draw_meeting_table(
        ax, z["x"], z["y"], z["width"], z["height"], z.get("table_shape", "oval"), z.get("seats", 8), c),
    "lounge": lambda ax, z, c: _draw_sofa(ax, z["x"], z["y"], z["width"], z["height"], z.get("seats", 3), c),
    "restroom": lambda ax, z, c: _draw_restroom(ax, z["x"], z["y"], z["width"], z["height"], c),
    "storage": lambda ax, z, c: _draw_storage(ax, z["x"], z["y"], z["width"], z["height"], c),
    "pantry": lambda ax, z, c: _draw_storage(ax, z["x"], z["y"], z["width"], z["height"], c),
    "cabin": lambda ax, z, c: _draw_cabin(ax, z["x"], z["y"], z["width"], z["height"], c),
}


def render_floor_plan(layout: dict, colors: dict = None, show_labels: bool = True):
    colors = colors or DEFAULT_COLORS
    room = layout["room"]
    width, height = float(room["width"]), float(room["height"])

    fig, ax = plt.subplots(figsize=(10, max(6, 10 * height / width if width else 10)))
    fig.patch.set_alpha(0)
    _draw_room_shell(ax, width, height, colors)

    for zone in layout.get("zones", []):
        ztype = zone.get("type")
        drawer = ZONE_DRAWERS.get(ztype)
        # Defensively clip each zone so a slightly-off LLM response never breaks the drawing
        zx = max(0.0, min(float(zone.get("x", 0)), width))
        zy = max(0.0, min(float(zone.get("y", 0)), height))
        zw = max(0.5, min(float(zone.get("width", 1)), width - zx))
        zh = max(0.5, min(float(zone.get("height", 1)), height - zy))
        clipped = {**zone, "x": zx, "y": zy, "width": zw, "height": zh}

        if drawer:
            try:
                drawer(ax, clipped, colors)
            except Exception:
                ax.add_patch(patches.Rectangle((zx, zy), zw, zh, fill=False,
                                                edgecolor=LINE_COLOR, linestyle="--"))
        else:
            ax.add_patch(patches.Rectangle((zx, zy), zw, zh, fill=False,
                                            edgecolor=LINE_COLOR, linestyle="--"))

        if show_labels:
            ax.text(zx + zw / 2, zy + zh + 0.35, zone.get("name", zone.get("type", "")),
                     ha="center", va="bottom", fontsize=8.5, color="#333333", zorder=8,
                     fontweight="bold")

    for door in layout.get("doors", []):
        _draw_door(ax, door.get("x", 0), door.get("y", 0), door.get("wall", "bottom"),
                   door.get("width", 3), colors)

    for win in layout.get("windows", []):
        _draw_window(ax, win.get("x1", 0), win.get("y1", 0), win.get("x2", 0), win.get("y2", 0))

    ax.set_xlim(-1, width + 1)
    ax.set_ylim(-1, height + 1)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout()
    return fig
