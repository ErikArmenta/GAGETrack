"""
Supabase Client - Singleton connection to Supabase
GageTrack - Sistema de Gestión de Instrumentos
"""
import streamlit as st
from supabase import create_client, Client


@st.cache_resource
def get_supabase_client() -> Client:
    """Initialize and cache the Supabase client"""
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        client = create_client(url, key)
        return client
    except Exception as e:
        st.error(f"❌ Error conectando a Supabase: {str(e)}")
        return None
