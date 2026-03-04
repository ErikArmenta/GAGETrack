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


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _freq_to_days(frequency: int, unit: str) -> int:
    """Convierte frecuencia + unidad a días para calcular próxima calibración."""
    unit = (unit or "").lower()
    if unit in ("daily", "días", "dia", "diaria"):
        return frequency
    elif unit in ("weekly", "semanas", "semana", "semanal"):
        return frequency * 7
    elif unit in ("monthly", "meses", "mes", "mensual"):
        return frequency * 30
    else:  # yearly / anual / default
        return frequency * 365


# ─── Render tarjetas de referencia (fuera del form para st.markdown HTML) ─────

def _render_ref_card_preview(idx: int, ref_val: float, measured: float,
                              tol_pos: float, tol_neg: float) -> str:
    """Devuelve HTML de una card de referencia (solo para preview, no dentro del form)."""
    if ref_val == 0.0:
        return ""
    usl = ref_val + tol_pos
    lsl = ref_val + tol_neg
    ok = lsl <= measured <= usl
    color_border = "#27ae60" if ok else "#e74c3c"
    color_bg = "rgba(39,174,96,0.1)" if ok else "rgba(231,76,60,0.1)"
    badge = "✅ OK" if ok else "❌ Fuera"
    badge_color = "#27ae60" if ok else "#e74c3c"
    return f"""
    <div style="border:2px solid {color_border}; background:{color_bg}; border-radius:10px;
                padding:0.75rem; margin-bottom:0.5rem; text-align:center;">
        <div style="font-weight:700; color:#e8eaf6; font-size:0.9rem;">Ref. {idx}</div>
        <div style="color:#9aa0b4; font-size:0.75rem;">Ref: <b style='color:#e8eaf6'>{ref_val:.6f}</b></div>
        <div style="color:#9aa0b4; font-size:0.75rem;">USL: <b style='color:#27ae60'>{usl:.6f}</b>
             &nbsp;|&nbsp; LSL: <b style='color:#e74c3c'>{lsl:.6f}</b></div>
        <div style="color:#9aa0b4; font-size:0.75rem;">Medido: <b style='color:#e8eaf6'>{measured:.6f}</b></div>
        <div style="font-weight:700; color:{badge_color}; margin-top:4px;">{badge}</div>
    </div>
    """


# ─── Formulario Nueva Calibración ─────────────────────────────────────────────

