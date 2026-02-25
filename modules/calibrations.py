"""
Calibrations Module - Complete calibration management
GageTrack - Sistema de Gestión de Instrumentos
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import sys
sys.path.append('..')
from utils.db_manager import (
    load_data, get_calibrations, add_calibration,
    delete_calibration, get_instrument_uuid, get_msa_studies
)


def render_calibration_form(instrument_id: str, instrument_uuid: str):
    """Form to capture a new calibration"""
    st.markdown("#### 📝 Datos de la Nueva Calibración")
    
    with st.form("form_nueva_calibracion", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            cal_date = st.date_input("📅 Fecha de Calibración *", value=date.today())
            technician = st.text_input("👷 Técnico Calibrador *", placeholder="Nombre del técnico")
            supplier = st.text_input("🏭 Proveedor / Laboratorio", placeholder="Ej: Laboratorio Externo SA")
            certificate_number = st.text_input("📋 Número de Certificado", placeholder="Ej: CAL-2026-001")
            result = st.selectbox("✅ Resultado *", ["Aprobado", "Rechazado", "Condicional"])

        with col2:
            next_cal_date = st.date_input(
                "📅 Próxima Calibración *",
                value=date.today() + timedelta(days=365)
            )
            cost = st.number_input("💰 Costo ($)", min_value=0.0, value=0.0, step=0.01)
            tolerance = st.text_input("⚙️ Tolerancia", placeholder="Ej: ±0.01 mm")
            measured_value = st.number_input("📏 Valor Medido", value=0.0, step=0.001, format="%.4f")
            reference_value = st.number_input("📐 Valor de Referencia", value=0.0, step=0.001, format="%.4f")

        uncertainty = st.number_input("📊 Incertidumbre (U)", min_value=0.0, value=0.0, step=0.0001, format="%.6f")
        observations = st.text_area("📝 Observaciones", placeholder="Condiciones de calibración, notas relevantes...")

        submitted = st.form_submit_button("💾 Guardar Calibración", use_container_width=True, type="primary")

        if submitted:
            if not technician:
                st.error("❌ El técnico calibrador es obligatorio.")
                return

            cal_data = {
                "instrument_id": instrument_uuid,
                "gage_id": instrument_id,
                "calibration_date": cal_date.isoformat(),
                "next_calibration_date": next_cal_date.isoformat(),
                "technician": technician,
                "supplier": supplier,
                "certificate_number": certificate_number,
                "result": result,
                "cost": float(cost) if cost else None,
                "tolerance": tolerance,
                "measured_value": float(measured_value) if measured_value else None,
                "reference_value": float(reference_value) if reference_value else None,
                "uncertainty": float(uncertainty) if uncertainty else None,
                "observations": observations,
            }

            if add_calibration(cal_data):
                st.success("✅ Calibración guardada exitosamente en la base de datos.")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ Error al guardar la calibración.")


def render_calibration_history(gage_id: str):
    """Show calibration history table for an instrument"""
    st.markdown("#### 📋 Historial de Calibraciones")
    
    df = get_calibrations(gage_id=gage_id)
    
    if df.empty:
        st.info("ℹ️ No hay calibraciones registradas para este instrumento.")
        return

    # Format columns for display
    display_cols = {
        "calibration_date": "Fecha Calibración",
        "next_calibration_date": "Próxima Calibración",
        "technician": "Técnico",
        "supplier": "Proveedor",
        "certificate_number": "N° Certificado",
        "result": "Resultado",
        "cost": "Costo ($)",
        "tolerance": "Tolerancia",
        "observations": "Observaciones",
    }

    df_display = df.rename(columns={k: v for k, v in display_cols.items() if k in df.columns})
    available = [v for k, v in display_cols.items() if k in df.columns]
    df_display = df_display[available]

    def style_result(val):
        color = {"Aprobado": "background-color:#d4edda; color:#155724",
                 "Rechazado": "background-color:#f8d7da; color:#721c24",
                 "Condicional": "background-color:#fff3cd; color:#856404"}.get(val, "")
        return color

    styled = df_display.style.applymap(style_result, subset=["Resultado"] if "Resultado" in df_display.columns else [])

    st.dataframe(styled, use_container_width=True, hide_index=True)

    # Delete option
    if "id" in df.columns:
        with st.expander("🗑️ Eliminar calibración"):
            cal_ids = df["id"].tolist()
            cal_labels = [
                f"{row.get('calibration_date', 'N/A')} - {row.get('result', 'N/A')}"
                for _, row in df.iterrows()
            ]
            selected_label = st.selectbox("Seleccionar", cal_labels)
            idx = cal_labels.index(selected_label)
            if st.button("Eliminar", type="secondary"):
                if delete_calibration(cal_ids[idx]):
                    st.success("✅ Calibración eliminada.")
                    st.rerun()


def render_msa_quick_access(gage_id: str):
    """Quick access buttons to MSA studies for this instrument"""
    st.markdown("#### 🔬 Estudios MSA Relacionados")
    
    studies_df = get_msa_studies(gage_id=gage_id)

    if studies_df.empty:
        st.info("ℹ️ No hay estudios MSA registrados para este instrumento.")
    else:
        for _, study in studies_df.iterrows():
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.markdown(f"**{study.get('study_name', study.get('study_type', 'Estudio'))}**")
            with col2:
                st.markdown(f"📅 {str(study.get('created_at', ''))[:10]}")
            with col3:
                etype = study.get("study_type", "GRR")
                if st.button(f"Ver {etype}", key=f"msa_{study['id']}"):
                    st.session_state.current_page = "MSA"
                    st.session_state.msa_gage_filter = gage_id
                    st.rerun()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Nuevo Estudio GRR", use_container_width=True):
            st.session_state.current_page = "MSA"
            st.session_state.msa_tab = "GRR"
            st.session_state.msa_gage_filter = gage_id
            st.rerun()
    with col2:
        if st.button("➕ Nuevo Estudio MSA", use_container_width=True):
            st.session_state.current_page = "MSA"
            st.session_state.msa_gage_filter = gage_id
            st.rerun()


def render_calibrations():
    """Main calibrations module interface"""
    st.title("🔬 Módulo de Calibraciones")

    # Load instruments for selector
    df_inst = load_data()
    
    if df_inst.empty:
        st.warning("⚠️ No hay instrumentos registrados. Agrega instrumentos en el módulo de Inventario.")
        return

    # Instrument selector
    st.markdown("### Seleccionar Instrumento")
    col1, col2 = st.columns([3, 1])
    with col1:
        instrument_ids = df_inst["Id. de Instrumento"].dropna().tolist()
        descriptions = df_inst.set_index("Id. de Instrumento")["Descripción"].to_dict()

        options = [f"{gid} — {descriptions.get(gid, '')}" for gid in instrument_ids]
        selected_option = st.selectbox("Instrumento", options, label_visibility="collapsed")
        selected_id = selected_option.split(" — ")[0] if selected_option else None

    with col2:
        if st.button("🔄 Actualizar", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    if not selected_id:
        return

    # Get instrument info
    instrument_uuid = get_instrument_uuid(selected_id)
    inst_row = df_inst[df_inst["Id. de Instrumento"] == selected_id].iloc[0]

    # Show instrument summary card
    st.markdown(f"""
    <div style="background:white; border-radius:12px; padding:1.5rem; box-shadow:0 2px 8px rgba(0,0,0,0.1); 
                margin-bottom:1.5rem; border-left:4px solid #667eea;">
        <div style="display:flex; justify-content:space-between; flex-wrap:wrap; gap:1rem;">
            <div>
                <p style="margin:0; color:#7f8c8d; font-size:0.8rem; text-transform:uppercase;">ID</p>
                <p style="margin:0; font-weight:700; font-size:1.2rem;">{selected_id}</p>
            </div>
            <div>
                <p style="margin:0; color:#7f8c8d; font-size:0.8rem; text-transform:uppercase;">Descripción</p>
                <p style="margin:0; font-weight:600;">{inst_row.get('Descripción', 'N/A')}</p>
            </div>
            <div>
                <p style="margin:0; color:#7f8c8d; font-size:0.8rem; text-transform:uppercase;">Estatus</p>
                <p style="margin:0; font-weight:600;">{inst_row.get('Estatus', 'N/A')}</p>
            </div>
            <div>
                <p style="margin:0; color:#7f8c8d; font-size:0.8rem; text-transform:uppercase;">Ubicación</p>
                <p style="margin:0; font-weight:600;">{inst_row.get('Ubicación Actual', 'N/A')}</p>
            </div>
            <div>
                <p style="margin:0; color:#7f8c8d; font-size:0.8rem; text-transform:uppercase;">Estado Calibración</p>
                <p style="margin:0; font-weight:700; color:{'#27ae60' if inst_row.get('Calibrado') == 'Aprobado' else '#e74c3c'};">
                    {inst_row.get('Calibrado', 'Sin calibrar') or 'Sin calibrar'}
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Tabs
    tab1, tab2, tab3 = st.tabs(["➕ Nueva Calibración", "📋 Historial", "🔬 Estudios MSA"])

    with tab1:
        # Confirmation dialog
        if "confirm_new_cal" not in st.session_state:
            st.session_state.confirm_new_cal = False

        if not st.session_state.confirm_new_cal:
            st.markdown("---")
            st.markdown("¿Deseas agregar una nueva calibración para este instrumento?")
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("✅ Sí, agregar calibración", type="primary", use_container_width=True):
                    st.session_state.confirm_new_cal = True
                    st.rerun()
        else:
            if instrument_uuid:
                render_calibration_form(selected_id, instrument_uuid)
            else:
                st.error("❌ No se pudo obtener el UUID del instrumento.")
            if st.button("❌ Cancelar"):
                st.session_state.confirm_new_cal = False
                st.rerun()

    with tab2:
        render_calibration_history(selected_id)

    with tab3:
        render_msa_quick_access(selected_id)


if __name__ == "__main__":
    render_calibrations()
