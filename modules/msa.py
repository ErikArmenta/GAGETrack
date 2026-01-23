"""
MSA Module - Measurement System Analysis
Gage R&R using ANOVA Method (AIAG Standard)
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols

def calculate_gage_rr_anova(df, parts_col='Part', operators_col='Operator', measurement_col='Measurement'):
    """
    Calculate Gage R&R using ANOVA method
    Based on AIAG MSA Manual
    """
    # Prepare data
    df = df.copy()
    df[parts_col] = df[parts_col].astype(str)
    df[operators_col] = df[operators_col].astype(str)
    
    # Number of parts, operators, and trials
    n_parts = df[parts_col].nunique()
    n_operators = df[operators_col].nunique()
    n_trials = len(df) // (n_parts * n_operators)
    
    # ANOVA Model: Measurement ~ Part + Operator + Part:Operator
    formula = f'{measurement_col} ~ C({parts_col}) + C({operators_col}) + C({parts_col}):C({operators_col})'
    model = ols(formula, data=df).fit()
    anova_table = sm.stats.anova_lm(model, typ=2)
    
    # Extract Mean Squares
    MS_part = anova_table.loc[f'C({parts_col})', 'sum_sq'] / anova_table.loc[f'C({parts_col})', 'df']
    MS_operator = anova_table.loc[f'C({operators_col})', 'sum_sq'] / anova_table.loc[f'C({operators_col})', 'df']
    MS_interaction = anova_table.loc[f'C({parts_col}):C({operators_col})', 'sum_sq'] / anova_table.loc[f'C({parts_col}):C({operators_col})', 'df']
    MS_error = anova_table.loc['Residual', 'sum_sq'] / anova_table.loc['Residual', 'df']
    
    # Variance Components
    var_repeatability = MS_error
    var_reproducibility = (MS_operator - MS_interaction) / (n_parts * n_trials)
    var_interaction = (MS_interaction - MS_error) / n_trials
    var_part = (MS_part - MS_interaction) / (n_operators * n_trials)
    
    # Ensure non-negative variances
    var_repeatability = max(0, var_repeatability)
    var_reproducibility = max(0, var_reproducibility)
    var_interaction = max(0, var_interaction)
    var_part = max(0, var_part)
    
    # Equipment Variation (EV) - Repeatability
    EV = var_repeatability
    
    # Appraiser Variation (AV) - Reproducibility
    AV = var_reproducibility + var_interaction
    
    # Gage R&R
    GRR = EV + AV
    
    # Part Variation (PV)
    PV = var_part
    
    # Total Variation (TV)
    TV = GRR + PV
    
    # Standard Deviations (multiply by 5.15 for 99% confidence, or 6 for 6σ)
    K = 5.15  # AIAG uses 5.15 for study variation
    
    SD_repeatability = np.sqrt(EV)
    SD_reproducibility = np.sqrt(AV)
    SD_GRR = np.sqrt(GRR)
    SD_part = np.sqrt(PV)
    SD_total = np.sqrt(TV)
    
    SV_repeatability = K * SD_repeatability
    SV_reproducibility = K * SD_reproducibility
    SV_GRR = K * SD_GRR
    SV_part = K * SD_part
    SV_total = K * SD_total
    
    # Percentages
    pct_EV = (SV_repeatability / SV_total) * 100 if SV_total > 0 else 0
    pct_AV = (SV_reproducibility / SV_total) * 100 if SV_total > 0 else 0
    pct_GRR = (SV_GRR / SV_total) * 100 if SV_total > 0 else 0
    pct_PV = (SV_part / SV_total) * 100 if SV_total > 0 else 0
    
    # Number of Distinct Categories (ndc)
    ndc = int(np.floor(np.sqrt(2) * (SD_part / SD_GRR))) if SD_GRR > 0 else 0
    
    results = {
        'variance_components': {
            'Repeatability (EV)': EV,
            'Reproducibility (AV)': AV,
            'Interaction': var_interaction,
            'Gage R&R': GRR,
            'Part Variation': PV,
            'Total Variation': TV
        },
        'std_dev': {
            'Repeatability': SD_repeatability,
            'Reproducibility': SD_reproducibility,
            'Gage R&R': SD_GRR,
            'Part': SD_part,
            'Total': SD_total
        },
        'study_var': {
            'Repeatability': SV_repeatability,
            'Reproducibility': SV_reproducibility,
            'Gage R&R': SV_GRR,
            'Part': SV_part,
            'Total': SV_total
        },
        'percentages': {
            '%EV': pct_EV,
            '%AV': pct_AV,
            '%GRR': pct_GRR,
            '%PV': pct_PV
        },
        'ndc': ndc,
        'anova_table': anova_table
    }
    
    return results

def create_xbar_r_charts(df, parts_col='Part', operators_col='Operator', measurement_col='Measurement'):
    """Create X-bar and R charts by operator"""
    
    operators = sorted(df[operators_col].unique())
    
    # Calculate averages and ranges for each part-operator combination
    grouped = df.groupby([parts_col, operators_col])[measurement_col].agg(['mean', lambda x: x.max() - x.min()])
    grouped.columns = ['Mean', 'Range']
    grouped = grouped.reset_index()
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('X-bar Chart by Operator', 'R Chart by Operator'),
        vertical_spacing=0.15
    )
    
    colors = px.colors.qualitative.Set2
    
    for i, operator in enumerate(operators):
        op_data = grouped[grouped[operators_col] == operator]
        
        # X-bar chart
        fig.add_trace(
            go.Scatter(
                x=op_data[parts_col],
                y=op_data['Mean'],
                mode='lines+markers',
                name=f'{operator}',
                line=dict(color=colors[i % len(colors)]),
                marker=dict(size=8),
                legendgroup=operator,
                showlegend=True
            ),
            row=1, col=1
        )
        
        # R chart
        fig.add_trace(
            go.Scatter(
                x=op_data[parts_col],
                y=op_data['Range'],
                mode='lines+markers',
                name=f'{operator}',
                line=dict(color=colors[i % len(colors)]),
                marker=dict(size=8),
                legendgroup=operator,
                showlegend=False
            ),
            row=2, col=1
        )
    
    # Add control limits (simplified - using overall mean and range)
    overall_mean = grouped['Mean'].mean()
    overall_range = grouped['Range'].mean()
    
    # X-bar control limits (using A2 constant for n=2 or 3)
    A2 = 1.88  # for n=2, use 1.02 for n=3
    UCL_xbar = overall_mean + A2 * overall_range
    LCL_xbar = overall_mean - A2 * overall_range
    
    fig.add_hline(y=overall_mean, line_dash="dash", line_color="green", row=1, col=1, 
                  annotation_text="Mean")
    fig.add_hline(y=UCL_xbar, line_dash="dot", line_color="red", row=1, col=1, 
                  annotation_text="UCL")
    fig.add_hline(y=LCL_xbar, line_dash="dot", line_color="red", row=1, col=1, 
                  annotation_text="LCL")
    
    # R chart control limits
    D4 = 3.27  # for n=2, use 2.57 for n=3
    D3 = 0     # for n=2, use 0 for n=3
    UCL_R = D4 * overall_range
    LCL_R = D3 * overall_range
    
    fig.add_hline(y=overall_range, line_dash="dash", line_color="green", row=2, col=1, 
                  annotation_text="R̄")
    fig.add_hline(y=UCL_R, line_dash="dot", line_color="red", row=2, col=1, 
                  annotation_text="UCL")
    
    fig.update_xaxes(title_text="Part", row=1, col=1)
    fig.update_xaxes(title_text="Part", row=2, col=1)
    fig.update_yaxes(title_text="Average", row=1, col=1)
    fig.update_yaxes(title_text="Range", row=2, col=1)
    
    fig.update_layout(height=700, hovermode='x unified')
    
    return fig

def create_interaction_plot(df, parts_col='Part', operators_col='Operator', measurement_col='Measurement'):
    """Create interaction plot (Part vs Operator)"""
    
    # Calculate means for each part-operator combination
    interaction_data = df.groupby([parts_col, operators_col])[measurement_col].mean().reset_index()
    
    fig = go.Figure()
    
    operators = sorted(df[operators_col].unique())
    colors = px.colors.qualitative.Set2
    
    for i, operator in enumerate(operators):
        op_data = interaction_data[interaction_data[operators_col] == operator]
        
        fig.add_trace(go.Scatter(
            x=op_data[parts_col],
            y=op_data[measurement_col],
            mode='lines+markers',
            name=operator,
            line=dict(color=colors[i % len(colors)], width=2),
            marker=dict(size=10)
        ))
    
    fig.update_layout(
        title='Interaction Plot: Part × Operator',
        xaxis_title='Part',
        yaxis_title='Average Measurement',
        hovermode='x unified',
        height=500
    )
    
    return fig

def create_boxplot_by_operator(df, operators_col='Operator', measurement_col='Measurement'):
    """Create boxplot by operator"""
    
    fig = px.box(
        df,
        x=operators_col,
        y=measurement_col,
        color=operators_col,
        points='all',
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    
    fig.update_layout(
        title='Measurement Distribution by Operator',
        xaxis_title='Operator',
        yaxis_title='Measurement',
        showlegend=False,
        height=500
    )
    
    return fig

def create_components_chart(results):
    """Create variance components chart"""
    
    percentages = results['percentages']
    
    fig = go.Figure()
    
    categories = ['%EV\n(Repeatability)', '%AV\n(Reproducibility)', '%GRR\n(Total Gage)', '%PV\n(Part Variation)']
    values = [percentages['%EV'], percentages['%AV'], percentages['%GRR'], percentages['%PV']]
    colors_map = ['#3498db', '#e74c3c', '#f39c12', '#27ae60']
    
    fig.add_trace(go.Bar(
        x=categories,
        y=values,
        marker_color=colors_map,
        text=[f'{v:.2f}%' for v in values],
        textposition='outside'
    ))
    
    # Add acceptance zones
    fig.add_hline(y=10, line_dash="dash", line_color="green", 
                  annotation_text="Acceptable (<10%)", annotation_position="right")
    fig.add_hline(y=30, line_dash="dash", line_color="orange", 
                  annotation_text="Marginal (10-30%)", annotation_position="right")
    
    fig.update_layout(
        title='Variance Components (%)',
        xaxis_title='Component',
        yaxis_title='Percentage of Total Variation',
        height=500,
        yaxis_range=[0, max(values) * 1.2]
    )
    
    return fig

def render_msa():
    """Main MSA interface"""
    st.title("📊 MSA - Análisis del Sistema de Medición")
    st.markdown("### Gage R&R - Método ANOVA (AIAG)")
    
    st.markdown("""
    Este módulo realiza estudios de **Gage R&R** utilizando el método **ANOVA** según el estándar **AIAG**.
    
    **Instrucciones:**
    1. Ingresa los datos de medición (Parte, Operador, Medición)
    2. El sistema calculará automáticamente las variaciones
    3. Revisa las gráficas interactivas y los resultados
    """)
    
    # Data input method
    input_method = st.radio("Método de Entrada de Datos", ["Manual", "Cargar CSV"])
    
    df_measurements = None
    
    if input_method == "Manual":
        st.markdown("#### Entrada Manual de Datos")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            n_parts = st.number_input("Número de Partes", min_value=2, max_value=20, value=10)
        with col2:
            n_operators = st.number_input("Número de Operadores", min_value=2, max_value=5, value=3)
        with col3:
            n_trials = st.number_input("Número de Ensayos", min_value=2, max_value=5, value=2)
        
        # Create empty dataframe for manual entry
        data_rows = []
        for part in range(1, n_parts + 1):
            for operator in ['A', 'B', 'C'][:n_operators]:
                for trial in range(1, n_trials + 1):
                    data_rows.append({
                        'Part': f'P{part}',
                        'Operator': operator,
                        'Trial': trial,
                        'Measurement': 0.0
                    })
        
        df_template = pd.DataFrame(data_rows)
        
        st.markdown("**Ingresa las mediciones:**")
        edited_df = st.data_editor(
            df_template,
            use_container_width=True,
            num_rows="fixed",
            column_config={
                "Part": st.column_config.TextColumn("Parte", disabled=True),
                "Operator": st.column_config.TextColumn("Operador", disabled=True),
                "Trial": st.column_config.NumberColumn("Ensayo", disabled=True),
                "Measurement": st.column_config.NumberColumn("Medición", format="%.4f")
            }
        )
        
        if st.button("🔬 Analizar Datos"):
            df_measurements = edited_df
    
    else:  # CSV Upload
        st.markdown("#### Cargar Archivo CSV")
        st.markdown("El archivo debe contener las columnas: `Part`, `Operator`, `Measurement`")
        
        uploaded_file = st.file_uploader("Seleccionar archivo CSV", type=['csv'])
        
        if uploaded_file is not None:
            df_measurements = pd.read_csv(uploaded_file)
            st.success("✅ Archivo cargado exitosamente")
            st.dataframe(df_measurements.head(10))
            
            if st.button("🔬 Analizar Datos"):
                pass  # df_measurements is already set
    
    # Perform analysis
    if df_measurements is not None and len(df_measurements) > 0:
        # Normalize columns (handle Spanish/English variations)
        df_measurements.columns = df_measurements.columns.str.strip()
        
        # Mapping variations to standard
        col_map = {}
        for col in df_measurements.columns:
            col_lower = col.lower()
            if col_lower in ['parte', 'part', 'id part', 'id parte']:
                col_map[col] = 'Part'
            elif col_lower in ['operador', 'operator', 'appraiser', 'analista']:
                col_map[col] = 'Operator'
            elif col_lower in ['medicion', 'medición', 'measurement', 'value', 'valor', 'reading', 'lectura']:
                col_map[col] = 'Measurement'
        
        if col_map:
            df_measurements = df_measurements.rename(columns=col_map)
        
        # Verify required columns exist
        required_cols = ['Part', 'Operator', 'Measurement']
        missing_cols = [c for c in required_cols if c not in df_measurements.columns]
        
        if missing_cols:
            st.error(f"❌ Faltan columnas requeridas o no se pudieron identificar: {', '.join(missing_cols)}")
            st.info("Asegúrate de que tu CSV tenga columnas como: 'Parte', 'Operador', 'Medición'")
        else:
            try:
                # Calculate Gage R&R
                results = calculate_gage_rr_anova(df_measurements)
                
                st.markdown("---")
                st.markdown("## 📈 Resultados del Análisis")
                
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    grr_pct = results['percentages']['%GRR']
                    color = "green" if grr_pct < 10 else "orange" if grr_pct < 30 else "red"
                    st.metric("% GRR", f"{grr_pct:.2f}%")
                    if grr_pct < 10:
                        st.success("✅ Aceptable")
                    elif grr_pct < 30:
                        st.warning("⚠️ Marginal")
                    else:
                        st.error("❌ Inaceptable")
                
                with col2:
                    st.metric("% EV (Repetibilidad)", f"{results['percentages']['%EV']:.2f}%")
                
                with col3:
                    st.metric("% AV (Reproducibilidad)", f"{results['percentages']['%AV']:.2f}%")
                
                with col4:
                    st.metric("ndc (Categorías)", results['ndc'])
                    if results['ndc'] >= 5:
                        st.success("✅ Adecuado")
                    else:
                        st.warning("⚠️ Insuficiente")
                
                # Variance components table
                st.markdown("### Componentes de Varianza")
                
                variance_df = pd.DataFrame({
                    'Componente': list(results['study_var'].keys()),
                    'Desviación Estándar (σ)': [f"{v:.6f}" for v in results['std_dev'].values()],
                    'Variación del Estudio (5.15σ)': [f"{v:.6f}" for v in results['study_var'].values()],
                    '% Contribución': [
                        f"{results['percentages']['%EV']:.2f}%",
                        f"{results['percentages']['%AV']:.2f}%",
                        f"{results['percentages']['%GRR']:.2f}%",
                        f"{results['percentages']['%PV']:.2f}%",
                        "100.00%"
                    ]
                })
                
                st.dataframe(variance_df, use_container_width=True, hide_index=True)
                
                # Charts
                st.markdown("### 📊 Gráficas de Análisis")
                
                tab1, tab2, tab3, tab4 = st.tabs([
                    "Componentes de Varianza",
                    "X-bar & R Charts",
                    "Interacción Parte × Operador",
                    "Distribución por Operador"
                ])
                
                with tab1:
                    fig_components = create_components_chart(results)
                    st.plotly_chart(fig_components, use_container_width=True)
                
                with tab2:
                    fig_xbar_r = create_xbar_r_charts(df_measurements)
                    st.plotly_chart(fig_xbar_r, use_container_width=True)
                
                with tab3:
                    fig_interaction = create_interaction_plot(df_measurements)
                    st.plotly_chart(fig_interaction, use_container_width=True)
                
                with tab4:
                    fig_boxplot = create_boxplot_by_operator(df_measurements)
                    st.plotly_chart(fig_boxplot, use_container_width=True)
                
                # ANOVA Table
                with st.expander("📋 Ver Tabla ANOVA Completa"):
                    st.dataframe(results['anova_table'], use_container_width=True)
                
                # Export results
                st.markdown("---")
                st.markdown("### 📥 Exportar Resultados")
                
                # Create summary report
                report_data = {
                    'Métrica': ['%GRR', '%EV', '%AV', '%PV', 'ndc'],
                    'Valor': [
                        f"{results['percentages']['%GRR']:.2f}%",
                        f"{results['percentages']['%EV']:.2f}%",
                        f"{results['percentages']['%AV']:.2f}%",
                        f"{results['percentages']['%PV']:.2f}%",
                        results['ndc']
                    ]
                }
                report_df = pd.DataFrame(report_data)
                
                csv = report_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Descargar Resumen (CSV)",
                    data=csv,
                    file_name=f"msa_results_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
                
            except Exception as e:
                st.error(f"❌ Error en el análisis: {str(e)}")
                st.exception(e)

if __name__ == "__main__":
    render_msa()
