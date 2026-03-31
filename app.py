# Done by
# - Aruna Cathciyal Gilbert Radjou

library(shiny)
library(httr2)
library(jsonlite)
library(dplyr)
library(lubridate)
library(plotly)
library(readr)
library(tibble)

# -----------------------------
# Config
# -----------------------------
BERLIN_LAT <- 52.52
BERLIN_LON <- 13.405
LOCATION_NAME <- "Berlin, Germany"
TZ_NAME <- "Europe/Berlin"

# -----------------------------
# Load artifacts
# -----------------------------
# IMPORTANT:
# Replace these with your real R model objects or use reticulate if needed.
rain_pipe <- readRDS("./rain_pipe.rds")
snow_pipe <- readRDS("./snow_pipe.rds")
rain_features <- readRDS("./rain_features.rds")
snow_features <- readRDS("./snow_features.rds")

# -----------------------------
# Forecast daily features
# -----------------------------
fetch_forecast_daily_features <- function(start_date, end_date) {
  url <- "https://api.open-meteo.com/v1/forecast"

  daily_vars <- paste(
    c(
      "temperature_2m_mean",
      "temperature_2m_min",
      "temperature_2m_max",
      "wet_bulb_temperature_2m_mean",
      "dew_point_2m_mean",
      "relative_humidity_2m_mean",
      "cloud_cover_mean",
      "wind_speed_10m_mean",
      "pressure_msl_mean"
    ),
    collapse = ","
  )

  resp <- request(url) |>
    req_url_query(
      latitude = BERLIN_LAT,
      longitude = BERLIN_LON,
      timezone = TZ_NAME,
      start_date = as.character(start_date),
      end_date = as.character(end_date),
      daily = daily_vars
    ) |>
    req_timeout(30) |>
    req_perform()

  j <- resp_body_json(resp, simplifyVector = TRUE)

  if (is.null(j$daily) || is.null(j$daily$time)) {
    return(tibble())
  }

  df <- as_tibble(j$daily)
  df$time <- as.Date(df$time)

  df
}

# -----------------------------
# Prediction: next 5 days
# -----------------------------
predict_next_5_days <- function() {
  today <- as.Date(with_tz(Sys.time(), tzone = TZ_NAME))
  end_date <- today + days(5)

  df <- fetch_forecast_daily_features(today, end_date)

  if (nrow(df) == 0) {
    return(tibble())
  }

  results <- lapply(seq_len(nrow(df)), function(i) {
    row <- df[i, , drop = FALSE]

    Xr <- row[, rain_features, drop = FALSE]
    Xs <- row[, snow_features, drop = FALSE]

    # Assumes models return class probabilities with type = "prob"
    rain_pred <- predict(rain_pipe, Xr, type = "prob")
    snow_pred <- predict(snow_pipe, Xs, type = "prob")

    # Assumes the positive class is in column 2 or named "1"/"yes"
    rain_prob <- as.numeric(rain_pred[[ncol(rain_pred)]])
    snow_prob <- as.numeric(snow_pred[[ncol(snow_pred)]])

    tibble(
      date = row$time,
      rain_prob = rain_prob,
      rain_yes = rain_prob >= 0.7,
      snow_prob = snow_prob,
      snow_yes = snow_prob >= 0.7
    )
  })

  bind_rows(results)
}

# -----------------------------
# Interactive chart
# -----------------------------
plot_5day_probabilities <- function(results) {
  if (nrow(results) == 0) return(NULL)

  dates <- format(results$date, "%d %b")
  rain_probs <- results$rain_prob * 100
  snow_probs <- results$snow_prob * 100

  plot_ly() |>
    add_trace(
      x = dates,
      y = rain_probs,
      type = "scatter",
      mode = "lines+markers",
      name = "Rain Probability 🌧️",
      line = list(color = "#0B3C5D", width = 4),
      marker = list(size = 9, color = "#0B3C5D", line = list(width = 2, color = "white"))
    ) |>
    add_trace(
      x = dates,
      y = snow_probs,
      type = "scatter",
      mode = "lines+markers",
      name = "Snow Probability ❄️",
      line = list(color = "#EAF6FF", width = 4),
      marker = list(size = 9, color = "#EAF6FF", line = list(width = 2, color = "#0B3C5D"))
    ) |>
    layout(
      title = list(
        text = "Rain & Snow Probability — Next 5 Days",
        font = list(size = 22, color = "white"),
        x = 0.02
      ),
      xaxis = list(
        title = "Date",
        tickfont = list(color = "white"),
        titlefont = list(color = "white"),
        showgrid = FALSE
      ),
      yaxis = list(
        title = "Probability (%)",
        tickfont = list(color = "white"),
        titlefont = list(color = "white"),
        range = c(0, 100),
        gridcolor = "rgba(255,255,255,0.25)",
        zerolinecolor = "rgba(255,255,255,0.4)"
      ),
      hovermode = "x unified",
      paper_bgcolor = "rgba(0,0,0,0)",
      plot_bgcolor = "rgba(0,0,0,0)",
      font = list(color = "white"),
      legend = list(
        orientation = "h",
        yanchor = "bottom",
        y = 1.05,
        xanchor = "right",
        x = 1,
        font = list(color = "white")
      ),
      margin = list(l = 50, r = 40, t = 80, b = 50)
    )
}

