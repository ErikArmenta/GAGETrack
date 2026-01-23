"""
Inventory Management Module
CRUD operations for instruments with QR code generation
"""
import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from datetime import datetime, timedelta
import sys
sys.path.append('..')
from utils.db_manager import (
    load_data, add_instrument, update_instrument, 
    delete_instrument, get_instrument_by_id, generate_next_id
)

def generate_qr_code(instrument_id, fill_color="#000000", back_color="#FFFFFF", box_size=10):
    """Generate QR code for an instrument"""
    # Create URL with instrument ID parameter
    app_url = st.secrets.get("app_url", "http://localhost:8501")
    qr_data = f"{app_url}?id={instrument_id}"
    
    # Create QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=box_size,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    # Generate image
    img = qr.make_image(fill_color=fill_color, back_color=back_color)
    img = img.convert("RGB")
    
    return img

def render_qr_generator(instrument_id):
    """Render QR code generator section"""
    st.markdown("### 🔳 Generador de Código QR")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fill_color = st.color_picker("Color del QR", "#000000")
    with col2:
        back_color = st.color_picker("Color de Fondo", "#FFFFFF")
    
    box_size = st.slider("Tamaño", min_value=5, max_value=20, value=10)
    
    if st.button("Generar Código QR"):
        img = generate_qr_code(instrument_id, fill_color, back_color, box_size)
        
        # Display QR code
        st.image(img, caption=f"QR Code para {instrument_id}", use_container_width=False, width=300)
        
        # Download option
        buf = BytesIO()
        img.save(buf, format="PNG")
        byte_im = buf.getvalue()
        
        st.download_button(
            label="📥 Descargar Código QR",
            data=byte_im,
            file_name=f"qr_{instrument_id}.png",
            mime="image/png"
        )

