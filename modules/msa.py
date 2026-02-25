"""
MSA Module - Measurement System Analysis (Expanded)
Studies: GRR ANOVA, Stability, Linearity, Bias, Kappa, Uncertainty
AIAG MSA Manual Reference
"""
from __future__ import annotations
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols
from datetime import datetime
from io import BytesIO
import sys
sys.path.append('..')
from utils.db_manager import (
    load_data, get_instrument_uuid, create_msa_study,
    save_msa_data, update_msa_study_results, get_msa_studies
)

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _gage_selector(key: str):
    df = load_data()
    if df.empty:
        st.warning("No hay instrumentos. Agrega uno en Inventario.")
        return None, None
    ids = df["Id. de Instrumento"].dropna().tolist()
    desc = df.set_index("Id. de Instrumento")["Descripción"].to_dict()
    opts = [f"{i} — {desc.get(i,'')}" for i in ids]
    default_idx = 0
    if "msa_gage_filter" in st.session_state:
        try:
            default_idx = ids.index(st.session_state.msa_gage_filter)
        except ValueError:
            pass
    sel = st.selectbox("🔧 Instrumento", opts, index=default_idx, key=key)
    gage_id = sel.split(" — ")[0]
    uuid = get_instrument_uuid(gage_id)
    return gage_id, uuid


