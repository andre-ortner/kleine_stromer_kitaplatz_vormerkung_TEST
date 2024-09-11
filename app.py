import streamlit as st
from streamlit_option_menu import option_menu  # Import option_menu from streamlit-option-menu
from optimization import optimization_page  # Import optimization_page from optimization.py
from settings import settings_page  # Import settings_page from settings.py

# Set up the Streamlit page configuration
st.set_page_config(page_title="Dashboard", layout="wide")

# Add a logo at the top of the sidebar
st.sidebar.image("dks_logo.png", use_column_width=True)

# Sidebar Navigation using option_menu
with st.sidebar:
    selected = option_menu(
        "Hauptmenü", ["Platzvergabe", "Einstellungen"],
        icons=["people", "gear"],
        menu_icon="cast", default_index=0,
        styles={
            "container": {"padding": "5!important", "background-color": "#ffffff"},  # White background
            "icon": {"color": "#000000", "font-size": "20px"},  # Black icons
            "nav-link": {"font-size": "14px", "text-align": "left", "margin": "0px", "color": "#000000"},  # Black text
            "nav-link-selected": {"background-color": "#FF0000", "color": "white"},  # Highlighted selection
            "menu-title": {"color": "black", "font-size": "20px"},  # White menu title
        }
        # black style
        #styles={
        #    "container": {"padding": "5!important", "background-color": "#262730"},
        #    "icon": {"color": "white", "font-size": "20px"},
        #    "nav-link": {"font-size": "14px", "text-align": "left", "margin": "0px", "color": "white"},
        #    "nav-link:hover": {"background-color": "#444444"},
        #    "nav-link-selected": {"background-color": "#FF0000", "color": "white"},
        #}
    )

# Dynamically load the selected page by calling its function
if selected == "Platzvergabe":
    optimization_page()  # Call the optimization page function
elif selected == "Einstellungen":
    settings_page()  # Call the settings page function
