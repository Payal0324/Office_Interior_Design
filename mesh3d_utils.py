"""
mesh3d_utils.py
----------------
Small generic helpers for building 3D scenes out of extruded polygons
("prisms") - a rectangle prism is a box, an N-gon prism approximates a
cylinder, etc. Vertices/faces are grouped per color so many small pieces of
furniture can be rendered as a handful of Mesh3d traces (fast + easy to
theme).
"""

import numpy as np
import plotly.graph_objects as go


def box_polygon(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def regular_polygon(cx, cy, rx, ry, n=16, rot=0.0):
    pts = []
    for i in range(n):
        a = rot + 2 * np.pi * i / n
        pts.append((cx + rx * np.cos(a), cy + ry * np.sin(a)))
    return pts


class MeshBuffer:
    """Accumulates prism geometry grouped by color, emits one Mesh3d trace per color."""

    def __init__(self):
        self.groups = {}

    def _group(self, color):
        return self.groups.setdefault(color, {"x": [], "y": [], "z": [], "i": [], "j": [], "k": []})

    def add_prism(self, polygon, z0, z1, color):
        g = self._group(color)
        n = len(polygon)
        base = len(g["x"])
        for (px, py) in polygon:
            g["x"].append(px); g["y"].append(py); g["z"].append(z0)
        for (px, py) in polygon:
            g["x"].append(px); g["y"].append(py); g["z"].append(z1)
        for i in range(1, n - 1):
            g["i"].append(base); g["j"].append(base + i); g["k"].append(base + i + 1)
        for i in range(1, n - 1):
            g["i"].append(base + n); g["j"].append(base + n + i + 1); g["k"].append(base + n + i)
        for i in range(n):
            ni = (i + 1) % n
            b0, b1 = base + i, base + ni
            t0, t1 = base + n + i, base + n + ni
            g["i"].append(b0); g["j"].append(b1); g["k"].append(t1)
            g["i"].append(b0); g["j"].append(t1); g["k"].append(t0)

    def add_box(self, x, y, z0, w, h, z1, color):
        self.add_prism(box_polygon(x, y, w, h), z0, z1, color)

    def add_cylinder(self, cx, cy, z0, rx, ry, z1, color, n=14, rot=0.0):
        self.add_prism(regular_polygon(cx, cy, rx, ry, n=n, rot=rot), z0, z1, color)

    def traces(self, opacity=1.0):
        out = []
        for color, g in self.groups.items():
            if not g["x"]:
                continue
            out.append(go.Mesh3d(
                x=g["x"], y=g["y"], z=g["z"],
                i=g["i"], j=g["j"], k=g["k"],
                color=color, opacity=opacity, flatshading=True,
                lighting=dict(ambient=0.55, diffuse=0.85, specular=0.25, roughness=0.6, fresnel=0.1),
                lightposition=dict(x=200, y=400, z=500),
                hoverinfo="skip",
            ))
        return out
