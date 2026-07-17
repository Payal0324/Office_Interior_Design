"""A hand-built sample layout (loosely modeled on the reference floor plan)
used as the default preview before the user generates their own, and as an
offline fallback if the Groq API call fails."""

SAMPLE_LAYOUT = {
    "room": {"width": 40, "height": 30, "unit": "ft"},
    "zones": [
        {"type": "reception", "name": "Reception", "x": 1, "y": 24, "width": 6, "height": 5, "seats": 4},
        {"type": "workstation_cluster", "name": "Open Workspace", "x": 12, "y": 18, "width": 24, "height": 10,
         "rows": 2, "cols": 5},
        {"type": "lounge", "name": "Lounge", "x": 1, "y": 8, "width": 9, "height": 8, "seats": 3},
        {"type": "meeting_room", "name": "Conference Room", "x": 22, "y": 1, "width": 16, "height": 14,
         "table_shape": "oval", "seats": 10},
        {"type": "cabin", "name": "Cabin", "x": 12, "y": 8, "width": 8, "height": 6},
        {"type": "restroom", "name": "Restroom", "x": 1, "y": 1, "width": 5, "height": 5},
        {"type": "storage", "name": "Storage", "x": 7, "y": 1, "width": 4, "height": 5},
    ],
    "doors": [{"x": 15, "y": 0, "wall": "bottom", "width": 3}],
    "windows": [{"x1": 0, "y1": 29.7, "x2": 20, "y2": 29.7},
                {"x1": 39.7, "y1": 5, "x2": 39.7, "y2": 20}],
}
