# Changelog

Todas las mejoras y cambios importantes del proyecto se documentan aquí.

## [1.1.0] - 2025-10-24

### 🚀 Nuevas Características Principales

#### API REST
- ✅ Implementada API completa con FastAPI
- ✅ 8 endpoints para acceso a datos:
  - `/` - Información general
  - `/covid/countries` - Lista de países
  - `/covid/metrics` - Métricas disponibles
  - `/covid/timeseries` - Series de tiempo
  - `/covid/summary` - Resumen por país
  - `/covid/compare` - Comparación entre países
  - `/covid/latest` - Datos más recientes
  - `/covid/global` - Estadísticas globales
- ✅ Documentación interactiva con Swagger UI
- ✅ Soporte CORS para integración web
- ✅ Manejo robusto de errores
- ✅ Script de inicio simplificado: `start_api.py`

#### Dashboard Interactivo
- ✅ Dashboard completo con Streamlit
- ✅ Mapa mundial coroplético interactivo
- ✅ Gráficos de series de tiempo comparativas
- ✅ Visualización de promedios móviles (7 días)
- ✅ Comparación de múltiples países
- ✅ Análisis detallado por país
- ✅ Filtros dinámicos (países, métricas, fechas)
- ✅ Exportación de datos a CSV
- ✅ Múltiples vistas y pestañas
- ✅ Script de inicio simplificado: `start_dashboard.py`

### 📚 Documentación
- ✅ `api/README.md` - Documentación completa de la API
- ✅ `dashboard/README.md` - Documentación del dashboard
- ✅ README principal actualizado con ejemplos
- ✅ Ejemplos de uso para cURL, Python y JavaScript

### 🔧 Dependencias Nuevas
- FastAPI>=0.104.0 - Framework para API REST
- uvicorn>=0.24.0 - Servidor ASGI
- Streamlit>=1.28.0 - Framework para dashboards
- Plotly>=5.17.0 - Visualizaciones interactivas
- pydantic>=2.4.0 - Validación de datos

### 📁 Estructura del Proyecto
- ✅ Nueva carpeta `api/` con módulos de API
- ✅ Nueva carpeta `dashboard/` con aplicación web
- ✅ Scripts de inicio dedicados para API y dashboard

## [1.0.0] - 2025-10-24

### Mejoras de Compatibilidad
- ✅ Agregada declaración de codificación UTF-8 a todos los archivos Python
- ✅ Eliminados emojis de quick_start.py para compatibilidad con Windows
- ✅ Verificada compatibilidad multiplataforma (Windows, Linux, macOS)

### Documentación
- ✅ Creado README.md completo con instrucciones de instalación y uso
- ✅ Agregado archivo de configuración config.ini con todas las opciones
- ✅ Creado script de prueba test_installation.py para verificar instalación
- ✅ Agregado .gitignore para control de versiones

### Estructura del Proyecto
- ✅ Organización modular de scripts en carpeta dedicada
- ✅ Separación clara de datos raw y procesados
- ✅ Estructura de carpetas profesional y escalable

### Módulos Implementados

#### data_loader.py
- Descarga automática desde Our World in Data
- Soporte para múltiples fuentes de datos
- Manejo robusto de errores de red
- Cache de datos descargados

#### data_cleaner.py
- Limpieza de valores outliers
- Eliminación de duplicados
- Validación de fechas y tipos de datos
- Manejo de columnas con exceso de valores faltantes

#### data_imputer.py
- Múltiples estrategias de imputación
- Imputación inteligente por tipo de columna
- Forward fill para series temporales
- Interpolación para datos continuos

#### feature_engineer.py
- Generación de métricas epidemiológicas
- Cálculo de tasas de mortalidad y vacunación
- Promedios móviles configurables
- Métricas de testing y movilidad

#### data_saver.py
- Exportación a múltiples formatos (CSV, Excel, Parquet, JSON)
- Generación de metadata automática
- Estadísticas resumidas
- Compresión eficiente de datos

### Scripts de Ejecución

#### quick_start.py
- Inicio rápido con configuración predeterminada
- Pipeline simplificado para usuarios nuevos
- Mensajes informativos de progreso
- Manejo de errores con sugerencias

#### main.py
- Pipeline completo con opciones avanzadas
- Interfaz de línea de comandos (CLI)
- Configuración flexible por argumentos
- Logging detallado

### Testing
- Script de verificación de instalación
- Validación de dependencias
- Verificación de estructura de proyecto
- Tests de importación de módulos

### Dependencias
- pandas>=2.0.0 - Manipulación de datos
- numpy>=1.24.0 - Operaciones numéricas
- requests>=2.31.0 - Descarga de datos
- openpyxl>=3.1.0 - Soporte Excel
- pyarrow>=14.0.0 - Formato Parquet
- matplotlib>=3.7.0 - Visualizaciones
- seaborn>=0.12.0 - Visualizaciones estadísticas
- jupyter>=1.0.0 - Notebooks interactivos
- scikit-learn>=1.3.0 - Machine learning

### Correcciones de Errores
- ✅ Eliminados caracteres problemáticos para Windows
- ✅ Corregidos problemas de codificación UTF-8
- ✅ Instaladas todas las dependencias requeridas
- ✅ Verificada compilación correcta de todos los módulos

### Características Futuras (Planificadas)
- [ ] Soporte para más fuentes de datos
- [ ] Modelos predictivos de tendencias
- [ ] Dashboard interactivo con visualizaciones
- [ ] API REST para acceso a datos procesados
- [ ] Tests automatizados con pytest
- [ ] Integración continua (CI/CD)
- [ ] Documentación de API con Sphinx

---

## Guía de Versionado

El proyecto sigue [Semantic Versioning](https://semver.org/):
- MAJOR: Cambios incompatibles en la API
- MINOR: Nueva funcionalidad compatible con versiones anteriores
- PATCH: Correcciones de errores compatibles

## Cómo Contribuir

Para contribuir al proyecto:
1. Actualiza este CHANGELOG con tus cambios
2. Sigue el formato de versiones semánticas
3. Documenta todas las características nuevas
4. Incluye correcciones de errores relevantes
