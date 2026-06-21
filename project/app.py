# Done by
# - Aruna Cathciyal Gilbert Radjou
# - Ceciliya Souce

import streamlit as st
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import joblib
import plotly.graph_objects as go

# -----------------------------
# Config
# -----------------------------
st.set_page_config(page_title="PrecipiNet", page_icon="🌦️", layout="wide")
BERLIN_LAT = 52.52
BERLIN_LON = 13.405
LOCATION_NAME = "Berlin, Germany"
BERLIN_TZ = ZoneInfo("Europe/Berlin")
TZ_NAME = "Europe/Berlin"

# -----------------------------
# Load artifacts
# -----------------------------
rain_pipe = joblib.load("./rain_pipe.pkl")
snow_pipe = joblib.load("./snow_pipe.pkl")
rain_features = joblib.load("./rain_features.pkl")
snow_features = joblib.load("./snow_features.pkl")

# -----------------------------
# Forecast daily features
# -----------------------------
@st.cache_data(ttl=1800)
def fetch_forecast_daily_features(start_date, end_date):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": BERLIN_LAT,
        "longitude": BERLIN_LON,
        "timezone": TZ_NAME,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "daily": ",".join([
            "temperature_2m_mean",
            "temperature_2m_min",
            "temperature_2m_max",
            "wet_bulb_temperature_2m_mean",
            "dew_point_2m_mean",
            "relative_humidity_2m_mean",
            "cloud_cover_mean",
            "wind_speed_10m_mean",
            "pressure_msl_mean",
        ])
    }

    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    j = r.json()

    if "daily" not in j or "time" not in j["daily"]:
        return pd.DataFrame()

    df = pd.DataFrame(j["daily"])
    df["time"] = pd.to_datetime(df["time"]).dt.date
    return df

# -----------------------------
# Prediction: next 5 days
# -----------------------------
def predict_next_5_days():
    today = datetime.now(BERLIN_TZ).date()
    end_date = today + timedelta(days=5)

    df = fetch_forecast_daily_features(today, end_date)
    results = []

    for _, row in df.iterrows():
        Xr = row[rain_features].to_frame().T
        Xs = row[snow_features].to_frame().T

        rain_prob = float(rain_pipe.predict_proba(Xr)[0, 1])
        snow_prob = float(snow_pipe.predict_proba(Xs)[0, 1])

        results.append({
            "date": row["time"],
            "rain_prob": rain_prob,
            "rain_yes": rain_prob >= 0.7,
            "snow_prob": snow_prob,
            "snow_yes": snow_prob >= 0.7,
        })

    return results

# -----------------------------
# Interactive chart (high contrast)
# -----------------------------
def plot_5day_probabilities(results):
    dates = [r["date"].strftime("%d %b") for r in results]
    rain_probs = [r["rain_prob"] * 100 for r in results]
    snow_probs = [r["snow_prob"] * 100 for r in results]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=dates,
        y=rain_probs,
        mode="lines+markers",
        name="Rain Probability 🌧️",
        line=dict(color="#0B3C5D", width=4),
        marker=dict(size=9, color="#0B3C5D",
                    line=dict(width=2, color="white")),
    ))

    fig.add_trace(go.Scatter(
        x=dates,
        y=snow_probs,
        mode="lines+markers",
        name="Snow Probability ❄️",
        line=dict(color="#EAF6FF", width=4),
        marker=dict(size=9, color="#EAF6FF",
                    line=dict(width=2, color="#0B3C5D")),
    ))

    fig.update_layout(
        title=dict(
            text="Rain & Snow Probability — Next 5 Days",
            font=dict(size=22, color="white"),
            x=0.02
        ),
        xaxis=dict(
            title="Date",
            tickfont=dict(color="white"),
            titlefont=dict(color="white"),
            showgrid=False
        ),
        yaxis=dict(
            title="Probability (%)",
            tickfont=dict(color="white"),
            titlefont=dict(color="white"),
            range=[0, 100],
            gridcolor="rgba(255,255,255,0.25)",
            zerolinecolor="rgba(255,255,255,0.4)"
        ),
        hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="right",
            x=1,
            font=dict(color="white")
        ),
        margin=dict(l=50, r=40, t=80, b=50),
    )

    return fig

