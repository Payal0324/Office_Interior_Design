"""
groq_layout_generator.py
-------------------------
Talks to the Groq API (fast open-source LLMs like Llama-3.3-70b, etc.)
and asks it to produce a structured JSON office floor-plan layout based on
the user's requirements.
"""

import json
import re
from groq import Groq

# Models available on Groq that are good at structured JSON output.
# (Check https://console.groq.com/docs/models for the current list -
#  Groq periodically retires/renames models.)
AVAILABLE_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "gemma2-9b-it",
]

SYSTEM_PROMPT = """You are an expert office interior space-planner.
You ALWAYS respond with a single valid JSON object and nothing else -
no markdown fences, no explanations, no comments.

The JSON must follow this exact schema:

{
  "room": {"width": <float, feet>, "height": <float, feet>, "unit": "ft"},
  "zones": [
    {
      "type": "reception" | "workstation_cluster" | "meeting_room" |
              "lounge" | "restroom" | "storage" | "pantry" | "cabin",
      "name": "<short label>",
      "x": <float>, "y": <float>, "width": <float>, "height": <float>,
      "rows": <int, only for workstation_cluster>,
      "cols": <int, only for workstation_cluster>,
      "table_shape": "oval" | "rectangle" | "round",
      "seats": <int, for meeting_room / lounge / reception>,
      "notes": "<optional short note>"
    }
  ],
  "doors": [{"x": <float>, "y": <float>, "wall": "top"|"bottom"|"left"|"right", "width": <float>}],
  "windows": [{"x1": <float>, "y1": <float>, "x2": <float>, "y2": <float>}]
}

Rules:
- x, y is the position of the zone's bottom-left corner in feet, measured from the
  room's bottom-left corner (0,0).
- All zones must fit fully inside the room (0 <= x, x + width <= room.width, same for y/height).
- Zones must not overlap. Leave at least 3 feet of circulation space between zones.
- Match the counts and features the user asked for as closely as possible.
- For workstation_cluster, rows * cols should be >= the requested number of workstations.
- Return ONLY the JSON object, nothing else.
"""


def _build_user_prompt(requirements: dict) -> str:
    lines = [
        f"Room size: {requirements['room_width']} ft (width) x {requirements['room_height']} ft (height).",
        f"Number of workstations needed: {requirements['num_workstations']}.",
        f"Meeting room: {'yes' if requirements['meeting_room'] else 'no'}"
        + (f", seating {requirements['meeting_seats']} people, {requirements['meeting_table_shape']} table."
           if requirements['meeting_room'] else "."),
        f"Reception area: {'yes' if requirements['reception'] else 'no'}.",
        f"Lounge / breakout area: {'yes' if requirements['lounge'] else 'no'}"
        + (f" with {requirements['lounge_sofas']} sofas." if requirements['lounge'] else "."),
        f"Restroom: {'yes' if requirements['restroom'] else 'no'}.",
        f"Pantry: {'yes' if requirements['pantry'] else 'no'}.",
        f"Private cabins/offices: {requirements['num_cabins']}.",
        f"Design style preference: {requirements['style']}.",
        "Design a full, non-overlapping office floor plan that satisfies the above, "
        "in the exact JSON schema you were given.",
    ]
    return "\n".join(lines)


def _extract_json(text: str) -> dict:
    """Models sometimes wrap JSON in ```json fences despite instructions - strip them."""
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in the model's response.")
    return json.loads(match.group(0))


def generate_layout(api_key: str, requirements: dict, model: str = "llama-3.3-70b-versatile") -> dict:
    """Call the Groq API and return a parsed layout dict."""
    client = Groq(api_key=api_key)

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(requirements)},
        ],
        temperature=0.4,
        max_tokens=2000,
    )

    raw = completion.choices[0].message.content
    layout = _extract_json(raw)
    return layout
