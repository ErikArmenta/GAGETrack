"""
Reports Module - Calibration Certificates and Notifications
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from jinja2 import Template
import base64
import sys
sys.path.append('..')
from utils.db_manager import load_data, get_instrument_by_id, get_overdue_instruments

# HTML Template for Calibration Certificate
CERTIFICATE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', Arial, sans-serif;
            padding: 40px;
            background: #f5f5f5;
        }
        
        .certificate {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            padding: 50px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            border: 2px solid #2c3e50;
        }
        
        .header {
            text-align: center;
            border-bottom: 3px solid #3498db;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        
        .logo {
            max-width: 200px;
            margin-bottom: 20px;
        }
        
        .title {
            font-size: 28px;
            font-weight: 700;
            color: #2c3e50;
            margin-bottom: 10px;
        }
        
        .subtitle {
            font-size: 16px;
            color: #7f8c8d;
        }
        
        .info-section {
            margin: 30px 0;
        }
        
        .info-title {
            font-size: 18px;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 15px;
            border-left: 4px solid #3498db;
            padding-left: 10px;
        }
        
        .info-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        
        .info-table td {
            padding: 10px;
            border: 1px solid #ddd;
        }
        
        .info-table td:first-child {
            font-weight: 600;
            background: #ecf0f1;
            width: 40%;
        }
        
        .status-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 14px;
        }
        
        .status-active {
            background: #27ae60;
            color: white;
        }
        
        .status-inactive {
            background: #e74c3c;
            color: white;
        }
        
        .footer {
            margin-top: 50px;
            padding-top: 20px;
            border-top: 2px solid #ecf0f1;
            text-align: center;
        }
        
        .signature-section {
            display: flex;
            justify-content: space-around;
            margin-top: 60px;
        }
        
        .signature {
            text-align: center;
            width: 200px;
        }
        
        .signature-line {
            border-top: 2px solid #2c3e50;
            margin-bottom: 10px;
        }
        
        .qr-section {
            text-align: center;
            margin: 30px 0;
        }
        
        .qr-code {
            max-width: 150px;
            margin: 10px auto;
        }
    </style>
</head>
<body>
    <div class="certificate">
        <div class="header">
            {% if logo_base64 %}
            <img src="data:image/png;base64,{{ logo_base64 }}" class="logo" alt="Company Logo">
            {% endif %}
            <div class="title">CERTIFICADO DE CALIBRACIÓN</div>
            <div class="subtitle">Measurement System Control</div>
        </div>
        
        <div class="info-section">
            <div class="info-title">Información del Instrumento</div>
            <table class="info-table">
                <tr>
                    <td>ID de Instrumento</td>
                    <td><strong>{{ instrument_id }}</strong></td>
                </tr>
                <tr>
                    <td>Descripción</td>
                    <td>{{ description }}</td>
                </tr>
                <tr>
                    <td>Tipo</td>
                    <td>{{ tipo }}</td>
                </tr>
                <tr>
                    <td>Número de Serie</td>
                    <td>{{ serial_number }}</td>
                </tr>
                <tr>
                    <td>Modelo</td>
                    <td>{{ model }}</td>
                </tr>
                <tr>
                    <td>Estatus</td>
                    <td><span class="status-badge status-{{ status_class }}">{{ status }}</span></td>
                </tr>
            </table>
        </div>
        
        <div class="info-section">
            <div class="info-title">Información de Calibración</div>
            <table class="info-table">
                <tr>
                    <td>Fecha de Última Calibración</td>
                    <td>{{ last_calibration }}</td>
                </tr>
                <tr>
                    <td>Próximo Vencimiento</td>
                    <td><strong>{{ next_due }}</strong></td>
                </tr>
                <tr>
                    <td>Frecuencia de Calibración</td>
                    <td>{{ frequency }} días</td>
                </tr>
                <tr>
                    <td>Ubicación Actual</td>
                    <td>{{ location }}</td>
                </tr>
                <tr>
                    <td>Persona Responsable</td>
                    <td>{{ responsible }}</td>
                </tr>
            </table>
        </div>
        
        {% if qr_base64 %}
        <div class="qr-section">
            <div class="info-title">Código QR de Verificación</div>
            <img src="data:image/png;base64,{{ qr_base64 }}" class="qr-code" alt="QR Code">
            <p style="color: #7f8c8d; font-size: 12px;">Escanea para verificar el instrumento</p>
        </div>
        {% endif %}
        
        <div class="signature-section">
            <div class="signature">
                <div class="signature-line"></div>
                <p><strong>Técnico de Calibración</strong></p>
                <p style="color: #7f8c8d; font-size: 12px;">Nombre y Firma</p>
            </div>
            <div class="signature">
                <div class="signature-line"></div>
                <p><strong>Supervisor de Calidad</strong></p>
                <p style="color: #7f8c8d; font-size: 12px;">Nombre y Firma</p>
            </div>
        </div>
        
        <div class="footer">
            <p style="color: #7f8c8d; font-size: 12px;">
                Certificado generado el {{ generation_date }}<br>
                Este documento certifica que el instrumento cumple con los estándares de calibración requeridos.
            </p>
        </div>
    </div>
</body>
</html>
"""

