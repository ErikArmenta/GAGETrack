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
from utils.db_manager import update_calibration_db


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
            measured_value = st.number_input("📏 Valor Medido", value=0.0, step=0.000001, format="%.6f")
            reference_value = st.number_input("📐 Valor de Referencia (principal)", value=0.0, step=0.000001, format="%.6f")

        uncertainty = st.number_input("📊 Incertidumbre (U)", min_value=0.0, value=0.0, step=0.000001, format="%.6f")

        # ── Límites de Control ─────────────────────────────────────────
        st.markdown("---")
        st.markdown("##### 🎯 Límites de Control")
        cl1, cl2, cl3 = st.columns(3)
        with cl1:
            control_nominal = st.number_input(
                "Nominal / Target", value=0.0, step=0.000001, format="%.6f",
                help="Valor nominal esperado del instrumento"
            )
        with cl2:
            control_ucl = st.number_input(
                "UCL (Límite Superior)", value=0.0, step=0.000001, format="%.6f",
                help="Upper Control Limit"
            )
        with cl3:
            control_lcl = st.number_input(
                "LCL (Límite Inferior)", value=0.0, step=0.000001, format="%.6f",
                help="Lower Control Limit"
            )

        # ── Valores de Referencia (hasta 10) ──────────────────────────
        st.markdown("---")
        st.markdown("##### 📐 Valores de Referencia (hasta 10)")
        st.caption("Ingresa los valores que apliquen. Los campos vacíos (0) se omiten automáticamente.")
        ref_cols_a = st.columns(5)
        ref_cols_b = st.columns(5)
        ref_inputs = []
        for i, col in enumerate(ref_cols_a):
            v = col.number_input(f"Ref. {i+1}", value=0.0, step=0.000001, format="%.6f",
                                 key=f"refval_{i+1}", label_visibility="visible")
            ref_inputs.append(v)
        for i, col in enumerate(ref_cols_b):
            v = col.number_input(f"Ref. {i+6}", value=0.0, step=0.000001, format="%.6f",
                                 key=f"refval_{i+6}", label_visibility="visible")
            ref_inputs.append(v)

        # ──────────────────────────────────────────────────────────────
        observations = st.text_area("📝 Observaciones", placeholder="Condiciones de calibración, notas relevantes...")

        submitted = st.form_submit_button("💾 Guardar Calibración", use_container_width=True, type="primary")

        if submitted:
            if not technician:
                st.error("❌ El técnico calibrador es obligatorio.")
                return

            # Filtrar valores de referencia: solo los distintos de 0
            reference_values_list = [round(v, 6) for v in ref_inputs if v != 0.0]

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
                "measured_value": round(float(measured_value), 6) if measured_value else None,
                "reference_value": round(float(reference_value), 6) if reference_value else None,
                "uncertainty": round(float(uncertainty), 6) if uncertainty else None,
                "observations": observations,
                # Nuevos campos
                "control_nominal": round(float(control_nominal), 6) if control_nominal != 0.0 else None,
                "control_ucl":    round(float(control_ucl), 6)    if control_ucl != 0.0    else None,
                "control_lcl":    round(float(control_lcl), 6)    if control_lcl != 0.0    else None,
                "reference_values": reference_values_list if reference_values_list else None,
            }

            if add_calibration(cal_data):
                st.success("✅ Calibración guardada exitosamente en la base de datos.")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ Error al guardar la calibración.")




