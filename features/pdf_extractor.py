import streamlit as st
import requests
import pandas as pd
import os
import json
from dotenv import load_dotenv
from project_logging import logging_module
load_dotenv()

#Fetching the Data 
FAST_API_URL = os.getenv('FAST_API_DEV_URL')

@st.fragment
def download_fragment(file_name: str) -> None:
    """
    A Streamlit fragment that displays a download button for the specified file.

    Args:
        file_name (str): The name of the file to be made available for download.

    Returns:
        None
    """
    st.download_button('Download file', file_name, file_name=file_name, key="download_file_button")

@st.fragment
def gpt_steps(data: pd.DataFrame, question: str, answer: str, model: str, headers) -> None:
    """
    Displays a toggle to provide steps and handles the wrong answer flow if activated.

    Args:
        question (str): The selected question.
        answer (str): The provided answer.
        model (str): The model used for generating responses.
        file (dict): The file details for handling file-based prompts.

    Returns:
        None
    """
    steps_on = st.toggle("**Provide Steps**")
    if steps_on:
        handle_wrong_answer_flow(data, question, answer, model, headers)

def manage_steps_widget() -> None:
    """
    Resets the specified buttons' state to False in the Streamlit session state.

    Args:
        None
    Returns:
        None
    """
    st.session_state["ask_gpt_clicked"] = True
    st.session_state["ask_again_button_clicked"] = False

def button_reset(button: str) -> None:
    """
    Resets the specified button's state to False in the Streamlit session state.

    Args:
        button (str): The key representing the button in the session state.

    Returns:
        None
    """
    st.session_state[button] = False

def buttons_reset(button_1: str, button_2: str) -> None:
    """
    Resets the specified buttons' state to False in the Streamlit session state.

    Args:
        button_1 (str): The key representing the button in the session state.
        button_2 (str): The key representing the button in the session state.
    Returns:
        None
    """
    st.session_state[button_1] = False
    st.session_state[button_2] = False

def button_click(button: str) -> None:
    """
    Sets the specified button's state to True in the Streamlit session state.

    Args:
        button (str): The key representing the button in the session state.

    Returns:
        None
    """
    st.session_state[button] = True

def filter_questions(data: pd.DataFrame, level_filter: str = None):
    """
    Filters questions from the session state DataFrame based on the specified level and/or file extension.

    Args:
        data (pd.DataFrame): The dataframe containing the questions.
        level_filter (str, optional): The level to filter questions by. Defaults to None.

    Returns:
        pd.Series: A pandas Series containing the filtered questions.
    # """
    filtered_questions = data['Question']
    if level_filter:
        filtered_questions = data[data['Level'] == level_filter]['Question']
    
    return filtered_questions

def handle_file_processing(question_selected: str, dataframe: pd.DataFrame, headers) -> None:
    """
    Processes the associated file for the selected question and provides a download option.

    Args:
        question_selected (str): The question for which the associated file needs to be processed.
        dataframe (pd.DataFrame): The DataFrame containing data for the selected question.

    Returns:
        dict: A dictionary containing the details of the downloaded file if successful.
        None: Returns None if no file is associated with the selected question.
    """
    df_json = dataframe.to_dict(orient="records")
    payload = {
        "question": question_selected,
        "df": df_json
    }

    response = requests.get(f"{FAST_API_URL}/fetch-download-url/", json=payload, headers=headers)
    loaded_file = response.json()
    download_fragment(loaded_file["path"])

def handle_wrong_answer_flow(data_frame, question_selected: str, validate_answer: str, model: str, headers) -> None:
    """
    Handles the flow for handling wrong answers by displaying next steps and allowing the option to ask GPT again.

    Args:
        data_frame (pd.DataFrame): The DataFrame containing questions and their associated metadata.
        question_selected (str): The question for which the answer is being validated.
        openai_client (OpenAIClient): The client instance used to interact with the OpenAI API.
        validate_answer (str): The correct answer against which the GPT's response will be validated.
        model (str): The model to be used for generating the response (e.g., "gpt-4").
        loaded_file (dict, optional): The file details dictionary containing 'path' and 'extension' for handling file-based prompts. Defaults to None.

    Returns:
        None: This function does not return a value; it handles the logic of displaying results and updating session state.
    """
    steps = data_frame[data_frame['Question'] == question_selected]
    steps = steps['Annotator Metadata'].iloc[0]
    steps_dict = json.loads(steps)
    steps_text = steps_dict.get('Steps', 'No steps found')

    st.session_state.steps_text = st.text_area(
        '**Steps:**',
        steps_text,
        on_change=manage_steps_widget,
        )

    st.button("Ask GPT Again", on_click=button_click, args=("ask_again_button_clicked",))
    if st.session_state.ask_again_button_clicked:
        payload = {
            "question_selected": question_selected,
            "model": model,
            "annotated_steps": st.session_state.steps_text
        }
        response = requests.get(f"{FAST_API_URL}/fetch-openai-response/", json=payload, headers=headers)

        if response.status_code == 200:
            ann_ai_response = response.text
        else:
            logging_module.log_error(f"Error: {response.status_code} - {response.text}")
        if ann_ai_response:
            "**LLM Response**: " + ann_ai_response
        else:
            "**LLM Response**: No response generated by the LLM"

        if  answer_validation_check(validate_answer,ann_ai_response):
            st.error("Sorry! GPT predicted the wrong answer even after providing steps.")
            insert_model_response(st.session_state.task_id_sel, datetime.now().date(), model, ann_ai_response, 'wrong answer')
        else:
            st.success('GPT predicted the correct answer after the steps were provided.')
            insert_model_response(st.session_state.task_id_sel, datetime.now().date(), model, ann_ai_response, 'correct after steps')

