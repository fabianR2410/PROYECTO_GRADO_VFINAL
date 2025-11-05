# Dashboard Documentation

## COVID-19 Interactive Dashboard

Dashboard interactivo para visualizar y explorar datos de COVID-19 a nivel mundial.

### Inicio Rápido

```bash
python start_dashboard.py
```

El dashboard estará disponible en: http://localhost:8501

## Características Principales

### 1. Estadísticas Globales
Panel superior con métricas clave a nivel mundial:
- Total de casos
- Total de muertes
- Personas vacunadas
- Número de países

### 2. Mapa Mundial Coroplético
Visualización geográfica interactiva que muestra:
- Cualquier métrica seleccionable
- Datos por país
- Escala de colores proporcional
- Hover con información detallada

**Cómo usar:**
1. Selecciona la métrica en el sidebar (ej: "total_cases", "people_vaccinated")
2. El mapa se actualiza automáticamente
3. Pasa el mouse sobre un país para ver detalles

### 3. Análisis de Series de Tiempo
Gráficos de líneas para comparar la evolución temporal:

**Vista Combinada:**
- Múltiples métricas en subgráficos apilados
- Comparación entre países seleccionados
- Zoom y pan interactivo

**Vista Individual:**
- Un gráfico por métrica
- Comparación clara entre países
- Valores actuales mostrados al lado

**Cómo usar:**
1. Selecciona países en el sidebar (ej: Ecuador, Perú, Colombia)
2. Selecciona métricas a comparar (ej: new_cases, new_deaths)
3. Ajusta el rango de fechas si es necesario
4. Cambia entre vistas usando las pestañas

### 4. Comparación entre Países
Gráfico de barras que compara:
- Una métrica específica
- Valores más recientes
- Países seleccionados ordenados

**Cómo usar:**
1. Selecciona la métrica a comparar
2. Los países seleccionados se muestran ordenados
3. Colores indican magnitud relativa

### 5. Análisis Detallado por País
Vista profunda de un país específico:

**Estadísticas Resumidas:**
- Casos totales y nuevos
- Muertes totales y nuevas
- Datos de vacunación

**Promedios Móviles:**
- Suavizado de 7 días para reducir ruido
- Comparación con datos originales
- Visualización de tendencias

**Cómo usar:**
1. Selecciona un país del dropdown
2. Revisa las métricas clave
3. Explora los promedios móviles para métricas específicas

### 6. Visualización de Datos Crudos
Tabla interactiva con:
- Datos filtrados por selección
- Búsqueda y ordenamiento
- Descarga en formato CSV

**Cómo usar:**
1. Expande la sección "View Raw Data"
2. Navega por la tabla
3. Usa el botón de descarga para exportar

## Controles del Sidebar

### Selección de Países
```
Multiselect: Permite seleccionar múltiples países
Default: Ecuador, Perú, Colombia, Brasil
```

### Métrica del Mapa
```
Selectbox: Elige la métrica a mostrar en el mapa mundial
Opciones: Todas las métricas numéricas disponibles
```

### Métricas para Comparación
```
Multiselect: Selecciona métricas para gráficos de serie de tiempo
Default: new_cases, new_deaths
```

### Rango de Fechas
```
Date Input: Filtra datos por rango de fechas
Default: Últimos 90 días
```

## Métricas Disponibles

### Casos
- `new_cases`: Nuevos casos diarios
- `total_cases`: Casos acumulados
- `new_cases_smoothed`: Promedio móvil 7 días
- `total_cases_per_million`: Casos por millón de habitantes

### Muertes
- `new_deaths`: Nuevas muertes diarias
- `total_deaths`: Muertes acumuladas
- `new_deaths_smoothed`: Promedio móvil 7 días
- `total_deaths_per_million`: Muertes por millón de habitantes

### Vacunación
- `people_vaccinated`: Personas con al menos 1 dosis
- `people_fully_vaccinated`: Personas totalmente vacunadas
- `total_vaccinations`: Total de dosis administradas
- `total_boosters`: Dosis de refuerzo
- `people_vaccinated_per_hundred`: % población vacunada

### Testing
- `new_tests`: Nuevas pruebas diarias
- `total_tests`: Pruebas acumuladas
- `positive_rate`: Tasa de positividad
- `tests_per_case`: Pruebas por caso

### Hospitalización
- `hosp_patients`: Pacientes hospitalizados
- `icu_patients`: Pacientes en UCI

## Interactividad

