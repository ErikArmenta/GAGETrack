"""
GageTrack Replacement - Streamlit Application
Main entry point for the instrument management system
"""
import streamlit as st
import sys
from pathlib import Path

# Add modules to path
sys.path.append(str(Path(__file__).parent))

from utils.styles import load_css
from modules.dashboard import render_dashboard
from modules.inventory import render_inventory
from modules.calibrations import render_calibrations
from modules.msa import render_msa
from modules.reports import render_reports

# Page configuration
st.set_page_config(
    page_title="GageTrack - Sistema de Gestión de Instrumentos",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
st.markdown(load_css(), unsafe_allow_html=True)

def render_sidebar():
    """Render sidebar with logo and navigation"""
    with st.sidebar:
        # Logo section
        try:
            st.markdown('<div class="logo-container">', unsafe_allow_html=True)
            st.image("EA_2.png", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        except:
            st.markdown('<div class="logo-container">', unsafe_allow_html=True)
            st.markdown("### 🔧 GageTrack")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Navigation
        st.markdown("### 📍 Navegación")
        
        # Store selected page in session state
        if 'current_page' not in st.session_state:
            st.session_state.current_page = "Dashboard"
        
        pages = {
            "📊 Dashboard": "Dashboard",
            "📦 Inventario": "Inventario",
            "🔬 Calibraciones": "Calibraciones",
            "📊 MSA": "MSA",
            "📄 Reportes": "Reportes"
        }
        
        for label, page_name in pages.items():
            if st.button(label, use_container_width=True, 
                        type="primary" if st.session_state.current_page == page_name else "secondary"):
                st.session_state.current_page = page_name
                st.rerun()
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: white; font-size: 0.8rem;'>
            <p><strong>GageTrack v2.0</strong></p>
            <p>Sistema de Gestión de Instrumentos</p>
            <p style='margin-top: 1rem;'>© 2026 - Developed by Master Engineer Erik Armenta</p>
        </div>
        """, unsafe_allow_html=True)

def main():
    """Main application logic"""
    
    # Render sidebar
    render_sidebar()
    
    # Check for URL parameter (for QR code scanning)
    query_params = st.query_params
    if 'id' in query_params:
        instrument_id = query_params['id']
        st.info(f"🔍 Instrumento escaneado: **{instrument_id}**")
        st.session_state.current_page = "Inventario"
    
    # Render selected page
    current_page = st.session_state.current_page
    
    if current_page == "Dashboard":
        render_dashboard()
    elif current_page == "Inventario":
        render_inventory()
    elif current_page == "Calibraciones":
        render_calibrations()
    elif current_page == "MSA":
        render_msa()
    elif current_page == "Reportes":
        render_reports()
    else:
        render_dashboard()

if __name__ == "__main__":
    main()