def _study_meta_form(study_type: str, gage_id: str, instrument_uuid: str, key: str) -> dict:
    with st.expander("📋 Datos del Estudio (requeridos para guardar/PDF)", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            study_name = st.text_input("Nombre del Estudio",
                                       value=f"{study_type} - {gage_id}",
                                       key=f"{key}_name")
            operator = st.text_input("Operador / Analista", key=f"{key}_op")
            characteristic = st.text_input("Característica Medida", key=f"{key}_char")
        with col2:
            usl = st.number_input("USL", value=0.0, step=0.001, format="%.4f", key=f"{key}_usl")
            lsl = st.number_input("LSL", value=0.0, step=0.001, format="%.4f", key=f"{key}_lsl")
            tol = abs(usl - lsl)
            st.metric("Tolerancia", f"{tol:.4f}")
        notes = st.text_area("Notas", key=f"{key}_notes")
    return {
        "instrument_id": instrument_uuid,
        "gage_id": gage_id,
        "study_type": study_type,
        "study_name": study_name,
        "operator": operator,
        "characteristic": characteristic,
        "specification_usl": usl,
        "specification_lsl": lsl,
        "tolerance": tol,
        "notes": notes,
    }


def _pdf_download_button(meta: dict, results: dict, study_type: str, suffix: str = ""):
    """Render a direct st.download_button that generates PDF on click."""
    from modules.reports import generate_msa_report
    gage_id = meta.get("gage_id", "N/A")
    buf = generate_msa_report(meta, results, study_type)
    fname = f"MSA_{study_type}_{gage_id}_{datetime.now().strftime('%Y%m%d%H%M')}.pdf"
    st.download_button(
        label=f"📥 Descargar Reporte {study_type} PDF",
        data=buf,
        file_name=fname,
        mime="application/pdf",
        use_container_width=True,
        key=f"dl_{study_type}_{suffix}"
    )


def _save_and_pdf_row(meta: dict, results: dict, study_type: str,
                        table: str, records: list, suffix: str = ""):
    col1, col2 = st.columns(2)
    saved_key = f"saved_{study_type}_{suffix}"

    with col1:
        if st.button("💾 Guardar en Supabase", key=f"save_{study_type}_{suffix}",
                     use_container_width=True, type="primary"):
            if not meta.get("instrument_id"):
                st.error("Selecciona un instrumento con UUID válido.")
            else:
                study_id = create_msa_study(meta)
                if study_id:
                    save_msa_data(table, records)
                    update_msa_study_results(study_id, results)
                    st.session_state[saved_key] = study_id
                    st.success(f"✅ Guardado. ID: `{study_id}`")
                else:
                    st.error("❌ Error al crear el estudio.")

    with col2:
        _pdf_download_button(meta, results, study_type, suffix)


# ─────────────────────────────────────────────
# GRR ANOVA
# ─────────────────────────────────────────────

def calculate_gage_rr_anova(df, parts_col='Part', operators_col='Operator', measurement_col='Measurement'):
    df = df.copy()
    df[parts_col] = df[parts_col].astype(str)
    df[operators_col] = df[operators_col].astype(str)

    n_parts = df[parts_col].nunique()
    n_operators = df[operators_col].nunique()
    n_trials = len(df) // (n_parts * n_operators)

    formula = f'{measurement_col} ~ C({parts_col}) + C({operators_col}) + C({parts_col}):C({operators_col})'
    model = ols(formula, data=df).fit()
    anova_table = sm.stats.anova_lm(model, typ=2)

    MS_part     = anova_table.loc[f'C({parts_col})',                   'sum_sq'] / anova_table.loc[f'C({parts_col})',                   'df']
    MS_operator = anova_table.loc[f'C({operators_col})',               'sum_sq'] / anova_table.loc[f'C({operators_col})',               'df']
    MS_inter    = anova_table.loc[f'C({parts_col}):C({operators_col})','sum_sq'] / anova_table.loc[f'C({parts_col}):C({operators_col})','df']
    MS_error    = anova_table.loc['Residual',                         'sum_sq'] / anova_table.loc['Residual',                         'df']

    var_EV   = max(0, MS_error)
    var_AV   = max(0, (MS_operator - MS_inter) / (n_parts * n_trials))
    var_inter= max(0, (MS_inter - MS_error)    / n_trials)
    var_PV   = max(0, (MS_part - MS_inter)     / (n_operators * n_trials))

    EV  = var_EV
    AV  = var_AV + var_inter
    GRR = EV + AV
    PV  = var_PV
    TV  = GRR + PV

    K  = 5.15
    SD = {k: np.sqrt(v) for k, v in [('EV',EV),('AV',AV),('GRR',GRR),('PV',PV),('TV',TV)]}
    SV = {k: K * v for k, v in SD.items()}
    pcts = {k: (SV[k] / SV['TV'] * 100) if SV['TV'] > 0 else 0 for k in SD}
    ndc = int(np.floor(np.sqrt(2) * SD['PV'] / SD['GRR'])) if SD['GRR'] > 0 else 0

    return {'percentages': {'%EV': pcts['EV'], '%AV': pcts['AV'],
                            '%GRR': pcts['GRR'], '%PV': pcts['PV']},
            'std_dev': SD, 'study_var': SV, 'ndc': ndc,
            'anova_table': anova_table,
            'n_parts': n_parts, 'n_operators': n_operators, 'n_trials': n_trials}


def render_grr_tab():
    st.markdown("## 📐 Gage R&R — Método ANOVA (AIAG)")
    gage_id, inst_uuid = _gage_selector("grr_gage")

    input_method = st.radio("Método de Entrada", ["Manual", "Cargar CSV"], horizontal=True)

    if input_method == "Manual":
        col1, col2, col3 = st.columns(3)
        with col1: n_parts    = st.number_input("Partes",    2, 20, 10, key="grr_parts")
        with col2: n_operators= st.number_input("Operadores",2,  5,  3, key="grr_ops")
        with col3: n_trials   = st.number_input("Ensayos",   2,  5,  2, key="grr_trials")

        rows = [{'Part': f'P{p}',
                 'Operator': ['A','B','C','D','E'][:n_operators][o-1],
                 'Trial': t, 'Measurement': 0.0}
                for p in range(1, n_parts+1)
                for o in range(1, n_operators+1)
                for t in range(1, n_trials+1)]
        edited = st.data_editor(pd.DataFrame(rows), use_container_width=True, num_rows="fixed",
                                column_config={"Measurement": st.column_config.NumberColumn(format="%.4f")})

        if st.button("🔬 Analizar GRR", type="primary", key="grr_analyze_btn"):
            _run_grr_analysis(edited, gage_id, inst_uuid)
    else:
        f = st.file_uploader("CSV (Part, Operator, Measurement)", type=["csv"], key="grr_csv")
        if f:
            df_csv = pd.read_csv(f)
            col_map = {}
            for c in df_csv.columns:
                cl = c.lower().strip()
                if cl in ['parte','part']:                               col_map[c] = 'Part'
                elif cl in ['operador','operator']:                     col_map[c] = 'Operator'
                elif cl in ['medicion','medición','measurement','valor']: col_map[c] = 'Measurement'
            df_csv = df_csv.rename(columns=col_map)
            st.dataframe(df_csv.head())
            if st.button("🔬 Analizar GRR", type="primary", key="grr_analyze_csv_btn"):
                _run_grr_analysis(df_csv, gage_id, inst_uuid)

    if "grr_results" in st.session_state:
        _render_grr_results(st.session_state["grr_results"],
                            st.session_state.get("grr_df", pd.DataFrame()),
                            st.session_state.get("grr_gage_id_val", gage_id), 
                            st.session_state.get("grr_uuid_val", inst_uuid))


def _run_grr_analysis(df_meas, gage_id, inst_uuid):
    for req in ['Part','Operator','Measurement']:
        if req not in df_meas.columns:
            st.error(f"Falta columna: {req}")
            return
    try:
        results = calculate_gage_rr_anova(df_meas)
        st.session_state["grr_results"] = results
        st.session_state["grr_df"]      = df_meas
        st.session_state["grr_gage_id_val"] = gage_id
        st.session_state["grr_uuid_val"]    = inst_uuid
    except Exception as e:
        st.error(f"Error en análisis: {e}")
        st.exception(e)


def _render_grr_results(results, df_meas, gage_id, inst_uuid):
    st.markdown("---")
    st.markdown("### 📈 Resultados GRR")
    pcts = results['percentages']
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        grr = pcts['%GRR']
        st.metric("%GRR", f"{grr:.2f}%")
        if grr < 10: st.success("✅ Aceptable")
        elif grr < 30: st.warning("⚠️ Marginal")
        else: st.error("❌ Inaceptable")
    with col2: st.metric("%EV (Repetibilidad)",      f"{pcts['%EV']:.2f}%")
    with col3: st.metric("%AV (Reproducibilidad)",   f"{pcts['%AV']:.2f}%")
    with col4:
        ndc = results['ndc']
        st.metric("ndc", ndc)
        if ndc >= 5: st.success("✅ Adecuado")
        else: st.warning("⚠️ Insuficiente")

    sort_by   = st.radio("Ordenar por", ["%GRR","%EV","%AV","%PV"], horizontal=True, key="grr_sort")
    sort_desc = st.checkbox("Mayor a menor", value=True, key="grr_sort_desc")
    result_df = pd.DataFrame({
        'Componente':           ['Repetibilidad (EV)','Reproducibilidad (AV)','Gage R&R (GRR)','Variación Parte (PV)'],
        'σ':                    [f"{results['std_dev'][k]:.6f}" for k in ['EV','AV','GRR','PV']],
        'Variación del Estudio':[f"{results['study_var'][k]:.6f}" for k in ['EV','AV','GRR','PV']],
        '%EV':  [pcts['%EV'],0,0,0],
        '%AV':  [0,pcts['%AV'],0,0],
        '%GRR': [0,0,pcts['%GRR'],0],
        '%PV':  [0,0,0,pcts['%PV']],
    })
    result_df = result_df.sort_values(sort_by, ascending=not sort_desc)
    st.dataframe(result_df[['Componente','σ','Variación del Estudio']], use_container_width=True, hide_index=True)

    t1, t2, t3, t4 = st.tabs(["Componentes","X-bar & R","Interacción","Distribución por Operador"])
    with t1:
        fig = go.Figure(go.Bar(
            x=['%EV','%AV','%GRR','%PV'],
            y=[pcts['%EV'],pcts['%AV'],pcts['%GRR'],pcts['%PV']],
            marker_color=['#3498db','#e74c3c','#f39c12','#27ae60'],
            text=[f"{v:.2f}%" for v in [pcts['%EV'],pcts['%AV'],pcts['%GRR'],pcts['%PV']]],
            textposition='outside'
        ))
        fig.add_hline(y=10, line_dash="dash", line_color="green")
        fig.add_hline(y=30, line_dash="dash", line_color="orange")
        fig.update_layout(height=420, yaxis_title="% Variación Total")
        st.plotly_chart(fig, use_container_width=True)
    with t2:
        if not df_meas.empty: _xbar_r_chart(df_meas)
    with t3:
        if not df_meas.empty: _interaction_chart(df_meas)
    with t4:
        if not df_meas.empty: _boxplot_by_operator(df_meas)

    st.markdown("---")
    meta = _study_meta_form("GRR", gage_id or "N/A", inst_uuid or "", "grr_meta")
    flat = {**pcts, "ndc": results["ndc"],
            **{f"SD_{k}":v for k,v in results["std_dev"].items()}}
    records = []
    if not df_meas.empty:
        for _, row in df_meas.iterrows():
            records.append({"study_id": "__PLACEHOLDER__",
                            "part_id": str(row.get("Part","?")),
                            "operator": str(row.get("Operator","?")),
                            "trial": int(row.get("Trial",1)),
                            "measurement": float(row.get("Measurement",0))})
    _save_and_pdf_row(meta, flat, "GRR", "gt_msa_grr_data", records, "grr")


def _natural_sort_parts(parts):
    import re
    def _key(s):
        return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', str(s))]
    return sorted(parts, key=_key)


def _xbar_r_chart(df):
    grp = df.groupby(["Part","Operator"])["Measurement"].agg(["mean", lambda x: x.max()-x.min()])
    grp.columns = ["Mean","Range"]
    grp = grp.reset_index()
    sorted_parts = _natural_sort_parts(df["Part"].unique())
    grp["Part"] = pd.Categorical(grp["Part"], categories=sorted_parts, ordered=True)
    grp = grp.sort_values("Part")

    fig = make_subplots(rows=2, cols=1, subplot_titles=("X-bar Chart","R Chart"))
    colors_list = px.colors.qualitative.Set2
    for i, op in enumerate(sorted(df["Operator"].unique())):
        d = grp[grp["Operator"]==op]
        fig.add_trace(go.Scatter(x=d["Part"].astype(str), y=d["Mean"], mode="markers+lines",
                                 name=op, line=dict(color=colors_list[i%len(colors_list)]),
                                 legendgroup=op), row=1, col=1)
        fig.add_trace(go.Scatter(x=d["Part"].astype(str), y=d["Range"], mode="markers+lines",
                                 name=op, line=dict(color=colors_list[i%len(colors_list)]),
                                 legendgroup=op, showlegend=False), row=2, col=1)
    grand_mean = grp["Mean"].mean(); grand_r = grp["Range"].mean()
    fig.add_hline(y=grand_mean,             line_dash="dash", line_color="green", row=1, col=1)
    fig.add_hline(y=grand_mean+1.88*grand_r, line_dash="dot", line_color="red",   row=1, col=1)
    fig.add_hline(y=grand_mean-1.88*grand_r, line_dash="dot", line_color="red",   row=1, col=1)
    fig.add_hline(y=grand_r,     line_dash="dash", line_color="green", row=2, col=1)
    fig.add_hline(y=3.27*grand_r, line_dash="dot", line_color="red",  row=2, col=1)
    fig.update_layout(height=650)
    st.plotly_chart(fig, use_container_width=True)


def _boxplot_by_operator(df):
    colors_list = px.colors.qualitative.Set2
    fig1 = go.Figure()
    for i, op in enumerate(sorted(df["Operator"].unique())):
        d = df[df["Operator"] == op]["Measurement"]
        fig1.add_trace(go.Box(y=d, name=op, marker_color=colors_list[i % len(colors_list)],
                            boxmean=True, boxpoints="all", jitter=0.3))
    fig1.update_layout(title="Distribución por Operador", height=420, showlegend=False)
    st.plotly_chart(fig1, use_container_width=True)

    sorted_parts = _natural_sort_parts(df["Part"].unique())
    fig2 = go.Figure()
    for i, part in enumerate(sorted_parts):
        d = df[df["Part"] == part]["Measurement"]
        fig2.add_trace(go.Box(y=d, name=str(part), marker_color=colors_list[i % len(colors_list)],
                            boxmean=True, boxpoints="all", jitter=0.3))
    fig2.update_layout(title="Distribución por Pieza", height=420, showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)


def _interaction_chart(df):
    inter = df.groupby(["Part","Operator"])["Measurement"].mean().reset_index()
    sorted_parts = _natural_sort_parts(df["Part"].unique())
    inter["Part"] = pd.Categorical(inter["Part"], categories=sorted_parts, ordered=True)
    inter = inter.sort_values("Part")
    fig = px.line(inter, x="Part", y="Measurement", color="Operator", markers=True, title="Interacción Parte × Operador")
    fig.update_layout(height=450)
    st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────
# STABILITY
# ─────────────────────────────────────────────

def render_stability_tab():
    st.markdown("## 📈 Estudio de Estabilidad")
    gage_id, inst_uuid = _gage_selector("stab_gage")

    col1, col2 = st.columns(2)
    with col1:
        n_subgroups  = st.number_input("Subgrupos", 5, 50, 10, key="stab_sg")
        n_readings   = st.number_input("Lecturas por subgrupo", 2, 10, 3, key="stab_rd")
    with col2:
        reference_val = st.number_input("Valor de Referencia", value=0.0, format="%.4f", key="stab_ref")

    rows = [{"Subgrupo": s, "Lectura": r, "Medición": 0.0}
            for s in range(1, n_subgroups+1)
            for r in range(1, n_readings+1)]
    df_stab = st.data_editor(pd.DataFrame(rows), use_container_width=True, num_rows="fixed",
                              column_config={"Medición": st.column_config.NumberColumn(format="%.4f")})

    if st.button("🔬 Analizar Estabilidad", type="primary", key="stab_analyze"):
        grp    = df_stab.groupby("Subgrupo")["Medición"]
        means  = grp.mean()
        ranges = grp.apply(lambda x: x.max()-x.min())
        x_bar = means.mean(); r_bar = ranges.mean()
        d2 = {2:1.128,3:1.693,4:2.059,5:2.326}.get(n_readings,1.693)
        A2 = {2:1.880,3:1.023,4:0.729,5:0.577}.get(n_readings,1.023)
        D4 = {2:3.267,3:2.574,4:2.282,5:2.114}.get(n_readings,2.574)
        sigma = r_bar / d2
        UCL_xbar = x_bar + A2*r_bar; LCL_xbar = x_bar - A2*r_bar
        UCL_r    = D4*r_bar
        bias_mean = float((means - reference_val).mean())
        out_ctrl  = int(((means > UCL_xbar) | (means < LCL_xbar)).sum())

        st.session_state["stab_results"] = {
            "x_bar": x_bar,"r_bar": r_bar,"sigma": sigma,
            "UCL_xbar": UCL_xbar,"LCL_xbar": LCL_xbar,"UCL_r": UCL_r,
            "bias_mean": bias_mean,"out_of_control": out_ctrl,
            "means": means.tolist(),"ranges": ranges.tolist(),
            "sg_idx": list(means.index),
        }
        st.session_state["stab_df_val"]    = df_stab.copy()
        st.session_state["stab_ref_val"]   = reference_val
        st.session_state["stab_gage_id_val"]  = gage_id
        st.session_state["stab_uuid_val"]  = inst_uuid
        st.session_state["stab_nread_val"] = n_readings

    if "stab_results" in st.session_state:
        r        = st.session_state["stab_results"]
        sg_idx   = r["sg_idx"]
        means    = r["means"]
        rng_vals = r["ranges"]
        ref_val  = st.session_state.get("stab_ref_val", 0.0)

        fig = make_subplots(rows=2, cols=1, subplot_titles=("Gráfica X-bar (Estabilidad)","Gráfica R"))
        fig.add_trace(go.Scatter(x=sg_idx, y=means, mode="lines+markers", name="Promedio",
                                 line=dict(color="#2a5298")), row=1, col=1)
        fig.add_hline(y=r["x_bar"],    line_dash="dash",  line_color="green",  row=1, col=1)
        fig.add_hline(y=r["UCL_xbar"], line_dash="dot",   line_color="red",    row=1, col=1)
        fig.add_hline(y=r["LCL_xbar"], line_dash="dot",   line_color="red",    row=1, col=1)
        fig.add_hline(y=ref_val,        line_dash="solid", line_color="orange", row=1, col=1)
        fig.add_trace(go.Scatter(x=sg_idx, y=rng_vals, mode="lines+markers", name="Rango",
                                 line=dict(color="#e74c3c")), row=2, col=1)
        fig.add_hline(y=r["r_bar"],  line_dash="dash", line_color="green", row=2, col=1)
        fig.add_hline(y=r["UCL_r"], line_dash="dot",  line_color="red",   row=2, col=1)
        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("X̄", f"{r['x_bar']:.4f}")
        c2.metric("R̄", f"{r['r_bar']:.4f}")
        c3.metric("σ", f"{r['sigma']:.4f}")
        c4.metric("Sesgo promedio", f"{r['bias_mean']:.4f}")

        st.markdown("---")
        meta = _study_meta_form("Stability", st.session_state.get("stab_gage_id_val", "N/A"),
                                st.session_state.get("stab_uuid_val", ""), "stab_meta")
        records = [{"study_id":"__PH__","subgroup":int(row["Subgrupo"]),
                    "measurement":float(row["Medición"]),
                    "reference_value":float(st.session_state.get("stab_ref_val", 0))}
                    for _,row in st.session_state.get("stab_df_val", pd.DataFrame()).iterrows()]
        flat_r = {k:round(v,6) for k,v in r.items() if isinstance(v,(int,float))}
        _save_and_pdf_row(meta, flat_r, "Stability", "gt_msa_stability_data", records, "stab")


# ─────────────────────────────────────────────
# LINEARITY
# ─────────────────────────────────────────────

def render_linearity_tab():
    st.markdown("## 📏 Estudio de Linealidad")
    gage_id, inst_uuid = _gage_selector("lin_gage")

    col1, col2 = st.columns(2)
    with col1: n_parts  = st.number_input("Piezas de referencia", 3, 10, 5, key="lin_nparts")
    with col2: n_trials = st.number_input("Réplicas por pieza",   2, 10, 5, key="lin_ntrials")

    rows = [{"Pieza": f"P{p+1}", "Referencia": 0.0, "Medición": 0.0, "Réplica": r+1}
            for p in range(n_parts) for r in range(n_trials)]
    df_lin = st.data_editor(pd.DataFrame(rows), use_container_width=True, num_rows="fixed",
                             column_config={"Referencia": st.column_config.NumberColumn(format="%.4f"),
                                            "Medición":   st.column_config.NumberColumn(format="%.4f")})

    if st.button("🔬 Analizar Linealidad", type="primary", key="lin_analyze"):
        df_l = df_lin.copy()
        df_l["Sesgo"] = df_l["Medición"] - df_l["Referencia"]
        part_stats = df_l.groupby("Pieza").agg(Referencia=("Referencia","first"), Sesgo_Promedio=("Sesgo","mean")).reset_index()
        refs   = part_stats["Referencia"].values
        biases = part_stats["Sesgo_Promedio"].values
        slope, intercept, r_val, p_val, _ = stats.linregress(refs, biases)
        r2          = r_val**2
        linearity   = abs(slope) * (max(refs)-min(refs)) if max(refs)!=min(refs) else 0
        st.session_state["lin_results"] = {
            "slope":slope,"intercept":intercept,"r_squared":r2,
            "p_value":p_val,"linearity":linearity,
            "refs":refs.tolist(),"biases":biases.tolist(),
        }
        st.session_state["lin_df_val"]    = df_lin.copy()
        st.session_state["lin_gage_id_val"]  = gage_id
        st.session_state["lin_uuid_val"]  = inst_uuid

    if "lin_results" in st.session_state:
        r    = st.session_state["lin_results"]
        refs = r["refs"]; biases = r["biases"]
        x_line = np.linspace(min(refs), max(refs), 100)
        y_line = r["slope"]*x_line + r["intercept"]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=refs, y=biases, mode="markers", name="Sesgo promedio", marker=dict(size=12, color="#2a5298")))
        fig.add_trace(go.Scatter(x=x_line.tolist(), y=y_line.tolist(), mode="lines", name=f"Regresión (R²={r['r_squared']:.4f})", line=dict(color="#e74c3c",width=2)))
        fig.add_hline(y=0, line_dash="dash", line_color="green")
        fig.update_layout(title="Linealidad: Sesgo vs. Referencia", xaxis_title="Referencia", yaxis_title="Sesgo", height=420)
        st.plotly_chart(fig, use_container_width=True)

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Pendiente (b₁)", f"{r['slope']:.4f}")
        c2.metric("R²",             f"{r['r_squared']:.4f}")
        c3.metric("Linealidad",     f"{r['linearity']:.4f}")
        c4.metric("p-valor",        f"{r['p_value']:.4f}")

        st.markdown("---")
        meta = _study_meta_form("Linearity", st.session_state.get("lin_gage_id_val", "N/A"),
                                st.session_state.get("lin_uuid_val", ""), "lin_meta")
        records = [{"study_id":"__PH__","part_id":str(row["Pieza"]),
                    "reference_value":float(row["Referencia"]),
                    "measured_value":float(row["Medición"]),"trial":int(row["Réplica"])}
                    for _,row in st.session_state.get("lin_df_val", pd.DataFrame()).iterrows()]
        flat_r = {k:round(v,6) for k,v in r.items() if isinstance(v,(int,float))}
        _save_and_pdf_row(meta, flat_r, "Linearity", "gt_msa_linearity_data", records, "lin")


