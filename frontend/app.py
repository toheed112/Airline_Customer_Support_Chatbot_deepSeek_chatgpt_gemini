import sys
import os

# ✅ Fix backend import issue (VERY IMPORTANT)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

import streamlit as st
from backend.graph.workflow import run_graph_v4

# ----------------------------
# Page config
# ----------------------------
st.set_page_config(
    page_title="Swiss Airlines AI Assistant (Demo)",
    page_icon="✈️",
    layout="wide",
)

# ----------------------------
# Session state initialization
# ----------------------------
if "history" not in st.session_state:
    st.session_state.history = []

if "passenger_id" not in st.session_state:
    st.session_state.passenger_id = ""

if "user_info" not in st.session_state:
    st.session_state.user_info = "Guest User"

# ✅ NEW: persist flight context across messages
if "last_flight_id" not in st.session_state:
    st.session_state.last_flight_id = None

if "last_booking" not in st.session_state:
    st.session_state.last_booking = None

# ----------------------------
# Sidebar
# ----------------------------
with st.sidebar:
    st.title("✈️ Swiss Airlines AI")
    st.caption("Prototype Travel Assistant")

    st.divider()
    st.subheader("👤 Demo Identity")

    if st.session_state.passenger_id:
        st.success("Passenger Mode (Demo)")
        st.write(f"**Passenger ID:** `{st.session_state.passenger_id}`")
        st.caption("Bookings enabled (simulated)")
        # ✅ Show last booking if any
        if st.session_state.last_booking:
            b = st.session_state.last_booking
            st.divider()
            st.caption("🎫 Last Booking")
            st.write(f"**Ticket:** `{b.get('ticket_no', 'N/A')}`")
            st.write(f"**Route:** {b.get('route', 'N/A')}")
            st.write(f"**Seat:** {b.get('seat', 'N/A')}")
    else:
        st.info("Guest Mode")
        st.caption("Explore only · No bookings")

    st.divider()
    st.subheader("🔐 Demo Note")
    st.caption(
        "This is a prototype system.\n\n"
        "- Authentication is simulated using Passenger ID\n"
        "- Data comes from a demo database\n"
        "- No real-time airline systems or payments\n"
        "- Booking services are conceptual"
    )

    st.divider()
    st.subheader("🔑 Switch Mode")

    passenger_input = st.text_input(
        "Enter Passenger ID (demo)",
        placeholder="e.g. 000543216",
    )

    if st.button("Apply Passenger ID"):
        st.session_state.passenger_id = passenger_input.strip()
        st.session_state.user_info = (
            f"Passenger {passenger_input}" if passenger_input else "Guest User"
        )
        st.success("Session updated")
        st.rerun()

    # ✅ Clear session button for easy testing
    if st.button("🔄 Reset Session"):
        st.session_state.passenger_id = ""
        st.session_state.user_info = "Guest User"
        st.session_state.history = []
        st.session_state.last_flight_id = None
        st.session_state.last_booking = None
        st.rerun()

# ----------------------------
# Main UI
# ----------------------------
st.title("💬 Swiss Airlines Virtual Assistant")

st.caption(
    "Ask in natural language — flights, hotels, cars, activities, and policies.\n"
    "The assistant understands intent using AI (LLM-first routing)."
)

# ----------------------------
# Chat history
# ----------------------------
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ----------------------------
# User input
# ----------------------------
user_input = st.chat_input("Ask me about flights, hotels, or travel plans...")

if user_input:
    st.session_state.history.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    # ✅ FIXED: pass ALL persistent state into the agent
    config = {
        "passenger_id": st.session_state.passenger_id,
        "user_info": st.session_state.user_info,
        "last_flight_id": st.session_state.last_flight_id,
        "last_booking": st.session_state.last_booking,
    }

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = run_graph_v4(
                user_input=user_input,
                config=config,
                history=st.session_state.history[:-1],
            )

            # ✅ FIXED: run_graph_v4 must return (messages, updated_state)
            # Handle both old format (list) and new format (tuple)
            if isinstance(result, tuple):
                updated_messages, updated_state = result
            else:
                # Legacy: result is just messages list
                updated_messages = result
                updated_state = {}

            assistant_reply = updated_messages[-1]["content"]
            st.markdown(assistant_reply)

    # ✅ FIXED: save state back to session so it persists next message
    st.session_state.history = updated_messages

    if updated_state.get("passenger_id"):
        st.session_state.passenger_id = updated_state["passenger_id"]
        st.session_state.user_info = f"Passenger {updated_state['passenger_id']}"

    if updated_state.get("last_flight_id"):
        st.session_state.last_flight_id = updated_state["last_flight_id"]

    if updated_state.get("last_booking"):
        st.session_state.last_booking = updated_state["last_booking"]

    # ✅ Rerun to update sidebar (shows Passenger Mode, last booking etc.)
    st.rerun()