### Gráficos Plotly
Todos los gráficos son interactivos:
- **Zoom**: Arrastra para seleccionar área
- **Pan**: Click y arrastra para mover
- **Hover**: Información detallada al pasar el mouse
- **Leyenda**: Click para ocultar/mostrar series
- **Reset**: Doble click para restablecer vista

### Filtros Dinámicos
Los filtros se actualizan en tiempo real:
- Cambios en países → Actualiza todos los gráficos
- Cambios en métricas → Actualiza visualizaciones
- Cambios en fechas → Filtra todos los datos

## Casos de Uso

### 1. Comparar Ecuador con Vecinos
```
1. Selecciona: Ecuador, Perú, Colombia, Brasil
2. Métrica: new_cases, new_deaths
3. Rango: Últimos 6 meses
4. Observa tendencias en el gráfico de series
```

### 2. Analizar Campaña de Vacunación
```
1. Selecciona países de interés
2. Métricas: people_vaccinated, people_fully_vaccinated
3. Compara en gráfico de barras
4. Revisa evolución en series de tiempo
```

### 3. Estudiar Oleadas de COVID
```
1. Selecciona un país específico
2. Ve a "Detailed Country Analysis"
3. Observa promedios móviles de new_cases
4. Identifica picos y valles
```

### 4. Análisis Regional
```
1. Selecciona países de una región
2. Usa mapa mundial para contexto
3. Compara métricas clave
4. Exporta datos para análisis adicional
```

## Rendimiento

### Optimizaciones
- **Cache de datos**: Los datos se cargan una vez y se cachean
- **Formato eficiente**: Usa Parquet para carga rápida
- **Renderizado selectivo**: Solo actualiza componentes necesarios

### Recomendaciones
- Para datasets grandes, filtra por países
- Usa rangos de fechas razonables
- Limita el número de métricas simultáneas

## Personalización

### Modificar Países por Default
Edita `dashboard/app.py`, línea con `default_countries`:
```python
default_countries = ['Ecuador', 'Peru', 'Colombia', 'Brazil']
```

### Cambiar Colores
Modifica el CSS en la sección `st.markdown()`:
```python
st.markdown("""
    <style>
    .stMetric {
        background-color: #tu_color;
    }
    </style>
""", unsafe_allow_html=True)
```

### Agregar Nuevas Visualizaciones
Crea funciones en `dashboard/app.py`:
```python
def create_custom_chart(df, params):
    # Tu código de visualización
    fig = px.scatter(...)
    return fig
```

## Solución de Problemas

### Dashboard no carga
```bash
# Verifica que los datos estén procesados
ls data/processed/

# Si no hay datos, ejecuta:
python quick_start.py
```

### Gráficos no se muestran
```bash
# Reinstala plotly
pip install --upgrade plotly

# Limpia cache de streamlit
streamlit cache clear
```

### Error de memoria
```
# Reduce el rango de fechas
# Selecciona menos países
# Usa menos métricas simultáneas
```

### Puerto en uso
```bash
# Usa un puerto diferente
streamlit run dashboard/app.py --server.port 8502
```

## Desarrollo

### Estructura del Código
```
dashboard/
├── __init__.py          # Inicialización del módulo
├── app.py              # Aplicación principal
└── README.md           # Esta documentación
```

### Agregar Nueva Pestaña
```python
# En main() de app.py
new_tab = st.tabs(["Existing", "New Tab"])

with new_tab[1]:
    st.write("Tu contenido")
```

### Crear Nuevo Tipo de Gráfico
```python
def create_heatmap(df, metric):
    fig = px.density_heatmap(
        df, 
        x='date', 
        y='location', 
        z=metric
    )
    return fig
```

## Exportación de Datos

El dashboard permite exportar:
- Datos filtrados en CSV
- Gráficos como PNG (botón en cada gráfico)
- Estadísticas personalizadas

## Despliegue

### Local
```bash
python start_dashboard.py
```

### Producción
```bash
streamlit run dashboard/app.py --server.port 80 --server.address 0.0.0.0
```

### Docker (opcional)
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "dashboard/app.py"]
```

## Soporte

Para problemas o preguntas:
1. Revisa esta documentación
2. Consulta el código en `dashboard/app.py`
3. Verifica que los datos estén procesados
4. Revisa los logs de Streamlit

## Recursos Adicionales

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Plotly Python](https://plotly.com/python/)
- [Pandas Documentation](https://pandas.pydata.org/)
