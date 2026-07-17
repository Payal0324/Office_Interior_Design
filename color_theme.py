"""
color_theme.py
--------------
Central place for the app's color palette. The same colors feed both the
2D blueprint (as fills) and the 3D scene (as material colors), so switching
a color in the sidebar updates both views consistently.
"""

DEFAULT_COLORS = {
    "floor": "#F6F1E9",
    "wall": "#B7B0A6",
    "workstation": "#4C8BF5",   # desks
    "chair": "#F5A623",
    "monitor": "#2B2B2B",
    "meeting_table": "#8E6C46",
    "meeting_chair": "#2FBF9F",
    "lounge": "#E8735B",
    "reception": "#3D5A80",
    "restroom": "#9FB4C7",
    "storage": "#8C8C8C",
    "cabin": "#6C63A6",
    "plant_leaf": "#4C9A5B",
    "plant_pot": "#8A5A3B",
}

ZONE_COLOR_KEY = {
    "workstation_cluster": "workstation",
    "meeting_room": "meeting_table",
    "lounge": "lounge",
    "reception": "reception",
    "restroom": "restroom",
    "storage": "storage",
    "pantry": "storage",
    "cabin": "cabin",
}


def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def lighten(hex_color: str, amount: float = 0.5) -> str:
    """Blend a hex color toward white by `amount` (0-1)."""
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    r = int(r + (255 - r) * amount)
    g = int(g + (255 - g) * amount)
    b = int(b + (255 - b) * amount)
    return f"#{r:02x}{g:02x}{b:02x}"


def build_colors(overrides: dict | None = None) -> dict:
    colors = dict(DEFAULT_COLORS)
    if overrides:
        colors.update({k: v for k, v in overrides.items() if v})
    return colors
