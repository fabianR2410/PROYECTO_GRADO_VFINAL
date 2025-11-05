# GUÍA RÁPIDA - COVID-19 Project v1.1.0
## API + Dashboard + Pipeline de Datos

================================================================================
INICIO EN 4 PASOS
================================================================================

## PASO 1: Instalar Dependencias

```bash
pip install -r requirements.txt
```

## PASO 2: Verificar Instalación

```bash
python test_installation.py
```

Deberías ver: "TODOS LOS TESTS PASARON"

## PASO 3: Procesar Datos (REQUERIDO ANTES DE API/DASHBOARD)

```bash
python quick_start.py
```

Este comando:
- Descarga datos de COVID-19 desde Our World in Data
- Limpia y procesa los datos
- Genera métricas epidemiológicas
- Guarda resultados en data/processed/

⚠️ **IMPORTANTE**: Debes ejecutar este paso antes de usar la API o el Dashboard

## PASO 4: Iniciar API o Dashboard

### Opción A: Iniciar API REST

```bash
python start_api.py
```

- URL: http://localhost:8000
- Documentación: http://localhost:8000/docs
- Endpoints disponibles:
  * `/covid/countries` - Lista de países
  * `/covid/timeseries` - Series de tiempo
  * `/covid/summary` - Resumen por país
  * `/covid/compare` - Comparar países
  * Y más...

### Opción B: Iniciar Dashboard Interactivo

```bash
python start_dashboard.py
```

- URL: http://localhost:8501
- Características:
  * Mapa mundial interactivo
  * Gráficos de series de tiempo
  * Comparación entre países
  * Análisis detallado por país
  * Exportación de datos

================================================================================
EJEMPLOS RÁPIDOS
================================================================================

### API - Ejemplos con cURL

```bash
# 1. Ver países disponibles
curl http://localhost:8000/covid/countries

# 2. Obtener datos de Ecuador
curl "http://localhost:8000/covid/summary?country=Ecuador"

# 3. Serie de tiempo de nuevos casos
curl "http://localhost:8000/covid/timeseries?country=Ecuador&metric=new_cases"

# 4. Comparar Ecuador, Perú y Colombia
curl "http://localhost:8000/covid/compare?countries=Ecuador,Peru,Colombia&metric=new_cases"

# 5. Estadísticas globales
curl "http://localhost:8000/covid/global"
```

### API - Ejemplo con Python

```python
import requests

# Obtener resumen de Ecuador
response = requests.get(
    "http://localhost:8000/covid/summary",
    params={"country": "Ecuador"}
)
print(response.json())

# Comparar países
response = requests.get(
    "http://localhost:8000/covid/compare",
    params={
        "countries": "Ecuador,Peru,Colombia",
        "metric": "new_cases"
    }
)
data = response.json()
```

### Dashboard - Cómo Usar

1. Abre http://localhost:8501 en tu navegador
2. Usa el sidebar para:
   - Seleccionar países (ej: Ecuador, Perú, Colombia)
   - Elegir métricas a visualizar
   - Ajustar rango de fechas
3. Explora las diferentes secciones:
   - Mapa mundial
   - Series de tiempo
   - Comparación de países
   - Análisis detallado
4. Descarga datos usando el botón de exportación

================================================================================
ESTRUCTURA DEL PROYECTO
================================================================================

```
covid_project/
├── data/
│   ├── raw/              # Datos descargados
│   └── processed/        # Datos procesados ← REQUERIDO para API/Dashboard
├── api/
│   ├── main.py          # Servidor API FastAPI
│   └── README.md        # Documentación de API
├── dashboard/
│   ├── app.py           # Aplicación Streamlit
│   └── README.md        # Documentación de Dashboard
├── scripts/             # Módulos de procesamiento
├── quick_start.py       # ← EJECUTAR PRIMERO
├── start_api.py         # Iniciar API
└── start_dashboard.py   # Iniciar Dashboard
```

================================================================================
SOLUCIÓN DE PROBLEMAS COMUNES
================================================================================

### Error: "No processed data files found"