def answer_validation_check(final_answer: str,validation_answer: str) -> bool:
    """
    Checks whether the final answer is present in the validation answer. The check is case-insensitive 
    and handles both numeric and non-numeric answers.

    Args:
        final_answer (str): The answer provided that needs to be validated.
        validation_answer (str): The correct answer against which validation is performed.

    Returns:
        bool: Returns True if the final answer is not present in the validation answer, 
              otherwise returns False.
    """
    final_answer = final_answer.strip().lower()
    validation_answer = validation_answer.strip().lower().replace('`', '')

        # Check if final_answer consists only of numbers
    if final_answer.isdigit():
        # Convert validation_answer to a list of elements split by whitespace
        validation_list = validation_answer.split()
        
        # Check if final_answer exists in the validation_list
        return final_answer not in validation_list
    else:
        # If final_answer is not only numbers, perform the original check
        return final_answer not in validation_answer

# Function for the user login page
def pdf_extractor():

    if "ask_gpt_clicked" not in st.session_state:
        st.session_state.ask_gpt_clicked = False
    if "ask_again_button_clicked" not in st.session_state:
        st.session_state.ask_again_button_clicked = False
    if "steps_text" not in st.session_state:
        st.session_state.steps_text = ""

    headers = {
        "Authorization": f"Bearer {st.session_state.token}"
    }
    #Request to get the data
    response = requests.get(f"{FAST_API_URL}/fetch-questions/", headers=headers)
    if response.status_code == 200:
        data = response.json()
        data = pd.DataFrame(data)

        with st.sidebar:
            level_filter = st.selectbox("**Difficulty Level**",
                                        sorted(data['Level'].unique()),
                                        index=None,
                                        on_change=button_reset,
                                        args=("ask_gpt_clicked",)
                                        )
        question_selected = st.selectbox(
                                    "**Select a Question:**", 
                                    options=filter_questions(data, level_filter) ,
                                    index=None,
                                    on_change=buttons_reset,
                                    args=("ask_gpt_clicked", "ask_again_button_clicked"),
                                )
        model_options = ["GPT-4o", "GPT-4", "GPT-3.5-turbo"]

        if question_selected:
                st.text_area("**Selected Question**:", question_selected)
                validate_answer = data[data['Question'] == question_selected]
                task_id_sel = validate_answer['task_id'].iloc[0]
                validate_answer = validate_answer['final_answer'].iloc[0]
                st.text_input("**Selected Question Answer is:**", validate_answer)

                handle_file_processing(question_selected, data, headers)

                col1, col2 = st.columns(2)

                model_chosen = col1.selectbox("**Model**",
                                            options=model_options,
                                            index=None,
                                            label_visibility="collapsed",
                                            on_change=button_reset,
                                            args=("ask_gpt_clicked",)
                )
                try:
                    col2.button("Ask GPT", on_click=button_click, args=("ask_gpt_clicked",))
                    if st.session_state.ask_gpt_clicked:
                        if not model_chosen:
                            button_reset(st.session_state.ask_gpt_clicked)
                            st.error("Please choose a model")
                        else:
                            payload = {
                                "question_selected": question_selected,
                                "model": model_chosen
                            }
                            response = requests.get(f"{FAST_API_URL}/fetch-openai-response/", json=payload, headers=headers)
                            if response.status_code == 200:
                                ai_response = response.text
                            else:
                                logging_module.log_error(f"Error: {response.status_code} - {response.text}")
                            
                            "**LLM Response:** " + ai_response

                            if  answer_validation_check(validate_answer,ai_response):
                                st.error("Sorry, GPT predicted the wrong answer. Do you need the steps?")
                                gpt_steps(data, question_selected, validate_answer, model_chosen, headers)
                            else:
                                st.success("GPT predicted the correct answer.")
                                insert_model_response(task_id_sel, datetime.now().date(), model_chosen, ai_response, 'correct as-is')
                except Exception as e:
                    logging_module.log_error(f"An error occurred: {str(e)}")
                    "An unexpected error occurred: App is being refreshed..."
                    time.sleep(2)
                    st.rerun()
    else:
        st.write(f"Error: {response.status_code} - {response.text}")
