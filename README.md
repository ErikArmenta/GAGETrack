# 🔧 GageTrack - Sistema de Gestión Metrológica

**Reemplazo moderno para GAGEtrak desarrollado en Python + Streamlit con integración a Google Sheets.**

Este sistema permite gestionar el inventario de instrumentos, programar calibraciones, generar certificados profesionales y realizar estudios MSA (Gage R&R) avanzados según normas AIAG.

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-green.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.50+-red.svg)

---

## 🚀 Características Principales

### 📊 Dashboard de Control
- KPIs en tiempo real (Instrumentos totales, Vencidos, Próximos a vencer).
- Gráficas interactivas de distribución por Estatus y Tipo.
- Tabla dinámica con filtrado avanzado y exportación a CSV.

### 📦 Gestión de Inventario
- **CRUD Completo:** Alta, Baja, Modificación y Consulta de instrumentos.
- **Generación de QR:** Creación automática de códigos QR únicos que vinculan a la ficha del equipo.
- **Historial:** Trazabilidad de cambios y ubicaciones.

### 🔬 Módulo MSA (Gage R&R)
- **Método ANOVA:** Cálculos robustos según manual AIAG (4ta Edición).
- **Métricas:** %GRR, %EV (Repetibilidad), %AV (Reproducibilidad), %PV, ndc.
- **Visualización:** Gráficas de Control X-bar & R, Boxplots, e Interacción Parte vs Operador.

### 📄 Reportes y Certificados
- **Certificados PDF/HTML:** Diseño corporativo con logo, firmas y código QR embebido.
- **Alertas:** Sistema de notificaciones para calibraciones vencidas.

---

## 🛠️ Instalación y Configuración Local

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/GageTrack.git
cd GageTrack
```

### 2. Configurar Entorno Virtual (Recomendado)
```bash
python -m venv venv
# En Windows:
.\venv\Scripts\activate
# En Mac/Linux:
source venv/bin/activate
```

### 3. Instalar Dependencias
Instala las librerías necesarias (específicamente probadas con Python 3.9+):
```bash
pip install -r requirements.txt
```

### 4. Configurar Credenciales
Crea una carpeta `.streamlit` y dentro un archivo `secrets.toml`:
```toml
# .streamlit/secrets.toml

# URL de tu Google Sheet
spreadsheet_url = "https://docs.google.com/spreadsheets/d/TU_ID_DE_SHEET_AQUI/edit"

[gcp_service_account]
type = "service_account"
project_id = "tu-project-id"
private_key_id = "tu-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nTu Clave Privada Aquí\n-----END PRIVATE KEY-----\n"
client_email = "tu-service-account@project.iam.gserviceaccount.com"
client_id = "tu-client-id"
# ... resto de tus credenciales JSON
```

### 5. Configurar Google Sheets
1. Crea una hoja llamada **`BaseDatos`**.
2. Copia EXACTAMENTE los encabezados definidos en [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md).
3. Comparte la hoja con el email de tu Service Account (permiso de Editor).

### 6. Ejecutar la Aplicación
```bash
python -m streamlit run app.py
```

---

## ☁️ Despliegue en Streamlit Cloud (GitHub)

Sigue estos pasos para subir tu proyecto a internet:

### 1. Preparar el Repositorio
Asegúrate de tener el archivo `.gitignore` incluido para **NO subir tus secretos**.
```bash
git init
git add .
git commit -m "Initial commit GageTrack v2.0"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/GageTrack.git
git push -u origin main
```

### 2. Configurar en Streamlit Cloud
1. Ve a [share.streamlit.io](https://share.streamlit.io) y conecta tu cuenta de GitHub.
2. Haz clic en **"New app"**.
3. Selecciona tu repositorio, rama (`main`) y archivo principal (`app.py`).
4. **IMPORTANTE:** Haz clic en **"Advanced settings"**.

### 3. Configurar Secretos en la Nube
En la sección "Secrets", pega el contenido exacto de tu archivo local `.streamlit/secrets.toml`.

```toml
spreadsheet_url = "..."

[gcp_service_account]
...
```
5. Haz clic en **"Save"** y luego en **"Deploy"**.

---

## 📂 Estructura del Proyecto

```
GageTrack/
├── modules/                 # Módulos principales de la aplicación
│   ├── dashboard.py         # Lógica del Dashboard y KPIs
│   ├── inventory.py         # Gestión de inventario y QR
│   ├── msa.py               # Cálculos estadísticos y gráficas
│   └── reports.py           # Generación de certificados
├── utils/                   # Utilidades y configuración
│   ├── db_manager.py        # Conexión a BD (Google Sheets API)
│   └── styles.py            # Estilos CSS personalizados
├── .streamlit/              # Configuración local (NO SUBIR A GITHUB)
│   └── secrets.toml         # Credenciales de acceso
├── assets/                  # Recursos estáticos
├── app.py                   # Punto de entrada principal
├── requirements.txt         # Lista de dependencias
├── DATABASE_SCHEMA.md       # Definición de columnas de la BD
├── EA_2.png                 # Logotipo corporativo
└── README.md                # Documentación del proyecto
```

---

## 🛡️ Notas de Seguridad
- **NUNCA** subas el archivo `secrets.toml` a GitHub.
- El archivo `.gitignore` ya está configurado para prevenir esto.
- Si necesitas dar acceso a alguien más, compárteles el archivo de secretos por un medio seguro privado.

---

## 📞 Soporte
Desarrollado para reemplazar el sistema legacy GAGEtrak.
Para dudas técnicas sobre los cálculos de MSA o la conexión a base de datos, contactar al administrador del sistema.