**Problema**: No has ejecutado el pipeline de datos
**Solución**: 
```bash
python quick_start.py
```

### Error: "Address already in use" (API)

**Problema**: El puerto 8000 está ocupado
**Solución**: Cierra otras aplicaciones o usa otro puerto:
```bash
uvicorn api.main:app --port 8001
```

### Error: "Address already in use" (Dashboard)

**Problema**: El puerto 8501 está ocupado
**Solución**: Usa otro puerto:
```bash
streamlit run dashboard/app.py --server.port 8502
```

### Error: "Module not found"

**Problema**: Falta alguna dependencia
**Solución**:
```bash
pip install -r requirements.txt --upgrade
```

### Dashboard no muestra datos

**Problema**: Datos no procesados o cache corrupto
**Solución**:
```bash
# 1. Procesar datos nuevamente
python quick_start.py

# 2. Limpiar cache de Streamlit
streamlit cache clear

# 3. Reiniciar dashboard
python start_dashboard.py
```

================================================================================
MÉTRICAS DISPONIBLES
================================================================================

### Casos
- new_cases: Nuevos casos diarios
- total_cases: Casos acumulados
- new_cases_smoothed: Promedio móvil 7 días

### Muertes
- new_deaths: Nuevas muertes diarias
- total_deaths: Muertes acumuladas
- new_deaths_smoothed: Promedio móvil 7 días

### Vacunación
- people_vaccinated: Personas con ≥1 dosis
- people_fully_vaccinated: Personas completamente vacunadas
- total_vaccinations: Total de dosis
- total_boosters: Dosis de refuerzo

### Testing
- new_tests: Nuevas pruebas diarias
- total_tests: Pruebas acumuladas
- positive_rate: Tasa de positividad

### Tasas (por millón de habitantes)
- total_cases_per_million
- total_deaths_per_million
- total_tests_per_million

================================================================================
FLUJO DE TRABAJO RECOMENDADO
================================================================================

1. **Primera vez:**
   ```bash
   pip install -r requirements.txt
   python test_installation.py
   python quick_start.py
   ```

2. **Desarrollo:**
   ```bash
   # Terminal 1: API
   python start_api.py
   
   # Terminal 2: Dashboard
   python start_dashboard.py
   ```

3. **Actualizar datos:**
   ```bash
   python quick_start.py  # Descarga y procesa nuevos datos
   # Reinicia API y Dashboard
   ```

4. **Análisis personalizado:**
   ```bash
   python main.py --help  # Ver opciones avanzadas
   python main.py --locations "Ecuador,Peru" --features all
   ```

================================================================================
RECURSOS ADICIONALES
================================================================================

📚 Documentación Completa:
- README.md - Documentación principal
- api/README.md - Documentación de API
- dashboard/README.md - Documentación de Dashboard
- CHANGELOG.md - Historial de cambios

🔗 URLs Importantes:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Dashboard: http://localhost:8501

📊 Fuente de Datos:
- Our World in Data: https://ourworldindata.org/coronavirus

================================================================================
PREGUNTAS FRECUENTES
================================================================================

**Q: ¿Cada cuánto se actualizan los datos?**
A: Los datos de Our World in Data se actualizan diariamente. Ejecuta `python quick_start.py` para obtener los datos más recientes.

**Q: ¿Puedo usar la API y el Dashboard simultáneamente?**
A: Sí, puedes ejecutar ambos en terminales separadas.

**Q: ¿Cómo agrego más países?**
A: Todos los países disponibles se cargan automáticamente. Usa el selector en el Dashboard o especifica el país en la API.

**Q: ¿Puedo exportar los datos?**
A: Sí, el Dashboard tiene un botón de exportación a CSV. También puedes acceder a los datos procesados en `data/processed/`.

**Q: ¿Funciona sin internet?**
A: Una vez descargados los datos, la API y el Dashboard funcionan offline. Solo necesitas internet para actualizar datos.

================================================================================

¡Listo para explorar datos de COVID-19! 🦠📊

Para ayuda adicional, consulta los README en cada carpeta.
