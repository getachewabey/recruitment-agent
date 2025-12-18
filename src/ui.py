import streamlit as st

def apply_custom_css():
    """Injects custom CSS based on the selected theme in session state."""
    
    # Default to light if not set
    if "theme" not in st.session_state:
        st.session_state.theme = "light"
        
    theme = st.session_state.theme
    
    # Define colors based on theme
    if theme == "dark":
        # Dark Theme Palette
        bg_color = "#0F172A"       # Slate-900
        sidebar_bg = "#1E293B"     # Slate-800
        text_color = "#F8FAFC"     # Slate-50
        text_sub = "#94A3B8"       # Slate-400
        card_bg = "#1E293B"        # Slate-800
        border_color = "#334155"   # Slate-700
        metric_bg = "#134E4A"      # Teal-900
        metric_border = "#115E59"  # Teal-800
        metric_label = "#2DD4BF"   # Teal-400
        input_bg = "#334155"
        button_bg = "#1E293B"      # Slate-800
        button_item_color = "#2DD4BF" # Teal-400 (Border/Text for secondary)
    else:
        # Light Theme Palette
        bg_color = "#FFFFFF"
        sidebar_bg = "#F8FAFC"     # Slate-50
        text_color = "#0F172A"     # Slate-900
        text_sub = "#64748B"       # Slate-500
        card_bg = "#FFFFFF"
        border_color = "#E2E8F0"   # Slate-200
        metric_bg = "#F0FDFA"      # Teal-50
        metric_border = "#CCFBF1"  # Teal-100
        metric_label = "#14B8A6"   # Teal-500
        input_bg = "#FFFFFF"
        button_bg = "#FFFFFF"
        button_item_color = "#14B8A6" # Teal-500

    # Inject CSS with Variables and Overrides
    st.markdown(f"""
        <style>
        :root {{
            --card-bg: {card_bg};
            --card-border: {border_color};
            --text-main: {text_color};
            --text-sub: {text_sub};
        }}

        /* Force App Background, HTML, Body, Root, and Header */
        html, body, .stApp, #root, [data-testid="stAppViewContainer"], header[data-testid="stHeader"] {{
            background-color: {bg_color} !important;
            color: {text_color} !important;
            transition: background-color 0.2s ease-in-out, color 0.2s ease-in-out;
        }}
        
        /* Force Sidebar Background */
        section[data-testid="stSidebar"] {{
            background-color: {sidebar_bg};
            border-right: 1px solid {border_color};
        }}
        
        /* Text Colors */
        h1, h2, h3, h4, h5, h6, p, li, span, div, label {{
            color: {text_color} !important;
        }}
        
        /* Input Fields */
        .stTextInput input, .stSelectbox div[data-baseweb="select"], .stTextArea textarea {{
            background-color: {input_bg} !important;
            color: {text_color} !important;
            border-color: {border_color} !important;
        }}
        
        /* Buttons - Explicit Override for Contrast */
        div[data-testid="stButton"] > button, div[data-testid="stFormSubmitButton"] > button {{
            background-color: {button_bg} !important;
            color: {button_item_color} !important;
            border: 1px solid {button_item_color} !important;
        }}
        div[data-testid="stButton"] > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {{
            border-color: {text_color} !important;
            color: {text_color} !important;
            background-color: {button_bg} !important; 
        }}
        div[data-testid="stButton"] > button:active, div[data-testid="stFormSubmitButton"] > button:active, div[data-testid="stButton"] > button:focus, div[data-testid="stFormSubmitButton"] > button:focus {{
            color: {text_color} !important;
            background-color: {button_bg} !important;
            border-color: {text_color} !important;
        }}

        
        /* Modern Cards */
        .stCard {{
            background-color: {card_bg};
            padding: 1.5rem;
            border-radius: 0.75rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            border: 1px solid {border_color};
            margin-bottom: 1rem;
        }}
        
        /* Metric Styling */
        div[data-testid="stMetric"] {{
            background-color: {metric_bg};
            padding: 1rem;
            border-radius: 0.5rem;
            border: 1px solid {metric_border};
        }}
        
        div[data-testid="stMetricLabel"] label {{
            color: {metric_label} !important;
        }}
        
        div[data-testid="stMetricValue"] {{
            color: {text_color} !important;
        }}
        
        /* Header Gradients */
        h1 {{
            background: linear-gradient(to right, {text_color}, #14B8A6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: inline-block;
        }}

        </style>
    """, unsafe_allow_html=True)

def display_theme_toggle():
    """Renders a toggle in the sidebar to switch themes."""
    if "theme" not in st.session_state:
        st.session_state.theme = "light"

    # We use a callback to force a rerun immediately upon usage
    def toggle_theme():
        st.session_state.theme = "dark" if st.session_state.toggle_val else "light"

    current = st.session_state.theme == "dark"
    with st.sidebar:
        st.toggle("🌙 Dark Mode", value=current, key="toggle_val", on_change=toggle_theme)

def card_container(key=None):
    """Helper to create a container with card styling"""
    container = st.container()
    container.markdown('<div class="stCard">', unsafe_allow_html=True)
    return container

def close_card():
    st.markdown('</div>', unsafe_allow_html=True)

