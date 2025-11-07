# -*- coding: utf-8 -*-
"""
Panel COVID-19 - Análisis (Versión 2.1 - Corregida y Optimizada)
Este dashboard consulta la API para visualización.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta, date, datetime
import numpy as np
from scipy import stats
import requests
import time
import statsmodels.api as sm
from functools import reduce 

# =============================================================================
# --- 0. CONFIGURACIÓN DE PÁGINA (¡CORREGIDO!) ---
# =============================================================================
# Esto DEBE ser el primer comando de Streamlit
st.set_page_config(
    page_title="Panel COVID-19",
    page_icon="🌍",
    layout="wide" 
)

# =============================================================================
# --- 1. CONFIGURACIÓN Y CONSTANTES ---
# =============================================================================

# --- CONFIGURACIÓN DE LA API ---
API_BASE_URL = st.secrets["API_URL"]
# -------------------------------

# --- CONSTANTES ---
AGGREGATES = ['world', 'europe', 'asia', 'africa', 'north america', 'south america', 'oceania',
              'european union', 'high income', 'upper middle income', 'lower middle income', 'low income']

# --- Listas de Métricas (Tu código original) ---
CROSS_SECTIONAL_EXCLUDE_METRICS = [
    'new_cases', 'new_deaths', 'new_tests', 'new_vaccinations', 
    'new_cases_smoothed', 'new_deaths_smoothed', 'new_tests_smoothed', 'new_vaccinations_smoothed', 
    'new_cases_per_million', 'new_deaths_per_million', 'new_cases_smoothed_per_million', 
    'new_deaths_smoothed_per_million', 'weekly_icu_admissions', 'weekly_hosp_admissions', 
    'weekly_icu_admissions_per_million', 'weekly_hosp_admissions_per_million'
]
STATIC_METRICS_EXCLUDE_LIST = [
    'population', 'population_density', 'median_age', 'aged_65_older', 
    'aged_70_older', 'gdp_per_capita', 'extreme_poverty', 'cardiovasc_death_rate', 
    'diabetes_prevalence', 'female_smokers', 'male_smokers', 'handwashing_facilities', 
    'hospital_beds_per_thousand', 'life_expectancy', 'human_development_index'
]
CUMULATIVE_METRICS_EXCLUDE_LIST = [
    'total_cases', 'total_deaths', 'total_tests', 'total_vaccinations', 
    'people_vaccinated', 'people_fully_vaccinated', 'total_boosters',
    'total_cases_per_million', 'total_deaths_per_million', 
    'total_tests_per_thousand', 'total_vaccinations_per_hundred', 
    'people_vaccinated_per_hundred', 'people_fully_vaccinated_per_hundred', 
    'total_boosters_per_hundred'
]
PIE_ALLOWED_METRICS = [
    'total_cases', 'total_deaths', 'people_vaccinated', 
    'people_fully_vaccinated', 'total_boosters'
]

# =============================================================================
# --- 2. FUNCIONES DE UTILIDAD (Formato, Traducción, Selectores) ---
# =============================================================================

# --- FUNCIÓN PARA FORMATEAR NÚMEROS (MEJORADA) ---
def formatar_numero_grande(num):
    """Abrevia números grandes a M (Millones) o B (Billones/Millardos)."""
    if pd.isna(num):
        return "N/A"
    if abs(num) >= 1_000_000_000:
        return f"{num / 1_000_000_000:.2f} B"
    if abs(num) >= 1_000_000:
        return f"{num / 1_000_000:.2f} M"
    if abs(num) >= 1_000:
        return f"{num / 1_000:.1f} K" 
    if abs(num) < 10 and num != 0:
        return f"{num:.1f}" 
    return f"{num:,.0f}" 

# --- DICCIONARIO DE TRADUCCIÓN (completo) ---
TRANSLATIONS = {
    # Casos
    'total_cases': 'Casos Totales',
    'new_cases': 'Nuevos Casos',
    'new_cases_smoothed': 'Nuevos Casos (media 7 días)',
    'total_cases_per_million': 'Casos Totales por Millón',
    'new_cases_per_million': 'Nuevos Casos por Millón',
    'new_cases_smoothed_per_million': 'Nuevos Casos por Millón (media 7 días)',
    # ... (Tu diccionario de traducciones completo va aquí)
    'total_deaths': 'Muertes Totales',
    'new_deaths': 'Nuevas Muertes',
    'new_deaths_smoothed': 'Nuevas Muertes (media 7 días)',
    'total_deaths_per_million': 'Muertes Totales por Millón',
    'gdp_per_capita': 'PIB per Cápita',
    'life_expectancy': 'Esperanza de Vida',
    'positive_rate': 'Tasa de Positividad (%)',
    'people_fully_vaccinated_per_hundred': 'Personas Totalmente Vacunadas por Cien',
    'location': 'País/Región',
    'iso_code': 'Código ISO',
    'continent': 'Continente',
    'date': 'Fecha',
}

def translate_column(col):
    """Traducir nombre de columna al español."""
    return TRANSLATIONS.get(col, col.replace('_', ' ').title())

def get_translated_columns(df, exclude_cols=[], include_only=[]): 
    """Obtener columnas numéricas traducidas."""
    cols_to_search = df.columns
    if exclude_cols:
        cols_to_search = [c for c in cols_to_search if c not in exclude_cols]
    if include_only: 
        cols_to_search = [c for c in cols_to_search if c in include_only]
    numeric_cols = [c for c in df.select_dtypes(include=['float64', 'int64', 'float', 'int']).columns
                   if c in cols_to_search] 
    return {col: translate_column(col) for col in numeric_cols}

def create_translated_selectbox(label, df, exclude_cols=[], include_only=[], key=None, index=0, default_col=None): 
    """Crear selectbox con opciones traducidas."""
    cols_dict = get_translated_columns(df, exclude_cols=exclude_cols, include_only=include_only) 
    if not cols_dict:
        st.warning(f"No hay métricas disponibles para '{label}' con los filtros aplicados.")
        return None, None
    options_translated = list(cols_dict.values())
    if default_col and default_col in cols_dict:
        try:
            index = options_translated.index(cols_dict[default_col])
        except ValueError:
            index = 0
    elif index >= len(options_translated):
        index = 0
    selected_translated = st.selectbox(label, options_translated, index=index, key=key)
    if not selected_translated:
        return None, None
    original_col = [k for k, v in cols_dict.items() if v == selected_translated][0]
    return original_col, selected_translated

def create_translated_multiselect(label, df, exclude_cols=[], include_only=[], default_cols=[], key=None): 
    """Crear multiselect con opciones traducidas."""
    cols_dict = get_translated_columns(df, exclude_cols=exclude_cols, include_only=include_only) 
    if not cols_dict:
        st.warning(f"No hay métricas disponibles para '{label}' con los filtros aplicados.")
        return [], []
    options_translated = list(cols_dict.values())
    defaults_translated = [translate_column(col) for col in default_cols if col in cols_dict]
    selected_translated = st.multiselect(label, options_translated, default=defaults_translated, key=key)
    original_cols = [k for k, v in cols_dict.items() if v in selected_translated]
    return original_cols, selected_translated

# =============================================================================
# --- 3. CSS PERSONALIZADO ---
# =============================================================================
st.markdown("""
    <style>
    /* ... (Tu CSS completo va aquí) ... */
    .main-title { font-size: 32px; font-weight: 700; }
    .status-badge {
        display: inline-block; padding: 4px 12px; border-radius: 20px;
        font-size: 12px; font-weight: 600; background-color: #28a745; color: white;
    }
    </style>
