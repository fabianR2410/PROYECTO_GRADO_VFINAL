# API Documentation

## COVID-19 Data API

REST API para acceder a datos de COVID-19 procesados.

### Inicio Rápido

```bash
python start_api.py
```

La API estará disponible en: http://localhost:8000

### Documentación Interactiva

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Endpoints Disponibles

### 1. Root Endpoint
```
GET /
```
Información general de la API y lista de endpoints.

**Respuesta:**
```json
{
  "name": "COVID-19 Data API",
  "version": "1.0.0",
  "endpoints": {...}
}
```

### 2. Lista de Países
```
GET /covid/countries
```
Obtiene la lista de todos los países disponibles.

**Respuesta:**
```json
{
  "total": 200,
  "countries": ["Ecuador", "Peru", "Colombia", ...]
}
```

### 3. Lista de Métricas
```
GET /covid/metrics
```
Obtiene todas las métricas disponibles categorizadas.

**Respuesta:**
```json
{
  "total": 50,
  "categories": {
    "cases": ["new_cases", "total_cases", ...],
    "deaths": ["new_deaths", "total_deaths", ...],
    "vaccinations": [...],
    "testing": [...],
    ...
  },
  "all_metrics": [...]
}
```

### 4. Serie de Tiempo
```
GET /covid/timeseries?country=Ecuador&metric=new_cases
```

Obtiene datos de serie de tiempo para un país y métrica específicos.

**Parámetros:**
- `country` (requerido): Nombre del país
- `metric` (requerido): Métrica a obtener (default: "new_cases")
- `start_date` (opcional): Fecha de inicio (YYYY-MM-DD)
- `end_date` (opcional): Fecha de fin (YYYY-MM-DD)

**Ejemplo:**
```bash
curl "http://localhost:8000/covid/timeseries?country=Ecuador&metric=new_cases&start_date=2021-01-01"
```

**Respuesta:**
```json
{
  "country": "Ecuador",
  "metric": "new_cases",
  "data_points": 365,
  "start_date": "2021-01-01",
  "end_date": "2021-12-31",
  "data": [
    {"date": "2021-01-01", "new_cases": 1500},
    {"date": "2021-01-02", "new_cases": 1800},
    ...
  ]
}
```

### 5. Resumen de País
```
GET /covid/summary?country=Ecuador
```

Obtiene estadísticas resumidas para un país.

**Parámetros:**
- `country` (requerido): Nombre del país

**Ejemplo:**
```bash
curl "http://localhost:8000/covid/summary?country=Ecuador"
```

**Respuesta:**
```json
{
  "country": "Ecuador",
  "last_updated": "2025-10-24",
  "totals": {
    "cases": 1500000,
    "deaths": 35000
  },
  "current_rates": {
    "new_cases": 150,
    "new_deaths": 5
  },
  "vaccination": {
    "people_vaccinated": 10000000,
    "people_fully_vaccinated": 8000000,
    "total_boosters": 5000000
  },
  "testing": {
    "total_tests": 5000000,
    "positive_rate": 0.05
  }
}
```

### 6. Comparación entre Países
```
GET /covid/compare?countries=Ecuador,Peru,Colombia&metric=new_cases
```

Compara una métrica entre varios países.

**Parámetros:**
- `countries` (requerido): Lista de países separados por comas
- `metric` (requerido): Métrica a comparar
- `start_date` (opcional): Fecha de inicio
- `end_date` (opcional): Fecha de fin

**Ejemplo:**
```bash
curl "http://localhost:8000/covid/compare?countries=Ecuador,Peru,Colombia&metric=new_cases"
```

**Respuesta:**
```json
{
  "metric": "new_cases",
  "countries": ["Ecuador", "Peru", "Colombia"],
  "comparison": [
    {
      "country": "Ecuador",
      "data": [{"date": "2021-01-01", "new_cases": 1500}, ...]
    },
    {
      "country": "Peru",
      "data": [{"date": "2021-01-01", "new_cases": 3000}, ...]
    },
    ...
  ]
}
```

