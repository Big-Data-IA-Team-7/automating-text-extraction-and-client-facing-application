import streamlit as st
import os
import json
from utils.session_helpers import declare_session_state, buttons_reset, buttons_set
from utils.api_helpers import fetch_questions, fetch_download_url, fetch_openai_response
from utils.validators import answer_validation_check, extract_json_contents, extract_txt_contents, num_tokens_from_string
from project_logging import logging_module
import time
from parameter_config import FAST_API_DEV_URL

@st.fragment
def download_fragment(file_name: str) -> None:
    st.download_button('**Download File**', file_name, file_name=file_name, key="download_file_button")

@st.fragment
def gpt_steps(data, question, answer, model, headers, question_contents):
    steps_on = st.toggle("**Provide Steps**")
    if steps_on:
        handle_wrong_answer_flow(data, question, answer, model, headers, question_contents)

@st.fragment
def user_validation_buttons(data, question_selected, validate_answer, model_chosen, headers, ai_response, question_contents):
    wrong_col, correct_col = st.columns(2)
                    
    wrong_col.button("**Incorrect Response**", on_click=buttons_set, args=("incorrect_response_clicked",))
    correct_col.button("**Correct Response**", on_click=buttons_set, args=("correct_response_clicked",))

    if st.session_state.incorrect_response_clicked:
        gpt_steps(data, question_selected, validate_answer, model_chosen, headers, question_contents)
    elif st.session_state.correct_response_clicked:
        # Handle insert into db here
        pass
        
def handle_file_processing(question_selected, dataframe, headers):
    loaded_file = fetch_download_url(FAST_API_DEV_URL, question_selected, dataframe, headers)
    if loaded_file:
        download_fragment(loaded_file["path"])
        os.remove(loaded_file["path"])

def handle_wrong_answer_flow(data_frame, question_selected, validate_answer, model, headers, question_contents):
    steps = data_frame[data_frame['Question'] == question_selected]['Annotator_Metadata'].iloc[0]
    steps_dict = json.loads(steps)
    steps_text = steps_dict.get('Steps', 'No steps found')

    st.session_state.steps_text = st.text_area(
        '**Steps:**',
        steps_text,
        on_change=lambda: buttons_set("unstructured_ask_gpt_clicked", "pymupdf_ask_gpt_clicked")
    )

    st.button("**Ask GPT Again**", on_click=buttons_set, args=("ask_again_button_clicked",))
    if st.session_state.ask_again_button_clicked:
        payload = {
            "question_selected": question_contents,
            "model": model,
            "annotated_steps": st.session_state.steps_text,
        }
        ann_ai_response = fetch_openai_response(FAST_API_DEV_URL, payload, headers)

        if ann_ai_response:
            st.write(f"**LLM Response**: {ann_ai_response}")
        else:
            st.write("**LLM Response**: No response generated by the LLM")

        answer_check = answer_validation_check(ann_ai_response, validate_answer)
        if answer_check == 1:
            st.error("Sorry! GPT predicted the wrong answer even after providing steps.")
        elif answer_check == 2:
            st.success("GPT predicted the correct answer after the steps were provided.")
            # Insert into db the response performance here

def pdf_extractor():
    
    declare_session_state()

    st.title(f":wave: Hello, {st.session_state.first_name}")

    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    data = fetch_questions(FAST_API_DEV_URL, headers)

    if data is not None:
        with st.sidebar:
            level_filter = st.selectbox(
                "**Difficulty Level**",
                sorted(data['Level'].unique()),
                index=None,
                on_change=buttons_reset,
                args=("unstructured_ask_gpt_clicked", "pymupdf_ask_gpt_clicked", "ask_again_button_clicked")
            )

        question_selected = st.selectbox(
            "**Select a Question:**",
            options=data[data['Level'] == level_filter]['Question'] if level_filter else data['Question'],
            index=None,
            on_change=buttons_reset,
            args=("unstructured_ask_gpt_clicked", "pymupdf_ask_gpt_clicked", "ask_again_button_clicked")
        )

        model_options = ["GPT-4o", "GPT-4", "GPT-3.5-turbo"]

        if question_selected:
            try:
                st.text_area("**Selected Question**:", question_selected)
                validate_answer = data[data['Question'] == question_selected]['final_answer'].iloc[0]
                if validate_answer == '?':
                    st.write("**No answer provided for this question**")
                    validate_answer = None
                else:
                    st.text_input("**Selected Question Answer is:**", validate_answer)

                handle_file_processing(question_selected, data, headers)

                model_chosen = st.selectbox("**Model**",
                                            options=model_options,
                                            on_change=buttons_reset,
                                            args=("unstructured_ask_gpt_clicked", "pymupdf_ask_gpt_clicked")
                                        )
                
                unstructured_col, pymupdf_col = st.columns(2)
                
                unstructured_col.button("**Ask GPT - Extraction Using Unstructured**",
                                        on_click=buttons_set,
                                        args=("unstructured_ask_gpt_clicked",))
                pymupdf_col.button("**Ask GPT - Extraction Using PyMuPDF**",
                                on_click=buttons_set,
                                args=("pymupdf_ask_gpt_clicked",))

                if st.session_state.unstructured_ask_gpt_clicked or st.session_state.pymupdf_ask_gpt_clicked:
                    
                    buttons_reset("incorrect_response_clicked", "correct_response_clicked")

                    if st.session_state.unstructured_ask_gpt_clicked:
                        loaded_file = fetch_download_url(FAST_API_DEV_URL, question_selected, data, headers, 'U')
                        file_contents = extract_json_contents(loaded_file["path"])
                    else:
                        loaded_file = fetch_download_url(FAST_API_DEV_URL, question_selected, data, headers, 'P')
                        file_contents = extract_txt_contents(loaded_file["path"])
                    
                    question_contents = question_selected + 'Context:```' + file_contents + "```"

                    num_tokens = num_tokens_from_string(question_contents, model_chosen.lower())
                    
                    if num_tokens > 60000:
                        payload = {
                            "question_selected": question_selected,
                            "model": model_chosen,
                            "file_extract": True,
                            "loaded_file": loaded_file
                        }
                    else:
                        payload = {
                            "question_selected": question_contents,
                            "model": model_chosen
                        }
                    
                    ai_response = fetch_openai_response(FAST_API_DEV_URL, payload, headers)
                    os.remove(loaded_file["path"])

                    if ai_response:
                        st.write(f"**LLM Response:** {ai_response}")
                        answer_check = answer_validation_check(ai_response, validate_answer)
                        if answer_check == 1:
                            st.error("Sorry, GPT predicted the wrong answer. Do you need the steps?")
                        elif answer_check == 2:
                            st.success("GPT predicted the correct answer.")
                        user_validation_buttons(data, question_selected, validate_answer, 
                                                model_chosen, headers, ai_response, question_contents)
            except Exception as e:
                logging_module.log_error(f"An error occurred: {str(e)}")
                "An unexpected error occurred: App is being refreshed..."
                time.sleep(2)
                st.rerun()