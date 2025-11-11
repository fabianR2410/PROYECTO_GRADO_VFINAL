# dashboard_pro.py
# -*- coding: utf-8 -*-
"""
Versión Pro del dashboard COVID-19:
- Incluye todo lo de la versión optimizada.
- Insights automáticos: correlaciones (Spearman) + tendencia (% cambio).
- Detección simple de picos/anomalías en series temporales.
- Story cards automáticas.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime
from scipy import stats
from statsmodels.tsa.seasonal import STL

# Config
st.set_page_config(page_title="COVID-19 - Pro", page_icon="🔬", layout="wide")
API_BASE_URL = st.secrets.get("API_URL", None)
LOCAL_CSV_PATH = "data/owid-covid-data.csv"

# Caches
@st.cache_data(ttl=300)
def load_csv_local(path=LOCAL_CSV_PATH):
    df = pd.read_csv(path, parse_dates=['date'])
    return df

@st.cache_data(ttl=120)
def load_latest_from_csv(csv_df):
    df = csv_df.sort_values(['location','date']).groupby('location').tail(1).reset_index(drop=True)
    return df

# helpers
def format_large(n):
    if pd.isna(n): return "N/A"
    n = float(n)
    if abs(n) >= 1_000_000_000: return f"{n/1_000_000_000:.2f} B"
    if abs(n) >= 1_000_000: return f"{n/1_000_000:.2f} M"
    if abs(n) >= 1_000: return f"{n/1_000:.1f} K"
    return f"{n:.0f}"

def translated(c): return c.replace('_',' ').title()

# load data (prefer API, fallback CSV)
def load_data_prefer_api():
    df_latest = None
    csv_df = None
    try:
        if API_BASE_URL:
            resp = requests.get(f"{API_BASE_URL}/covid/latest", timeout=15)
            resp.raise_for_status()
            df_latest = pd.DataFrame(resp.json().get('data', []))
            if 'date' in df_latest.columns: df_latest['date'] = pd.to_datetime(df_latest['date'])
    except Exception:
        df_latest = None
    try:
        csv_df = load_csv_local()
        if df_latest is None:
            df_latest = load_latest_from_csv(csv_df)
    except Exception:
        csv_df = None
    return df_latest, csv_df

# DETECCIÓN DE PICOS SIMPLE (usando STL o descomposición simple)
def detect_peaks(series, window=7, z_thresh=2.5):
    # series: pd.Series indexed by date
    s = series.dropna()
    if s.empty or len(s) < 10:
        return []
    # usar diferencia z-score sobre rolling mean
    rolling = s.rolling(window=window, min_periods=1, center=True).mean()
    resid = s - rolling
    z = (resid - resid.mean()) / (resid.std() if resid.std()!=0 else 1)
    peaks = z[z.abs() > z_thresh].index.tolist()
    return peaks

# INSIGHTS: correlaciones + tendencias
def compute_insights(latest_df, csv_df=None, outcome='total_deaths_per_million', topk=5):
    res = {"correlations": [], "trends": []}
    if latest_df is None:
        return res
    # correlaciones: calcular Spearman entre outcome y varias features
    candidate_factors = [c for c in latest_df.select_dtypes(include=[np.number]).columns if c != outcome]
    df_corr = latest_df[[outcome] + candidate_factors].dropna()
    if len(df_corr) >= 10:
        corr_series = df_corr.corr(method='spearman')[outcome].drop(outcome).abs().sort_values(ascending=False)
        top = corr_series.head(topk)
        res['correlations'] = [{"factor": idx, "corr": float(df_corr.corr(method='spearman').loc[idx, outcome])} for idx in top.index]
    # tendencias: si csv_df disponible, calcular % cambio reciente por país y resumir países con mayor subida
    if csv_df is not None:
        recent = csv_df.copy()
        recent = recent.sort_values(['location','date'])
        # calcular tasa de cambio entre última fecha y 14 días antes para new_cases_smoothed
        metric = 'new_cases_smoothed'
        if metric in recent.columns:
            df_last = recent.groupby('location').tail(15).groupby('location').apply(lambda g: (g[metric].iloc[-1], g[metric].iloc[0]))
            df_last = df_last.apply(pd.Series)
            df_last.columns = ['recent','past']
            df_last['pct_change'] = (df_last['recent'] - df_last['past']) / (df_last['past'].replace(0,np.nan))
            df_last = df_last.dropna().sort_values('pct_change', ascending=False)
            top_inc = df_last.head(topk)
            res['trends'] = [{"location": idx, "pct_change": float(row['pct_change']), "recent": float(row['recent']), "past": float(row['past'])} for idx,row in top_inc.iterrows()]
    return res

# RENDER / UI
def render_overview(latest_df):
    st.header("Panorama Global (Pro)")
    if latest_df is None:
        st.warning("No hay datos disponibles")
        return
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Casos Totales", format_large(latest_df['total_cases'].sum() if 'total_cases' in latest_df.columns else np.nan))
    with col2:
        st.metric("Muertes Totales", format_large(latest_df['total_deaths'].sum() if 'total_deaths' in latest_df.columns else np.nan))
    with col3:
        st.metric("Población", format_large(latest_df['population'].sum() if 'population' in latest_df.columns else np.nan))
    with col4:
        st.metric("Países", latest_df['location'].nunique() if 'location' in latest_df.columns else 0)

def render_insights_card(insights):
    st.markdown("### 📌 Insights automáticos")
    if not insights['correlations'] and not insights['trends']:
        st.info("No hay suficientes datos para generar insights automáticos.")
        return
    # mostrar correlaciones
    if insights['correlations']:
        st.subheader("Correlaciones (Spearman) — Top factores")
        for item in insights['correlations']:
            sign = "positivo" if item['corr'] > 0 else "negativo"
            st.write(f"- **{translated(item['factor'])}** — coeficiente: {item['corr']:.2f} ({sign})")
    # mostrar tendencias
    if insights['trends']:
        st.subheader("Tendencias recientes (mayor aumento en casos)")
        for t in insights['trends']:
            pct = t['pct_change'] * 100
            st.write(f"- **{t['location']}**: cambio {pct:.1f}% en 14 días (último: {int(t['recent'])})")

def render_country_detail(csv_df):
    st.header("Análisis por País — Detalle de Series")
    countries = sorted(csv_df['location'].unique().tolist())
    c = st.selectbox("Selecciona país", countries, index=countries.index("Ecuador") if "Ecuador" in countries else 0, key="country_pro")
    df = csv_df[csv_df['location']==c].sort_values('date').set_index('date')
    metric = st.selectbox("Métrica", [m for m in df.select_dtypes(include=[np.number]).columns], index=0, key="metric_pro")
    window = st.slider("Window rolling (días) para suavizado/detección", 3, 21, 7)
    if metric:
        st.line_chart(df[metric].fillna(0))
        # detectar picos
        peaks = detect_peaks(df[metric], window=window, z_thresh=2.8)
        if peaks:
            st.write(f"Se detectaron {len(peaks)} picos (posibles anomalías). Fechas: {', '.join([p.strftime('%Y-%m-%d') for p in peaks])}")
            # anotar en gráfico con plotly
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df.index, y=df[metric], mode='lines', name=metric))
            fig.add_trace(go.Scatter(x=peaks, y=df.loc[peaks, metric], mode='markers', marker=dict(size=10, color='red'), name='Picos'))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No se detectaron picos significativos.")

def main():
    st.title("Dashboard COVID-19 — Pro")
    latest_df, csv_df = load_data_prefer_api()
    if latest_df is None:
        st.error("No hay datos (ni API ni CSV). Coloca el CSV en data/owid-covid-data.csv")
        st.stop()

    # overview
    render_overview(latest_df)

    # compute insights (corr + trends)
    with st.spinner("Generando insights..."):
        insights = compute_insights(latest_df, csv_df, outcome='total_deaths_per_million', topk=6)
    render_insights_card(insights)

    # Tabs
    tab1, tab2 = st.tabs(["Explorar País", "Comparativo"])
    with tab1:
        if csv_df is not None:
            render_country_detail(csv_df)
        else:
            st.info("Para análisis por país se requiere CSV histórico local.")

    with tab2:
        st.header("Comparativo simple")
        # comparación por métrica entre países usando latest_df
        metric = st.selectbox("Métrica", [c for c in latest_df.columns if latest_df[c].dtype in [np.float64, np.int64]], index=0, key="comp_metric")
        countries = st.multiselect("Países", sorted(latest_df['location'].unique().tolist()), default=["Ecuador","Peru","Colombia"])
        if metric and countries:
            comp = latest_df[latest_df['location'].isin(countries)].set_index('location')[[metric]]
            comp[metric] = comp[metric].fillna(0)
            fig = px.bar(comp.reset_index(), x='location', y=metric, title=f"{translated(metric)} por país", text=metric)
            st.plotly_chart(fig, use_container_width=True)

if __name__=="__main__":
    main()
