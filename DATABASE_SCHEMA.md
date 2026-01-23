# Estructura de la Base de Datos - Google Sheets

## Hoja: "BaseDatos"

Esta es la estructura exacta de columnas que debes crear en tu Google Sheet. **IMPORTANTE:** Los nombres de las columnas deben coincidir EXACTAMENTE como se muestran aquí (incluyendo tildes y espacios).

### Columnas (en orden):

| # | Nombre de Columna | Tipo de Dato | Descripción | Ejemplo |
|---|-------------------|--------------|-------------|---------|
| 1 | Id. de Instrumento | Texto | Identificador único del instrumento | 2SL0001 |
| 2 | Estatus | Texto | Estado actual del instrumento | Active, Inactive, In Calibration, Retired |
| 3 | Descripción | Texto | Descripción del instrumento | VERNIER 6" |
| 4 | Tipo | Texto | Tipo de instrumento | INSTRUMENTO, GO NOGO, EQUIPO, PATRON, HERRAMIENTA |
| 5 | Ubicación de Almacén | Texto | Ubicación de almacenamiento | CALIDAD |
| 6 | Ubicación Actual | Texto | Ubicación actual del instrumento | LABORATORIO DE METROLOGIA |
| 7 | Fecha del última programación | Fecha | Fecha de la última calibración | 2025-06-10 |
| 8 | Próximo vencimiento | Fecha | Fecha del próximo vencimiento | 2026-06-10 |
| 9 | Frecuencia de calibración | Número | Frecuencia en días | 365 |
| 10 | Unidades de frecuencia | Texto | Unidades de la frecuencia | Daily, Weekly, Monthly, Yearly |
| 11 | Persona responsable | Texto | Responsable del instrumento | INTERNO |
| 12 | Custodio actual | Texto | Custodio actual | (Opcional) |
| 13 | N/S del Instrumento | Texto | Número de serie | VERNIER 6" |
| 14 | No. de Contabilidad | Texto | Número de contabilidad | 15334832 |
| 15 | No.  de Modelo | Texto | Número de modelo | CD-6" PSX |

## Instrucciones de Configuración:

### 1. Crear la Hoja de Google Sheets

1. Abre tu Google Sheet: https://docs.google.com/spreadsheets/d/1SFFHqero_qBZ8GwWvU88TA8R9ETBKliih9ggEJXR4mc/edit
2. Crea una hoja llamada **"BaseDatos"** (exactamente con ese nombre)
3. En la primera fila, copia los siguientes nombres de columna **EXACTAMENTE** como aparecen:

```
Id. de Instrumento	Estatus	Descripción	Tipo	Ubicación de Almacén	Ubicación Actual	Fecha del última programación	Próximo vencimiento	Frecuencia de calibración	Unidades de frecuencia	Persona responsable	Custodio actual	N/S del Instrumento	No. de Contabilidad	No.  de Modelo
```

### 2. Dar Permisos a la Cuenta de Servicio

1. En tu Google Sheet, haz clic en "Compartir" (esquina superior derecha)
2. Agrega el email: `inventario-almacen@gestionterritorial.iam.gserviceaccount.com`
3. Dale permisos de **Editor**
4. Haz clic en "Enviar"

### 3. Formato de Datos

- **Fechas**: Formato DD/MM/YYYY o YYYY-MM-DD
- **Números**: Sin comas, solo puntos decimales
- **Texto**: Sin caracteres especiales que puedan causar problemas

### 4. Datos de Ejemplo

Puedes copiar los datos del archivo `GAGE TRACK 2026...xlsx` a esta hoja, asegurándote de que las columnas coincidan exactamente.

## Notas Importantes:

⚠️ **CRÍTICO**: Los nombres de las columnas deben ser EXACTOS. Si hay alguna diferencia (incluso un espacio extra), la aplicación no funcionará correctamente.

✅ **Verificación**: Después de configurar la hoja, ejecuta la aplicación y ve al Dashboard. Si ves los datos cargados correctamente, la configuración es correcta.

🔄 **Caché**: La aplicación cachea los datos por 60 segundos. Si haces cambios en Google Sheets y no los ves reflejados inmediatamente, espera un minuto o reinicia la aplicación.