def render_calibration_form(instrument_id: str, instrument_uuid: str, inst_row=None):
    """Formulario para capturar una nueva calibración."""
    st.markdown("#### 📝 Datos de la Nueva Calibración")

    # Calcular próxima fecha de calibración automáticamente
    freq_value = 365
    freq_unit = "Yearly"
    if inst_row is not None:
        raw_freq = inst_row.get("Frecuencia de calibración", 365)
        raw_unit = inst_row.get("Unidades de frecuencia", "Yearly")
        try:
            freq_value = int(float(raw_freq)) if raw_freq else 365
        except (ValueError, TypeError):
            freq_value = 365
        freq_unit = str(raw_unit) if raw_unit else "Yearly"

    freq_days = _freq_to_days(freq_value, freq_unit)

    with st.form("form_nueva_calibracion", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            cal_date = st.date_input("📅 Fecha de Calibración *", value=date.today())
            technician = st.text_input("👷 Técnico Calibrador *", placeholder="Nombre del técnico")
            supplier = st.text_input("🏭 Proveedor / Laboratorio", placeholder="Ej: Laboratorio Externo SA")
            certificate_number = st.text_input("📋 Número de Certificado", placeholder="Ej: CAL-2026-001")
            result = st.selectbox("✅ Resultado *", ["Aprobado", "Rechazado", "Condicional"])

        with col2:
            cost = st.number_input("💰 Costo ($)", min_value=0.0, value=0.0, step=0.01)
            uncertainty = st.number_input(
                "📊 Incertidumbre (U)", min_value=0.0, value=0.0,
                step=0.000001, format="%.6f"
            )

            # ── Tolerancia positiva y negativa ────────────────────────────
            st.markdown("**⚙️ Tolerancia**")
            tc1, tc2 = st.columns(2)
            with tc1:
                tolerance_pos = st.number_input(
                    "➕ Positiva", value=0.0, step=0.000001, format="%.6f",
                    help="Tolerancia positiva (ej: +0.05)"
                )
            with tc2:
                tolerance_neg = st.number_input(
                    "➖ Negativa", value=0.0, step=0.000001, format="%.6f",
                    help="Tolerancia negativa (ej: -0.05); usa valor negativo"
                )

        # ── Próxima calibración calculada automáticamente ─────────────────
        computed_next = cal_date + timedelta(days=freq_days)
        st.info(
            f"📅 **Próxima Calibración (calculada automáticamente):** {computed_next.strftime('%Y-%m-%d')} "
            f"— basada en frecuencia de **{freq_value} {freq_unit}** del instrumento."
        )

        # ── Límites de Especificación ──────────────────────────────────────
        st.markdown("---")
        st.markdown("##### 🎯 Límites de Especificación")
        cl1, cl2 = st.columns(2)
        with cl1:
            control_ucl = st.number_input(
                "USL (Límite Superior de Especificación)", value=0.0,
                step=0.000001, format="%.6f", help="Upper Specification Limit"
            )
        with cl2:
            control_lcl = st.number_input(
                "LSL (Límite Inferior de Especificación)", value=0.0,
                step=0.000001, format="%.6f", help="Lower Specification Limit"
            )

        # ── Cards de Valores de Referencia (10) ───────────────────────────
        st.markdown("---")
        st.markdown("##### 📐 Valores de Referencia (hasta 10)")
        st.caption(
            "Para cada referencia activa ingresa el valor y el valor medido. "
            "Los límites USL/LSL se calculan automáticamente con la tolerancia. "
            "Las cards son rojas si el medido está fuera de especificación."
        )

        # Almacenar datos de cada card
        ref_cards_data = []

        # 2 filas × 5 columnas = 10 cards
        row1_cols = st.columns(5)
        row2_cols = st.columns(5)
        all_card_cols = row1_cols + row2_cols

        for i, col in enumerate(all_card_cols, start=1):
            with col:
                ref_val = st.number_input(
                    f"Ref. {i}", value=0.0, step=0.000001,
                    format="%.6f", key=f"ref_val_{i}"
                )
                measured_val = st.number_input(
                    f"Medido {i}", value=0.0, step=0.000001,
                    format="%.6f", key=f"ref_med_{i}"
                )
                ref_cards_data.append((ref_val, measured_val))

        # ──────────────────────────────────────────────────────────────────
        observations = st.text_area(
            "📝 Observaciones",
            placeholder="Condiciones de calibración, notas relevantes..."
        )

        submitted = st.form_submit_button(
            "💾 Guardar Calibración", use_container_width=True, type="primary"
        )

        if submitted:
            if not technician:
                st.error("❌ El técnico calibrador es obligatorio.")
                return

            # Construir lista de cards (solo las con ref != 0)
            reference_cards = []
            reference_values_list = []
            for ref_val, measured_val in ref_cards_data:
                if ref_val == 0.0:
                    continue
                usl = round(ref_val + tolerance_pos, 6)
                lsl = round(ref_val + tolerance_neg, 6)
                ok = bool(lsl <= measured_val <= usl)
                reference_cards.append({
                    "ref": round(ref_val, 6),
                    "measured": round(measured_val, 6),
                    "usl": usl,
                    "lsl": lsl,
                    "ok": ok,
                })
                reference_values_list.append(round(ref_val, 6))

            cal_data = {
                "instrument_id": instrument_uuid,
                "gage_id": instrument_id,
                "calibration_date": cal_date.isoformat(),
                "next_calibration_date": computed_next.isoformat(),
                "technician": technician,
                "supplier": supplier,
                "certificate_number": certificate_number,
                "result": result,
                "cost": float(cost) if cost else None,
                # Tolerancia como texto legible (compatibilidad) y valores numéricos
                "tolerance": f"+{tolerance_pos:.6f} / {tolerance_neg:.6f}",
                "tolerance_pos": round(float(tolerance_pos), 6) if tolerance_pos != 0.0 else None,
                "tolerance_neg": round(float(tolerance_neg), 6) if tolerance_neg != 0.0 else None,
                "uncertainty": round(float(uncertainty), 6) if uncertainty else None,
                "observations": observations,
                # Límites de Especificación (se guardan en control_ucl/lcl por compatibilidad BD)
                "control_nominal": None,
                "control_ucl": round(float(control_ucl), 6) if control_ucl != 0.0 else None,
                "control_lcl": round(float(control_lcl), 6) if control_lcl != 0.0 else None,
                # Cards de referencia (JSONB)
                "reference_cards": reference_cards if reference_cards else None,
                "reference_values": reference_values_list if reference_values_list else None,
            }

            if add_calibration(cal_data):
                st.success("✅ Calibración guardada exitosamente en la base de datos.")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ Error al guardar la calibración.")

    # ── Preview visual de cards (fuera del form, se actualiza con rerun) ──────
    # Mostrar cards coloreadas en base a los valores del último estado del form
    # (No podemos leer session_state dentro del form, así que mostramos ayuda visual)
    st.markdown("---")
    st.markdown("##### 👁️ Vista Previa de Cards de Referencia")
    st.caption(
        "Ingresa tolerancia y valores de referencia en el formulario arriba, "
        "guarda para ver las cards coloreadas en el historial."
    )


# ─── Historial de Calibraciones ───────────────────────────────────────────────

def render_calibration_history(gage_id: str):
    """Muestra el historial editable de calibraciones para un instrumento."""
    st.markdown("#### 📋 Historial de Calibraciones (Editable)")

    df = get_calibrations(gage_id=gage_id)

    if df.empty:
        st.info("ℹ️ No hay calibraciones registradas para este instrumento.")
        return

    # Columnas a mostrar en el editor
    edit_cols = [
        "id", "calibration_date", "next_calibration_date", "technician",
        "supplier", "certificate_number", "result", "cost",
        "tolerance", "tolerance_pos", "tolerance_neg",
        "control_ucl", "control_lcl",
        "uncertainty", "observations"
    ]

    available_cols = [c for c in edit_cols if c in df.columns]
    df_to_edit = df[available_cols].copy()

    # Convertir fechas
    for col in ["calibration_date", "next_calibration_date"]:
        if col in df_to_edit.columns:
            df_to_edit[col] = pd.to_datetime(df_to_edit[col], errors='coerce')

    # Asegurar tipos numéricos
    for num_col in ["cost", "tolerance_pos", "tolerance_neg", "control_ucl", "control_lcl", "uncertainty"]:
        if num_col in df_to_edit.columns:
            df_to_edit[num_col] = pd.to_numeric(df_to_edit[num_col], errors='coerce')

    try:
        edited_df = st.data_editor(
            df_to_edit,
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": None,
                "calibration_date": st.column_config.DateColumn("Fecha Cal.", format="YYYY-MM-DD"),
                "next_calibration_date": st.column_config.DateColumn("Próxima Cal.", format="YYYY-MM-DD"),
                "result": st.column_config.SelectboxColumn(
                    "Resultado", options=["Aprobado", "Rechazado", "Condicional"]
                ),
                "cost": st.column_config.NumberColumn("Costo ($)", format="$%.2f"),
                "technician": "Técnico",
                "supplier": "Proveedor",
                "certificate_number": "Certificado",
                "tolerance": "Tolerancia (texto)",
                "tolerance_pos": st.column_config.NumberColumn("Tol. +", format="%.6f"),
                "tolerance_neg": st.column_config.NumberColumn("Tol. −", format="%.6f"),
                "control_ucl": st.column_config.NumberColumn("USL", format="%.6f"),
                "control_lcl": st.column_config.NumberColumn("LSL", format="%.6f"),
                "uncertainty": st.column_config.NumberColumn("Incertidumbre", format="%.6f"),
                "observations": "Observaciones",
            },
            key=f"editor_{gage_id}"
        )
    except Exception as e:
        st.error(f"Error visualizando la tabla: {e}")
        return

    # Guardar cambios si los hay
    if not edited_df.equals(df_to_edit):
        c1, _ = st.columns([1, 4])
        if c1.button("💾 Guardar cambios", type="primary"):
            success_count = 0
            for i in range(len(edited_df)):
                row_id = edited_df.iloc[i]["id"]
                current_row = edited_df.iloc[i].to_dict()
                orig_rows = df_to_edit[df_to_edit["id"] == row_id]
                if orig_rows.empty:
                    continue
                original_row = orig_rows.iloc[0].to_dict()

                if current_row != original_row:
                    for k, v in current_row.items():
                        if hasattr(v, "isoformat") and not pd.isna(v):
                            current_row[k] = v.isoformat()
                        elif pd.isna(v) if not isinstance(v, str) else False:
                            current_row[k] = None

                    if update_calibration_db(row_id, current_row):
                        success_count += 1

            if success_count > 0:
                st.success(f"✅ Se actualizaron {success_count} registros.")
                st.rerun()

    # Mostrar cards de referencia del registro seleccionado
    if "reference_cards" in df.columns:
        st.markdown("---")
        st.markdown("##### 📐 Cards de Referencia por Calibración")
        for _, row in df.iterrows():
            cards = row.get("reference_cards")
            if not cards:
                continue
            cal_label = f"📅 {str(row.get('calibration_date', ''))[:10]} — {row.get('result', '')}"
            with st.expander(cal_label):
                card_cols = st.columns(5)
                for j, card in enumerate(cards):
                    with card_cols[j % 5]:
                        ok = card.get("ok", True)
                        border_color = "#27ae60" if ok else "#e74c3c"
                        bg_color = "rgba(39,174,96,0.12)" if ok else "rgba(231,76,60,0.12)"
                        badge = "✅ OK" if ok else "❌ Fuera"
                        badge_color = "#27ae60" if ok else "#e74c3c"
                        st.markdown(f"""
                        <div style="border:2px solid {border_color}; background:{bg_color};
                                    border-radius:10px; padding:0.6rem; margin-bottom:0.5rem;
                                    text-align:center; font-size:0.8rem;">
                            <div style='font-weight:700;color:#e8eaf6;'>Ref. {j+1}</div>
                            <div style='color:#9aa0b4;'>Ref: <b style='color:#e8eaf6;'>{card.get('ref',0):.6f}</b></div>
                            <div style='color:#9aa0b4;'>USL: <b style='color:#27ae60;'>{card.get('usl',0):.6f}</b></div>
                            <div style='color:#9aa0b4;'>LSL: <b style='color:#e74c3c;'>{card.get('lsl',0):.6f}</b></div>
                            <div style='color:#9aa0b4;'>Med: <b style='color:#e8eaf6;'>{card.get('measured',0):.6f}</b></div>
                            <div style='font-weight:700;color:{badge_color};margin-top:4px;'>{badge}</div>
                        </div>
                        """, unsafe_allow_html=True)

    # Sección de eliminación
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