def render_calibration_history(gage_id: str):
    """Show editable calibration history table for an instrument"""
    st.markdown("#### 📋 Historial de Calibraciones (Editable)")

    # 1. Cargar datos
    df = get_calibrations(gage_id=gage_id)

    if df.empty:
        st.info("ℹ️ No hay calibraciones registradas para este instrumento.")
        return

    # Columnas que queremos manejar
    edit_cols = [
        "id", "calibration_date", "next_calibration_date", "technician",
        "supplier", "certificate_number", "result", "cost", "tolerance", "observations"
    ]

    available_cols = [c for c in edit_cols if c in df.columns]
    df_to_edit = df[available_cols].copy()

    # --- CORRECCIÓN CRÍTICA DE TIPOS ---
    # Convertimos las columnas de fecha a objetos datetime de Python.
    # Si vienen como string desde Supabase, st.column_config.DateColumn fallará sin esto.
    for col in ["calibration_date", "next_calibration_date"]:
        if col in df_to_edit.columns:
            df_to_edit[col] = pd.to_datetime(df_to_edit[col], errors='coerce')

    # Aseguramos que el costo sea numérico para el NumberColumn
    if "cost" in df_to_edit.columns:
        df_to_edit["cost"] = pd.to_numeric(df_to_edit["cost"], errors='coerce')
    # ----------------------------------

    # 2. Configurar el Editor de Datos
    try:
        edited_df = st.data_editor(
            df_to_edit,
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": None,
                "calibration_date": st.column_config.DateColumn("Fecha Cal.", format="YYYY-MM-DD"),
                "next_calibration_date": st.column_config.DateColumn("Próxima Cal.", format="YYYY-MM-DD"),
                "result": st.column_config.SelectboxColumn("Resultado", options=["Aprobado", "Rechazado", "Condicional"]),
                "cost": st.column_config.NumberColumn("Costo ($)", format="$%.2f"),
                "technician": "Técnico",
                "supplier": "Proveedor",
                "certificate_number": "Certificado",
                "tolerance": "Tolerancia",
                "observations": "Observaciones"
            },
            key=f"editor_{gage_id}"
        )
    except Exception as e:
        st.error(f"Error visualizando la tabla: {e}")
        st.info("Asegúrate de que los formatos de fecha en la base de datos sean válidos (YYYY-MM-DD).")
        return

    # 3. Lógica de Guardado (Se mantiene igual que la anterior)
    if not edited_df.equals(df_to_edit):
        c1, _ = st.columns([1, 4])
        if c1.button("💾 Guardar cambios", type="primary"):
            success_count = 0
            for i in range(len(edited_df)):
                row_id = edited_df.iloc[i]["id"]
                current_row = edited_df.iloc[i].to_dict()
                original_row = df_to_edit[df_to_edit["id"] == row_id].iloc[0].to_dict()

                if current_row != original_row:
                    # Convertir para Supabase
                    for k, v in current_row.items():
                        if hasattr(v, "isoformat") and not pd.isna(v):
                            current_row[k] = v.isoformat()
                        elif pd.isna(v):
                            current_row[k] = None

                    if update_calibration_db(row_id, current_row):
                        success_count += 1

            if success_count > 0:
                st.success(f"✅ Se actualizaron {success_count} registros.")
                st.rerun()

    # Mantener el expansor de eliminación abajo
    st.markdown("---")
    if "id" in df.columns:
        with st.expander("🗑️ Eliminar calibración permanentemente"):
            cal_ids = df["id"].tolist()
            cal_labels = [
                f"{row.get('calibration_date', 'N/A')} - {row.get('result', 'N/A')}"
                for _, row in df.iterrows()
            ]
            selected_label = st.selectbox("Seleccionar registro para eliminar", cal_labels)
            idx = cal_labels.index(selected_label)
            if st.button("Confirmo eliminar", type="secondary"):
                if delete_calibration(cal_ids[idx]):
                    st.success("✅ Registro eliminado.")
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
                    # Fix 5: indicar qué tab abrir en MSA
                    st.session_state.msa_tab = etype
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
    <div style="background:#1a1f2e; border-radius:12px; padding:1.5rem;
                box-shadow:0 4px 24px rgba(0,0,0,0.4);
                margin-bottom:1.5rem; border-left:4px solid #667eea;
                border-top:1px solid rgba(255,255,255,0.08);">
        <div style="display:flex; justify-content:space-between; flex-wrap:wrap; gap:1rem;">
            <div>
                <p style="margin:0; color:#9aa0b4; font-size:0.8rem; text-transform:uppercase; letter-spacing:1px;">ID</p>
                <p style="margin:0; font-weight:700; font-size:1.2rem; color:#e8eaf6;">{selected_id}</p>
            </div>
            <div>
                <p style="margin:0; color:#9aa0b4; font-size:0.8rem; text-transform:uppercase; letter-spacing:1px;">Descripción</p>
                <p style="margin:0; font-weight:600; color:#e8eaf6;">{inst_row.get('Descripción', 'N/A')}</p>
            </div>
            <div>
                <p style="margin:0; color:#9aa0b4; font-size:0.8rem; text-transform:uppercase; letter-spacing:1px;">Estatus</p>
                <p style="margin:0; font-weight:600; color:#e8eaf6;">{inst_row.get('Estatus', 'N/A')}</p>
            </div>
            <div>
                <p style="margin:0; color:#9aa0b4; font-size:0.8rem; text-transform:uppercase; letter-spacing:1px;">Ubicación</p>
                <p style="margin:0; font-weight:600; color:#e8eaf6;">{inst_row.get('Ubicación Actual', 'N/A')}</p>
            </div>
            <div>
                <p style="margin:0; color:#9aa0b4; font-size:0.8rem; text-transform:uppercase; letter-spacing:1px;">Estado Calibración</p>
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