# ─────────────────────────────────────────────
# BIAS
# ─────────────────────────────────────────────

def render_bias_tab():
    st.markdown("## ⚖️ Estudio de Sesgo (Bias)")
    gage_id, inst_uuid = _gage_selector("bias_gage")

    col1, col2 = st.columns(2)
    with col1:
        reference_val = st.number_input("Valor de Referencia", value=0.0, format="%.4f", key="bias_ref")
        n_readings    = st.number_input("Lecturas", 10, 50, 25, key="bias_n")
    with col2:
        tolerance = st.number_input("Tolerancia (USL-LSL)", value=1.0, format="%.4f", key="bias_tol")

    rows = [{"Lectura": i+1, "Medición": 0.0} for i in range(n_readings)]
    df_bias = st.data_editor(pd.DataFrame(rows), use_container_width=True, num_rows="fixed",
                              column_config={"Medición": st.column_config.NumberColumn(format="%.4f")})

    if st.button("🔬 Analizar Sesgo", type="primary", key="bias_analyze"):
        measurements = df_bias["Medición"].values
        bias_vals = measurements - reference_val
        x_bar = np.mean(measurements)
        bias  = x_bar - reference_val
        sd    = np.std(measurements, ddof=1)
        n     = len(measurements)
        t_stat, p_value = stats.ttest_1samp(bias_vals, 0)
        pct_bias = abs(bias)/tolerance*100 if tolerance else 0
        st.session_state["bias_results"] = {
            "bias":bias,"pct_bias":pct_bias,"t_stat":t_stat,
            "p_value":p_value,"sd":sd,"n":n,
            "bias_vals":bias_vals.tolist(),"measurements":measurements.tolist(),
        }
        st.session_state["bias_df_val"]        = df_bias.copy()
        st.session_state["bias_ref_val"]   = reference_val
        st.session_state["bias_gage_id_val"]   = gage_id
        st.session_state["bias_uuid_val"]      = inst_uuid

    if "bias_results" in st.session_state:
        r    = st.session_state["bias_results"]
        bv   = r["bias_vals"]
        bias = r["bias"]
        fig  = go.Figure()
        fig.add_trace(go.Histogram(x=bv, name="Sesgo", marker_color="#2a5298", opacity=0.7, nbinsx=15))
        fig.add_vline(x=0,    line_dash="solid", line_color="green")
        fig.add_vline(x=bias, line_dash="dash",  line_color="red", annotation_text=f"Bias={bias:.4f}")
        fig.update_layout(title="Distribución del Sesgo", xaxis_title="Sesgo", height=380)
        st.plotly_chart(fig, use_container_width=True)

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Sesgo", f"{r['bias']:.4f}")
        c2.metric("% Sesgo", f"{r['pct_bias']:.2f}%")
        c3.metric("t estadístico", f"{r['t_stat']:.4f}")
        c4.metric("p-valor", f"{r['p_value']:.4f}")
        if r["p_value"] < 0.05: st.error("❌ Sesgo estadísticamente significativo")
        else:                   st.success("✅ Sesgo no significativo")

        st.markdown("---")
        meta = _study_meta_form("Bias", st.session_state.get("bias_gage_id_val", "N/A"),
                                st.session_state.get("bias_uuid_val", ""), "bias_meta")
        records = [{"study_id":"__PH__","reference_value":float(st.session_state.get("bias_ref_val", 0)),
                    "measured_value":float(m),"trial":i+1}
                    for i,m in enumerate(r["measurements"])]
        flat_r = {k:round(v,6) for k,v in r.items() if isinstance(v,(int,float))}
        _save_and_pdf_row(meta, flat_r, "Bias", "gt_msa_bias_data", records, "bias")


