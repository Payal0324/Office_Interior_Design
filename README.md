# AI Office Interior Layout Designer

A Streamlit app that uses an open-source LLM (via the **Groq API**) to design a
customizable office floor plan, and renders it as a 2D architectural-style
drawing (desks with monitors, an oval conference table with chairs, sofas,
plants, reception desk, restroom, storage, cabins) — similar in style to a
hand-drawn floor plan.

## How it works
1. You fill in room dimensions and requirements (workstation count, meeting
   room, lounge, restroom, style, etc.) in the sidebar.
2. `groq_layout_generator.py` sends those requirements to a Groq-hosted model
   (Llama 3.3 70B by default) with a strict JSON schema in the system prompt,
   and parses the model's JSON response into a layout dict.
3. `floorplan_renderer.py` takes that JSON and draws it with matplotlib —
   each zone type (`workstation_cluster`, `meeting_room`, `lounge`,
   `reception`, `restroom`, `storage`, `pantry`, `cabin`) has its own drawing
   function.
4. The app shows the rendered floor plan, the raw JSON (editable + downloadable),
   and a PNG download button.

## Files
```
office_designer/
├── app.py                      # Streamlit UI
├── groq_layout_generator.py    # Groq API call + prompt + JSON parsing
├── floorplan_renderer.py       # matplotlib drawing of the layout
├── sample_layout.py            # default/fallback layout shown on first load
├── requirements.txt
└── .streamlit/
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
  `groq_layout_generator.py` and add a matching drawer function + entry in
  `ZONE_DRAWERS` in `floorplan_renderer.py`.
- **Change furniture look**: each `_draw_*` function in
  `floorplan_renderer.py` uses plain `matplotlib.patches` (rectangles,
  circles, ellipses) — tweak proportions there.
- **Swap models**: any current Groq chat model works; edit
  `AVAILABLE_MODELS` in `groq_layout_generator.py`. Check
  https://console.groq.com/docs/models for the current list, since Groq
  periodically retires older models.
- **Manual tweaks without calling the API**: use the "Edit manually" JSON box
  in the app to hand-edit coordinates and re-render instantly.

## Notes / limitations
- The LLM is asked to keep zones inside the room and non-overlapping, but it's
  not guaranteed to reason about geometry perfectly — the renderer defensively
  clips any zone that goes out of bounds so the drawing never breaks, but you
  may occasionally get slightly imperfect layouts. Use the JSON editor to fix
  small issues by hand.
- This is a conceptual space-planning tool, not a substitute for a licensed
  architect or interior designer for actual construction/renovation.