# -----------------------------
# Current temperature + hourly
# -----------------------------
fetch_berlin_today <- function() {
  url <- "https://api.open-meteo.com/v1/forecast"

  resp <- request(url) |>
    req_url_query(
      latitude = BERLIN_LAT,
      longitude = BERLIN_LON,
      current = "temperature_2m",
      hourly = "temperature_2m",
      timezone = TZ_NAME
    ) |>
    req_timeout(30) |>
    req_perform()

  j <- resp_body_json(resp, simplifyVector = TRUE)

  current_temp <- as.numeric(j$current$temperature_2m)

  df_hourly <- tibble(
    time = ymd_hms(j$hourly$time, tz = TZ_NAME),
    temp = as.numeric(j$hourly$temperature_2m)
  )

  today <- as.Date(with_tz(Sys.time(), tzone = TZ_NAME))
  df_hourly <- df_hourly |> filter(as.Date(time) == today)

  list(current_temp = current_temp, df_hourly = df_hourly)
}

# -----------------------------
# UI
# -----------------------------
ui <- fluidPage(
  tags$head(
    tags$style(HTML("
      body, .container-fluid {
        background: linear-gradient(135deg, #6aa9e8 0%, #3e79bd 55%, #2d5f9f 100%);
        min-height: 100vh;
      }
      .topbar {
        display:flex;
        justify-content:space-between;
        color:white;
        font-weight:600;
        margin-bottom:20px;
      }
      .bigTitle {
        color:white;
        font-size:78px;
        font-weight:800;
      }
      .card {
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.20);
        border-radius: 24px;
        padding: 24px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.25);
        color: white;
        min-height: 170px;
      }
      .section-title {
        font-size:78px;
        font-weight:800;
        color:white;
      }
      .sub-title {
        font-size:34px;
        color:white;
      }
      .temp-big {
        text-align:right;
        font-size:115px;
        font-weight:800;
        color:white;
      }
      h3 {
        color: white;
      }
      .shiny-plot-output, .plotly {
        background: transparent !important;
      }
    "))
  ),

  div(class = "topbar",
      div("⬡ Weather Forecast"),
      textOutput("header_time", inline = TRUE)
  ),

  fluidRow(
    column(
      width = 8,
      div(class = "section-title", "Today"),
      div(class = "sub-title", "Current Temperature")
    ),
    column(
      width = 4,
      uiOutput("current_temp_ui")
    )
  ),

  br(),
  div(class = "bigTitle", "Next 5 Days Prediction 🌧️ ❄️"),
  br(),
  plotlyOutput("prob_plot", height = "450px"),
  br(),
  uiOutput("prediction_cards"),

  tags$hr(),
  h3("Hourly Temperature — Today (Berlin)"),
  plotlyOutput("hourly_plot", height = "300px")
)

# -----------------------------
# Server
# -----------------------------
server <- function(input, output, session) {

  today_data <- reactive({
    fetch_berlin_today()
  })

  predictions <- reactive({
    predict_next_5_days()
  })

  output$header_time <- renderText({
    now <- with_tz(Sys.time(), tzone = TZ_NAME)
    paste0(format(now, "%H:%M"), " · ", format(now, "%d %b %Y"), " · ", LOCATION_NAME)
  })

  output$current_temp_ui <- renderUI({
    temp_c <- today_data()$current_temp
    div(class = "temp-big", sprintf("%.0f°", temp_c))
  })

  output$prob_plot <- renderPlotly({
    results <- predictions()
    plot_5day_probabilities(results)
  })

  output$prediction_cards <- renderUI({
    results <- predictions()

    if (nrow(results) == 0) {
      return(div(style = "color:white;", "No prediction data available."))
    }

    fluidRow(
      lapply(seq_len(nrow(results)), function(i) {
        res <- results[i, ]

        column(
          width = floor(12 / nrow(results)),
          div(
            class = "card",
            HTML(sprintf("
              <div style='font-size:18px; font-weight:900; color:white;'>%s</div>

              <div style='margin-top:14px;'>
                <b style='color:white;'>🌧 Rain</b><br/>
                <span style='color:white; font-size:18px; font-weight:700;'>%s</span>
              </div>

              <div style='margin-top:12px;'>
                <b style='color:white;'>❄️ Snow</b><br/>
                <span style='color:white; font-size:18px; font-weight:700;'>%s</span>
              </div>
            ",
            format(res$date, "%d %b"),
            ifelse(res$rain_yes, "Yes ✅", "No ❌"),
            ifelse(res$snow_yes, "Yes ✅", "No ❌")
            ))
          )
        )
      })
    )
  })

  output$hourly_plot <- renderPlotly({
    df_hourly <- today_data()$df_hourly

    if (nrow(df_hourly) == 0) {
      return(plot_ly() |> layout(title = "No hourly temperature data available for today."))
    }

    plot_ly(df_hourly, x = ~time, y = ~temp, type = "scatter", mode = "lines+markers") |>
      layout(
        paper_bgcolor = "rgba(0,0,0,0)",
        plot_bgcolor = "rgba(0,0,0,0)",
        font = list(color = "white"),
        xaxis = list(title = "Time"),
        yaxis = list(title = "Temperature (°C)")
      )
  })
}

shinyApp(ui, server)
