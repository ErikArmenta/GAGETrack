"""
Dashboard Module - Main Overview
Displays KPIs and interactive instrument table
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
sys.path.append('..')
from utils.db_manager import load_data, get_kpis, get_overdue_instruments

def render_dashboard():
    """Render the main dashboard"""
    
    st.title("📊 Dashboard - Control de Instrumentos")
    
    # Load data
    df = load_data()
    kpis = get_kpis()
    
    # KPI Section
    st.markdown("### Métricas Clave")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="kpi-card total">
            <div class="kpi-label">Total Instrumentos</div>
            <div class="kpi-value">{kpis['total']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="kpi-card overdue">
            <div class="kpi-label">⚠️ Calibraciones Vencidas</div>
            <div class="kpi-value">{kpis['overdue']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="kpi-card due-soon">
            <div class="kpi-label">🔔 Próximas a Vencer (30 días)</div>
            <div class="kpi-value">{kpis['due_soon']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="kpi-card active">
            <div class="kpi-label">✅ Activos</div>
            <div class="kpi-value">{kpis['active']}</div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown(f"""
        <div class="kpi-card" style="background:linear-gradient(135deg,#27ae60,#2ecc71);color:white;border-radius:10px;padding:1rem;text-align:center;">
            <div class="kpi-label" style="color:rgba(255,255,255,0.85);">🔬 Calibrados (Aprobado)</div>
            <div class="kpi-value">{kpis.get('calibrated', 0)}</div>
        </div>
        """, unsafe_allow_html=True)

    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts Section
    if not df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Status Distribution
            st.markdown("### Distribución por Estatus")
            status_counts = df['Estatus'].value_counts()
            fig_status = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                color_discrete_sequence=px.colors.qualitative.Set3,
                hole=0.4
            )
            fig_status.update_traces(textposition='inside', textinfo='percent+label')
            fig_status.update_layout(
                showlegend=True,
                height=300,
                margin=dict(l=20, r=20, t=30, b=20)
            )
            st.plotly_chart(fig_status, use_container_width=True)
        
        with col2:
            # Type Distribution
            st.markdown("### Distribución por Tipo")
            type_counts = df['Tipo'].value_counts().head(10)
            fig_type = px.bar(
                x=type_counts.values,
                y=type_counts.index,
                orientation='h',
                color=type_counts.values,
                color_continuous_scale='Blues'
            )
            fig_type.update_layout(
                showlegend=False,
                height=300,
                margin=dict(l=20, r=20, t=30, b=20),
                xaxis_title="Cantidad",
                yaxis_title="Tipo"
            )
            st.plotly_chart(fig_type, use_container_width=True)
    
    # Alerts Section
    if kpis['overdue'] > 0:
        st.markdown(f"""
        <div class="alert-box danger">
            <strong>⚠️ Atención:</strong> Hay {kpis['overdue']} instrumentos con calibración vencida.
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("Ver Instrumentos Vencidos"):
            overdue_df = get_overdue_instruments()
            st.dataframe(
                overdue_df[['Id. de Instrumento', 'Descripción', 'Ubicación Actual', 
                           'Próximo vencimiento', 'Días Vencidos']],
                use_container_width=True,
                hide_index=True
            )
    
    if kpis['due_soon'] > 0:
        st.markdown(f"""
        <div class="alert-box warning">
            <strong>🔔 Recordatorio:</strong> {kpis['due_soon']} instrumentos vencen en los próximos 30 días.
        </div>
        """, unsafe_allow_html=True)
    
    # Interactive Table Section
    st.markdown("---")
    st.markdown("### 📋 Tabla Interactiva de Instrumentos")
    
    if not df.empty:
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            ubicaciones = ['Todas'] + sorted(df['Ubicación Actual'].dropna().unique().tolist())
            ubicacion_filter = st.selectbox("Filtrar por Ubicación", ubicaciones)
        
        with col2:
            tipos = ['Todos'] + sorted(df['Tipo'].dropna().unique().tolist())
            tipo_filter = st.selectbox("Filtrar por Tipo", tipos)
        
        with col3:
            estatus = ['Todos'] + sorted(df['Estatus'].dropna().unique().tolist())
            estatus_filter = st.selectbox("Filtrar por Estatus", estatus)
        
        # Apply filters
        filtered_df = df.copy()
        
        if ubicacion_filter != 'Todas':
            filtered_df = filtered_df[filtered_df['Ubicación Actual'] == ubicacion_filter]
        
        if tipo_filter != 'Todos':
            filtered_df = filtered_df[filtered_df['Tipo'] == tipo_filter]
        
        if estatus_filter != 'Todos':
            filtered_df = filtered_df[filtered_df['Estatus'] == estatus_filter]
        
        # Display filtered data
        st.markdown(f"**Mostrando {len(filtered_df)} de {len(df)} instrumentos**")
        
        # Configure columns for better display
        column_config = {
            "Id. de Instrumento": st.column_config.TextColumn("ID", width="small"),
            "Estatus": st.column_config.TextColumn("Estatus", width="small"),
            "Descripción": st.column_config.TextColumn("Descripción", width="medium"),
            "Tipo": st.column_config.TextColumn("Tipo", width="small"),
            "Ubicación Actual": st.column_config.TextColumn("Ubicación", width="medium"),
            "Próximo vencimiento": st.column_config.DateColumn(
                "Próximo Vencimiento",
                format="DD/MM/YYYY",
                width="medium"
            ),
            "Frecuencia de calibración": st.column_config.NumberColumn(
                "Frecuencia",
                width="small"
            ),
            "Calibrado": st.column_config.TextColumn("🔬 Calibrado", width="small"),
        }
        
        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True,
            column_config=column_config,
            height=400
        )
        
        # Export options
        col1, col2 = st.columns([1, 4])
        with col1:
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Exportar CSV",
                data=csv,
                file_name=f"instrumentos_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        with col2:
            if st.button("🔄 Actualizar Datos"):
                st.cache_data.clear()
                st.rerun()
    else:
        st.info("ℹ️ No hay datos disponibles. Verifica la conexión con Supabase o agrega instrumentos.")


if __name__ == "__main__":
    render_dashboard()
