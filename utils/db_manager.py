"""
Database Manager - Google Sheets Connection Layer
Handles all CRUD operations for the instrument inventory using gspread
"""
import streamlit as st
import pandas as pd
import gspread
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import json

# Scope for Google Sheets API
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def get_client():
    """Initialize and cache the Google Sheets client"""
    try:
        # Load credentials from Streamlit secrets
        service_account_info = st.secrets["gcp_service_account"]
        
        # Convert AttrDict to standard dict if necessary
        creds_dict = {
            "type": service_account_info["type"],
            "project_id": service_account_info["project_id"],
            "private_key_id": service_account_info["private_key_id"],
            "private_key": service_account_info["private_key"],
            "client_email": service_account_info["client_email"],
            "client_id": service_account_info["client_id"],
            "auth_uri": service_account_info["auth_uri"],
            "token_uri": service_account_info["token_uri"],
            "auth_provider_x509_cert_url": service_account_info["auth_provider_x509_cert_url"],
            "client_x509_cert_url": service_account_info["client_x509_cert_url"],
            "universe_domain": service_account_info.get("universe_domain", "googleapis.com")
        }
        
        # Use google.oauth2.service_account (modern approach)
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Error connecting to Google API: {str(e)}")
        return None

def get_worksheet():
    """Get the specific worksheet for the database"""
    client = get_client()
    if client is None:
        return None
        
    try:
        # Get URL from secrets
        spreadsheet_url = st.secrets["spreadsheet_url"]
        
        # Open spreadsheet by URL
        sh = client.open_by_url(spreadsheet_url)
        
        # Get worksheet by title
        # Note: Previous instructions said to name it "BaseDatos"
        try:
            worksheet = sh.worksheet("BaseDatos")
            return worksheet
        except gspread.WorksheetNotFound:
            st.error("No se encontró la hoja 'BaseDatos'. Por favor verifica el nombre.")
            return None
            
    except Exception as e:
        st.error(f"Error accessing worksheet: {str(e)}")
        return None

@st.cache_data(ttl=60)
def load_data():
    """Load data from Google Sheets with caching (60 seconds TTL)"""
    worksheet = get_worksheet()
    if worksheet is None:
        return pd.DataFrame()
    
    try:
        # Read as DataFrame using gspread-dataframe
        # evaluate_formulas=True gets value instead of formula
        df = get_as_dataframe(worksheet, evaluate_formulas=True, usecols=list(range(15)))
        
        # Drop empty rows (rows where all columns are NaN)
        df = df.dropna(how='all')
        
        # Ensure columns match expected schema (optional but good practice)
        expected_cols = [
            'Id. de Instrumento', 'Estatus', 'Descripción', 'Tipo', 
            'Ubicación de Almacén', 'Ubicación Actual', 'Fecha del última programación', 
            'Próximo vencimiento', 'Frecuencia de calibración', 'Unidades de frecuencia', 
            'Persona responsable', 'Custodio actual', 'N/S del Instrumento', 
            'No. de Contabilidad', 'No.  de Modelo'
        ]
        
        # Filter for expected columns only to avoid index issues
        # (in case gspread reads extra empty columns)
        existing_cols = [c for c in expected_cols if c in df.columns]
        if existing_cols:
            df = df[existing_cols]
        
        # Convert date columns to datetime
        date_columns = ['Fecha del última programación', 'Próximo vencimiento']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

def save_data(df):
    """Save DataFrame back to Google Sheets"""
    worksheet = get_worksheet()
    if worksheet is None:
        return False
    
    try:
        # Ensure date columns are formatted correctly as strings for Sheets
        df_save = df.copy()
        
        # Clear the worksheet properly before writing to avoid leftover rows
        worksheet.clear()
        
        # Write DataFrame
        set_with_dataframe(worksheet, df_save, include_column_header=True)
        
        # Clear cache to reflect changes immediately
        st.cache_data.clear()
        
        return True
    except Exception as e:
        st.error(f"Error saving data: {str(e)}")
        return False

