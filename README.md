### Done by
- Aruna Cathciyal Gilbert Radjou

# PrecipiNet – Weather Prediction Dashboard

PrecipiNet is an interactive **Streamlit dashboard built in Python** that predicts the probability of **rain and snow** using machine learning models and real-time weather data from the **Open-Meteo API**.

The application provides a clean interface for viewing **current weather conditions and precipitation predictions**.

---

## Project Overview

This project builds a **machine learning weather forecasting dashboard** focused on predicting precipitation events in **Berlin, Germany**.

The system:

- Fetches **real-time weather data** from Open-Meteo
- Uses trained **machine learning models** to predict rain and snow
- Displays predictions with **probability scores**
- Visualizes **weather trends and forecasts**

---

## Features

### Live Weather Data

- Fetches real-time temperature from **Open-Meteo API**
- Displays current weather conditions for **Berlin**

### Rain Prediction

- Predicts whether rain will occur
- Displays prediction probability and confidence

### Snow Prediction

- Predicts whether snowfall will occur
- Displays probability of snow events

### Interactive Visualizations

The dashboard uses:

- **Plotly (Python)** for interactive charts
- **Streamlit** for the web interface

---

## Machine Learning Models

Two **classification models** are used:

| Model | Target Variable |
|---------|----------------|
| Rain Model | `rain_binary` |
| Snow Model | `snow_binary` |

### Prediction Rule

- Probability ≥ 0.7 → Event predicted
- Probability < 0.7 → No event predicted

---

## Model Features

The models use the following meteorological variables:

- `temperature_2m_mean`
- `temperature_2m_min`
- `temperature_2m_max`
- `wet_bulb_temperature_2m_mean`
- `dew_point_2m_mean`
- `relative_humidity_2m_mean`
- `cloud_cover_mean`
- `wind_speed_10m_mean`
- `pressure_msl_mean`

These variables capture atmospheric conditions associated with precipitation events.

---

## Data Source

**Open-Meteo Weather API**

https://open-meteo.com/

The API provides:

- Current weather data
- Hourly forecasts
- Daily meteorological features
- Historical weather data

---

## Technologies Used

| Technology | Purpose |
|------------|---------|
| Python | Programming language |
| Streamlit | Web application framework |
| Plotly | Interactive visualizations |
| Pandas | Data manipulation |
| NumPy | Numerical computations |
| Requests | API requests |
| Scikit-learn | Machine learning models |
| Joblib / Pickle | Model serialization |
| Datetime | Date-time handling |
| Open-Meteo API | Weather data source |

---

## Project Structure

```text
precipinet/
│
├── app.py
├── rain_pipe.pkl
├── snow_pipe.pkl
├── rain_features.pkl
├── snow_features.pkl
├── metrics.pkl
├── requirements.txt
├── README.md
```

---