### 7. Datos Más Recientes
```
GET /covid/latest?countries=Ecuador,Peru
```

Obtiene los datos más recientes para países específicos o todos.

**Parámetros:**
- `countries` (opcional): Lista de países separados por comas

**Ejemplo:**
```bash
# Todos los países
curl "http://localhost:8000/covid/latest"

# Países específicos
curl "http://localhost:8000/covid/latest?countries=Ecuador,Peru"
```

**Respuesta:**
```json
{
  "total_countries": 2,
  "data": [
    {
      "location": "Ecuador",
      "date": "2025-10-24",
      "total_cases": 1500000,
      "new_cases": 150,
      ...
    },
    ...
  ]
}
```

### 8. Estadísticas Globales
```
GET /covid/global
```

Obtiene estadísticas agregadas globales.

**Ejemplo:**
```bash
curl "http://localhost:8000/covid/global"
```

**Respuesta:**
```json
{
  "last_updated": "2025-10-24",
  "total_countries": 200,
  "totals": {
    "total_cases": 700000000,
    "total_deaths": 7000000,
    "new_cases": 50000,
    "new_deaths": 500
  }
}
```

## Métricas Disponibles

### Casos
- `new_cases`: Nuevos casos reportados
- `total_cases`: Total de casos acumulados
- `new_cases_smoothed`: Casos nuevos suavizados (7 días)
- `total_cases_per_million`: Casos totales por millón de habitantes

### Muertes
- `new_deaths`: Nuevas muertes reportadas
- `total_deaths`: Total de muertes acumuladas
- `new_deaths_smoothed`: Muertes nuevas suavizadas (7 días)
- `total_deaths_per_million`: Muertes totales por millón de habitantes

### Vacunación
- `people_vaccinated`: Personas con al menos una dosis
- `people_fully_vaccinated`: Personas completamente vacunadas
- `total_vaccinations`: Total de dosis administradas
- `total_boosters`: Total de dosis de refuerzo
- `people_vaccinated_per_hundred`: Personas vacunadas por cada 100 habitantes

### Testing
- `new_tests`: Nuevas pruebas realizadas
- `total_tests`: Total de pruebas acumuladas
- `positive_rate`: Tasa de positividad
- `tests_per_case`: Pruebas por caso confirmado

### Hospitalización
- `hosp_patients`: Pacientes hospitalizados
- `icu_patients`: Pacientes en UCI

## Códigos de Estado HTTP

- `200 OK`: Solicitud exitosa
- `400 Bad Request`: Parámetros inválidos
- `404 Not Found`: Recurso no encontrado
- `500 Internal Server Error`: Error del servidor

## Manejo de Errores

Todos los errores devuelven un JSON con el siguiente formato:

```json
{
  "detail": "Descripción del error"
}
```

## Ejemplos de Uso

### Python
```python
import requests

# Obtener datos de serie de tiempo
response = requests.get(
    "http://localhost:8000/covid/timeseries",
    params={
        "country": "Ecuador",
        "metric": "new_cases",
        "start_date": "2021-01-01"
    }
)
data = response.json()
print(data)
```

### JavaScript
```javascript
// Obtener resumen de país
fetch('http://localhost:8000/covid/summary?country=Ecuador')
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error('Error:', error));
```

### cURL
```bash
# Comparar países
curl -X GET "http://localhost:8000/covid/compare?countries=Ecuador,Peru,Colombia&metric=new_cases" \
     -H "accept: application/json"
```

## CORS

La API tiene CORS habilitado para permitir solicitudes desde cualquier origen.

## Rate Limiting

Actualmente no hay límites de tasa implementados. Para uso en producción, se recomienda implementar rate limiting.

## Producción

Para ejecutar en producción:

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Soporte

Para problemas o preguntas sobre la API, consulta la documentación interactiva en `/docs` o revisa el código fuente en `api/main.py`.