""", unsafe_allow_html=True)

# =============================================================================
# --- 4. FUNCIONES DE DATOS (API) ---
# =============================================================================

# --- FUNCIÓN DE PING ---
def check_api_status():
    """Comprueba si la API en API_BASE_URL está en línea."""
    try:
        resp = requests.get(f"{API_BASE_URL}/", timeout=2)
        return resp.status_code == 200
    except requests.exceptions.RequestException:
        return False

# --- FUNCIÓN DE CARGA CON CACHÉ TTL (¡CORREGIDA!) ---
@st.cache_data(ttl=120)  # caché por 2 minutos
def load_dashboard_data():
    """
    Carga los datos iniciales (latest, countries, metrics) desde la API.
    Se usa un caché de 2 minutos y un timeout largo para el "cold start" de Render.
    """
    try:
        # ¡CORREGIDO! Timeout aumentado a 45 segundos
        timeout_largo = 45
        
        resp_latest = requests.get(f"{API_BASE_URL}/covid/latest", timeout=timeout_largo)
        resp_latest.raise_for_status()
        df_latest = pd.DataFrame(resp_latest.json().get('data', []))
        if 'date' in df_latest.columns:
            df_latest['date'] = pd.to_datetime(df_latest['date'])

        resp_countries = requests.get(f"{API_BASE_URL}/covid/countries", timeout=timeout_largo)
        resp_countries.raise_for_status()
        countries_list = resp_countries.json().get('countries', [])

        resp_metrics = requests.get(f"{API_BASE_URL}/covid/metrics", timeout=timeout_largo)
        resp_metrics.raise_for_status()
        all_metrics = resp_metrics.json().get('all_metrics', [])

        return df_latest, countries_list, all_metrics

    except requests.exceptions.RequestException as e:
        # ¡MEJORA! Un error más claro para el usuario.
        st.error(f"Error de Conexión con la API: {e}. La API en Render puede estar 'despertando'. Por favor, refresca la página en 30 segundos.")
        return None, None, None

# --- ¡NUEVA FUNCIÓN! (Para Pestaña 2) ---
@st.cache_data(ttl=600) # Caché por 10 minutos
def get_full_history(country):
    """
    Obtiene TODOS los datos históricos para UN país desde el nuevo endpoint.
    Se llama desde la Pestaña 2 (Evolución).
    """
    try:
        timeout_largo = 45 # Timeout largo para el "cold start" de Render
        api_params = {'country': country}
        
        response = requests.get(f"{API_BASE_URL}/covid/country-history", params=api_params, timeout=timeout_largo)
        response.raise_for_status()
        
        data = response.json()
        if not data:
            st.warning(f"No se encontraron datos históricos para '{country}'")
            return pd.DataFrame()
            
        df = pd.DataFrame(data)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            return df.set_index('date') # Devolver con índice de fecha
        else:
            st.error("La respuesta de la API no contiene la columna 'date'.")
            return pd.DataFrame()

    except requests.exceptions.RequestException as e:
        st.error(f"Error cargando el historial para '{country}': {e}")
        return pd.DataFrame()

# =============================================================================
# --- 5. FUNCIONES DE PESTAÑA (Lógica de cada Tab) ---
# =============================================================================

# --- FUNCIÓN Pestaña 1: Vista General ---
def vista_general(df_latest, metrics_df): 
    """LÓGICA PARA LA PESTAÑA 1: VISTA GENERAL"""
    # ... (Tu código de la Pestaña 1 va aquí. No necesita cambios) ...
    st.markdown("### 🗺️ Vista Geográfica")
    # (Omitido por brevedad)

# --- FUNCIÓN Pestaña 2: Evolución por País (¡REFACTORIZADA!) ---
def evolucion_por_pais(countries_list, metrics_df, data_min_date, data_max_date):
    """LÓGICA REFACTORIZADA PARA LA PESTAÑA 2: EVOLUCIÓN POR PAÍS"""

    # --- Filtros ---
    with st.container(border=True): 
        st.markdown('<div class="section-title">⚙️ Filtros de Evolución</div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([2, 3, 2])
        
        # Lista de países filtrada (sin agregados)
        aggregates_for_selector = [agg.title() for agg in AGGREGATES]
        filtered_countries = [c for c in countries_list if c not in aggregates_for_selector]
        # Aseguramos que 'World' (del endpoint) esté disponible
        if 'World' not in filtered_countries:
            filtered_countries.insert(0, 'World')
        
        with col1:
            default_index = filtered_countries.index('Ecuador') if 'Ecuador' in filtered_countries else 0
            selected_country = st.selectbox("País o Región", filtered_countries,
                                           index=default_index, key="evol_country")
            use_log = st.checkbox("Usar escala logarítmica", key="log_evol")
            show_raw_data = st.checkbox("Mostrar datos crudos (barras)", value=True, key="raw_evol")
        with col2:
            selected_metrics, selected_names = create_translated_multiselect(
                "Métricas a Graficar (Acumulativas o Diarias)",
                metrics_df,
                exclude_cols=STATIC_METRICS_EXCLUDE_LIST, 
                default_cols=['new_cases', 'total_cases'], 
                key="metrics_evol"
            )
        with col3:
            date_range = st.date_input(
                "Rango de Fechas",
                value=(data_min_date, data_max_date), 
                min_value=data_min_date, max_value=data_max_date,
                key="evol_date_range"
            )

    # --- Contenedor Principal de Resultados ---
    if selected_metrics and selected_country and len(date_range) == 2:
        
        # --- ¡REFACTOR! Carga de Datos (UNA SOLA LLAMADA A LA API) ---
        with st.spinner(f"Cargando historial completo para {selected_country}... (esto es rápido si está en caché)"):
            df_historia = get_full_history(selected_country)
        
        if df_historia.empty:
            st.warning(f"No se pudieron cargar datos para {selected_country}.")
            st.stop()
            
        # Filtrar el DataFrame local por fecha
        try:
            df_filtrado = df_historia.loc[date_range[0].strftime('%Y-%m-%d'):date_range[1].strftime('%Y-%m-%d')].copy() # type: ignore
        except Exception as e:
            st.error(f"Error al filtrar fechas: {e}")
            df_filtrado = pd.DataFrame()

        if df_filtrado.empty:
            st.warning("No hay datos en el rango de fechas seleccionado.")
            st.stop()

        with st.container(border=True):
            st.markdown(f'<h4>Resultados para {selected_country}</h4>', unsafe_allow_html=True)
            
            # --- KPIs de Resumen ---
            st.markdown(f'<div class="section-title" style="margin-top: 20px;">🗓️ Resumen del Período ({date_range[0].strftime("%Y-%m-%d")} al {date_range[1].strftime("%Y-%m-%d")})</div>', unsafe_allow_html=True) # type: ignore
            
            kpi_cols = st.columns(len(selected_metrics))
            for i, (metric, name) in enumerate(zip(selected_metrics, selected_names)):
                with kpi_cols[i]:
                    if metric in df_filtrado.columns and not df_filtrado[metric].dropna().empty:
                        if metric in CROSS_SECTIONAL_EXCLUDE_METRICS: 
                            total_periodo = df_filtrado[metric].sum()
                            promedio_diario = df_filtrado[metric].mean()
                            pico_maximo = df_filtrado[metric].max()
                            st.metric(label=f"Total {name} (en período)", value=formatar_numero_grande(total_periodo))
                            st.metric(label=f"Promedio Diario", value=formatar_numero_grande(promedio_diario))
                            st.metric(label=f"Pico Máximo", value=formatar_numero_grande(pico_maximo))
                        else: 
                            valor_reciente = df_filtrado[metric].dropna().iloc[-1]
                            valor_inicial = df_filtrado[metric].dropna().iloc[0]
                            st.metric(label=f"Valor Reciente ({name})", value=formatar_numero_grande(valor_reciente))
                            st.metric(label=f"Incremento en Período", value=formatar_numero_grande(valor_reciente - valor_inicial), help="Valor al final menos valor al inicio")
                    else:
                        st.metric(label=f"Total {name}", value="N/A")

            # --- Gráfico de Series de Tiempo ---
            st.markdown("---")
            st.markdown(f'<div class="section-title">📈 Gráfico de Series de Tiempo</div>', unsafe_allow_html=True)
            fig = make_subplots(
                rows=len(selected_metrics), cols=1,
                subplot_titles=selected_names,
                vertical_spacing=0.08, shared_xaxes=True
            )
            colors = ['#0066cc', '#dc3545', '#28a745', '#ffc107', '#17a2b8']
            
            for i, (metric, name) in enumerate(zip(selected_metrics, selected_names)):
                if metric in df_filtrado.columns:
                    country_data = df_filtrado.reset_index() # Plotly necesita 'date' como columna
                    color = colors[i % len(colors)]
                    
                    if metric in CROSS_SECTIONAL_EXCLUDE_METRICS:
                        metric_avg_7 = f"{metric}_avg_7"
                        country_data[metric_avg_7] = country_data[metric].rolling(window=7, center=True, min_periods=1).mean()
                        fill_color_rgba = f'rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.3)'
                        if show_raw_data:
                            fig.add_trace(go.Bar(
                                x=country_data['date'], y=country_data[metric], name=name,
                                marker_color=fill_color_rgba,
                                hovertemplate='<b>%{x|%Y-%m-%d}</b><br>' + f'{name}: %{{y:,.0f}}<extra></extra>'
                            ), row=i+1, col=1)
                        fig.add_trace(go.Scatter(
                            x=country_data['date'], y=country_data[metric_avg_7], name=f"Media 7 Días ({name})",
                            line=dict(color=color, width=3), mode='lines',
                            hovertemplate='<b>%{x|%Y-%m-%d}</b><br>' + f'Media 7 Días: %{{y:,.1f}}<extra></extra>'
                        ), row=i+1, col=1)
                    else: 
                        fig.add_trace(go.Scatter(
                            x=country_data['date'], y=country_data[metric], name=name,
                            line=dict(color=color, width=3), mode='lines',
                            hovertemplate='<b>%{x|%Y-%m-%d}</b><br>' + f'{name}: %{{y:,.0f}}<extra></extra>'
                        ), row=i+1, col=1)
                        
                    if use_log:
                        fig.update_yaxes(type="log", row=i+1, col=1)

            fig.update_layout(height=350 * len(selected_metrics), showlegend=True, hovermode='x unified', barmode='overlay')
            if len(selected_metrics) == 1: fig.update_layout(showlegend=False)
            
            st.plotly_chart(fig, use_container_width=True) 

            # --- Tabla de Datos ---
            with st.expander("Ver datos tabulados"):
                cols_to_show_in_table = [col for col in selected_metrics if col in df_filtrado.columns]
                st.dataframe(df_filtrado[cols_to_show_in_table].rename(columns=TRANSLATIONS).sort_index(ascending=False))
                
    elif not selected_metrics:
        st.info("Selecciona al menos una métrica para graficar.")

# --- FUNCIÓN Pestaña 3: Comparaciones ---
def comparaciones_paises(df_latest, metrics_df): 
    # ... (Tu código para la Pestaña 3 va aquí. No necesita cambios) ...
    st.markdown("### 🌎 Comparaciones (Países)")

# --- FUNCIÓN Pestaña 4: Estadísticas ---
def estadisticas_global(df_latest, metrics_df): 
    # ... (Tu código para la Pestaña 4 va aquí. No necesita cambios) ...
    st.markdown("### 📊 Estadísticas (Global)")

# --- FUNCIÓN Pestaña 5: Correlaciones ---
def correlaciones_global(df_latest, metrics_df): 
    # ... (Tu código para la Pestaña 5 va aquí. No necesita cambios) ...
    st.markdown("### 🔗 Correlaciones (Global)")


# =============================================================================
# --- 6. FUNCIÓN PRINCIPAL (main) ---
# =============================================================================
def main():
    """
    Punto de entrada principal de la aplicación Streamlit.
    """
    
    # --- Título y Estado de la API ---
    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown('<div class="main-title">🌍 Panel COVID-19 - Análisis</div>', unsafe_allow_html=True)
        st.markdown('<div class="subtitle">Datos y comparativas de COVID-19 a nivel mundial y por país</div>', unsafe_allow_html=True)
    with col2:
        if check_api_status():
            st.markdown('<div class="status-badge">✓ API Conectada</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-badge" style="background-color: #dc3545;">API Desconectada</div>', unsafe_allow_html=True)

    # --- Carga de Datos Inicial ---
    try:
        with st.spinner(f"Cargando datos iniciales desde la API ({API_BASE_URL})... (Puede tardar 45s si la API duerme)"):
            df_latest, countries_list, all_metrics = load_dashboard_data()
    except Exception as e:
        st.error(f"Error fatal al intentar cargar datos: {e}")
        st.warning("Asegúrate de que la API esté corriendo y sea accesible.")
        return

    if df_latest is None:
        # El error ya se muestra en load_dashboard_data
        st.stop()

    st.toast("¡Datos cargados exitosamente!", icon="✅")

    # --- Preparación de DataFrames para Selectores ---
    metrics_df = pd.DataFrame({metric: pd.Series(dtype='float64') for metric in (all_metrics or [])})
    
    data_max_date = df_latest['date'].max() if ('date' in df_latest.columns and not df_latest['date'].empty) else pd.to_datetime(date.today())
    # Fijar fecha mínima para evitar errores
    data_min_date = pd.to_datetime("2020-01-22") 
    
    # --- KPIs Globales ---
    st.markdown('<div class="section-title">Resumen Global (Últimos Datos)</div>', unsafe_allow_html=True)
    latest = df_latest 

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_cases = latest['total_cases'].sum() if 'total_cases' in latest.columns else np.nan
        new_cases = latest['new_cases'].sum() if 'new_cases' in latest.columns else np.nan
        st.metric(label="Casos Totales", value=formatar_numero_grande(total_cases),
                  delta=f"{new_cases:,.0f} (Nuevos)" if pd.notna(new_cases) and new_cases != 0 else None)
    with col2:
        total_deaths = latest['total_deaths'].sum() if 'total_deaths' in latest.columns else np.nan
        new_deaths = latest['new_deaths'].sum() if 'new_deaths' in latest.columns else np.nan
        st.metric(label="Muertes Totales", value=formatar_numero_grande(total_deaths),
                  delta=f"{new_deaths:,.0f} (Nuevas)" if pd.notna(new_deaths) and new_deaths != 0 else None, delta_color="inverse")
    with col3:
        pop_label = "Población Mundial"
        pop_help = "Población mundial reportada por Our World in Data ('World')."
        total_pop = np.nan 
        world_pop_row = latest[latest['location'].str.lower() == 'world'] if 'location' in latest.columns else pd.DataFrame()
        if not world_pop_row.empty and 'population' in world_pop_row.columns:
            total_pop = world_pop_row['population'].iloc[0]
        else:
            try:
                non_aggregate_pop = latest[~latest['location'].str.lower().isin(AGGREGATES)]['population'].sum() if 'location' in latest.columns and 'population' in latest.columns else np.nan
                total_pop = non_aggregate_pop
                pop_label = "Población (Suma Países)"
                pop_help = "Suma de poblaciones de países individuales (excluyendo regiones agregadas)."
            except Exception:
                pop_label = "Población (Error)"
                pop_help = "No se pudo calcular la población."
        st.metric(label=pop_label, value=formatar_numero_grande(total_pop), help=pop_help)
    with col4:
        unique_countries = latest[~latest['location'].str.lower().isin(AGGREGATES)]['location'].nunique() if 'location' in latest.columns else 0
        st.metric(label="Países/Regiones", value=unique_countries, help="Número de países/regiones individuales (excluyendo agregados).")
    
    st.markdown("---") # Separador antes de las pestañas
    
    # --- INICIO DE LA CREACIÓN DE PESTAÑAS ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🗺️ Vista Geográfica", 
        "📈 Evolución por País",
        "🌎 Comparaciones (Países)",
        "📊 Estadísticas (Global)",
        "🔗 Correlaciones (Global)"
    ])

    with tab1:
        vista_general(df_latest, metrics_df) 
    with tab2:
        evolucion_por_pais(countries_list, metrics_df, data_min_date, data_max_date)
    with tab3:
        comparaciones_paises(df_latest, metrics_df) 
    with tab4:
        estadisticas_global(df_latest, metrics_df) 
    with tab5:
        correlaciones_global(df_latest, metrics_df) 

    # --- Pie de Página ---
    st.markdown("---")
    unique_countries_count = df_latest[~latest['location'].str.lower().isin(AGGREGATES)]['location'].nunique() if 'location' in latest.columns else 0
    st.markdown(f"""
        <div style='text-align: center; color: #6c757d; padding: 20px;'>
            <p><strong>Fuente de Datos:</strong> API COVID-19 (vía Our World in Data) |
            <strong>Última Actualización:</strong> {data_max_date.strftime('%Y-%m-%d')} |
            <strong>Países/Regiones:</strong> {unique_countries_count:,}</p>
        </div>
    """, unsafe_allow_html=True)

# --- Punto de entrada para ejecutar el script ---
if __name__ == "__main__":
    main()