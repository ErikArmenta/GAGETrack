# COLUMNAS PARA GOOGLE SHEETS - HOJA "BaseDatos"

## ⚠️ IMPORTANTE: Copia EXACTAMENTE estos nombres de columna

Copia la siguiente línea y pégala en la **primera fila** de tu hoja "BaseDatos" en Google Sheets:

```
Id. de Instrumento	Estatus	Descripción	Tipo	Ubicación de Almacén	Ubicación Actual	Fecha del última programación	Próximo vencimiento	Frecuencia de calibración	Unidades de frecuencia	Persona responsable	Custodio actual	N/S del Instrumento	No. de Contabilidad	No.  de Modelo
```

## Pasos para Configurar:

1. Abre tu Google Sheet: https://docs.google.com/spreadsheets/d/1SFFHqero_qBZ8GwWvU88TA8R9ETBKliih9ggEJXR4mc/edit

2. Crea una nueva hoja llamada exactamente: **BaseDatos**

3. Selecciona la celda A1

4. Copia la línea de arriba (las 15 columnas separadas por tabulaciones)

5. Pega en A1

6. Verifica que tengas 15 columnas (A hasta O)

7. Comparte la hoja con: **inventario-almacen@gestionterritorial.iam.gserviceaccount.com** (permisos de Editor)

## Verificación:

Tus columnas deben verse así:

| A | B | C | D | E | F | G | H | I | J | K | L | M | N | O |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Id. de Instrumento | Estatus | Descripción | Tipo | Ubicación de Almacén | Ubicación Actual | Fecha del última programación | Próximo vencimiento | Frecuencia de calibración | Unidades de frecuencia | Persona responsable | Custodio actual | N/S del Instrumento | No. de Contabilidad | No.  de Modelo |

## Datos de Ejemplo:

Puedes copiar los datos del archivo `GAGE TRACK 2026...xlsx` a partir de la fila 2.

## ✅ Listo!

Una vez configurado, ejecuta la aplicación con:

```bash
streamlit run app.py
```

Y verifica que los datos se carguen correctamente en el Dashboard.
