import streamlit as st
import requests
from parameter_config import FAST_API_DEV_URL

# Function for the login page
def login():
    st.title("PDF Extractor Tool :page_with_curl:")
    st.header("Login")
    
    # Initialize session state for login status if it doesn't exist
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'token' not in st.session_state:
        st.session_state.token = None
    if 'first_name' not in st.session_state:
        st.session_state.first_name = None

    # Create a form for user input
    with st.form(key='login_form'):
        username = st.text_input("**Username**", placeholder='Enter your username')
        password = st.text_input("**Password**", type='password', placeholder='Enter your password')
        submit_button = st.form_submit_button("Login")
        
        if submit_button:
            payload = {
                "username": username,
                "password": password
            }

            # Send a POST request to the FastAPI login endpoint
            response = requests.post(f"{FAST_API_DEV_URL}/auth/login/", json=payload)

            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                first_name = data.get("first_name")
                
                st.success("Login successful!")
                st.session_state.logged_in = True  # Update login status
                st.session_state.token = token  # Store the token
                st.session_state.first_name = first_name
                st.rerun()  # Rerun the script to refresh the page
            elif response.status_code == 401:
                st.error("Invalid credentials. Please try again.")
            else:
                st.error("An error occurred while trying to log in.")
