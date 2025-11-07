# -*- coding: utf-8 -*-
"""
Panel COVID-19 - Análisis (Versión 4.1 - Estadísticas Mejoradas)

- ELIMINADO: Pestaña interna de Evolución Temporal Comparada (Tab 3).
- ELIMINADO: Sección de Análisis Guiado (Tab 4).
- MEJORADO (Tab 4): Tarjetas de estadísticas en grid 2x2.
- MEJORADO (Tab 4): Añadida escala logarítmica al histograma.
- MEJORADO (Tab 4): Añadido Diagrama de Cajas (Box Plot) para continentes.
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
    page_title="Panel COVID-19 (Proyecto de Grado)",
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

    # Muertes
    'total_deaths': 'Muertes Totales',
    'new_deaths': 'Nuevas Muertes',
    'new_deaths_smoothed': 'Nuevas Muertes (media 7 días)',
    'total_deaths_per_million': 'Muertes Totales por Millón',
    'new_deaths_per_million': 'Nuevas Muertes por Millón',
    'new_deaths_smoothed_per_million': 'Nuevas Muertes por Millón (media 7 días)',

    # Tests
    'total_tests': 'Tests Totales',
    'new_tests': 'Nuevos Tests',
    'new_tests_smoothed': 'Nuevos Tests (media 7 días)',
    'total_tests_per_thousand': 'Tests Totales por Mil',
    'new_tests_per_thousand': 'Nuevos Tests por Mil',
    'new_tests_smoothed_per_thousand': 'Nuevos Tests por Mil (media 7 días)',
    'positive_rate': 'Tasa de Positividad (%)',
    'tests_per_case': 'Tests por Caso',

    # Vacunación
    'total_vaccinations': 'Vacunaciones Totales',
    'people_vaccinated': 'Personas Vacunadas',
    'people_fully_vaccinated': 'Personas Totalmente Vacunadas',
    'total_boosters': 'Dosis de Refuerzo Totales',
    'new_vaccinations': 'Nuevas Vacunaciones',
    'new_vaccinations_smoothed': 'Nuevas Vacunaciones (media 7 días)',
    'total_vaccinations_per_hundred': 'Vacunaciones Totales por Cien',
    'people_vaccinated_per_hundred': 'Personas Vacunadas por Cien',
    'people_fully_vaccinated_per_hundred': 'Personas Totalmente Vacunadas por Cien',
    'total_boosters_per_hundred': 'Dosis de Refuerzo por Cien',
    'new_vaccinations_smoothed_per_million': 'Nuevas Vacunaciones por Millón (media 7 días)',

    # Hospitalización
    'icu_patients': 'Pacientes en UCI',
    'icu_patients_per_million': 'Pacientes en UCI por Millón',
    'hosp_patients': 'Pacientes Hospitalizados',
    'hosp_patients_per_million': 'Pacientes Hospitalizados por Millón',
    'weekly_icu_admissions': 'Ingresos Semanales a UCI',
    'weekly_icu_admissions_per_million': 'Ingresos Semanales a UCI por Millón',
    'weekly_hosp_admissions': 'Ingresos Semanales a Hospital',
    'weekly_hosp_admissions_per_million': 'Ingresos Semanales a Hospital por Millón',

    # Demografía
    'population': 'Población',
    'population_density': 'Densidad de Población',
    'median_age': 'Edad Mediana',
    'aged_65_older': 'Población Mayor de 65 años (%)',
    'aged_70_older': 'Población Mayor de 70 años (%)',
    'gdp_per_capita': 'PIB per Cápita',
    'extreme_poverty': 'Pobreza Extrema (%)',
    'cardiovasc_death_rate': 'Tasa de Mortalidad Cardiovascular',
    'diabetes_prevalence': 'Prevalencia de Diabetes (%)',
    'female_smokers': 'Fumadoras (%)',
    'male_smokers': 'Fumadores (%)',
    'handwashing_facilities': 'Instalaciones de Lavado de Manos (%)',
    'hospital_beds_per_thousand': 'Camas de Hospital por Mil',
    'life_expectancy': 'Esperanza de Vida',
    'human_development_index': 'Índice de Desarrollo Humano',

    # Tasas y ratios
    'reproduction_rate': 'Tasa de Reproducción (R)',
    'stringency_index': 'Índice de Rigurosidad',
    'excess_mortality': 'Mortalidad Excedente',
    'excess_mortality_cumulative': 'Mortalidad Excedente Acumulada',
    'excess_mortality_cumulative_absolute': 'Mortalidad Excedente Acumulada Absoluta',
    'excess_mortality_cumulative_per_million': 'Mortalidad Excedente Acumulada por Millón',

    # Características calculadas
    'cases_per_million': 'Casos por Millón',
    'deaths_per_million': 'Muertes por Millón',
    'case_fatality_rate': 'Tasa de Letalidad (%)',
    'death_rate': 'Tasa de Mortalidad',
    'new_cases_7day_avg': 'Nuevos Casos (promedio 7 días)',
    'new_deaths_7day_avg': 'Nuevas Muertes (promedio 7 días)',
    'new_cases_14day_avg': 'Nuevos Casos (promedio 14 días)',
    'new_deaths_14day_avg': 'Nuevas Muertes (promedio 14 días)',
    'cases_growth_rate': 'Tasa de Crecimiento de Casos',
    'deaths_growth_rate': 'Tasa de Crecimiento de Muertes',
    'new_cases_lag_1': 'Nuevos Casos (día anterior)',
    'new_cases_lag_7': 'Nuevos Casos (hace 7 días)',
    'new_deaths_lag_1': 'Nuevas Muertes (día anterior)',
    'new_deaths_lag_7': 'Nuevas Muertes (hace 7 días)',

    # Ubicación
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
# --- 3. CSS PERSONALIZADO (Estilo Tarjetas) ---
# =============================================================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

    * {
        font-family: 'Poppins', sans-serif;
    }

    /* Fondo de la app (coincide con config.toml) */
    .stApp {
        background-color: #f0f2f5;
    }

    /* Ocultar elementos de Streamlit */
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Títulos */
    .main-title {
        font-size: 32px;
        font-weight: 700;
        color: #1a1a1a; /* Texto oscuro */
        margin-bottom: 5px;
    }
    .subtitle {
        font-size: 14px;
        color: #6c757d; /* Texto gris */
        margin-bottom: 30px;
    }
    .section-title {
        font-size: 18px;
        font-weight: 600;
        color: #1a1a1a;
        margin-bottom: 20px;
    }

    /* ---- ¡EL ESTILO DE "TARJETA"! ---- */
    /* Esto aplica a todos los st.container */
    [data-testid="stVerticalBlock"] > [data-testid="stContainer"] {
        background-color: #FFFFFF; /* Fondo de la tarjeta BLANCO */
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.08); /* Sombra suave */
        border: 1px solid #E0E0E0; /* Borde muy sutil */
    }

    /* Estilo de las Métricas (KPIs) */
    [data-testid="stMetric"] {
        background-color: #FFFFFF; /* Fondo blanco */
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.08);
        border: 1px solid #E0E0E0;
    }

    /* Pestañas (Tabs) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #FFFFFF; /* Fondo de pestañas blanco */
        border-radius: 12px;
        padding: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08);
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: #6c757d;
        border-radius: 8px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e7f3ff; /* Color de pestaña seleccionada (azul claro) */
        color: #0066cc; /* Color primario */
    }
    
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
def render_tab_global(df_latest, metrics_df): 
    """LÓGICA PARA LA PESTAÑA 1: VISTA GENERAL"""
    
    # --- Gráficos Principales (Mapa y Pastel) ---
    main_col1, main_col2 = st.columns([2, 1])

    with main_col1:
        with st.container(border=False): 
            st.markdown('<div class="section-title">🗺️ Distribución Global (Mapa)</div>', unsafe_allow_html=True)
            
            # --- ¡MEJORA! Selector de tipo de mapa ---
            tipo_mapa = st.radio("Tipo de Proyección del Mapa", ["Globo", "Plano"], horizontal=True, key="map_type")
            proyeccion = "orthographic" if tipo_mapa == "Globo" else "natural earth"

            selected_metric_map, selected_name_map = create_translated_selectbox(
                "Seleccione métrica para el mapa",
                metrics_df, 
                exclude_cols=CROSS_SECTIONAL_EXCLUDE_METRICS, 
                key="map_metric",
                default_col='total_cases'
            )

            if selected_metric_map and 'iso_code' in df_latest.columns:
                map_data = df_latest[~df_latest['location'].str.lower().isin(AGGREGATES)]
                fig = go.Figure(data=go.Choropleth(
                    locations=map_data['iso_code'],
                    z=map_data[selected_metric_map],
                    text=map_data['location'],
                    colorscale='Blues', autocolorscale=False, reversescale=False,
                    marker_line_color='darkgray', marker_line_width=0.5,
                    colorbar_title=selected_name_map,
                    hovertemplate='<b>%{text}</b><br>' + f'{selected_name_map}: %{{z:,.0f}}<extra></extra>'
                ))
                fig.update_layout(
                    title_text=f'{selected_name_map} por País',
                    geo=dict(showframe=False, showcoastlines=True, projection_type=proyeccion), # <-- Proyección dinámica
                    height=600, margin=dict(l=0, r=0, t=40, b=0),
                    template="plotly_white"
                )
                st.plotly_chart(fig, use_container_width=True) 
            elif not selected_metric_map:
                st.info("Selecciona una métrica para mostrar el mapa.")

    with main_col2:
        with st.container(border=False): 
            st.markdown('<div class="section-title">🌍 Distribución por Continente</div>', unsafe_allow_html=True)
            
            default_pie_col = 'total_cases' if 'total_cases' in PIE_ALLOWED_METRICS else (PIE_ALLOWED_METRICS[0] if PIE_ALLOWED_METRICS else None)
            selected_metric_bar, selected_name_bar = create_translated_selectbox(
                "Seleccione métrica para el gráfico",
                metrics_df, 
                include_only=PIE_ALLOWED_METRICS, 
                key="pie_metric",
                default_col=default_pie_col
            )

            if selected_metric_bar:
                countries_only_df = df_latest[~df_latest['location'].str.lower().isin(AGGREGATES)]
                if 'continent' in countries_only_df.columns and selected_metric_bar in countries_only_df.columns:
                    pie_data = countries_only_df.groupby('continent')[selected_metric_bar].sum().reset_index()
                    pie_data = pie_data.dropna(subset=['continent', selected_metric_bar])
                    pie_data = pie_data[pie_data[selected_metric_bar] > 0] 
                    
                    if not pie_data.empty:
                        # --- ¡MEJORA! Reemplazado Pastel por Barras Horizontales ---
                        pie_data_sorted = pie_data.sort_values(by=selected_metric_bar, ascending=True)
                        fig_bar = px.bar(
                            pie_data_sorted,
                            x=selected_metric_bar,
                            y='continent',
                            orientation='h',
                            title=f'Distribución de {selected_name_bar} por Continente',
                            template="plotly_white",
                            text=selected_metric_bar
                        )
                        fig_bar.update_traces(texttemplate='%{text:,.2s}', textposition='outside')
                        fig_bar.update_layout(
                            height=600, margin=dict(l=0, r=0, t=40, b=0),
                            yaxis_title="Continente", 
                            xaxis_title=selected_name_bar
                        )
                        st.plotly_chart(fig_bar, use_container_width=True)
                    else:
                        st.warning("No se encontraron datos de países para agrupar por continente.")
                else:
                    st.warning("El DataFrame no contiene la columna 'continent' o la métrica seleccionada para agrupar.")
            else:
                st.info("Selecciona una métrica para mostrar el gráfico.")

# --- FUNCIÓN Pestaña 2: Evolución por País (¡REFACTORIZADA!) ---
def render_tab_pais(countries_list, metrics_df, data_min_date, data_max_date):
    """LÓGICA REFACTORIZADA PARA LA PESTAÑA 2: EVOLUCIÓN POR PAÍS"""

    # --- Filtros ---
    with st.container(border=False): 
        st.markdown('<div class="section-title">⚙️ Filtros de Evolución</div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([2, 3, 2])
        
        aggregates_for_selector = [agg.title() for agg in AGGREGATES]
        filtered_countries = [c for c in countries_list if c not in aggregates_for_selector]
        if 'World' not in filtered_countries:
            filtered_countries.insert(0, 'World')
        
        with col1:
            default_index = filtered_countries.index('Ecuador') if 'Ecuador' in filtered_countries else 0
            selected_country = st.selectbox("País o Región", filtered_countries,
                                           index=default_index, key="evol_country")
        with col2:
            selected_metrics, selected_names = create_translated_multiselect(
                "Métricas a Graficar (Acumulativas o Diarias)",
                metrics_df,
                exclude_cols=STATIC_METRICS_EXCLUDE_LIST, 
                default_cols=['new_cases_smoothed', 'total_deaths'], 
                key="metrics_evol"
            )
        with col3:
            date_range = st.date_input(
                "Rango de Fechas",
                value=(data_min_date, data_max_date), 
                min_value=data_min_date, max_value=data_max_date,
                key="evol_date_range"
            )
            use_log = st.checkbox("Usar escala logarítmica", key="log_evol")
            show_raw_data = st.checkbox("Mostrar datos crudos (barras)", value=True, key="raw_evol")


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

        with st.container(border=False): 
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

            fig.update_layout(height=350 * len(selected_metrics), showlegend=True, hovermode='x unified', barmode='overlay', template="plotly_white")
            if len(selected_metrics) == 1: fig.update_layout(showlegend=False)
            
            st.plotly_chart(fig, use_container_width=True) 

            # --- Tabla de Datos ---
            with st.expander("Ver datos tabulados"):
                cols_to_show_in_table = [col for col in selected_metrics if col in df_filtrado.columns]
                st.dataframe(df_filtrado[cols_to_show_in_table].rename(columns=TRANSLATIONS).sort_index(ascending=False))
                
    elif not selected_metrics:
        st.info("Selecciona al menos una métrica para graficar.")

# --- FUNCIÓN Pestaña 3: Comparaciones (MODIFICADA) ---
def render_tab_comparativo(df_latest, metrics_df): 
    """LÓGICA PARA LA PESTAÑA 3: COMPARACIONES (PAÍSES)"""
    latest = df_latest
    latest_countries_only = latest[~latest['location'].str.lower().isin(AGGREGATES)] if 'location' in latest.columns else latest
    
    # --- Filtros ---
    with st.container(border=False): 
        st.markdown('<div class="section-title">⚙️ Filtros de Comparación</div>', unsafe_allow_html=True)
        col1, col2 = st.columns([1, 3])
        with col1:
            selected_metric_bar, selected_name_bar = create_translated_selectbox(
                "Métrica (Gráfico de Barras)",
                metrics_df, 
                exclude_cols=CROSS_SECTIONAL_EXCLUDE_METRICS, 
                key="metric_comp",
                default_col='total_cases_per_million'
            )
        with col2:
            countries = sorted(latest_countries_only['location'].unique()) if 'location' in latest_countries_only.columns else []
            selected_countries = st.multiselect(
                "Selecciona Países (para todos los análisis)",
                countries,
                default=[c for c in ['Ecuador', 'Peru', 'Colombia', 'Brazil', 'Argentina'] if c in countries]
            )
    
    # --- PESTAÑAS INTERNAS ELIMINADAS ---
    
    main_col1, main_col2 = st.columns([3, 2]) 
    # --- Columna 1: Gráfico de Barras ---
    with main_col1:
        with st.container(border=False): 
            st.markdown('<div class="section-title" style="margin-top: 20px;">📊 Comparación por Métrica</div>', unsafe_allow_html=True)
            if selected_countries and selected_metric_bar:
                st.markdown(f'<div class="section-title">{selected_name_bar}</div>', unsafe_allow_html=True)
                comp_data = latest_countries_only[latest_countries_only['location'].isin(selected_countries)].sort_values(selected_metric_bar, ascending=False)
                colors = {'Ecuador': '#0066cc', 'Peru': '#dc3545', 'Colombia': '#28a745', 'Brazil': '#ffc107', 'Argentina': '#17a2b8'}
                fig = go.Figure(data=[
                    go.Bar(
                        y=comp_data['location'], x=comp_data[selected_metric_bar], orientation='h',
                        text=comp_data[selected_metric_bar].apply(lambda x: f'{x:,.0f}' if pd.notna(x) else 'N/A'),
                        textposition='outside',
                        marker=dict(color=[colors.get(c, '#6c757d') for c in comp_data['location']])
                    )
                ])
                fig.update_layout(
                    height=max(300, len(selected_countries) * 60),
                    xaxis_title=selected_name_bar, yaxis_title="",
                    showlegend=False, template='plotly_white'
                )
                st.plotly_chart(fig, use_container_width=True) 
            elif not selected_countries:
                st.warning("Selecciona al menos un país para el gráfico de barras.")
            elif selected_metric_bar:
                st.info("Selecciona al menos un país.")
            else:
                st.info("Selecciona una métrica y al menos un país.")

    # --- Columna 2: Tabla de Resumen y Heatmap ---
    with main_col2:
        with st.container(border=False): 
            st.markdown('<div class="section-title" style="margin-top: 20px;">📄 Resumen Comparativo</div>', unsafe_allow_html=True)
            selected_metrics_table, selected_names_table = create_translated_multiselect(
                "Métricas (para Tabla y Heatmap)",
                metrics_df, 
                exclude_cols=CROSS_SECTIONAL_EXCLUDE_METRICS,
                default_cols=['total_cases_per_million', 'total_deaths_per_million', 'people_fully_vaccinated_per_hundred'],
                key="metrics_comp_table"
            )
            
            if selected_countries and selected_metrics_table:
                st.markdown(f'<div class="section-title" style="margin-top: 20px;">Tabla de Datos</div>', unsafe_allow_html=True)
                
                # --- CORRECCIÓN KeyError en Tabla Comparativa ---
                existing_cols_table = [col for col in selected_metrics_table if col in latest_countries_only.columns]
                if not existing_cols_table:
                    st.warning("Ninguna de las métricas seleccionadas para la tabla existe en los datos procesados.")
                else:
                    comp_data = latest_countries_only[latest_countries_only['location'].isin(selected_countries)]
                    table_data = comp_data.set_index('location')[existing_cols_table] 
                    table_data.columns = [translate_column(c) for c in table_data.columns]
                    st.dataframe(table_data.style.format("{:,.1f}", na_rep="N/A").background_gradient(cmap='Blues', axis=0), use_container_width=True) 

                    st.markdown("---")
                    st.markdown(f'<div class="section-title">🔥 Heatmap (Normalizado)</div>', unsafe_allow_html=True)
                    df_to_norm = comp_data.set_index('location')[existing_cols_table].dropna() 
                    if not df_to_norm.empty:
                        df_norm = (df_to_norm - df_to_norm.min(axis=0)) / (df_to_norm.max(axis=0) - df_to_norm.min(axis=0))
                        df_norm.columns = [translate_column(c) for c in df_norm.columns]
                        
                        fig_heat = px.imshow(
                            df_norm.T, 
                            text_auto=True,
                            aspect="auto",
                            color_continuous_scale='RdYlGn', 
                            title="Comparación Normalizada (0=Peor, 1=Mejor)"
                        )
                        fig_heat.update_traces(texttemplate="%{z:.2f}") 
                        fig_heat.update_layout(height=max(400, len(existing_cols_table) * 70))
                        st.plotly_chart(fig_heat, use_container_width=True) 
                    else:
                        st.warning("No hay datos suficientes para generar el heatmap (verifique valores nulos).")

            elif not selected_countries:
                st.warning("Por favor, selecciona al menos un país en el filtro de arriba.")
            else:
                st.info("Selecciona al menos una métrica para la tabla/heatmap.")


# --- FUNCIÓN Pestaña 4: Factores y Correlaciones (¡MEJORADA!) ---
def render_tab_factores(df_latest, metrics_df): 
    """LÓGICA PARA LA PESTAÑA 4: FACTORES Y CORRELACIONES (¡COMPLETA!)"""
    st.markdown("Analiza las relaciones globales entre métricas socioeconómicas y los resultados de la pandemia.")
    latest = df_latest
    latest_countries_only = latest[~latest['location'].str.lower().isin(AGGREGATES)] if 'location' in latest.columns else latest
    
    # --- (Tu código de Pestaña 4: Estadísticas) ---
    with st.container(border=False): 
        st.markdown('<div class="section-title">📊 Estadísticas (Global)</div>', unsafe_allow_html=True)
        
        # --- Filtros ---
        with st.container(border=False):
            col1, col2, col3 = st.columns([2, 3, 1])
            with col1:
                continents_list = sorted(latest_countries_only['continent'].dropna().unique().tolist()) if 'continent' in latest_countries_only.columns else []
                options_continent = ["Global (Todos)"] + continents_list
                selected_continent = st.selectbox("Filtrar por Continente", options_continent, key="stats_continent")
            with col2:
                selected_metric, selected_name = create_translated_selectbox(
                    "Métrica", metrics_df, 
                    exclude_cols=CROSS_SECTIONAL_EXCLUDE_METRICS, 
                    key="metric_stats", default_col='total_cases_per_million'
                )
            with col3:
                st.markdown("<br>", unsafe_allow_html=True) 
                include_outliers = st.checkbox("Incluir outliers", value=False, key="stats_outliers")
                # --- MEJORA 1: Añadir Escala Logarítmica ---
                use_log_scale = st.checkbox("Escala Logarítmica", value=True, key="stats_log", help="Recomendado para datos muy sesgados.")

        title_suffix = ""
        if selected_continent != "Global (Todos)":
            data_to_analyze = latest_countries_only[latest_countries_only['continent'] == selected_continent]
            title_suffix = f"({selected_continent})"
        else:
            data_to_analyze = latest_countries_only
            title_suffix = "(Global)"
        
        data_df = pd.DataFrame() 
        values = pd.Series(dtype=float)
        if selected_metric and selected_metric in data_to_analyze.columns:
            data_df = data_to_analyze[['location', 'continent', selected_metric]].dropna(subset=[selected_metric])
            if not include_outliers:
                if pd.api.types.is_numeric_dtype(data_df[selected_metric]) and len(data_df) > 1:
                    Q1 = data_df[selected_metric].quantile(0.25)
                    Q3 = data_df[selected_metric].quantile(0.75)
                    IQR = Q3 - Q1 if (Q3 - Q1) > 0 else 1 
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    data_df = data_df[(data_df[selected_metric] >= lower_bound) & (data_df[selected_metric] <= upper_bound)]
            if not data_df.empty:
                values = data_df[selected_metric]
        
        main_col1, main_col2 = st.columns([1, 1])
        with main_col1:
            st.markdown(f'<div class="section-title">Estadísticas Descriptivas {title_suffix}</div>', unsafe_allow_html=True)
            if pd.api.types.is_numeric_dtype(values) and not values.empty:
                
                # --- MEJORA 2: Arreglar tarjetas truncadas (Grid 2x2) ---
                row1_col1, row1_col2 = st.columns(2)
                with row1_col1:
                    st.metric("Media", formatar_numero_grande(values.mean()))
                with row1_col2:
                    st.metric("Mediana", formatar_numero_grande(values.median()))
                
                row2_col1, row2_col2 = st.columns(2)
                with row2_col1:
                    st.metric("Desv. Std", formatar_numero_grande(values.std()))
                with row2_col2:
                    st.metric("N (Países)", f"{len(values)}")
                # --- Fin de la Mejora 2 ---

        with main_col2:
            st.markdown(f'<div class="section-title">Distribución ({selected_name}) - {title_suffix}</div>', unsafe_allow_html=True)
            if pd.api.types.is_numeric_dtype(values) and not values.empty:
                fig_hist = px.histogram(
                    data_df, 
                    x=selected_metric, 
                    nbins=50, 
                    title=f"Histograma", 
                    template='plotly_white', 
                    color="continent", 
                    hover_data=['location'],
                    log_x=use_log_scale # <-- MEJORA 1 aplicada
                )
                fig_hist.add_vline(x=values.mean(), line_width=3, line_dash="dash", line_color="#dc3545", annotation_text="Media")
                fig_hist.add_vline(x=values.median(), line_width=3, line_dash="dot", line_color="#28a745", annotation_text="Mediana")
                st.plotly_chart(fig_hist, use_container_width=True) 

        # --- MEJORA 3: Añadir Diagrama de Cajas (Box Plot) ---
        st.markdown("---")
        st.markdown(f'<div class="section-title">Comparación por Continente ({selected_name}) - {title_suffix}</div>', unsafe_allow_html=True)
        st.markdown("Un **Diagrama de Cajas** es ideal para comparar las distribuciones (mediana, rangos) entre continentes.")
        if pd.api.types.is_numeric_dtype(values) and not values.empty:
            fig_box = px.box(
                data_df,
                x=selected_metric,
                y="continent",
                color="continent",
                title=f"Diagrama de Cajas por Continente",
                template='plotly_white',
                log_x=use_log_scale, # <-- Usar la misma escala
                points="all", # Muestra todos los países como puntos
                hover_data=['location']
            )
            fig_box.update_layout(yaxis_title="Continente", xaxis_title=selected_name)
            st.plotly_chart(fig_box, use_container_width=True)
        # --- Fin de la Mejora 3 ---

    st.markdown("---")

    # --- (Tu código de Pestaña 5: Correlaciones) ---
    with st.container(border=False):
        st.markdown('<div class="section-title">🔗 Exploración de Correlaciones (Manual)</div>', unsafe_allow_html=True)
        main_col1, main_col2 = st.columns(2)
        with main_col1:
            st.markdown('<div class="section-title" style="margin-top: 20px;">Matriz de Correlación</div>', unsafe_allow_html=True)
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    selected_metrics, selected_names = create_translated_multiselect(
                        "Métricas (Matriz)", metrics_df, 
                        exclude_cols=CROSS_SECTIONAL_EXCLUDE_METRICS, 
                        default_cols=['total_cases_per_million', 'total_deaths_per_million', 'people_fully_vaccinated_per_hundred', 'population'],
                        key="metrics_corr"
                    )
                with col2:
                    method = st.selectbox("Método", ["Spearman", "Pearson"])
            if len(selected_metrics) >= 2:
                corr_data = latest_countries_only[selected_metrics].dropna()
                numeric_selected_metrics = corr_data.select_dtypes(include=np.number).columns.tolist()
                if len(numeric_selected_metrics) < 2:
                    st.warning("Selecciona al menos dos métricas numéricas.")
                else:
                    corr_data_numeric = corr_data[numeric_selected_metrics]
                    corr_matrix = corr_data_numeric.corr(method=method.lower()) # type: ignore
                    translated_labels = [translate_column(m) for m in numeric_selected_metrics]
                    fig = go.Figure(data=go.Heatmap(
                        z=corr_matrix.values, x=translated_labels, y=translated_labels,
                        colorscale='RdBu', zmid=0, text=corr_matrix.values,
                        texttemplate='%{text:.2f}', textfont={"size": 12},
                        colorbar=dict(title="Corr.")
                    ))
                    fig.update_layout(height=500, xaxis=dict(side='bottom'), yaxis=dict(autorange='reversed'))
                    st.plotly_chart(fig, use_container_width=True) 
        with main_col2:
            st.markdown('<div class="section-title" style="margin-top: 20px;">Dispersión Detallada</div>', unsafe_allow_html=True)
            with st.container():
                col_x, col_y = st.columns(2)
                with col_x:
                    selected_x, name_x = create_translated_selectbox("Métrica Eje X", metrics_df, exclude_cols=CROSS_SECTIONAL_EXCLUDE_METRICS, key="corr_x", default_col='total_cases_per_million')
                with col_y:
                    selected_y, name_y = create_translated_selectbox("Métrica Eje Y", metrics_df, exclude_cols=CROSS_SECTIONAL_EXCLUDE_METRICS, key="corr_y", default_col='total_deaths_per_million')
            if selected_x and selected_y:
                fig_scatter = px.scatter(
                    latest_countries_only.dropna(subset=[selected_x, selected_y]),
                    x=selected_x, y=selected_y, title=f"{name_x} vs. {name_y}",
                    color="continent", hover_name="location",   
                    trendline="ols", template='plotly_white', height=600,
                    hover_data={selected_x:':,.1f', selected_y:':,.1f', 'continent':False}
                )
                st.plotly_chart(fig_scatter, use_container_width=True) 


# --- ¡NUEVA FUNCIÓN! Pestaña 5: Arquitectura ---
def render_tab_arquitectura():
    """LÓGICA PARA LA PESTAÑA 5: ARQUITECTURA DEL PROYECTO"""
    st.markdown('<div class="section-title">🏗️ Sobre este Proyecto de Grado</div>', unsafe_allow_html=True)
    
    with st.container(border=False):
        st.markdown("### Resumen del Proyecto")
        st.markdown("""
        Este dashboard es la capa de visualización (Frontend) de un sistema de Business Intelligence (BI) completo. 
        El objetivo fue diseñar y desplegar una arquitectura de software moderna, desacoplada y escalable para el análisis de datos en un contexto de Ingeniería de Software.
        """)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container(border=False):
            st.markdown("### 🚀 Backend (La API)")
            st.markdown(f"""
            El "cerebro" del sistema es una API RESTful construida con **FastAPI** y desplegada en **Render**.
            
            * **Desacoplado:** El frontend (Streamlit) está 100% separado del backend. Esto permite que en el futuro, otros servicios (como una app móvil) puedan consumir la misma fuente de datos.
            * **ETL en Memoria:** Al iniciar, la API carga el CSV (`api/data/owid-covid-data.csv`), lo procesa completamente en memoria usando **Pandas** (limpieza, imputación, ingeniería de features) y lo almacena en una variable global para un acceso instantáneo.
            * **Rendimiento:** Se usó FastAPI por su alto rendimiento asíncrono, ideal para aplicaciones de datos.
            * **Despliegue:** La API está alojada en [Render]({API_BASE_URL.split('/docs')[0]}).
            """)
            st.link_button("Ver Documentación de la API (Swagger)", f"{API_BASE_URL}/docs")

    with col2:
        with st.container(border=False):
            st.markdown("### 💻 Frontend (El Dashboard)")
            st.markdown("""
            Esta aplicación que estás usando fue construida con **Streamlit** y desplegada en **Streamlit Cloud**.
            
            * **Interactividad:** Se usó Streamlit por su capacidad de convertir scripts de Python en dashboards web interactivos de forma rápida.
            * **Optimización:** Se aplicaron varias técnicas para asegurar una experiencia de usuario fluida:
                1.  **`st.cache_data`**: Las llamadas a la API se guardan en caché para evitar recargas innecesarias.
                2.  **Manejo de "Cold Start"**: Se implementó un `timeout` de 45 segundos, ya que la API en Render (plan gratuito) se "duerme" y necesita tiempo para despertar.
                3.  **Refactor de Endpoints**: La pestaña "Análisis por País" se optimizó para hacer una sola llamada (`/country-history`) en lugar de una por métrica, mejorando drástiC.
            """)
            st.link_button("Ver el Repositorio en GitHub", "https://github.com/fabianR2410/PROYECTO_GRADO_VFINAL")
    
    st.markdown("---")

    with st.container(border=False):
        st.markdown("### 🙏 Agradecimientos")
        st.markdown("""
        Quiero extender mi más sincero agradecimiento a mi director de proyecto, a los miembros del jurado por su tiempo y orientación, y a mi familia por su apoyo incondicional durante el desarrollo de este trabajo de grado.
        
        Este proyecto representa la culminación de años de estudio en Ingeniería de Software y la aplicación práctica de conceptos de arquitectura, desarrollo backend, frontend y despliegue en la nube (CI/CD).
        """)

# =============================================================================
# --- 6. FUNCIÓN PRINCIPAL (main) ---
# =============================================================================
def main():
    """
    Punto de entrada principal de la aplicación Streamlit.
    """
    
    # (st.set_page_config() ya se llamó al inicio del script)
    
    # --- Título y Estado de la API ---
    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown('<div class="main-title">🌍 Panel COVID-19 - Proyecto de Grado</div>', unsafe_allow_html=True)
        st.markdown('<div class="subtitle">Análisis de datos, arquitectura de sistema y despliegue en la nube</div>', unsafe_allow_html=True)
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
    
    # --- ¡PESTAÑAS NARRATIVAS MEJORADAS! ---
    tab_global, tab_pais, tab_comparar, tab_factores, tab_arquitectura = st.tabs([
        "🌍 Panorama Global", 
        "📈 Análisis por País",
        "🆚 Análisis Comparativo",
        "🔬 Factores y Correlaciones",
        "🏗️ Arquitectura del Proyecto"
    ])

    with tab_global:
        render_tab_global(df_latest, metrics_df) 
    with tab_pais:
        render_tab_pais(countries_list, metrics_df, data_min_date, data_max_date)
    with tab_comparar:
        render_tab_comparativo(df_latest, metrics_df) 
    with tab_factores:
        render_tab_factores(df_latest, metrics_df) 
    with tab_arquitectura:
        render_tab_arquitectura() 

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