# ─────────────────────────────────────────────
# KAPPA
# ─────────────────────────────────────────────

def render_kappa_tab():
    st.markdown("## 🏷️ Estudio de Kappa (Atributos)")
    gage_id, inst_uuid = _gage_selector("kappa_gage")

    col1, col2, col3 = st.columns(3)
    with col1: n_parts     = st.number_input("Partes",     10, 50, 20, key="k_parts")
    with col2: n_appraisers= st.number_input("Evaluadores", 2,  5,  3, key="k_apps")
    with col3: n_trials    = st.number_input("Ensayos",     1,  3,  2, key="k_trials")

    attribute_options = ["Pass","Fail"]
    rows = []
    for p in range(1, n_parts+1):
        row = {"Parte": f"P{p:02d}", "Referencia": "Pass"}
        for a in range(1, n_appraisers+1):
            for t in range(1, n_trials+1):
                row[f"E{a}_T{t}"] = "Pass"
        rows.append(row)

    col_cfg = {"Referencia": st.column_config.SelectboxColumn("Referencia", options=attribute_options)}
    for a in range(1, n_appraisers+1):
        for t in range(1, n_trials+1):
            col_cfg[f"E{a}_T{t}"] = st.column_config.SelectboxColumn(f"Eval{a} T{t}", options=attribute_options)

    df_kappa = st.data_editor(pd.DataFrame(rows), use_container_width=True, column_config=col_cfg)

    if st.button("🔬 Calcular Kappa", type="primary", key="kappa_analyze"):
        from sklearn.metrics import cohen_kappa_score
        ref = df_kappa["Referencia"].values
        kappas = {}; agreements = {}
        for a in range(1, n_appraisers+1):
            col = f"E{a}_T1"
            vals = df_kappa[col].values if col in df_kappa.columns else ref
            try:   k = cohen_kappa_score(ref, vals)
            except: k = float("nan")
            kappas[f"Evaluador {a}"] = round(k, 4)
            agreements[f"Evaluador {a}"] = round((vals==ref).mean()*100, 2)

        st.session_state["kappa_results"] = {"kappas": kappas, "agreements": agreements}
        st.session_state["kappa_df_val"]      = df_kappa.copy()
        st.session_state["kappa_gage_id_val"]    = gage_id
        st.session_state["kappa_uuid_val"]    = inst_uuid
        st.session_state["kappa_napp_val"]    = n_appraisers
        st.session_state["kappa_ntr_val"]      = n_trials

    if "kappa_results" in st.session_state:
        r = st.session_state["kappa_results"]
        kappas = r["kappas"]; agreements = r["agreements"]

        def kappa_status(k):
            if k > 0.9: return "✅ Excelente"
            elif k > 0.7: return "🟡 Aceptable"
            else: return "❌ Inaceptable"

        kappa_df = pd.DataFrame({"Evaluador": list(kappas.keys()), "Kappa": list(kappas.values()), "% Acuerdo vs Ref": list(agreements.values()), "Evaluación": [kappa_status(v) for v in kappas.values()]})
        st.dataframe(kappa_df, use_container_width=True, hide_index=True)

        fig = px.bar(kappa_df, x="Evaluador", y="Kappa", color="Kappa", color_continuous_scale=["red","orange","green"], range_color=[0,1], text="Kappa", title="Kappa de Cohen por Evaluador")
        fig.add_hline(y=0.9, line_dash="dash", line_color="green")
        fig.add_hline(y=0.7, line_dash="dash", line_color="orange")
        fig.update_traces(texttemplate="%{text:.3f}", textposition="outside")
        fig.update_layout(height=380)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        meta = _study_meta_form("Kappa", st.session_state.get("kappa_gage_id_val", "N/A"),
                                st.session_state.get("kappa_uuid_val", ""), "kappa_meta")
        n_app  = st.session_state.get("kappa_napp_val", 1)
        n_tr   = st.session_state.get("kappa_ntr_val", 1)
        df_k   = st.session_state.get("kappa_df_val", pd.DataFrame())
        records = []
        for _,row in df_k.iterrows():
            for a in range(1, n_app+1):
                for t in range(1, n_tr+1):
                    col = f"E{a}_T{t}"
                    if col in row:
                        records.append({"study_id":"__PH__","part_id":str(row["Parte"]),
                                        "appraiser":f"Evaluador {a}","trial":t,
                                        "result":str(row[col]),
                                        "reference_result":str(row["Referencia"])})
        _save_and_pdf_row(meta, kappas, "Kappa", "gt_msa_kappa_data", records, "kappa")


