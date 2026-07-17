import io
import json

import streamlit as st

from groq_layout_generator import generate_layout, AVAILABLE_MODELS
from floorplan_renderer import render_floor_plan
from sample_layout import SAMPLE_LAYOUT

st.set_page_config(page_title="AI Office Interior Designer", layout="wide", page_icon="🏢")

st.title("🏢 AI-Powered Office Interior Layout Designer")
st.caption("Describe your office needs — an open-source LLM on Groq drafts a floor plan, "
           "rendered as an architectural-style 2D drawing.")

# ---------------------------------------------------------------------------
# Sidebar - inputs
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("1. Groq API")
    default_key = st.secrets.get("GROQ_API_KEY", "") if hasattr(st, "secrets") else ""
    api_key = st.text_input("Groq API Key", value=default_key, type="password",
                             help="Get a free key at https://console.groq.com/keys")
    model = st.selectbox("Model", AVAILABLE_MODELS, index=0)

    st.header("2. Room Dimensions")
    room_width = st.number_input("Width (ft)", min_value=10.0, value=40.0, step=1.0)
    room_height = st.number_input("Height (ft)", min_value=10.0, value=30.0, step=1.0)

    st.header("3. Requirements")
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

    generate_clicked = st.button("🚀 Generate Floor Plan", type="primary", use_container_width=True)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "layout" not in st.session_state:
    st.session_state.layout = SAMPLE_LAYOUT
if "error" not in st.session_state:
    st.session_state.error = None

requirements = {
    "room_width": room_width,
    "room_height": room_height,
    "num_workstations": num_workstations,
    "reception": reception,
    "meeting_room": meeting_room,
    "meeting_seats": meeting_seats,
    "meeting_table_shape": meeting_table_shape,
    "lounge": lounge,
    "lounge_sofas": lounge_sofas,
    "restroom": restroom,
    "pantry": pantry,
    "num_cabins": num_cabins,
    "style": style,
}

# ---------------------------------------------------------------------------
# Generate on click
# ---------------------------------------------------------------------------
if generate_clicked:
    if not api_key:
        st.error("Please enter your Groq API key in the sidebar.")
    else:
        with st.spinner("Asking the LLM to design your office layout..."):
            try:
                layout = generate_layout(api_key, requirements, model=model)
                st.session_state.layout = layout
                st.session_state.error = None
            except Exception as e:
                st.session_state.error = str(e)

if st.session_state.error:
    st.error(f"Generation failed: {st.session_state.error}")
    st.info("Tip: try a different model, simplify the requirements, or check your API key, then generate again. "
            "Showing the last valid layout below.")

# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Floor Plan")
    fig = render_floor_plan(st.session_state.layout)
    st.pyplot(fig, use_container_width=True)

    png_buf = io.BytesIO()
    fig.savefig(png_buf, format="png", dpi=200, bbox_inches="tight")
    st.download_button("⬇ Download floor plan (PNG)", data=png_buf.getvalue(),
                        file_name="office_floor_plan.png", mime="image/png")

with col2:
    st.subheader("Layout JSON")
    st.json(st.session_state.layout, expanded=False)
    st.download_button("⬇ Download layout (JSON)",
                        data=json.dumps(st.session_state.layout, indent=2),
                        file_name="office_layout.json", mime="application/json")

    st.divider()
    st.subheader("Edit manually")
    edited = st.text_area("Tweak the JSON and click 'Apply' to re-render without calling the API.",
                           value=json.dumps(st.session_state.layout, indent=2), height=300)
    if st.button("Apply JSON edits"):
        try:
            st.session_state.layout = json.loads(edited)
            st.session_state.error = None
            st.rerun()
        except Exception as e:
            st.error(f"Invalid JSON: {e}")

st.markdown("---")
st.caption("Built with Streamlit + Groq API. This is a conceptual planning tool, not a substitute "
           "for a licensed architect or interior designer.")
