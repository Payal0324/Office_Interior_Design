import io
import json

import streamlit as st
from google import genai

from groq_layout_generator import generate_layout, AVAILABLE_MODELS
from floorplan_renderer import render_floor_plan
from plan3d_renderer import render_3d_plan
from image_renderer import build_prompt, generate_image
from color_theme import DEFAULT_COLORS, build_colors
from sample_layout import SAMPLE_LAYOUT

st.set_page_config(page_title="AI Office Interior Designer", layout="wide", page_icon="🏢")

# ---------------------------------------------------------------------------
# Global CSS - colorful, card-based, modern look
# ---------------------------------------------------------------------------
st.markdown("""
<style>
.stApp { background: linear-gradient(180deg, #F5F7FF 0%, #FFFFFF 320px); }

.hero {
    background: linear-gradient(120deg, #5B4FE9 0%, #8E6CF0 45%, #2FBF9F 100%);
    border-radius: 20px;
    padding: 28px 32px;
    color: white;
    margin-bottom: 22px;
    box-shadow: 0 10px 30px rgba(91,79,233,0.25);
}
.hero h1 { margin: 0; font-size: 2.0rem; }
.hero p { margin: 6px 0 0 0; opacity: 0.92; font-size: 1.02rem; }

div[data-testid="stMetric"] {
    background: white;
    border-radius: 14px;
    padding: 14px 16px 8px 16px;
    box-shadow: 0 4px 14px rgba(30,30,60,0.08);
    border: 1px solid #EEF0FA;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #FBFAFF 0%, #F1F0FF 100%);
    border-right: 1px solid #E7E4FB;
}

.stTabs [data-baseweb="tab-list"] { gap: 6px; }
.stTabs [data-baseweb="tab"] {
    background-color: #F1F0FF;
    border-radius: 10px 10px 0 0;
    padding: 10px 18px;
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    background-color: #5B4FE9 !important;
    color: white !important;
}

.stButton>button, .stDownloadButton>button {
    border-radius: 10px;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>🏢 AI-Powered Office Interior Layout Designer</h1>
  <p>Describe your office needs — an open-source LLM on Groq drafts the layout,
  then explore it as a colorful 2D blueprint or an interactive 3D space.</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar - inputs
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🔑 Groq API")
    default_key = st.secrets.get("GROQ_API_KEY", "") if hasattr(st, "secrets") else ""
    api_key = st.text_input("Groq API Key", value=default_key, type="password",
                             help="Get a free key at https://console.groq.com/keys")
    model = st.selectbox("Model", AVAILABLE_MODELS, index=0)
    
    st.markdown("### 🎨 Hugging Face API (for photoreal render)")
    default_hf_key = (
    st.secrets.get("HUGGINGFACE_API_KEY", "")
    if hasattr(st, "secrets")
    else ""
    )

    hf_api_key = st.text_input(
    "Hugging Face API Key",
    value=default_hf_key,
    type="password",
    help="Get a free key at https://huggingface.co/settings/tokens"
    )

    st.markdown("### 📐 Room Dimensions")
    c1, c2 = st.columns(2)
    room_width = c1.number_input("Width (ft)", min_value=10.0, value=40.0, step=1.0)
    room_height = c2.number_input("Height (ft)", min_value=10.0, value=30.0, step=1.0)

    st.markdown("### 🧩 Requirements")
    num_workstations = st.slider("Number of workstations", 2, 60, 10)
    reception = st.checkbox("Include reception area", value=True)
    meeting_room = st.checkbox("Include meeting room", value=True)
    meeting_seats = st.slider("Meeting room seats", 4, 16, 8) if meeting_room else 0
    meeting_table_shape = (st.selectbox("Meeting table shape", ["oval", "rectangle", "round"])
                            if meeting_room else "oval")
    lounge = st.checkbox("Include lounge / breakout area", value=True)
    lounge_sofas = st.slider("Number of sofas", 1, 6, 2) if lounge else 0
    restroom = st.checkbox("Include restroom", value=True)
    pantry = st.checkbox("Include pantry", value=False)
    num_cabins = st.slider("Private cabins/offices", 0, 6, 0)
    style = st.selectbox("Design style", ["Modern minimal", "Corporate formal", "Creative/casual", "Industrial"])

    st.markdown("### 🎨 Colors & Style")
    with st.expander("Customize palette", expanded=False):
        cc1, cc2 = st.columns(2)
        col_workstation = cc1.color_picker("Desks", DEFAULT_COLORS["workstation"])
        col_chair = cc2.color_picker("Chairs", DEFAULT_COLORS["chair"])
        col_meeting = cc1.color_picker("Meeting table", DEFAULT_COLORS["meeting_table"])
        col_meeting_chair = cc2.color_picker("Meeting chairs", DEFAULT_COLORS["meeting_chair"])
        col_lounge = cc1.color_picker("Lounge / sofas", DEFAULT_COLORS["lounge"])
        col_reception = cc2.color_picker("Reception", DEFAULT_COLORS["reception"])
        col_cabin = cc1.color_picker("Cabins", DEFAULT_COLORS["cabin"])
        col_floor = cc2.color_picker("Floor", DEFAULT_COLORS["floor"])
        col_wall = cc1.color_picker("Walls", DEFAULT_COLORS["wall"])
        if st.button("Reset colors", use_container_width=True):
            st.rerun()

    generate_clicked = st.button("🚀 Generate Floor Plan", type="primary", use_container_width=True)

colors = build_colors({
    "workstation": col_workstation, "chair": col_chair,
    "meeting_table": col_meeting, "meeting_chair": col_meeting_chair,
    "lounge": col_lounge, "reception": col_reception,
    "cabin": col_cabin, "floor": col_floor, "wall": col_wall,
})

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "layout" not in st.session_state:
    st.session_state.layout = SAMPLE_LAYOUT
if "error" not in st.session_state:
    st.session_state.error = None

requirements = {
    "room_width": room_width, "room_height": room_height,
    "num_workstations": num_workstations, "reception": reception,
    "meeting_room": meeting_room, "meeting_seats": meeting_seats,
    "meeting_table_shape": meeting_table_shape, "lounge": lounge,
    "lounge_sofas": lounge_sofas, "restroom": restroom, "pantry": pantry,
    "num_cabins": num_cabins, "style": style,
}

if generate_clicked:
    if not api_key:
        st.error("Please enter your Groq API key in the sidebar.")
    else:
        with st.spinner("✨ Asking the LLM to design your office layout..."):
            try:
                layout = generate_layout(api_key, requirements, model=model)
                st.session_state.layout = layout
                st.session_state.error = None
            except Exception as e:
                st.session_state.error = str(e)

if st.session_state.error:
    st.error(f"Generation failed: {st.session_state.error}")
    st.info("Tip: try a different model, simplify the requirements, or check your API key. "
            "Showing the last valid layout below.")

layout = st.session_state.layout

# ---------------------------------------------------------------------------
# Summary metric cards
# ---------------------------------------------------------------------------
def _summarize(layout):
    zones = layout.get("zones", [])
    room = layout.get("room", {})
    area = float(room.get("width", 0)) * float(room.get("height", 0))
    desks = sum(int(z.get("rows", 0)) * int(z.get("cols", 0))
                for z in zones if z.get("type") == "workstation_cluster")
    meeting_seats_total = sum(int(z.get("seats", 0)) for z in zones if z.get("type") == "meeting_room")
    lounge_seats_total = sum(int(z.get("seats", 0)) for z in zones if z.get("type") == "lounge")
    return area, desks, meeting_seats_total, lounge_seats_total, len(zones)

area, desks, meet_seats, lounge_seats, zone_count = _summarize(layout)
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("🧮 Total area", f"{area:,.0f} sq ft")
m2.metric("💺 Workstations", desks)
m3.metric("🤝 Meeting seats", meet_seats)
m4.metric("🛋️ Lounge seats", lounge_seats)
m5.metric("🗂️ Zones", zone_count)

st.write("")

# ---------------------------------------------------------------------------
# Tabs: 2D blueprint / 3D view / data
# ---------------------------------------------------------------------------
tab_2d, tab_3d, tab_image, tab_data = st.tabs(
    ["📐 2D Blueprint", "🧊 Interactive 3D View", "📸 Photoreal Render", "🗂️ Data & Export"]
)

with tab_2d:
    fig = render_floor_plan(layout, colors=colors)
    st.pyplot(fig, use_container_width=True)
    png_buf = io.BytesIO()
    fig.savefig(png_buf, format="png", dpi=200, bbox_inches="tight", transparent=True)
    st.download_button("⬇ Download floor plan (PNG)", data=png_buf.getvalue(),
                        file_name="office_floor_plan.png", mime="image/png")

with tab_3d:
    st.caption("🖱️ Drag to rotate · scroll to zoom · shift-drag to pan")
    fig3d = render_3d_plan(layout, colors=colors)
    st.plotly_chart(fig3d, use_container_width=True, config={"displaylogo": False})

with tab_image:
    st.caption("Generates a photorealistic 'mood render' of your office in the chosen style and palette. "
               "It reflects the right zones, furniture mix, and colors — not pixel-exact desk positions.")

    if "photo_bytes" not in st.session_state:
        st.session_state.photo_bytes = None
    if "photo_prompt" not in st.session_state:
        st.session_state.photo_prompt = build_prompt(layout, colors, style=style)

    col_prompt, col_settings = st.columns([3, 1])
    with col_prompt:
        edited_prompt = st.text_area("Prompt (auto-built from your layout — feel free to edit)",
                                      value=st.session_state.photo_prompt, height=160)
    with col_settings:
        img_size = st.selectbox("Aspect", ["1536x1024 (landscape)", "1024x1024 (square)", "1024x1536 (portrait)"])
        size_value = img_size.split(" ")[0]
        img_quality = st.selectbox("Quality", ["medium", "high", "low"])
        regen_prompt = st.button("🔄 Rebuild prompt from current layout", use_container_width=True)

    if regen_prompt:
        st.session_state.photo_prompt = build_prompt(layout, colors, style=style)
        st.rerun()

    generate_photo = st.button("🎨 Generate Photoreal Render", type="primary", use_container_width=True)

    if generate_photo:
        if not openai_api_key:
            st.error("Please enter your OpenAI API key in the sidebar.")
        else:
            with st.spinner("🖌️ Rendering your office... this can take 10-30 seconds"):
                try:
                    img_bytes = generate_image(openai_api_key, edited_prompt,
                                                size=size_value, quality=img_quality)
                    st.session_state.photo_bytes = img_bytes
                    st.session_state.photo_prompt = edited_prompt
                except Exception as e:
                    st.error(f"Image generation failed: {e}")

    if st.session_state.photo_bytes:
        st.image(st.session_state.photo_bytes, use_container_width=True)
        st.download_button("⬇ Download render (PNG)", data=st.session_state.photo_bytes,
                            file_name="office_photoreal_render.png", mime="image/png")
    else:
        st.info("Click **Generate Photoreal Render** to create your first image.")

with tab_data:
    col_json, col_edit = st.columns(2)
    with col_json:
        st.subheader("Layout JSON")
        st.json(layout, expanded=False)
        st.download_button("⬇ Download layout (JSON)",
                            data=json.dumps(layout, indent=2),
                            file_name="office_layout.json", mime="application/json")
    with col_edit:
        st.subheader("Edit manually")
        edited = st.text_area("Tweak the JSON and click 'Apply' to re-render without calling the API.",
                               value=json.dumps(layout, indent=2), height=350)
        if st.button("Apply JSON edits"):
            try:
                st.session_state.layout = json.loads(edited)
                st.session_state.error = None
                st.rerun()
            except Exception as e:
                st.error(f"Invalid JSON: {e}")

st.markdown("---")
st.caption("Built with Streamlit + Groq API + Plotly. This is a conceptual planning tool, "
           "not a substitute for a licensed architect or interior designer.")
