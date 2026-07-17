# AI Office Interior Layout Designer

A Streamlit app that uses an open-source LLM (via the **Groq API**) to design
a customizable office floor plan, with:
- a **colorful 2D blueprint** (matplotlib) — filled zones/furniture, not just line art
- an **interactive 3D view** (Plotly) you can rotate, zoom, and pan in the browser
- a **customizable color palette** — pick colors for desks, chairs, meeting
  table, lounge, reception, cabins, floor, and walls; the same palette drives
  both the 2D and 3D views
- summary metric cards (total area, workstation count, seating capacity, zone count)

## How it works
1. Fill in room dimensions and requirements in the sidebar (workstation count,
   meeting room, lounge, restroom, cabins, style, colors).
2. `groq_layout_generator.py` sends those requirements to a Groq-hosted model
   (Llama 3.3 70B by default) with a strict JSON schema in the system prompt,
   and parses the model's JSON response into a layout dict.
3. `floorplan_renderer.py` draws the 2D colored blueprint with matplotlib.
4. `plan3d_renderer.py` builds an interactive 3D scene with Plotly — every
   piece of furniture (desks, monitors, chairs, tables, sofas, plants,
   reception desk, restroom fixtures, storage, cabin partitions, walls) is
   built from simple extruded-polygon "prisms" (see `mesh3d_utils.py`),
   grouped by color for fast rendering.
5. The app shows all of this across three tabs: 2D Blueprint, Interactive 3D
   View, and Data & Export (JSON view/edit/download).

## Files
```
office_designer/
├── app.py                      # Streamlit UI (colorful theme, tabs, metrics)
├── groq_layout_generator.py    # Groq API call + prompt + JSON parsing
├── floorplan_renderer.py       # matplotlib 2D colored blueprint
├── plan3d_renderer.py          # Plotly interactive 3D scene
├── mesh3d_utils.py             # generic prism/box mesh-building helpers
├── color_theme.py              # shared color palette (feeds 2D + 3D)
├── sample_layout.py            # default/fallback layout shown on first load
├── requirements.txt
└── .streamlit/
    ├── config.toml             # Streamlit color theme
    └── secrets.toml.example    # copy to secrets.toml for local dev
```

## 1. Get a Groq API key
Sign up at https://console.groq.com/keys and create a free API key.

## 2. Run locally
```bash
cd office_designer
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Option A: paste the key into the app's sidebar text field each run
streamlit run app.py

# Option B: store it so it's pre-filled automatically
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# edit .streamlit/secrets.toml and paste your real key
streamlit run app.py
```
The app opens at http://localhost:8501.

## 3. Deploy on Streamlit Community Cloud
1. Push this folder to a GitHub repo (public or private).
2. Go to https://share.streamlit.io → "New app" → pick the repo/branch and
   set **Main file path** to `app.py`.
3. In **App settings → Secrets**, add:
   ```toml
   GROQ_API_KEY = "gsk_your_real_key"
   ```
4. Deploy. The key will be pre-filled in the sidebar via `st.secrets`, but
   users can still override it with their own key if you keep the app public.

## Customizing further
- **Change the schema / add zone types**: edit the `SYSTEM_PROMPT` in
  `groq_layout_generator.py`, then add matching drawer functions in
  `floorplan_renderer.py` (`ZONE_DRAWERS`) **and** `plan3d_renderer.py`
  (`ZONE_BUILDERS`) so both views stay in sync.
- **Change furniture look (2D)**: each `_draw_*` function in
  `floorplan_renderer.py` uses plain `matplotlib.patches`.
- **Change furniture look (3D)**: each `_add_*` function in
  `plan3d_renderer.py` composes boxes/cylinders via `MeshBuffer` from
  `mesh3d_utils.py` — e.g. `buf.add_box(x, y, z0, w, h, z1, color)` or
  `buf.add_cylinder(cx, cy, z0, rx, ry, z1, color)`.
- **Change the default palette**: edit `DEFAULT_COLORS` in `color_theme.py`.
  Anything a user picks in the sidebar overrides these at runtime.
- **Swap models**: any current Groq chat model works; edit
  `AVAILABLE_MODELS` in `groq_layout_generator.py`. Check
  https://console.groq.com/docs/models for the current list, since Groq
  periodically retires older models.
- **Manual tweaks without calling the API**: use the "Edit manually" JSON box
  in the Data & Export tab to hand-edit coordinates and re-render instantly.

## Notes / limitations
- The LLM is asked to keep zones inside the room and non-overlapping, but it's
  not guaranteed to reason about geometry perfectly — both renderers
  defensively clip any zone that goes out of bounds so drawings never break,
  but you may occasionally get slightly imperfect layouts. Use the JSON
  editor to fix small issues by hand.
- The 3D view currently draws continuous walls (no door cutouts) for
  simplicity; door markers still show on the 2D blueprint.
- This is a conceptual space-planning tool, not a substitute for a licensed
  architect or interior designer for actual construction/renovation.