def get_logo_base64():
    """Convert logo to base64 for embedding in HTML"""
    try:
        with open("EA_2.png", "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

def generate_qr_base64(instrument_id):
    """Generate QR code and convert to base64"""
    try:
        import qrcode
        from io import BytesIO
        
        app_url = st.secrets.get("app_url", "http://localhost:8501")
        qr_data = f"{app_url}?id={instrument_id}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img = img.convert("RGB")
        
        buf = BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    except:
        return None

def generate_certificate_html(instrument_data):
    """Generate calibration certificate HTML"""
    
    template = Template(CERTIFICATE_TEMPLATE)
    
    # Prepare data
    logo_base64 = get_logo_base64()
    qr_base64 = generate_qr_base64(instrument_data.get('Id. de Instrumento', 'N/A'))
    
    status = instrument_data.get('Estatus', 'Unknown')
    status_class = 'active' if status == 'Active' else 'inactive'
    
    # Format dates
    last_cal = instrument_data.get('Fecha del última programación')
    next_due = instrument_data.get('Próximo vencimiento')
    
    if pd.notna(last_cal):
        last_cal_str = pd.to_datetime(last_cal).strftime('%d/%m/%Y')
    else:
        last_cal_str = 'N/A'
    
    if pd.notna(next_due):
        next_due_str = pd.to_datetime(next_due).strftime('%d/%m/%Y')
    else:
        next_due_str = 'N/A'
    
    html = template.render(
        logo_base64=logo_base64,
        qr_base64=qr_base64,
        instrument_id=instrument_data.get('Id. de Instrumento', 'N/A'),
        description=instrument_data.get('Descripción', 'N/A'),
        tipo=instrument_data.get('Tipo', 'N/A'),
        serial_number=instrument_data.get('N/S del Instrumento', 'N/A'),
        model=instrument_data.get('No.  de Modelo', 'N/A'),
        status=status,
        status_class=status_class,
        last_calibration=last_cal_str,
        next_due=next_due_str,
        frequency=instrument_data.get('Frecuencia de calibración', 'N/A'),
        location=instrument_data.get('Ubicación Actual', 'N/A'),
        responsible=instrument_data.get('Persona responsable', 'N/A'),
        generation_date=datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    )
    
    return html

def send_email_notification(recipients, subject, body):
    """
    Send email notification (pseudocode/logic for SMTP or Microsoft Graph)
    This is a placeholder - implement with actual SMTP or Graph API
    """
    st.info("""
    **Configuración de Email Pendiente**
    
    Para habilitar notificaciones por email, configura uno de los siguientes métodos:
    
    **Opción 1: SMTP (Outlook)**
    ```python
    import smtplib
    from email.mime.text import MIMEText
    
    smtp_server = "smtp.office365.com"
    smtp_port = 587
    sender_email = "tu_email@empresa.com"
    password = "tu_contraseña"
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = ', '.join(recipients)
    
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, password)
        server.send_message(msg)
    ```
    
    **Opción 2: Microsoft Graph API**
    - Registra una aplicación en Azure AD
    - Obtén permisos para Mail.Send
    - Usa la biblioteca `msal` para autenticación
    """)

def render_reports():
    """Main reports interface"""
    st.title("📄 Reportes y Notificaciones")
    
    tab1, tab2 = st.tabs(["📋 Certificados de Calibración", "📧 Notificaciones"])
    
    with tab1:
        st.markdown("### Generar Certificado de Calibración")
        
        df = load_data()
        
        if df.empty:
            st.warning("No hay instrumentos disponibles.")
        else:
            instrument_ids = df['Id. de Instrumento'].tolist()
            selected_id = st.selectbox("Seleccionar Instrumento", instrument_ids)
            
            if selected_id:
                instrument = get_instrument_by_id(selected_id)
                
                if instrument:
                    # Preview section
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown("#### Vista Previa")
                        st.markdown(f"**ID:** {instrument.get('Id. de Instrumento')}")
                        st.markdown(f"**Descripción:** {instrument.get('Descripción')}")
                        st.markdown(f"**Próximo Vencimiento:** {pd.to_datetime(instrument.get('Próximo vencimiento')).strftime('%d/%m/%Y') if pd.notna(instrument.get('Próximo vencimiento')) else 'N/A'}")
                    
                    with col2:
                        st.markdown("#### Acciones")
                        
                        if st.button("🔍 Ver Certificado", use_container_width=True):
                            html_content = generate_certificate_html(instrument)
                            st.components.v1.html(html_content, height=800, scrolling=True)
                        
                        # Generate and download
                        html_content = generate_certificate_html(instrument)
                        
                        st.download_button(
                            label="📥 Descargar HTML",
                            data=html_content,
                            file_name=f"certificado_{selected_id}_{datetime.now().strftime('%Y%m%d')}.html",
                            mime="text/html",
                            use_container_width=True
                        )
                        
                        st.info("💡 Abre el archivo HTML en tu navegador y usa 'Imprimir a PDF' para obtener el PDF final.")
    
    with tab2:
        st.markdown("### Sistema de Notificaciones por Email")
        
        # Get overdue instruments
        overdue_df = get_overdue_instruments()
        
        if not overdue_df.empty:
            st.markdown(f"""
            <div class="alert-box danger">
                <strong>⚠️ Atención:</strong> Hay {len(overdue_df)} instrumentos con calibración vencida.
            </div>
            """, unsafe_allow_html=True)
            
            st.dataframe(
                overdue_df[['Id. de Instrumento', 'Descripción', 'Próximo vencimiento', 'Días Vencidos']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.success("✅ No hay instrumentos con calibración vencida.")
        
        st.markdown("---")
        st.markdown("#### Configurar Notificación")
        
        with st.form("email_notification_form"):
            recipients = st.text_area(
                "Destinatarios (separados por coma)",
                placeholder="email1@empresa.com, email2@empresa.com"
            )
            
            subject = st.text_input(
                "Asunto",
                value="Alerta: Calibraciones Vencidas"
            )
            
            # Generate default body
            default_body = f"""
Estimado equipo,

Se han detectado {len(overdue_df) if not overdue_df.empty else 0} instrumentos con calibración vencida.

Por favor, revise el sistema para más detalles.

Saludos,
Sistema de Gestión de Instrumentos
            """
            
            body = st.text_area(
                "Mensaje",
                value=default_body,
                height=200
            )
            
            submitted = st.form_submit_button("📧 Enviar Notificación")
            
            if submitted:
                if not recipients:
                    st.error("Por favor ingresa al menos un destinatario.")
                else:
                    recipient_list = [r.strip() for r in recipients.split(',')]
                    send_email_notification(recipient_list, subject, body)
                    st.success(f"✅ Notificación preparada para {len(recipient_list)} destinatario(s).")

if __name__ == "__main__":
    render_reports()