def render_add_instrument_form():
    """Render form to add new instrument"""
    st.markdown("### ➕ Agregar Nuevo Instrumento")
    
    with st.form("add_instrument_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_id = generate_next_id()
            instrument_id = st.text_input("ID de Instrumento", value=new_id, disabled=True)
            descripcion = st.text_input("Descripción *", placeholder="Ej: VERNIER 6\"")
            tipo = st.selectbox("Tipo *", [
                "INSTRUMENTO",
                "GO NOGO",
                "EQUIPO",
                "PATRON",
                "HERRAMIENTA"
            ])
            ubicacion_almacen = st.text_input("Ubicación de Almacén *", placeholder="Ej: CALIDAD")
            ubicacion_actual = st.text_input("Ubicación Actual *", placeholder="Ej: LABORATORIO DE METROLOGIA")
            numero_serie = st.text_input("Número de Serie", placeholder="Opcional")
            numero_contabilidad = st.text_input("No. de Contabilidad", placeholder="Opcional")
        
        with col2:
            estatus = st.selectbox("Estatus *", ["Active", "Inactive", "In Calibration", "Retired"])
            fecha_calibracion = st.date_input("Fecha Última Calibración *", value=datetime.now())
            frecuencia = st.number_input("Frecuencia de Calibración (días) *", min_value=1, value=365)
            
            # Calculate next due date
            next_due = fecha_calibracion + timedelta(days=frecuencia)
            st.date_input("Próximo Vencimiento", value=next_due, disabled=True)
            
            unidades_frecuencia = st.selectbox("Unidades de Frecuencia", ["Daily", "Weekly", "Monthly", "Yearly"])
            persona_responsable = st.text_input("Persona Responsable", placeholder="Ej: INTERNO")
            custodio_actual = st.text_input("Custodio Actual", placeholder="Opcional")
            numero_modelo = st.text_input("No. de Modelo", placeholder="Opcional")
        
        submitted = st.form_submit_button("💾 Guardar Instrumento", use_container_width=True)
        
        if submitted:
            # Validate required fields
            if not descripcion or not tipo or not ubicacion_almacen or not ubicacion_actual:
                st.error("Por favor completa todos los campos obligatorios (*)")
                return
            
            # Create instrument data
            instrument_data = {
                'Id. de Instrumento': instrument_id,
                'Estatus': estatus,
                'Descripción': descripcion,
                'Tipo': tipo,
                'Ubicación de Almacén': ubicacion_almacen,
                'Ubicación Actual': ubicacion_actual,
                'Fecha del última programación': fecha_calibracion,
                'Próximo vencimiento': next_due,
                'Frecuencia de calibración': frecuencia,
                'Unidades de frecuencia': unidades_frecuencia,
                'Persona responsable': persona_responsable,
                'Custodio actual': custodio_actual,
                'N/S del Instrumento': numero_serie,
                'No. de Contabilidad': numero_contabilidad,
                'No.  de Modelo': numero_modelo
            }
            
            # Add to database
            if add_instrument(instrument_data):
                st.success(f"✅ Instrumento {instrument_id} agregado exitosamente!")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ Error al agregar el instrumento. Verifica la conexión.")

def render_edit_instrument_form():
    """Render form to edit existing instrument"""
    st.markdown("### ✏️ Editar Instrumento")
    
    df = load_data()
    
    if df.empty:
        st.warning("No hay instrumentos disponibles para editar.")
        return
    
    # Select instrument to edit
    instrument_ids = df['Id. de Instrumento'].tolist()
    selected_id = st.selectbox("Seleccionar Instrumento", instrument_ids)
    
    if selected_id:
        instrument = get_instrument_by_id(selected_id)
        
        if instrument:
            with st.form("edit_instrument_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.text_input("ID de Instrumento", value=selected_id, disabled=True)
                    descripcion = st.text_input("Descripción *", value=instrument.get('Descripción', ''))
                    tipo = st.selectbox("Tipo *", [
                        "INSTRUMENTO", "GO NOGO", "EQUIPO", "PATRON", "HERRAMIENTA"
                    ], index=["INSTRUMENTO", "GO NOGO", "EQUIPO", "PATRON", "HERRAMIENTA"].index(
                        instrument.get('Tipo', 'INSTRUMENTO')
                    ) if instrument.get('Tipo') in ["INSTRUMENTO", "GO NOGO", "EQUIPO", "PATRON", "HERRAMIENTA"] else 0)
                    
                    ubicacion_almacen = st.text_input("Ubicación de Almacén *", 
                                                     value=instrument.get('Ubicación de Almacén', ''))
                    ubicacion_actual = st.text_input("Ubicación Actual *", 
                                                    value=instrument.get('Ubicación Actual', ''))
                    numero_serie = st.text_input("Número de Serie", 
                                                value=instrument.get('N/S del Instrumento', ''))
                    numero_contabilidad = st.text_input("No. de Contabilidad", 
                                                       value=instrument.get('No. de Contabilidad', ''))
                
                with col2:
                    estatus = st.selectbox("Estatus *", 
                                         ["Active", "Inactive", "In Calibration", "Retired"],
                                         index=["Active", "Inactive", "In Calibration", "Retired"].index(
                                             instrument.get('Estatus', 'Active')
                                         ) if instrument.get('Estatus') in ["Active", "Inactive", "In Calibration", "Retired"] else 0)
                    
                    fecha_cal = instrument.get('Fecha del última programación')
                    if pd.notna(fecha_cal):
                        fecha_calibracion = st.date_input("Fecha Última Calibración *", 
                                                         value=pd.to_datetime(fecha_cal).date())
                    else:
                        fecha_calibracion = st.date_input("Fecha Última Calibración *", 
                                                         value=datetime.now())
                    
                    frecuencia = st.number_input("Frecuencia de Calibración (días) *", 
                                               min_value=1, 
                                               value=int(instrument.get('Frecuencia de calibración', 365)))
                    
                    next_due = fecha_calibracion + timedelta(days=frecuencia)
                    st.date_input("Próximo Vencimiento", value=next_due, disabled=True)
                    
                    unidades_frecuencia = st.selectbox("Unidades de Frecuencia", 
                                                      ["Daily", "Weekly", "Monthly", "Yearly"],
                                                      index=["Daily", "Weekly", "Monthly", "Yearly"].index(
                                                          instrument.get('Unidades de frecuencia', 'Daily')
                                                      ) if instrument.get('Unidades de frecuencia') in ["Daily", "Weekly", "Monthly", "Yearly"] else 0)
                    
                    persona_responsable = st.text_input("Persona Responsable", 
                                                       value=instrument.get('Persona responsable', ''))
                    custodio_actual = st.text_input("Custodio Actual", 
                                                   value=instrument.get('Custodio actual', ''))
                    numero_modelo = st.text_input("No. de Modelo", 
                                                 value=instrument.get('No.  de Modelo', ''))
                
                col1, col2 = st.columns(2)
                with col1:
                    submitted = st.form_submit_button("💾 Actualizar", use_container_width=True)
                with col2:
                    delete = st.form_submit_button("🗑️ Eliminar", use_container_width=True, type="secondary")
                
                if submitted:
                    updated_data = {
                        'Estatus': estatus,
                        'Descripción': descripcion,
                        'Tipo': tipo,
                        'Ubicación de Almacén': ubicacion_almacen,
                        'Ubicación Actual': ubicacion_actual,
                        'Fecha del última programación': fecha_calibracion,
                        'Próximo vencimiento': next_due,
                        'Frecuencia de calibración': frecuencia,
                        'Unidades de frecuencia': unidades_frecuencia,
                        'Persona responsable': persona_responsable,
                        'Custodio actual': custodio_actual,
                        'N/S del Instrumento': numero_serie,
                        'No. de Contabilidad': numero_contabilidad,
                        'No.  de Modelo': numero_modelo
                    }
                    
                    if update_instrument(selected_id, updated_data):
                        st.success(f"✅ Instrumento {selected_id} actualizado exitosamente!")
                        st.rerun()
                    else:
                        st.error("❌ Error al actualizar el instrumento.")
                
                if delete:
                    if delete_instrument(selected_id):
                        st.success(f"✅ Instrumento {selected_id} eliminado exitosamente!")
                        st.rerun()
                    else:
                        st.error("❌ Error al eliminar el instrumento.")
            
            # QR Code section for this instrument
            st.markdown("---")
            render_qr_generator(selected_id)

def render_inventory():
    """Main inventory management interface"""
    st.title("📦 Gestión de Inventario")
    
    tab1, tab2 = st.tabs(["➕ Agregar Instrumento", "✏️ Editar Instrumento"])
    
    with tab1:
        render_add_instrument_form()
    
    with tab2:
        render_edit_instrument_form()

if __name__ == "__main__":
    render_inventory()
