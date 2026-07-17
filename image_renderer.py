"""
image_renderer.py
-------------------
Turns the JSON office layout + chosen color palette into a natural-language
prompt, then calls OpenAI's image API (gpt-image-1) to generate a
photorealistic interior render. This is a "style/mood" render: it reflects
the right zones, furniture mix, palette, and design style convincingly, but
is not pixel-matched to exact desk positions in the blueprint.

Requires: pip install openai
"""

import base64
from openai import OpenAI

# Small palette of common color names used to translate hex codes into
# words an image model understands well (e.g. "#4C8BF5" -> "blue").
_NAMED_COLORS = {
    "red": (220, 50, 50), "orange": (240, 140, 40), "amber": (245, 175, 40),
    "yellow": (235, 210, 60), "lime": (170, 210, 60), "green": (60, 160, 90),
    "teal": (40, 170, 150), "cyan": (60, 190, 210), "blue": (60, 120, 220),
    "indigo": (80, 80, 200), "purple": (140, 90, 200), "magenta": (200, 70, 170),
    "pink": (230, 130, 170), "brown": (140, 95, 60), "beige": (225, 210, 180),
    "cream": (245, 240, 225), "gray": (140, 140, 140), "charcoal": (55, 55, 60),
    "white": (245, 245, 245), "black": (25, 25, 25),
}


def _nearest_color_name(hex_color: str) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    best_name, best_dist = "neutral", float("inf")
    for name, (nr, ng, nb) in _NAMED_COLORS.items():
        dist = (r - nr) ** 2 + (g - ng) ** 2 + (b - nb) ** 2
        if dist < best_dist:
            best_dist, best_name = dist, name
    return best_name


def _zone_summary(layout: dict) -> dict:
    zones = layout.get("zones", [])
    summary = {
        "workstations": 0, "has_meeting_room": False, "meeting_seats": 0,
        "meeting_shape": "oval", "has_lounge": False, "lounge_seats": 0,
        "has_reception": False, "has_cabins": False, "num_cabins": 0,
    }
    for z in zones:
        t = z.get("type")
        if t == "workstation_cluster":
            summary["workstations"] += int(z.get("rows", 0)) * int(z.get("cols", 0))
        elif t == "meeting_room":
            summary["has_meeting_room"] = True
            summary["meeting_seats"] = int(z.get("seats", 8))
            summary["meeting_shape"] = z.get("table_shape", "oval")
        elif t == "lounge":
            summary["has_lounge"] = True
            summary["lounge_seats"] += int(z.get("seats", 3))
        elif t == "reception":
            summary["has_reception"] = True
        elif t == "cabin":
            summary["has_cabins"] = True
            summary["num_cabins"] += 1
    return summary


def build_prompt(layout: dict, colors: dict, style: str = "Modern minimal", extra_notes: str = "") -> str:
    """Build a descriptive text-to-image prompt from the layout + color theme."""
    s = _zone_summary(layout)

    desk_color = _nearest_color_name(colors.get("workstation", "#4C8BF5"))
    chair_color = _nearest_color_name(colors.get("chair", "#F5A623"))
    table_color = _nearest_color_name(colors.get("meeting_table", "#8E6C46"))
    lounge_color = _nearest_color_name(colors.get("lounge", "#E8735B"))
    floor_color = _nearest_color_name(colors.get("floor", "#F6F1E9"))
    wall_color = _nearest_color_name(colors.get("wall", "#B7B0A6"))

    parts = [
        f"A professional wide-angle interior photograph of a {style.lower()} office space.",
        f"{floor_color.capitalize()} flooring and {wall_color} walls.",
    ]

    if s["workstations"] > 0:
        parts.append(
            f"An open-plan workspace with about {s['workstations']} desks arranged in neat rows, "
            f"{desk_color} desk accents, {chair_color} ergonomic office chairs, dual monitors on each desk."
        )
    if s["has_meeting_room"]:
        parts.append(
            f"A glass-walled conference room with a {s['meeting_shape']} {table_color} meeting table "
            f"seating about {s['meeting_seats']} people."
        )
    if s["has_lounge"]:
        parts.append(f"A cozy lounge/breakout area with {lounge_color} sofas and potted plants.")
    if s["has_reception"]:
        parts.append("A welcoming reception desk near the entrance.")
    if s["has_cabins"]:
        parts.append(f"{s['num_cabins']} enclosed private cabins/offices with glass partitions.")

    parts.append(
        "Bright natural daylight through large windows, clean architectural lines, potted plants for "
        "biophilic design, shot on a 24mm lens, photorealistic, high detail, architectural digest style, "
        "no people, no text, no logos."
    )
    if extra_notes:
        parts.append(extra_notes.strip())

    return " ".join(parts)


def generate_image(api_key: str, prompt: str, size: str = "1024x1024", quality: str = "medium") -> bytes:
    """
    Call OpenAI's image API and return raw PNG bytes.
    size: one of "1024x1024", "1536x1024" (landscape), "1024x1536" (portrait)
    quality: "low" | "medium" | "high"
    """
    client = OpenAI(api_key=api_key)
    result = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size=size,
        quality=quality,
        n=1,
    )
    b64_data = result.data[0].b64_json
    return base64.b64decode(b64_data)
