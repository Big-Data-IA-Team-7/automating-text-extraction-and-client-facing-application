import streamlit as st
from Pages.login import login
from Pages.Register import register
from Pages.user_login import user_login

# Initialize session state for page tracking
if 'page' not in st.session_state:
    st.session_state.page = 'login'

# Display the appropriate page based on the session state
if st.session_state.page == 'login':
    login()
elif st.session_state.page == 'register':
    register()
elif st.session_state.page == 'login_user':
    user_login()