# ─────────────────────────────────────────────
# UNCERTAINTY
# ─────────────────────────────────────────────

def render_uncertainty_tab():
    st.markdown("## 📊 Cálculo de Incertidumbre de Medición")
    gage_id, inst_uuid = _gage_selector("unc_gage")

    default_sources = [
        {"Fuente":"Resolución",        "Tipo":"Tipo B","Distribución":"Rectangular","Valor":0.001,"Divisor":3.464,"Sensibilidad":1.0},
        {"Fuente":"Calibración Patrón","Tipo":"Tipo B","Distribución":"Normal",     "Valor":0.002,"Divisor":2.0,  "Sensibilidad":1.0},
        {"Fuente":"Repetibilidad (EV)","Tipo":"Tipo A","Distribución":"Normal",     "Valor":0.003,"Divisor":1.0,  "Sensibilidad":1.0},
        {"Fuente":"Reproducibilidad",  "Tipo":"Tipo A","Distribución":"Normal",     "Valor":0.001,"Divisor":1.0,  "Sensibilidad":1.0},
        {"Fuente":"Temperatura",       "Tipo":"Tipo B","Distribución":"Rectangular","Valor":0.0005,"Divisor":1.732,"Sensibilidad":1.0},
    ]

    df_unc = st.data_editor(pd.DataFrame(default_sources), use_container_width=True, num_rows="dynamic",
                             column_config={
                                 "Tipo":          st.column_config.SelectboxColumn("Tipo",        options=["Tipo A","Tipo B"]),
                                 "Distribución": st.column_config.SelectboxColumn("Distribución",options=["Normal","Rectangular","Triangular","U"]),
                                 "Valor":         st.column_config.NumberColumn(format="%.6f"),
                                 "Divisor":       st.column_config.NumberColumn(format="%.4f"),
                                 "Sensibilidad": st.column_config.NumberColumn(format="%.4f"),
                             })
    k_factor = st.number_input("Factor de cobertura k", value=2.0, step=0.1, key="unc_k")

    if st.button("🔬 Calcular Incertidumbre", type="primary", key="unc_analyze"):
        df_u = df_unc.copy()
        df_u["u_std"]    = df_u["Valor"] / df_u["Divisor"]
        df_u["u_contrib"]= (df_u["u_std"] * df_u["Sensibilidad"])**2
        u_combined = np.sqrt(df_u["u_contrib"].sum())
        U_expanded = k_factor * u_combined
        st.session_state["unc_results"] = {
            "u_combined": u_combined,"U_expanded": U_expanded,"k": k_factor,
            "n_sources": len(df_u),
        }
        st.session_state["unc_df_val"]    = df_u.copy()
        st.session_state["unc_gage_id_val"]  = gage_id
        st.session_state["unc_uuid_val"]  = inst_uuid
        st.session_state["unc_k_val"] = k_factor

    if "unc_results" in st.session_state:
        r    = st.session_state["unc_results"]
        df_u = st.session_state["unc_df_val"]
        total_var = df_u["u_contrib"].sum()
        df_disp   = df_u[["Fuente","Tipo","Distribución","Valor","Divisor","u_std","Sensibilidad","u_contrib"]].copy()
        df_disp.columns = ["Fuente","Tipo","Distribución","a","Divisor","u_i","c_i","Contribución"]
        df_disp["% Contribución"] = (df_u["u_contrib"] / total_var * 100).round(2)
        st.dataframe(df_disp.style.format({"u_i":"{:.6f}","Contribución":"{:.8f}","% Contribución":"{:.2f}%"}), use_container_width=True, hide_index=True)

        c1,c2,c3 = st.columns(3)
        c1.metric("u_c (Combinada)",  f"{r['u_combined']:.6f}")
        c2.metric(f"U (k={r['k']})", f"{r['U_expanded']:.6f}")
        c3.metric("k",                str(r["k"]))

        fig = px.pie(df_disp, names="Fuente", values="% Contribución", title="Contribución por fuente", hole=0.35)
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(height=380)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        meta    = _study_meta_form("Uncertainty", st.session_state.get("unc_gage_id_val", "N/A"),
                                   st.session_state.get("unc_uuid_val", ""), "unc_meta")
        records = [{"study_id":"__PH__","source":str(row["Fuente"]),
                    "uncertainty_type":str(row["Tipo"]),
                    "distribution":str(row.get("Distribución","Normal")),
                    "value":float(row["Valor"]),"divisor":float(row["Divisor"]),
                    "standard_uncertainty":float(row["u_i"]),
                    "sensitivity":float(row["c_i"]),
                    "contribution":float(row["Contribución"])}
                    for _,row in df_disp.iterrows()]
        flat_r = {k:round(v,8) if isinstance(v,float) else v for k,v in r.items()}
        _save_and_pdf_row(meta, flat_r, "Uncertainty", "gt_msa_uncertainty_data", records, "unc")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def render_msa():
    st.title("📊 MSA — Análisis del Sistema de Medición")
    st.markdown("Estudios según **Manual AIAG MSA** 4ª Edición.")

    tabs = st.tabs(["📐 GRR ANOVA","📈 Estabilidad","📏 Linealidad",
                    "⚖️ Sesgo","🏷️ Kappa","📊 Incertidumbre"])

    with tabs[0]: render_grr_tab()
    with tabs[1]: render_stability_tab()
    with tabs[2]: render_linearity_tab()
    with tabs[3]: render_bias_tab()
    with tabs[4]: render_kappa_tab()
    with tabs[5]: render_uncertainty_tab()


if __name__ == "__main__":
    render_msa()
