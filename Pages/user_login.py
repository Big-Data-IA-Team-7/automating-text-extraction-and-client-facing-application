import streamlit as st
import requests
import pandas as pd
import os
from dotenv import load_dotenv
load_dotenv()

#Fetching the Data 
data_api_url = os.getenv('data_api_url')

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

def filter_questions(level_filter: str = None):
    """
    Filters questions from the session state DataFrame based on the specified level and/or file extension.

    Args:
        level_filter (str, optional): The level to filter questions by. Defaults to None.
        extension_filter (str, optional): The file extension to filter questions by. Defaults to None.

    Returns:
        pd.Series: A pandas Series containing the filtered questions.
    # """
    data_level = pd.Series(dtype='object')
    if level_filter:
        response=requests.get(data_api_url)
        if response.status_code==200:
            data_level=response.json()
            data_level=pd.DataFrame(data_level)
            data_level=data_level[data_level['Level']==level_filter]['Question']
        else:
            data_level=data_level['Question']
    
    return data_level


# Function for the user login page
def user_login():
    # Check if the user is logged in
    if 'logged_in' in st.session_state and st.session_state.logged_in:
        st.title(f"Welcome, {st.session_state.username}!")  # Display the username
    else:
        st.error("You need to log in first.")  # If not logged in, show error
    #Request to get the data
    response=requests.get(data_api_url)
    if response.status_code==200:
        data=response.json()
        data=pd.DataFrame(data)
        # data=data[data['Question']]
        with st.sidebar:
            level_filter = st.selectbox("**Difficulty Level**",
                                        sorted(data['Level'].unique()),
                                        index=None,
                                        on_change=button_reset,
                                        args=("ask_gpt_clicked",)
                                        )
        question_selected = st.selectbox(
                                    "**Select a Question:**", 
                                    options=filter_questions(level_filter) ,
                                    index=None,
                                    on_change=buttons_reset,
                                    args=("ask_gpt_clicked", "ask_again_button_clicked"),
                                )
            
    else:
        st.write(f"Error: {response.status_code} - {response.text}")
    
    #Logout Button
    if st.button("Logout"):
        st.session_state.logged_in = False  # Update login status
        st.session_state.page = 'login'  # Switch to login page
        st.rerun()  # Rerun the script to refresh the page