# -----------------------------
# Current temperature + hourly
# -----------------------------
@st.cache_data(ttl=300)
def fetch_berlin_today():
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": BERLIN_LAT,
        "longitude": BERLIN_LON,
        "current": "temperature_2m",
        "hourly": "temperature_2m",
        "timezone": TZ_NAME
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    j = r.json()

    current_temp = float(j["current"]["temperature_2m"])
    df_hourly = pd.DataFrame({
        "time": pd.to_datetime(j["hourly"]["time"]),
        "temp": j["hourly"]["temperature_2m"]
    })

    today = pd.Timestamp.now(tz=TZ_NAME).date()
    df_hourly = df_hourly[df_hourly["time"].dt.date == today]

    return current_temp, df_hourly

temp_c, df_hourly = fetch_berlin_today()
now = datetime.now(BERLIN_TZ)

# -----------------------------
# CSS
# -----------------------------
st.markdown("""
<style>
.stApp {
  background: linear-gradient(135deg, #6aa9e8 0%, #3e79bd 55%, #2d5f9f 100%);
}
header, footer {visibility: hidden;}
.card {
  background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.20);
  border-radius: 24px;
  padding: 24px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.25);
}
.bigTitle {
  color:white;
  font-size:78px;
  font-weight:800;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# HEADER
# -----------------------------
st.markdown(
    f"""
<div style="display:flex; justify-content:space-between; color:white; font-weight:600;">
  <div>⬡ Weather Forecast</div>
  <div>{now.strftime("%H:%M")} · {now.strftime("%d %b %Y")} · {LOCATION_NAME}</div>
</div>
""",
    unsafe_allow_html=True
)

# -----------------------------
# TODAY
# -----------------------------
left, right = st.columns([1.6, 1], gap="large")

with left:
    st.markdown("<div style='font-size:78px; font-weight:800; color:white;'>Today</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:34px; color:white;'>Current Temperature</div>", unsafe_allow_html=True)

with right:
    st.markdown(
        f"<div style='text-align:right; font-size:115px; font-weight:800; color:white;'>{temp_c:.0f}°</div>",
        unsafe_allow_html=True
    )

# -----------------------------
# 5-DAY PREDICTION
# -----------------------------
st.write("")
st.markdown("<div class='bigTitle'>Next 5 Days Prediction 🌧️ ❄️</div>", unsafe_allow_html=True)

results = predict_next_5_days()

# Interactive chart
st.plotly_chart(plot_5day_probabilities(results), use_container_width=True)

# Cards (YES / NO only)
cols = st.columns(len(results), gap="medium")

for col, res in zip(cols, results):
    with col:
        st.markdown(
            f"""
            <div class="card">
              <div style="font-size:18px; font-weight:900; color:white;">
                {res["date"].strftime('%d %b')}
              </div>

              <div style="margin-top:14px;">
                <b style="color:white;">🌧 Rain</b><br/>
                <span style="color:white; font-size:18px; font-weight:700;">
                  {"Yes ✅" if res["rain_yes"] else "No ❌"}
                </span>
              </div>

              <div style="margin-top:12px;">
                <b style="color:white;">❄️ Snow</b><br/>
                <span style="color:white; font-size:18px; font-weight:700;">
                  {"Yes ✅" if res["snow_yes"] else "No ❌"}
                </span>
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )

# -----------------------------
# HOURLY TEMPERATURE
# -----------------------------
st.markdown("---")
st.markdown("### Hourly Temperature — Today (Berlin)")

if df_hourly.empty:
    st.warning("No hourly temperature data available for today.")
else:
    st.line_chart(df_hourly.set_index("time")[["temp"]])
