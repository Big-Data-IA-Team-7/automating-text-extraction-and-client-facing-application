import streamlit as st
from auth.login import login
from auth.register import register
from auth.logout import logout
from features.pdf_extractor import pdf_extractor

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Define Pages
login_page = st.Page(login, title="Log in", icon=":material/login:")
register_page = st.Page(register, title="Register", icon=":material/person_add:")
logout_page = st.Page(logout, title="Log out", icon=":material/logout:")

pdf_extractor_page = st.Page(
    pdf_extractor, title="PDF Extractor", icon=":material/description:"
)

# Define Navigation
if st.session_state.logged_in:
    pg = st.navigation(
        {
            "Features": [pdf_extractor_page],
            "Account": [logout_page]
        }
    )
else:
    pg = st.navigation([login_page, register_page])

# Set Configurations
st.set_page_config(page_title="My Application", page_icon=":material/lock:")

# Run the selected page
pg.run()
