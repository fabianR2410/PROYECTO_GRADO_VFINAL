# -*- coding: utf-8 -*-
"""
Panel COVID-19 - Análisis
Este dashboard consulta la API local (FastAPI) para visualización.

MODIFICADO para incluir un gráfico de pastel en la vista general y simplificar HTML.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta, date 
import numpy as np
from scipy import stats
import requests
import time
import statsmodels.api as sm
from functools import reduce 

# =============================================================================
# --- CONFIGURACIÓN DE PÁGINA (MOVIDO AQUÍ) ---
# =============================================================================
# Esto DEBE ser el primer comando de Streamlit en el script
st.set_page_config(
    page_title="Panel COVID-19",
    page_icon="🌍",
    layout="wide" 
)

# =============================================================================
# --- 1. CONFIGURACIÓN Y CONSTANTES ---
# =============================================================================

# --- CONFIGURACIÓN DE LA API ---
# Lee la URL pública desde los "Secrets" de Streamlit
API_BASE_URL = st.secrets["API_URL"]
# -------------------------------

# --- CONSTANTES ---
AGGREGATES = ['world', 'europe', 'asia', 'africa', 'north america', 'south america', 'oceania',
              'european union', 'high income', 'upper middle income', 'lower middle income', 'low income']

# --- Listas de Métricas para Filtrar Pestañas ---

# 1. MÉTRICAS DE "FLUJO" O DIARIAS (Se excluyen de comparaciones, estadísticas, correlaciones)
CROSS_SECTIONAL_EXCLUDE_METRICS = [
    'new_cases', 'new_deaths', 'new_tests', 'new_vaccinations', 
    'new_cases_smoothed', 'new_deaths_smoothed', 'new_tests_smoothed', 'new_vaccinations_smoothed', 
    'new_cases_per_million', 'new_deaths_per_million', 'new_cases_smoothed_per_million', 
    'new_deaths_smoothed_per_million', 'weekly_icu_admissions', 'weekly_hosp_admissions', 
    'weekly_icu_admissions_per_million', 'weekly_hosp_admissions_per_million'
]

# 2. MÉTRICAS "ESTÁTICAS" (Se excluyen de *todas* las series de tiempo)
STATIC_METRICS_EXCLUDE_LIST = [
    'population', 'population_density', 'median_age', 'aged_65_older', 
    'aged_70_older', 'gdp_per_capita', 'extreme_poverty', 'cardiovasc_death_rate', 
    'diabetes_prevalence', 'female_smokers', 'male_smokers', 'handwashing_facilities', 
    'hospital_beds_per_thousand', 'life_expectancy', 'human_development_index'
]

# 3. MÉTRICAS "TOTALES" (Se permiten en evolución)
CUMULATIVE_METRICS_EXCLUDE_LIST = [
    'total_cases', 'total_deaths', 'total_tests', 'total_vaccinations', 
    'people_vaccinated', 'people_fully_vaccinated', 'total_boosters',
    'total_cases_per_million', 'total_deaths_per_million', 
    'total_tests_per_thousand', 'total_vaccinations_per_hundred', 
    'people_vaccinated_per_hundred', 'people_fully_vaccinated_per_hundred', 
    'total_boosters_per_hundred'
]

# 4. MÉTRICAS PARA GRÁFICO DE PASTEL (Solo totales absolutos)
PIE_ALLOWED_METRICS = [
    'total_cases', 'total_deaths', 'people_vaccinated', 
    'people_fully_vaccinated', 'total_boosters'
]
# ----------------------------------------------------

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

    # Características temporales
    'year': 'Año',
    'month': 'Mes',
    'day': 'Día',
    'day_of_week': 'Día de la Semana',
    'week_of_year': 'Semana del Año',

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
# --- 3. CSS PERSONALIZADO (MOVIDO DENTRO DE MAIN) ---
# =============================================================================
# El st.markdown() para el CSS fue movido a la función main()

# =============================================================================
# --- 4. FUNCIONES DE DATOS (API) ---
# =============================================================================

# --- FUNCIÓN DE PING ---
def check_api_status():
    """
    Comprueba si la API en API_BASE_URL está en línea.
    """
    try:
        resp = requests.get(f"{API_BASE_URL}/", timeout=2)
        return resp.status_code == 200
    except requests.exceptions.RequestException:
        return False

# --- FUNCIÓN DE CARGA CON CACHÉ TTL (CORREGIDA) ---
@st.cache_data(ttl=120)  # caché por 2 minutos
def load_dashboard_data():
    """
    Carga los datos iniciales (latest, countries, metrics) desde la API.
    Se usa un caché de 2 minutos y un timeout largo para el "cold start" de Render.
    """
    try:
        # Aumentamos el timeout a 45 segundos para que Render despierte
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
        st.error(f"Error en load_dashboard_data: {e}")
        return None, None, None

# =============================================================================
# --- 5. FUNCIONES DE PESTAÑA (Lógica de cada Tab) ---
# =============================================================================

# --- FUNCIÓN Pestaña 1: Vista General ---
def vista_general(df_latest, metrics_df): 
    """LÓGICA PARA LA PESTAÑA 1: VISTA GENERAL"""
    
    # --- Gráficos Principales (Mapa y Pastel) ---
    main_col1, main_col2 = st.columns([2, 1])

    with main_col1:
        with st.container(border=True): # --- 💡 MEJORA: Contenedor ---
            st.markdown('<div class="section-title">🗺️ Distribución Global (Mapa)</div>', unsafe_allow_html=True)
            
            selected_metric_map, selected_name_map = create_translated_selectbox(
                "Seleccione métrica para el mapa",
                metrics_df, 
                exclude_cols=CROSS_SECTIONAL_EXCLUDE_METRICS, 
                key="map_metric",
                default_col='total_cases'
            )

            if selected_metric_map and 'iso_code' in df_latest.columns:
                map_data = df_latest[~df_latest['location'].str.lower().isin(AGGREGATES)] if 'location' in df_latest.columns else df_latest
                fig = go.Figure(data=go.Choropleth(
                    locations=map_data['iso_code'],
                    z=map_data[selected_metric_map],
                    text=map_data['location'] if 'location' in map_data.columns else None,
                    colorscale='Blues', autocolorscale=False, reversescale=False,
                    marker_line_color='darkgray', marker_line_width=0.5,
                    colorbar_title=selected_name_map,
                    hovertemplate='<b>%{text}</b><br>' + f'{selected_name_map}: %{{z:,.0f}}<extra></extra>'
                ))
                fig.update_layout(
                    title_text=f'{selected_name_map} por País (Globo Interactivo)',
                    geo=dict(showframe=False, showcoastlines=True, projection_type='orthographic'),
                    height=600, margin=dict(l=0, r=0, t=40, b=0),
                    annotations=[dict(
                        text='Arrastra el globo para rotar', align='left', showarrow=False,
                        xref='paper', yref='paper', x=0.05, y=0.05,
                        bgcolor='rgba(255, 255, 255, 0.7)', borderpad=4
                    )]
                )
                st.plotly_chart(fig, use_container_width=True) 
            elif not selected_metric_map:
                st.info("Selecciona una métrica para mostrar el mapa.")

    with main_col2:
        with st.container(border=True): # --- 💡 MEJORA: Contenedor ---
            st.markdown('<div class="section-title">🌍 Distribución por Continente</div>', unsafe_allow_html=True)
            
            default_pie_col = 'total_cases' if 'total_cases' in PIE_ALLOWED_METRICS else (PIE_ALLOWED_METRICS[0] if PIE_ALLOWED_METRICS else None)
            selected_metric_pie, selected_name_pie = create_translated_selectbox(
                "Seleccione métrica para el pastel",
                metrics_df, 
                include_only=PIE_ALLOWED_METRICS, 
                key="pie_metric",
                default_col=default_pie_col
            )

            if selected_metric_pie:
                countries_only_df = df_latest[~df_latest['location'].str.lower().isin(AGGREGATES)]
                if 'continent' in countries_only_df.columns and selected_metric_pie in countries_only_df.columns:
                    pie_data = countries_only_df.groupby('continent')[selected_metric_pie].sum().reset_index()
                    pie_data = pie_data.dropna(subset=['continent', selected_metric_pie])
                    pie_data = pie_data[pie_data[selected_metric_pie] > 0] 
                    if not pie_data.empty:
                        fig_pie = px.pie(
                            pie_data, names='continent', values=selected_metric_pie,
                            title=f'Distribución de {selected_name_pie} por Continente',
                            hole=0.3, color_discrete_sequence=px.colors.sequential.Blues_r
                        )
                        fig_pie.update_traces(
                            textposition='inside', textinfo='percent+label',
                            hovertemplate='<b>%{label}</b><br>' + f'{selected_name_pie}: %{{value:,.0f}}<br>' + 'Porcentaje: %{percent}<extra></extra>'
                        )
                        fig_pie.update_layout(
                            height=600, margin=dict(l=0, r=0, t=40, b=0),
                            legend=dict(orientation="h", yanchor="bottom", y= -0.1, xanchor="center", x=0.5)
                        )
                        st.plotly_chart(fig_pie, use_container_width=True) 
                    else:
                        st.warning("No se encontraron datos de países para agrupar por continente.")
                else:
                    st.warning("El DataFrame no contiene la columna 'continent' o la métrica seleccionada para agrupar.")
            else:
                st.info("Selecciona una métrica para mostrar el gráfico de pastel.")

# --- FUNCIÓN Pestaña 2: Evolución por País ---
def evolucion_por_pais(countries_list, metrics_df, data_min_date, data_max_date):
    """LÓGICA PARA LA PESTAÑA 2: EVOLUCIÓN POR PAÍS"""

    # --- Filtros ---
    with st.container(border=True): # --- 💡 MEJORA: Contenedor ---
        st.markdown('<div class="section-title">⚙️ Filtros de Evolución</div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([2, 3, 2])
        aggregates_for_selector = ['World', 'Europe', 'Asia', 'Africa', 'North America', 'South America', 'Oceania',
                                 'European Union', 'High income', 'Upper middle income', 'Lower middle income', 'Low income']
        # --- 💡 MEJORA: Añadido 'World' al selector de países ---
        filtered_countries = ['World'] + [c for c in countries_list if c not in aggregates_for_selector]
        
        with col1:
            default_index = filtered_countries.index('Ecuador') if 'Ecuador' in filtered_countries else 0
            selected_country = st.selectbox("País o Región", filtered_countries,
                                           index=default_index)
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
            # Rango de fechas usa min/max de los datos cargados (¡Correcto!)
            date_range = st.date_input(
                "Rango de Fechas",
                value=(data_min_date, data_max_date), 
                min_value=data_min_date, max_value=data_max_date 
            )

    # --- Contenedor Principal de Resultados ---
    if selected_metrics and selected_country and len(date_range) == 2: # type: ignore
        with st.container(border=True): # --- 💡 MEJORA: Contenedor ---
            st.markdown(f'<h4>Resultados para {selected_country}</h4>', unsafe_allow_html=True)
            data_cache = {} 
            
            # --- Carga de Datos ---
            with st.spinner(f"Cargando {len(selected_metrics)} métrica(s) para {selected_country}..."):
                for i, (metric, name) in enumerate(zip(selected_metrics, selected_names)):
                    try:
                        api_params = {
                            'country': selected_country, 'metric': metric,
                            'start_date': date_range[0].strftime('%Y-%m-%d') if date_range[0] else None, # pyright: ignore[reportIndexIssue]
                            'end_date': date_range[1].strftime('%Y-%m-%d') if date_range[1] else None, # type: ignore
                        }
                        response = requests.get(f"{API_BASE_URL}/covid/timeseries", params=api_params, timeout=8)
                        response.raise_for_status()
                        data = response.json().get('data', [])
                        if data:
                            country_data = pd.DataFrame(data)
                            country_data['date'] = pd.to_datetime(country_data['date'])
                            data_cache[metric] = country_data
                        else:
                            st.warning(f"No se encontraron datos para '{name}'")
                            data_cache[metric] = pd.DataFrame() 
                    except requests.exceptions.RequestException as e:
                        st.error(f"Error cargando la métrica '{name}': {e}")
                        data_cache[metric] = pd.DataFrame()

            # --- KPIs de Resumen ---
            st.markdown(f'<div class="section-title" style="margin-top: 20px;">🗓️ Resumen del Período ({date_range[0].strftime("%Y-%m-%d")} al {date_range[1].strftime("%Y-%m-%d")})</div>', unsafe_allow_html=True) # type: ignore
            if not selected_metrics:
                st.info("Seleccione al menos una métrica para ver el resumen.")
            else:
                kpi_cols = st.columns(len(selected_metrics))
                for i, (metric, name) in enumerate(zip(selected_metrics, selected_names)):
                    with kpi_cols[i]:
                        df = data_cache.get(metric)
                        if df is not None and not df.empty and metric in df.columns:
                            if metric in CROSS_SECTIONAL_EXCLUDE_METRICS: 
                                total_periodo = df[metric].sum()
                                promedio_diario = df[metric].mean()
                                pico_maximo = df[metric].max()
                                st.metric(label=f"Total {name} (en período)", value=formatar_numero_grande(total_periodo))
                                st.metric(label=f"Promedio Diario", value=formatar_numero_grande(promedio_diario))
                                st.metric(label=f"Pico Máximo", value=formatar_numero_grande(pico_maximo))
                            else: 
                                valor_reciente = df[metric].iloc[-1] if not df.empty else 0
                                valor_inicial = df[metric].iloc[0] if not df.empty else 0
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
                country_data = data_cache.get(metric)
                if country_data is not None and not country_data.empty and metric in country_data.columns:
                    color = colors[(i-1) % len(colors)]
                    
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
            if len(selected_metrics) == 1:
                fig.update_layout(showlegend=False)
            
            st.plotly_chart(fig, use_container_width=True) 

            # --- Tabla de Datos ---
            with st.expander("Ver datos tabulados"):
                dfs_to_merge = []
                for metric, name in zip(selected_metrics, selected_names):
                    df = data_cache.get(metric)
                    if df is not None and not df.empty and 'date' in df.columns and metric in df.columns:
                        metric_avg_7 = f"{metric}_avg_7"
                        cols_to_keep = ['date', metric]
                        if metric_avg_7 in df.columns and metric in CROSS_SECTIONAL_EXCLUDE_METRICS:
                            cols_to_keep.append(metric_avg_7)
                        
                        df_renamed = df[cols_to_keep].rename(columns={
                            metric: name, 
                            metric_avg_7: f"Media 7 Días ({name})"
                        })
                        dfs_to_merge.append(df_renamed)
                
                if dfs_to_merge:
                    merged_df = reduce(lambda left, right: pd.merge(left, right, on='date', how='outer'), dfs_to_merge)
                    merged_df = merged_df.sort_values(by='date', ascending=False).set_index('date')
                    st.dataframe(merged_df.style.format(na_rep="N/A", precision=1), use_container_width=True) 
                else:
                    st.write("No hay datos para mostrar en la tabla.")
    elif not selected_metrics:
        st.info("Selecciona al menos una métrica para graficar.")

# --- FUNCIÓN Pestaña 3: Comparaciones ---
def comparaciones_paises(df_latest, metrics_df): 
    """LÓGICA PARA LA PESTAÑA 3: COMPARACIONES (PAÍSES)"""
    latest = df_latest
    latest_countries_only = latest[~latest['location'].str.lower().isin(AGGREGATES)] if 'location' in latest.columns else latest
    
    # --- Filtros ---
    with st.container(border=True): # --- 💡 MEJORA: Contenedor ---
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

    st.markdown("---")
    main_col1, main_col2 = st.columns([3, 2]) 

    # --- Columna 1: Gráfico de Barras ---
    with main_col1:
        with st.container(border=True): # --- 💡 MEJORA: Contenedor ---
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
        with st.container(border=True): # --- 💡 MEJORA: Contenedor ---
            st.markdown('<div class="section-title" style="margin-top: 20px;">📄 Resumen Comparativo</div>', unsafe_allow_html=True)
            selected_metrics_table, selected_names_table = create_translated_multiselect(
                "Métricas (para Tabla y Heatmap)",
                metrics_df, 
                exclude_cols=CROSS_SECTIONAL_EXCLUDE_METRICS,
                default_cols=['total_cases_per_million', 'total_deaths_per_million', 'people_fully_vaccinated_per_hundred', 'gdp_per_capita', 'life_expectancy'],
                key="metrics_comp_table"
            )
            
            if selected_countries and selected_metrics_table:
                st.markdown(f'<div class="section-title" style="margin-top: 20px;">Tabla de Datos</div>', unsafe_allow_html=True)
                comp_data = latest_countries_only[latest_countries_only['location'].isin(selected_countries)]
                table_data = comp_data.set_index('location')[selected_metrics_table]
                table_data.columns = [translate_column(c) for c in table_data.columns]
                st.dataframe(table_data.style.format("{:,.1f}", na_rep="N/A").background_gradient(cmap='Blues', axis=0), use_container_width=True) 

                st.markdown("---")
                st.markdown(f'<div class="section-title">🔥 Heatmap (Normalizado)</div>', unsafe_allow_html=True)
                df_to_norm = comp_data.set_index('location')[selected_metrics_table].dropna()
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
                    fig_heat.update_layout(height=max(400, len(selected_metrics_table) * 70))
                    st.plotly_chart(fig_heat, use_container_width=True) 
                else:
                    st.warning("No hay datos suficientes para generar el heatmap (verifique valores nulos).")

            elif not selected_countries:
                st.warning("Por favor, selecciona al menos un país en el filtro de arriba.")
            else:
                st.info("Selecciona al menos una métrica para la tabla/heatmap.")

# --- FUNCIÓN Pestaña 4: Estadísticas ---
def estadisticas_global(df_latest, metrics_df): 
    """LÓGICA PARA LA PESTAÑA 4: ESTADÍSTICAS (GLOBAL)"""
    latest = df_latest
    latest_countries_only = latest[~latest['location'].str.lower().isin(AGGREGATES)] if 'location' in latest.columns else latest
    
    # --- Filtros ---
    with st.container(border=True): # --- 💡 MEJORA: Contenedor ---
        st.markdown('<div class="section-title">⚙️ Filtros de Estadísticas</div>', unsafe_allow_html=True)
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

    title_suffix = ""
    if selected_continent != "Global (Todos)":
        data_to_analyze = latest_countries_only[latest_countries_only['continent'] == selected_continent]
        title_suffix = f"({selected_continent})"
    else:
        data_to_analyze = latest_countries_only
        title_suffix = "(Global)"

    # --- Procesamiento de datos ---
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
            elif not (pd.api.types.is_numeric_dtype(data_df[selected_metric]) and len(data_df) > 1):
                st.info(f"No se puede calcular IQR sin outliers para esta métrica en {title_suffix}.")
        
        if not data_df.empty:
            values = data_df[selected_metric]
    
    main_col1, main_col2 = st.columns([1, 1])
    
    # --- Columna 1: KPIs ---
    with main_col1:
        with st.container(border=True): # --- 💡 MEJORA: Contenedor ---
            st.markdown(f'<div class="section-title">📊 Estadísticas Descriptivas {title_suffix}</div>', unsafe_allow_html=True)
            if pd.api.types.is_numeric_dtype(values) and not values.empty:
                stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
                
                with stats_col1: st.metric("Media", formatar_numero_grande(values.mean()))
                with stats_col2: st.metric("Mediana", formatar_numero_grande(values.median()))
                with stats_col3: st.metric("Desv. Std", formatar_numero_grande(values.std()))
                with stats_col4: st.metric("N (Países)", f"{len(values)}")
                
                st.markdown("<br>", unsafe_allow_html=True)
                more_col1, more_col2, more_col3, more_col4 = st.columns(4)
                
                with more_col1: st.metric("Mín", formatar_numero_grande(values.min()))
                with more_col2: st.metric("Q1 (25%)", formatar_numero_grande(values.quantile(0.25)))
                with more_col3: st.metric("Q3 (75%)", formatar_numero_grande(values.quantile(0.75)))
                with more_col4: st.metric("Máx", formatar_numero_grande(values.max()))
                
            elif selected_metric:
                st.warning(f"No se pueden calcular estadísticas para '{selected_name}' en {title_suffix}.")
            else:
                st.info("Selecciona una métrica para ver las estadísticas.")

    # --- Columna 2: Gráficos de Distribución ---
    with main_col2:
        with st.container(border=True): # --- 💡 MEJORA: Contenedor ---
            st.markdown(f'<div class="section-title">📈 Distribución ({selected_name}) - {title_suffix}</div>', unsafe_allow_html=True)
            if pd.api.types.is_numeric_dtype(values) and not values.empty:
                
                fig_hist = px.histogram(
                    data_df, x=selected_metric, nbins=50,
                    title=f"Histograma de {selected_name}",
                    template='plotly_white', color="continent",
                    hover_data=['location'] 
                )
                fig_hist.add_vline(x=values.mean(), line_width=3, line_dash="dash", line_color="#dc3545", annotation_text="Media")
                fig_hist.add_vline(x=values.median(), line_width=3, line_dash="dot", line_color="#28a745", annotation_text="Mediana")
                st.plotly_chart(fig_hist, use_container_width=True) 
                
                st.markdown("---")
                st.markdown(f'<div class="section-title">📦 Diagrama de Cajas ({selected_name}) - {title_suffix}</div>', unsafe_allow_html=True)
                fig_box = px.box(
                    data_df, y=selected_metric, points="all", 
                    color="continent",
                    hover_data=['location'],
                    title=f"Diagrama de Cajas de {selected_name}"
                )
                st.plotly_chart(fig_box, use_container_width=True) 

            elif selected_metric:
                st.warning(f"No se pueden mostrar datos de distribución para '{selected_name}' en {title_suffix}.")
            else:
                st.info("Selecciona una métrica para ver la distribución.")

# --- FUNCIÓN Pestaña 5: Correlaciones ---
def correlaciones_global(df_latest, metrics_df): 
    """LÓGICA PARA LA PESTAÑA 5: CORRELACIONES (GLOBAL)"""
    st.markdown("Analiza las relaciones globales entre métricas a nivel de país (excluyendo agregados).")
    latest = df_latest
    latest_countries_only = latest[~latest['location'].str.lower().isin(AGGREGATES)] if 'location' in latest.columns else latest
    main_col1, main_col2 = st.columns(2)

    # --- Columna 1: Matriz de Correlación ---
    with main_col1:
        with st.container(border=True): # --- 💡 MEJORA: Contenedor ---
            st.markdown('<div class="section-title" style="margin-top: 20px;">🔗 Matriz de Correlación</div>', unsafe_allow_html=True)
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    selected_metrics, selected_names = create_translated_multiselect(
                        "Métricas (Matriz)", metrics_df, 
                        exclude_cols=CROSS_SECTIONAL_EXCLUDE_METRICS, 
                        default_cols=['total_cases_per_million', 'total_deaths_per_million', 'gdp_per_capita', 'life_expectancy', 'positive_rate'],
                        key="metrics_corr"
                    )
                with col2:
                    method = st.selectbox("Método", ["Spearman", "Pearson"])
            if len(selected_metrics) >= 2:
                corr_data = latest_countries_only[selected_metrics].dropna()
                numeric_selected_metrics = corr_data.select_dtypes(include=np.number).columns.tolist()
                if len(numeric_selected_metrics) < 2:
                    st.warning("Selecciona al menos dos métricas numéricas para calcular la correlación.")
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
                    
                    st.markdown("---")
                    st.markdown(f'<div class="section-title">Correlaciones Destacadas ({method})</div>', unsafe_allow_html=True)
                    corr_pairs = corr_matrix.unstack().sort_values(kind="quicksort")
                    corr_pairs = corr_pairs[corr_pairs != 1.0]
                    num_pairs = len(corr_pairs) // 2
                    if num_pairs > 0:
                        strong_pos = corr_pairs.iloc[num_pairs:].iloc[-3:].sort_values(ascending=False)
                        strong_neg = corr_pairs.iloc[:num_pairs].iloc[:3]
                        
                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown("<h6>📈 Más Fuertes (Positivas)</h6>", unsafe_allow_html=True)
                            if strong_pos.empty:
                                st.info("No se encontraron correlaciones positivas fuertes.")
                            for (idx, val) in strong_pos.items():
                                st.metric(label=f"{translate_column(idx[0])} & {translate_column(idx[1])}", value=f"{val:.3f}")
                        with c2:
                            st.markdown("<h6>📉 Más Fuertes (Negativas)</h6>", unsafe_allow_html=True)
                            if strong_neg.empty or strong_neg.min() > -0.1:
                                st.info("No se encontraron correlaciones negativas fuertes.")
                            for (idx, val) in strong_neg.items():
                                st.metric(label=f"{translate_column(idx[0])} & {translate_column(idx[1])}", value=f"{val:.3f}")
                    else:
                        st.info("No hay suficientes pares para mostrar correlaciones destacadas.")
            else:
                st.info("Selecciona 2 o más métricas para generar la matriz de correlación.")

    # --- Columna 2: Gráfico de Dispersión ---
    with main_col2:
        with st.container(border=True): # --- 💡 MEJORA: Contenedor ---
            st.markdown('<div class="section-title" style="margin-top: 20px;">🔍 Dispersión Detallada</div>', unsafe_allow_html=True)
            with st.container():
                col_x, col_y = st.columns(2)
                with col_x:
                    selected_x, name_x = create_translated_selectbox(
                        "Métrica Eje X", metrics_df, 
                        exclude_cols=CROSS_SECTIONAL_EXCLUDE_METRICS, 
                        key="corr_x", default_col='gdp_per_capita' 
                    )
                with col_y:
                    selected_y, name_y = create_translated_selectbox(
                        "Métrica Eje Y", metrics_df, 
                        exclude_cols=CROSS_SECTIONAL_EXCLUDE_METRICS, 
                        key="corr_y", default_col='total_deaths_per_million'
                    )
            if selected_x and selected_y:
                fig_scatter = px.scatter(
                    latest_countries_only.dropna(subset=[selected_x, selected_y]) if selected_x in latest_countries_only.columns and selected_y in latest_countries_only.columns else pd.DataFrame(),
                    x=selected_x, y=selected_y, title=f"{name_x} vs. {name_y}",
                    color="continent" if 'continent' in latest_countries_only.columns else None,      
                    hover_name="location" if 'location' in latest_countries_only.columns else None,   
                    trendline="ols", template='plotly_white', height=600,
                    hover_data={selected_x:':,.1f', selected_y:':,.1f', 'continent':False} if 'continent' in latest_countries_only.columns else None
                )
                st.plotly_chart(fig_scatter, use_container_width=True) 
            else:
                st.info("Selecciona métricas X e Y para el gráfico de dispersión.")

# =============================================================================
# --- 6. FUNCIÓN PRINCIPAL (main) ---
# =============================================================================
def main():
    """
    Punto de entrada principal de la aplicación Streamlit.
    Aquí se configura la página, se cargan los datos y se definen las pestañas.
    """
    # st.set_page_config() FUE MOVIDO AL INICIO DEL SCRIPT (FUERA DE MAIN)

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

    # --- CSS PERSONALIZADO (MOVIDO AQUÍ, DENTRO DE MAIN) ---
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        * {
            font-family: 'Inter', sans-serif;
        }

        .stApp {
            background: linear-gradient(180deg, #f8f9fa 0%, #f0f2f5 100%);
        }

        footer {visibility: hidden;}
        header {visibility: hidden;}

        .main-title {
            font-size: 32px;
            font-weight: 700;
            color: #1a1a1a;
            margin-bottom: 5px;
        }

        .subtitle {
            font-size: 14px;
            color: #6c757d;
            margin-bottom: 30px;
        }

        [data-testid="stMetric"] {
            background-color: #ffffff;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.08);
            transition: all 0.3s ease-in-out;
            height: 100%; 
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        
        [data-testid="stMetric"]:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.12);
        }
        
        [data-testid="stMetricLabel"] {
            order: -1;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: white;
            border-radius: 12px;
            padding: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.08);
        }

        .stTabs [data-baseweb="tab"] {
            height: 50px;
            padding: 0 24px;
            background-color: transparent;
            border-radius: 8px;
            color: #6c757d;
            font-weight: 500;
        }

        .stTabs [aria-selected="true"] {
            background-color: #e7f3ff;
            color: #0066cc;
        }

        .section-title {
            font-size: 18px;
            font-weight: 600;
            color: #1a1a1a;
            margin-bottom: 20px;
        }

        .stSelectbox, .stMultiSelect {
            background: transparent; 
        }

        .stButton button {
            border-radius: 8px;
            font-weight: 500;
            padding: 8px 24px;
        }

        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            background-color: #28a745;
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- Carga de Datos Inicial ---
    try:
        with st.spinner(f"Cargando datos iniciales desde la API ({API_BASE_URL})..."):
            df_latest, countries_list, all_metrics = load_dashboard_data()
    except Exception as e:
        st.error(f"Error fatal al intentar cargar datos: {e}")
        st.warning("Asegúrate de que la API esté corriendo y sea accesible.")
        return

    if df_latest is None:
        st.error(f"Error al cargar datos. Asegúrate de que la API esté corriendo en {API_BASE_URL} y limpia la caché (tecla C).")
        return

    st.toast("¡Datos cargados exitosamente!", icon="✅")

    # --- Preparación de DataFrames para Selectores ---
    metrics_df = pd.DataFrame({metric: pd.Series(dtype='float64') for metric in (all_metrics or [])})
    
    # --- 💡 MEJORA: Asegurarse de que min_date venga de los datos cargados ---
    data_max_date = df_latest['date'].max() if ('date' in df_latest.columns and not df_latest['date'].empty) else pd.to_datetime(date.today())
    data_min_date = df_latest['date'].min() if ('date' in df_latest.columns and not df_latest['date'].empty) else pd.to_datetime("2020-01-01")
    
    # --- 💡 MEJORA: KPIs Globales movidos aquí (fuera de las pestañas) ---
    st.markdown('<div class="section-title">Resumen Global (Últimos Datos)</div>', unsafe_allow_html=True)
    latest = df_latest 

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_cases = latest['total_cases'].sum() if 'total_cases' in latest.columns else np.nan
        new_cases = latest['new_cases'].sum() if 'new_cases' in latest.columns else np.nan
        st.metric(label="Casos Totales", value=formatar_numero_grande(total_cases),
                  delta=f"{new_cases:,.0f} (Nuevos)" if pd.notna(new_cases) else None)
    with col2:
        total_deaths = latest['total_deaths'].sum() if 'total_deaths' in latest.columns else np.nan
        new_deaths = latest['new_deaths'].sum() if 'new_deaths' in latest.columns else np.nan
        st.metric(label="Muertes Totales", value=formatar_numero_grande(total_deaths),
                  delta=f"{new_deaths:,.0f} (Nuevas)" if pd.notna(new_deaths) else None, delta_color="inverse")
    with col3:
        pop_label = "Población Mundial"
        pop_help = "Población mundial reportada por Our World in Data ('World')."
        total_pop = np.nan 
        world_pop_row = latest[latest['location'].str.lower() == 'world'] if 'location' in latest.columns else pd.DataFrame()
        if not world_pop_row.empty and 'population' in world_pop_row.columns:
            total_pop = world_pop_row['population'].iloc[0]
        else:
            # Plan B: Sumar países si 'World' no existe o no tiene población
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
        "🗺️ Vista Geográfica", # <-- Título cambiado
        "📈 Evolución por País",
        "🌎 Comparaciones (Países)",
        "📊 Estadísticas (Global)",
        "🔗 Correlaciones (Global)"
    ])

    # =======================================================
    # --- PESTAÑA 1: VISTA GENERAL ---
    # =======================================================
    with tab1:
        vista_general(df_latest, metrics_df) 
    # --- FIN PESTAÑA 1 ---

    # =======================================================
    # --- PESTAÑA 2: EVOLUCIÓN POR PAÍS ---
    # =======================================================
    with tab2:
        evolucion_por_pais(countries_list, metrics_df, data_min_date, data_max_date)
    # --- FIN PESTAÑA 2 ---

    # =======================================================
    # --- PESTAÑA 3: COMPARACIONES (PAÍSES) ---
    # =======================================================
    with tab3:
        comparaciones_paises(df_latest, metrics_df) 
    # --- FIN PESTAÑA 3 ---

    # =======================================================
    # --- PESTAÑA 4: ESTADÍSTICAS (GLOBAL) ---
    # =======================================================
    with tab4:
        estadisticas_global(df_latest, metrics_df) 
    # --- FIN PESTAÑA 4 ---

    # =======================================================
    # --- PESTAÑA 5: CORRELACIONES (GLOBAL) ---
    # =======================================================
    with tab5:
        correlaciones_global(df_latest, metrics_df) 
    # --- FIN PESTAÑA 5 ---

    # =======================================================
    # --- Pie de Página ---
    st.markdown("---")
    unique_countries_count = df_latest[~latest['location'].str.lower().isin(AGGREGATES)]['location'].nunique() if 'location' in df_latest.columns else 0
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