def add_instrument(instrument_data):
    """Add a new instrument to the database"""
    df = load_data()
    
    # Create new row as DataFrame
    new_row = pd.DataFrame([instrument_data])
    
    # Append to existing data
    df = pd.concat([df, new_row], ignore_index=True)
    
    return save_data(df)

def update_instrument(instrument_id, updated_data):
    """Update an existing instrument"""
    df = load_data()
    
    # Find the instrument by ID
    mask = df['Id. de Instrumento'] == instrument_id
    
    if not mask.any():
        st.error(f"Instrument {instrument_id} not found")
        return False
    
    # Update the row
    for key, value in updated_data.items():
        if key in df.columns:
            df.loc[mask, key] = value
    
    return save_data(df)

def delete_instrument(instrument_id):
    """Delete an instrument from the database"""
    df = load_data()
    
    # Remove the row
    df = df[df['Id. de Instrumento'] != instrument_id]
    
    return save_data(df)

def get_instrument_by_id(instrument_id):
    """Retrieve a single instrument by ID"""
    df = load_data()
    
    mask = df['Id. de Instrumento'] == instrument_id
    
    if mask.any():
        return df[mask].iloc[0].to_dict()
    
    return None

def get_kpis():
    """Calculate KPIs for the dashboard"""
    df = load_data()
    
    if df.empty:
        return {
            'total': 0,
            'active': 0,
            'overdue': 0,
            'due_soon': 0,
            'in_use': 0
        }
    
    today = pd.Timestamp.now()
    
    # Total instruments
    total = len(df)
    
    # Active instruments
    # Handle NaN in 'Estatus'
    if 'Estatus' in df.columns:
        active = len(df[df['Estatus'] == 'Active'])
    else:
        active = 0
    
    # Helper to check overdue
    if 'Próximo vencimiento' in df.columns:
        overdue = len(df[df['Próximo vencimiento'] < today])
        
        # Due soon (within 30 days)
        due_soon_date = today + timedelta(days=30)
        due_soon = len(df[(df['Próximo vencimiento'] >= today) & 
                          (df['Próximo vencimiento'] <= due_soon_date)])
    else:
        overdue = 0
        due_soon = 0
    
    # In use (not in storage)
    if 'Ubicación Actual' in df.columns and 'Ubicación de Almacén' in df.columns:
        in_use = len(df[df['Ubicación Actual'] != df['Ubicación de Almacén']])
    else:
        in_use = 0
    
    return {
        'total': total,
        'active': active,
        'overdue': overdue,
        'due_soon': due_soon,
        'in_use': in_use
    }

def get_overdue_instruments():
    """Get list of instruments with overdue calibrations"""
    df = load_data()
    
    if df.empty or 'Próximo vencimiento' not in df.columns:
        return pd.DataFrame()
    
    today = pd.Timestamp.now()
    overdue_df = df[df['Próximo vencimiento'] < today].copy()
    
    # Calculate days overdue
    overdue_df['Días Vencidos'] = (today - overdue_df['Próximo vencimiento']).dt.days
    
    return overdue_df

def generate_next_id():
    """Generate the next instrument ID"""
    df = load_data()
    
    if df.empty or 'Id. de Instrumento' not in df.columns:
        return "2SL0001"
    
    # Extract numeric part from IDs
    ids = df['Id. de Instrumento'].dropna()
    
    if len(ids) == 0:
        return "2SL0001"
    
    # Get the maximum numeric value
    numeric_ids = []
    for id_str in ids:
        try:
            # Extract number from format like "2SL0001"
            # Handle potention non-string values
            id_s = str(id_str)
            if id_s.startswith('2SL'):
                num = int(id_s.replace('2SL', ''))
                numeric_ids.append(num)
        except:
            continue
    
    if numeric_ids:
        next_num = max(numeric_ids) + 1
        return f"2SL{next_num:04d}"
    
    return "2SL0001"
