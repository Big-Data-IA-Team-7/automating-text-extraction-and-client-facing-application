import streamlit as st

def declare_session_state():
    state_keys = [
        "ask_again_button_clicked",
        "steps_text",
        "incorrect_response_clicked",
        "correct_response_clicked",
        "unstructured_ask_gpt_clicked",
        "pymupdf_ask_gpt_clicked",
    ]
    for key in state_keys:
        if key not in st.session_state:
            st.session_state[key] = False if key != "steps_text" else ""

def buttons_reset(*buttons: str) -> None:
    for button in buttons:
        st.session_state[button] = False

def buttons_set(*buttons: str) -> None:
    for button in buttons:
        st.session_state[button] = True

def manage_steps_widget() -> None:
    st.session_state["ask_gpt_clicked"] = True
    st.session_state["ask_again_button_clicked"] = False