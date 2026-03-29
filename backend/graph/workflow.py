from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple
from typing_extensions import TypedDict

from backend.agents.primary_assistant import agent

logger = logging.getLogger(__name__)


class State(TypedDict, total=False):
    messages: List[Dict[str, Any]]
    user_info: str
    passenger_id: str
    last_flight_id: Any
    last_booking: Any
    interrupt: bool


def run_graph_v4(
    user_input: str,
    config: Dict[str, Any],
    history: List[Dict[str, Any]] | None = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Main workflow executor.
    Returns (messages, updated_state) so app.py can persist
    passenger_id, last_flight_id, last_booking across messages.
    """
    if history is None:
        history = []

    passenger_id = config.get("passenger_id", "") or None
    user_info = config.get("user_info", "Guest User")

    logger.info(
        f"Workflow started | passenger={'GUEST' if not passenger_id else passenger_id}"
    )

    # Build state — include all persistent fields from config
    state: State = {
        "messages": history + [{"role": "user", "content": user_input}],
        "passenger_id": passenger_id,
        "user_info": user_info,
        "last_flight_id": config.get("last_flight_id"),
        "last_booking": config.get("last_booking"),
        "interrupt": False,
    }

    try:
        state = agent(state)
        logger.info("✓ Agent execution successful")
    except Exception as e:
        logger.error(f"Agent failure: {e}")
        state["messages"].append({
            "role": "assistant",
            "content": (
                "I encountered an internal error while processing your request. "
                "Please try again."
            )
        })

    # Trim to last 10 messages
    messages = state.get("messages", [])
    if len(messages) > 10:
        messages = messages[-10:]
        state["messages"] = messages

    # Return messages + full state so app.py can save back
    # passenger_id, last_flight_id, last_booking to st.session_state
    updated_state = {
        "passenger_id": state.get("passenger_id"),
        "last_flight_id": state.get("last_flight_id"),
        "last_booking": state.get("last_booking"),
    }

    logger.info(
        f"Workflow done | passenger={updated_state['passenger_id']} | "
        f"last_flight={updated_state['last_flight_id']} | "
        f"booking={'yes' if updated_state['last_booking'] else 'no'}"
    )

    return messages, updated_state