# ─── Acceso Rápido MSA ────────────────────────────────────────────────────────

def render_msa_quick_access(gage_id: str):
    """Botones de acceso rápido a estudios MSA del instrumento."""
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


# ─── Módulo Principal ─────────────────────────────────────────────────────────

def render_calibrations():
    """Interfaz principal del módulo de calibraciones."""
    st.title("🔬 Módulo de Calibraciones")

    df_inst = load_data()

    if df_inst.empty:
        st.warning("⚠️ No hay instrumentos registrados. Agrega instrumentos en el módulo de Inventario.")
        return

    # Selector de instrumento
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

    # Info del instrumento
    instrument_uuid = get_instrument_uuid(selected_id)
    inst_row = df_inst[df_inst["Id. de Instrumento"] == selected_id].iloc[0]

    # Card resumen del instrumento
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
                <p style="margin:0; color:#9aa0b4; font-size:0.8rem; text-transform:uppercase; letter-spacing:1px;">Frecuencia</p>
                <p style="margin:0; font-weight:600; color:#e8eaf6;">
                    {inst_row.get('Frecuencia de calibración', 'N/A')} {inst_row.get('Unidades de frecuencia', '')}
                </p>
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
                render_calibration_form(selected_id, instrument_uuid, inst_row=inst_row)
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
