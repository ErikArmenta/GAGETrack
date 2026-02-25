"""
Database Manager - Supabase Connection Layer
Handles all CRUD operations for GageTrack
Migrated from Google Sheets to Supabase PostgreSQL
"""
from __future__ import annotations
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.supabase_client import get_supabase_client

# ─────────────────────────────────────────────
# INSTRUMENTS
# ─────────────────────────────────────────────

@st.cache_data(ttl=60)
def load_data() -> pd.DataFrame:
    """Load all instruments from Supabase with last calibration status"""
    supabase = get_supabase_client()
    if supabase is None:
        return pd.DataFrame()

    try:
        # Instruments
        resp = supabase.table("gt_instruments").select("*").order("gage_id").execute()
        if not resp.data:
            return pd.DataFrame()

        df = pd.DataFrame(resp.data)

        # Last calibration join
        cal_resp = supabase.table("gt_last_calibration").select("*").execute()
        if cal_resp.data:
            cal_df = pd.DataFrame(cal_resp.data)
            # Rename to avoid collision
            cal_df = cal_df.rename(columns={
                "calibration_date": "last_cal_date",
                "next_calibration_date": "cal_next_date",
                "result": "cal_result",
            })
            df = df.merge(
                cal_df[["instrument_id", "last_cal_date", "cal_next_date", "cal_result"]],
                left_on="id", right_on="instrument_id", how="left"
            )

        # Rename columns to standard names used throughout the app
        col_map = {
            "gage_id":                  "Id. de Instrumento",
            "status":                   "Estatus",
            "description":              "Descripción",
            "type":                     "Tipo",
            "storage_location":         "Ubicación de Almacén",
            "current_location":         "Ubicación Actual",
            "last_calibration_date":    "Fecha del última programación",
            "next_calibration_date":    "Próximo vencimiento",
            "calibration_frequency":    "Frecuencia de calibración",
            "frequency_unit":           "Unidades de frecuencia",
            "responsible_person":       "Persona responsable",
            "current_custodian":        "Custodio actual",
            "serial_number":            "N/S del Instrumento",
            "accounting_number":        "No. de Contabilidad",
            "model_number":             "No.  de Modelo",
            "cal_result":               "Calibrado",
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

        # Parse dates
        for col in ["Fecha del última programación", "Próximo vencimiento"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        return df

    except Exception as e:
        st.error(f"Error cargando datos: {str(e)}")
        return pd.DataFrame()


def add_instrument(instrument_data: dict) -> bool:
    """Add a new instrument to Supabase"""
    supabase = get_supabase_client()
    if supabase is None:
        return False

    try:
        row = _map_to_db(instrument_data)
        supabase.table("gt_instruments").insert(row).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error al agregar instrumento: {str(e)}")
        return False


def update_instrument(instrument_id: str, updated_data: dict) -> bool:
    """Update an existing instrument by gage_id"""
    supabase = get_supabase_client()
    if supabase is None:
        return False

    try:
        row = _map_to_db(updated_data)
        supabase.table("gt_instruments").update(row).eq("gage_id", instrument_id).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error al actualizar instrumento: {str(e)}")
        return False


def delete_instrument(instrument_id: str) -> bool:
    """Delete an instrument by gage_id"""
    supabase = get_supabase_client()
    if supabase is None:
        return False

    try:
        supabase.table("gt_instruments").delete().eq("gage_id", instrument_id).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error al eliminar instrumento: {str(e)}")
        return False


def get_instrument_by_id(instrument_id: str) -> dict | None:
    """Get a single instrument by gage_id"""
    supabase = get_supabase_client()
    if supabase is None:
        return None

    try:
        resp = supabase.table("gt_instruments").select("*").eq("gage_id", instrument_id).single().execute()
        return resp.data
    except Exception:
        return None


def get_instrument_uuid(gage_id: str) -> str | None:
    """Get the UUID of an instrument by gage_id"""
    supabase = get_supabase_client()
    if supabase is None:
        return None
    try:
        resp = supabase.table("gt_instruments").select("id").eq("gage_id", gage_id).single().execute()
        return resp.data["id"] if resp.data else None
    except Exception:
        return None


def generate_next_id() -> str:
    """Generate the next sequential gage ID"""
    supabase = get_supabase_client()
    if supabase is None:
        return "2SL0001"

    try:
        resp = supabase.table("gt_instruments").select("gage_id").execute()
        if not resp.data:
            return "2SL0001"

        numeric_ids = []
        for row in resp.data:
            gid = str(row.get("gage_id", ""))
            if gid.startswith("2SL"):
                try:
                    numeric_ids.append(int(gid.replace("2SL", "")))
                except ValueError:
                    pass

        return f"2SL{max(numeric_ids) + 1:04d}" if numeric_ids else "2SL0001"
    except Exception:
        return "2SL0001"


# ─────────────────────────────────────────────
# KPIs
# ─────────────────────────────────────────────

def get_kpis() -> dict:
    """Calculate KPIs from Supabase data"""
    df = load_data()
    if df.empty:
        return {"total": 0, "active": 0, "overdue": 0, "due_soon": 0, "in_use": 0, "calibrated": 0}

    today = pd.Timestamp.now()

    total = len(df)
    active = len(df[df.get("Estatus", pd.Series()).eq("Active")]) if "Estatus" in df.columns else 0

    if "Próximo vencimiento" in df.columns:
        overdue = len(df[df["Próximo vencimiento"] < today])
        due_soon_date = today + timedelta(days=30)
        due_soon = len(df[
            (df["Próximo vencimiento"] >= today) &
            (df["Próximo vencimiento"] <= due_soon_date)
        ])
    else:
        overdue = due_soon = 0

    if "Ubicación Actual" in df.columns and "Ubicación de Almacén" in df.columns:
        in_use = len(df[df["Ubicación Actual"] != df["Ubicación de Almacén"]])
    else:
        in_use = 0

    calibrated = len(df[df.get("Calibrado", pd.Series()).eq("Aprobado")]) if "Calibrado" in df.columns else 0

    return {
        "total": total, "active": active, "overdue": overdue,
        "due_soon": due_soon, "in_use": in_use, "calibrated": calibrated
    }


def get_overdue_instruments() -> pd.DataFrame:
    """Get instruments with overdue calibrations"""
    df = load_data()
    if df.empty or "Próximo vencimiento" not in df.columns:
        return pd.DataFrame()

    today = pd.Timestamp.now()
    overdue_df = df[df["Próximo vencimiento"] < today].copy()
    overdue_df["Días Vencidos"] = (today - overdue_df["Próximo vencimiento"]).dt.days
    return overdue_df


# ─────────────────────────────────────────────
# CALIBRATIONS
# ─────────────────────────────────────────────

def get_calibrations(gage_id: str = None) -> pd.DataFrame:
    """Get calibrations, optionally filtered by gage_id"""
    supabase = get_supabase_client()
    if supabase is None:
        return pd.DataFrame()

    try:
        query = supabase.table("gt_calibrations").select("*").order("calibration_date", desc=True)
        if gage_id:
            query = query.eq("gage_id", gage_id)
        resp = query.execute()
        return pd.DataFrame(resp.data) if resp.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error cargando calibraciones: {str(e)}")
        return pd.DataFrame()


def add_calibration(calibration_data: dict) -> bool:
    """Add a new calibration record"""
    supabase = get_supabase_client()
    if supabase is None:
        return False

    try:
        supabase.table("gt_calibrations").insert(calibration_data).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error al guardar calibración: {str(e)}")
        return False


def delete_calibration(cal_id: str) -> bool:
    """Delete a calibration by UUID"""
    supabase = get_supabase_client()
    if supabase is None:
        return False
    try:
        supabase.table("gt_calibrations").delete().eq("id", cal_id).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error al eliminar calibración: {str(e)}")
        return False


def update_calibration_db(cal_id: str, updated_data: dict) -> bool:
    """Update an existing calibration record in Supabase"""
    supabase = get_supabase_client()
    if supabase is None:
        return False
    try:
        # Limpiamos el dict para no enviar el ID en el cuerpo del update
        data_to_send = {k: v for k, v in updated_data.items() if k != 'id'}

        supabase.table("gt_calibrations").update(data_to_send).eq("id", cal_id).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error al actualizar calibración: {str(e)}")
        return False


# ─────────────────────────────────────────────
# MSA STUDIES
# ─────────────────────────────────────────────

def get_msa_studies(gage_id: str = None, study_type: str = None) -> pd.DataFrame:
    """Get MSA studies with optional filters"""
    supabase = get_supabase_client()
    if supabase is None:
        return pd.DataFrame()
    try:
        query = supabase.table("gt_msa_studies").select("*").order("created_at", desc=True)
        if gage_id:
            query = query.eq("gage_id", gage_id)
        if study_type:
            query = query.eq("study_type", study_type)
        resp = query.execute()
        return pd.DataFrame(resp.data) if resp.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error cargando estudios MSA: {str(e)}")
        return pd.DataFrame()


def create_msa_study(study_data: dict) -> str | None:
    """Create a new MSA study, returns its UUID"""
    supabase = get_supabase_client()
    if supabase is None:
        return None
    try:
        resp = supabase.table("gt_msa_studies").insert(study_data).execute()
        return resp.data[0]["id"] if resp.data else None
    except Exception as e:
        st.error(f"Error al crear estudio MSA: {str(e)}")
        return None


def update_msa_study_results(study_id: str, results: dict) -> bool:
    """Update the results_summary JSONB of an MSA study"""
    supabase = get_supabase_client()
    if supabase is None:
        return False
    try:
        supabase.table("gt_msa_studies").update({"results_summary": results}).eq("id", study_id).execute()
        return True
    except Exception as e:
        st.error(f"Error actualizando resultados MSA: {str(e)}")
        return False


def save_msa_data(table: str, records: list) -> bool:
    """Insert measurement records into an MSA data table"""
    supabase = get_supabase_client()
    if supabase is None:
        return False
    try:
        supabase.table(table).insert(records).execute()
        return True
    except Exception as e:
        st.error(f"Error guardando datos MSA: {str(e)}")
        return False


def get_msa_data(table: str, study_id: str) -> pd.DataFrame:
    """Get measurement data for a specific MSA study"""
    supabase = get_supabase_client()
    if supabase is None:
        return pd.DataFrame()
    try:
        resp = supabase.table(table).select("*").eq("study_id", study_id).execute()
        return pd.DataFrame(resp.data) if resp.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error cargando datos MSA: {str(e)}")
        return pd.DataFrame()


def delete_msa_study(study_id: str) -> bool:
    """Delete an MSA study and its data"""
    supabase = get_supabase_client()
    if supabase is None:
        return False
    try:
        supabase.table("gt_msa_studies").delete().eq("id", study_id).execute()
        return True
    except Exception as e:
        st.error(f"Error eliminando estudio MSA: {str(e)}")
        return False


# ─────────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────────

def _map_to_db(data: dict) -> dict:
    """Map form field names to DB column names"""
    mapping = {
        "Id. de Instrumento":           "gage_id",
        "Estatus":                       "status",
        "Descripción":                   "description",
        "Tipo":                          "type",
        "Ubicación de Almacén":          "storage_location",
        "Ubicación Actual":              "current_location",
        "Fecha del última programación": "last_calibration_date",
        "Próximo vencimiento":           "next_calibration_date",
        "Frecuencia de calibración":     "calibration_frequency",
        "Unidades de frecuencia":        "frequency_unit",
        "Persona responsable":           "responsible_person",
        "Custodio actual":               "current_custodian",
        "N/S del Instrumento":           "serial_number",
        "No. de Contabilidad":           "accounting_number",
        "No.  de Modelo":                "model_number",
        "Proveedor":                     "supplier",
        "Costo":                         "cost",
        "Propietario":                   "owner",
    }
    result = {}
    for key, value in data.items():
        db_key = mapping.get(key, key)
        # Convert dates to strings for Supabase
        if hasattr(value, "isoformat"):
            value = value.isoformat()
        result[db_key] = value
    return result
