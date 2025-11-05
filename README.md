# Proyecto de Métricas COVID-19

Sistema completo para análisis y visualización de datos de COVID-19 con API REST y dashboard interactivo.

## Características

- **Pipeline de Datos**: Descarga, limpieza e imputación automática
- **API REST**: Endpoints para acceder a series de tiempo y estadísticas
- **Dashboard Interactivo**: Visualizaciones avanzadas con mapas y gráficos
- **Generación de Características**: Métricas epidemiológicas avanzadas
- **Exportación Flexible**: Múltiples formatos (CSV, Excel, Parquet, JSON)

## Estructura del Proyecto

```
covid_project/
├── data/
│   ├── raw/              # Datos descargados sin procesar
│   └── processed/        # Datos procesados y listos para análisis
├── scripts/
│   ├── data_loader.py    # Carga de datos desde fuentes externas
│   ├── data_cleaner.py   # Limpieza y validación de datos
│   ├── data_imputer.py   # Imputación de valores faltantes
│   ├── feature_engineer.py  # Generación de características
│   └── data_saver.py     # Exportación de resultados
├── api/
│   ├── main.py          # API REST con FastAPI
│   └── README.md        # Documentación de la API
├── dashboard/
│   ├── app.py           # Dashboard interactivo con Streamlit
│   └── README.md        # Documentación del dashboard
├── script_prueba/        # Notebooks de exploración
├── main.py              # Pipeline completo
├── quick_start.py       # Inicio rápido
├── start_api.py         # Iniciar servidor API
├── start_dashboard.py   # Iniciar dashboard
└── requirements.txt     # Dependencias
```

## Instalación

### Requisitos previos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Pasos de instalación

1. Clona o descarga el proyecto
2. Instala las dependencias:

```bash
pip install -r requirements.txt
```

## Uso

### Inicio Rápido

Para procesar datos COVID con configuración predeterminada:

```bash
python quick_start.py
```

Esto descargará datos recientes, los limpiará, imputará valores faltantes y generará características básicas.

### Pipeline Completo

Para mayor control sobre el procesamiento:

```bash
# Ver todas las opciones disponibles
python main.py --help

# Procesar con configuración personalizada
python main.py --source owid --locations "Spain,France,Germany" --output-format parquet

# Generar solo características específicas
python main.py --features mortality vaccination testing --no-download
```

### API REST

#### Iniciar la API

```bash
python start_api.py
```

La API estará disponible en: `http://localhost:8000`

Documentación interactiva: `http://localhost:8000/docs`

#### Ejemplos de Uso de la API

```bash
# Obtener lista de países
curl http://localhost:8000/covid/countries

# Serie de tiempo para Ecuador
curl "http://localhost:8000/covid/timeseries?country=Ecuador&metric=new_cases"

# Resumen de estadísticas
curl "http://localhost:8000/covid/summary?country=Ecuador"

# Comparar países
curl "http://localhost:8000/covid/compare?countries=Ecuador,Peru,Colombia&metric=new_cases"

# Obtener datos más recientes
curl "http://localhost:8000/covid/latest?countries=Ecuador"

# Estadísticas globales
curl "http://localhost:8000/covid/global"
```

Ver documentación completa en: [`api/README.md`](api/README.md)

### Dashboard Interactivo

#### Iniciar el Dashboard

```bash
python start_dashboard.py
```

El dashboard estará disponible en: `http://localhost:8501`

#### Características del Dashboard

- 🗺️ **Mapa Mundial Coroplético**: Visualiza cualquier métrica por país
- 📈 **Series de Tiempo**: Compara múltiples métricas entre países
- 📊 **Comparación de Países**: Gráficos de barras con valores recientes
- 🔍 **Análisis Detallado**: Promedios móviles y estadísticas por país
- 💾 **Exportación de Datos**: Descarga datos filtrados en CSV
- 🎯 **Filtros Interactivos**: Selección de países, métricas y fechas

Ver documentación completa en: [`dashboard/README.md`](dashboard/README.md)

### Opciones del Pipeline

- `--source`: Fuente de datos ('owid' o 'owid_latest')
- `--locations`: Países a procesar (separados por comas)
- `--features`: Características a generar (mortality, vaccination, testing, mobility)
- `--output-format`: Formato de salida (csv, excel, parquet, json)
- `--no-download`: Usar datos existentes sin descargar
- `--verbose`: Mostrar información detallada del procesamiento

### Uso Programático

```python
from scripts.data_loader import CovidDataLoader
from scripts.data_cleaner import CovidDataCleaner
from scripts.feature_engineer import CovidFeatureEngineer

# Cargar datos
loader = CovidDataLoader()
df = loader.load_data(source='owid_latest')

# Limpiar
cleaner = CovidDataCleaner()
df_clean = cleaner.clean_data(df)

# Generar características
engineer = CovidFeatureEngineer()
df_final = engineer.create_all_features(df_clean)
```

## Características Generadas

El sistema genera automáticamente las siguientes características:

### Métricas de Mortalidad
- Tasas de letalidad (CFR)
- Muertes por millón
- Promedios móviles de muertes

### Métricas de Vacunación
- Porcentaje de población vacunada
- Personas totalmente vacunadas
- Dosis de refuerzo

### Métricas de Pruebas
- Tasa de positividad
- Pruebas por millón
- Tests realizados

### Métricas de Movilidad (si están disponibles)
- Cambios en lugares de trabajo
- Cambios en áreas residenciales
- Cambios en lugares de recreación

## Salida de Datos

Los datos procesados se guardan en `data/processed/` con los siguientes archivos:

- `covid_data_*.parquet` - Datos principales (formato eficiente)
- `covid_data_*.csv` - Datos principales (formato legible)
- `*_metadata.json` - Información sobre el procesamiento
- `*_summary.txt` - Estadísticas resumidas

## Solución de Problemas

### Error de conexión
```
Verifica tu conexión a internet
Las fuentes de datos requieren acceso web
```

### Falta de dependencias
```bash
pip install -r requirements.txt --upgrade
```

### Problemas de memoria
```
Para datasets grandes, usa el formato Parquet
Procesa países específicos con --locations
```

### Errores de codificación en Windows
```
El proyecto ya está optimizado para Windows
Todos los archivos usan codificación UTF-8
Los emojis han sido removidos para compatibilidad
```

## Fuentes de Datos

- **Our World in Data**: https://ourworldindata.org/coronavirus
  - Datos globales actualizados diariamente
  - Incluye vacunación, pruebas, casos y muertes
  - Licencia: CC BY 4.0

## Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Mantén el código modular y bien documentado
2. Añade tests para nuevas funcionalidades
3. Actualiza este README con cambios relevantes

## Licencia

Este proyecto se proporciona como está, para fines educativos y de análisis.

## Contacto y Soporte

Para reportar problemas o sugerir mejoras, consulta la documentación en el código o revisa los ejemplos en `script_prueba/`.

---

**Última actualización**: Octubre 2025
**Versión**: 1.0.0
