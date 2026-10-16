from __future__ import annotations

import json
import logging
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False


@app.errorhandler(HTTPException)
def handle_api_http_error(error: HTTPException):
    if request.path.startswith("/api/"):
        return jsonify({"error": error.description}), error.code
    return error


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
CITY_COORDINATES = {"latitude": 18.6575, "longitude": -91.8325}
REPORTS_FILE = Path(__file__).resolve().parent / "reports.json"
REPORTS_LOCK = threading.Lock()

# Riesgo base: 1 = bajo, 2 = moderado, 3 = alto.
RISK_ZONES = [
    {
        "name": "Centro Histórico",
        "latitude": 18.6388,
        "longitude": -91.8367,
        "base_risk": 2,
    },
    {
        "name": "Colonia Santa Margarita",
        "latitude": 18.6505,
        "longitude": -91.8298,
        "base_risk": 3,
    },
    {
        "name": "Colonia 23 de Julio",
        "latitude": 18.6652,
        "longitude": -91.8195,
        "base_risk": 2,
    },
    {
        "name": "Colonia La Manigua",
        "latitude": 18.6325,
        "longitude": -91.8322,
        "base_risk": 3,
    },
    {
        "name": "Colonia El Caracol",
        "latitude": 18.6438,
        "longitude": -91.8290,
        "base_risk": 3,
    },
    {
        "name": "Playón / Arroyo de los Franceses",
        "latitude": 18.6410,
        "longitude": -91.8155,
        "base_risk": 3,
    },
    {
        "name": "La Caleta / Boquerón del Palmar",
        "latitude": 18.6535,
        "longitude": -91.8360,
        "base_risk": 2,
    },
    {
        "name": "Colonia Tierra y Libertad",
        "latitude": 18.6360,
        "longitude": -91.8080,
        "base_risk": 2,
    },
    {
        "name": "Justo Sierra",
        "latitude": 18.6245,
        "longitude": -91.8315,
        "base_risk": 1,
    },
    {
        "name": "Playa Norte",
        "latitude": 18.6604,
        "longitude": -91.8068,
        "base_risk": 2,
    },
]

REPORT_TYPES = {"inundacion", "construccion", "accidente", "bloqueo"}


WMO_WEATHER_DESCRIPTIONS: dict[int, str] = {
    0: "Despejado",
    1: "Mayormente despejado",
    2: "Parcialmente nublado",
    3: "Nublado",
    45: "Niebla",
    48: "Niebla con escarcha",
    51: "Llovizna ligera",
    53: "Llovizna moderada",
    55: "Llovizna densa",
    61: "Lluvia ligera",
    63: "Lluvia moderada",
    65: "Lluvia fuerte",
    80: "Chubascos ligeros",
    81: "Chubascos moderados",
    82: "Chubascos violentos",
    95: "Tormenta eléctrica",
    96: "Tormenta con granizo leve",
    99: "Tormenta con granizo fuerte",
}

DIAS_SEMANA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]


def format_spanish_date(date_str: str) -> str:
    """Format YYYY-MM-DD to Spanish friendly date."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        dia_sem = DIAS_SEMANA[dt.weekday()]
        mes = MESES[dt.month - 1]
        return f"{dia_sem}, {dt.day} de {mes} de {dt.year}"
    except Exception:
        return date_str


def get_weather_and_forecast() -> tuple[dict[str, Any], dict[str, Any]]:
    """Return current weather and today's detailed forecast from Open-Meteo."""
    response = requests.get(
        OPEN_METEO_URL,
        params={
            **CITY_COORDINATES,
            "current": "precipitation,temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
            "hourly": "precipitation_probability,precipitation,temperature_2m,weather_code",
            "daily": "precipitation_probability_max,precipitation_sum,temperature_2m_max,temperature_2m_min",
            "timezone": "America/Mexico_City",
            "forecast_days": 2,
        },
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json()

    current_data = payload.get("current")
    if not isinstance(current_data, dict):
        raise ValueError("Open-Meteo no devolvió observaciones meteorológicas actuales.")

    wcode = int(current_data.get("weather_code", 0))
    current_weather = {
        "precipitation_mm": current_data.get("precipitation", 0.0),
        "temperature_c": current_data.get("temperature_2m"),
        "humidity_percent": current_data.get("relative_humidity_2m"),
        "wind_speed_kmh": current_data.get("wind_speed_10m"),
        "weather_code": wcode,
        "weather_desc": WMO_WEATHER_DESCRIPTIONS.get(wcode, "Variable"),
        "observed_at": current_data.get("time"),
    }

    daily = payload.get("daily", {})
    daily_times = daily.get("time", [])
    today_str = daily_times[0] if daily_times else datetime.now().strftime("%Y-%m-%d")

    prob_max = daily.get("precipitation_probability_max", [0])[0] if daily.get("precipitation_probability_max") else 0
    precip_sum = daily.get("precipitation_sum", [0.0])[0] if daily.get("precipitation_sum") else 0.0
    temp_max = daily.get("temperature_2m_max", [None])[0] if daily.get("temperature_2m_max") else None
    temp_min = daily.get("temperature_2m_min", [None])[0] if daily.get("temperature_2m_min") else None

    # Parse hourly forecast for today
    hourly = payload.get("hourly", {})
    times = hourly.get("time", [])
    probs = hourly.get("precipitation_probability", [])
    precs = hourly.get("precipitation", [])
    temps = hourly.get("temperature_2m", [])
    codes = hourly.get("weather_code", [])

    today_hours: list[dict[str, Any]] = []
    for t, prob, prec, temp, code in zip(times, probs, precs, temps, codes):
        if str(t).startswith(today_str):
            try:
                hour_part = str(t).split("T")[1]
                h_int = int(hour_part.split(":")[0])
                ampm = "am" if h_int < 12 else "pm"
                h12 = h_int % 12
                if h12 == 0:
                    h12 = 12
                label_12h = f"{h12}:00 {ampm}"
            except Exception:
                h_int = 0
                label_12h = str(t)

            today_hours.append(
                {
                    "time": t,
                    "hour": f"{h_int:02d}:00",
                    "label": label_12h,
                    "probability": int(prob) if prob is not None else 0,
                    "precipitation_mm": round(float(prec), 2) if prec is not None else 0.0,
                    "temperature_c": round(float(temp), 1) if temp is not None else None,
                    "weather_code": int(code) if code is not None else 0,
                    "weather_desc": WMO_WEATHER_DESCRIPTIONS.get(int(code) if code is not None else 0, "Variable"),
                }
            )

    # Identificar horas pico de lluvia de hoy
    afternoon_slots = [h for h in today_hours if 12 <= int(h["hour"][:2]) <= 18]
    top_afternoon = max(afternoon_slots, key=lambda x: (x["probability"], x["precipitation_mm"])) if afternoon_slots else None
    top_precip_hour = max(today_hours, key=lambda x: (x["precipitation_mm"], x["probability"])) if today_hours else None

    peak_hours = []
    if top_afternoon and top_afternoon["probability"] >= 30:
        peak_hours.append(
            {
                "type": "tarde",
                "label": top_afternoon["label"],
                "hour": top_afternoon["hour"],
                "probability": top_afternoon["probability"],
                "precipitation_mm": top_afternoon["precipitation_mm"],
                "desc": top_afternoon["weather_desc"],
                "zone_tag": "Playa Norte y Malecón",
            }
        )

    if (
        top_precip_hour
        and (not top_afternoon or top_precip_hour["hour"] != top_afternoon["hour"])
        and top_precip_hour["precipitation_mm"] > 0
    ):
        peak_hours.append(
            {
                "type": "tormenta",
                "label": top_precip_hour["label"],
                "hour": top_precip_hour["hour"],
                "probability": top_precip_hour["probability"],
                "precipitation_mm": top_precip_hour["precipitation_mm"],
                "desc": top_precip_hour["weather_desc"],
                "zone_tag": "Col. Centro y Zonas Bajas",
            }
        )
    elif len(peak_hours) < 2 and len(today_hours) >= 20:
        night_candidates = [h for h in today_hours if int(h["hour"][:2]) >= 18]
        if night_candidates:
            h_night = max(night_candidates, key=lambda x: x["probability"])
            peak_hours.append(
                {
                    "type": "noche",
                    "label": h_night["label"],
                    "hour": h_night["hour"],
                    "probability": h_night["probability"],
                    "precipitation_mm": h_night["precipitation_mm"],
                    "desc": h_night["weather_desc"],
                    "zone_tag": "Col. Centro y zonas bajas",
                }
            )

    # Resumen y alerta del día
    alert_message = ""
    if any(h.get("weather_code") in (95, 96, 99) for h in today_hours):
        storm_h = next(h for h in today_hours if h.get("weather_code") in (95, 96, 99))
        alert_message = f"Alerta meteorológica: Posibilidad de tormenta eléctrica hacia las {storm_h['label']} con {storm_h['precipitation_mm']} mm de precipitación."
    elif precip_sum >= 10:
        alert_message = f"Aviso de lluvia acumulada: Se pronostican hasta {precip_sum} mm durante el día de hoy."
    elif prob_max >= 60:
        alert_message = f"Alta probabilidad de precipitaciones hoy (hasta {prob_max}%)."
    else:
        alert_message = "Condiciones mayormente estables con baja probabilidad de chubascos severos."

    forecast_today = {
        "date": today_str,
        "date_formatted": format_spanish_date(today_str),
        "precipitation_probability_max": prob_max,
        "precipitation_sum_mm": round(float(precip_sum), 2),
        "temperature_max_c": round(float(temp_max), 1) if temp_max is not None else None,
        "temperature_min_c": round(float(temp_min), 1) if temp_min is not None else None,
        "alert_message": alert_message,
        "peak_hours": peak_hours,
        "hourly": today_hours,
    }

    return current_weather, forecast_today


def get_risk_level(base_risk: int, precipitation_mm: float, forecast_sum_mm: float = 0.0) -> tuple[str, str]:
    """Combine each zone's static risk with current precipitation and daily forecast."""
    # Riesgo alto si la lluvia actual es fuerte, o si el pronóstico del día supera los 15 mm en zona vulnerable
    if precipitation_mm >= 15 or base_risk >= 3:
        return "Rojo", "#ef4444"
    if precipitation_mm >= 5 or base_risk >= 2 or (forecast_sum_mm >= 10 and base_risk >= 2):
        return "Amarillo", "#f59e0b"
    return "Verde", "#22c55e"


def get_risk_zones(precipitation_mm: float, forecast_sum_mm: float = 0.0) -> list[dict[str, Any]]:
    zones = []
    for zone in RISK_ZONES:
        level, color = get_risk_level(zone["base_risk"], precipitation_mm, forecast_sum_mm)
        zones.append(
            {
                "name": zone["name"],
                "latitude": zone["latitude"],
                "longitude": zone["longitude"],
                "base_risk": zone["base_risk"],
                "level": level,
                "color": color,
            }
        )
    return zones


def read_reports() -> list[dict[str, Any]]:
    if not REPORTS_FILE.exists():
        return []
    with REPORTS_FILE.open("r", encoding="utf-8") as reports_file:
        reports = json.load(reports_file)
    if not isinstance(reports, list):
        raise ValueError("El archivo de reportes debe contener una lista JSON.")
    return reports


@app.get("/favicon.ico")
def favicon():
    return app.send_static_file("favicon.ico")


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/status")
def api_status():
    try:
        current_weather, forecast_today = get_weather_and_forecast()
    except (requests.RequestException, ValueError):
        app.logger.exception("No se pudo obtener el clima de Open-Meteo.")
        return (
            jsonify(
                {
                    "error": "No fue posible consultar el clima actual.",
                    "zones": get_risk_zones(0),
                }
            ),
            502,
        )

    precipitation = float(current_weather.get("precipitation_mm", 0.0))
    forecast_sum = float(forecast_today.get("precipitation_sum_mm", 0.0))
    return jsonify(
        {
            "location": "Ciudad del Carmen",
            "weather": current_weather,
            "forecast_today": forecast_today,
            "zones": get_risk_zones(precipitation, forecast_sum),
        }
    )


@app.route("/api/predict", methods=["GET", "POST"])
def api_predict():
    """Calcula predicción climática y riesgo para una hora y destino en específico hoy."""
    data = request.get_json(silent=True) or {}
    hour_input = request.args.get("hora") or data.get("hora") or request.args.get("hour") or data.get("hour") or "17:00"
    destination_input = (
        request.args.get("destino")
        or data.get("destino")
        or request.args.get("destination")
        or data.get("destination")
        or "Playa Norte"
    )

    try:
        _, forecast_today = get_weather_and_forecast()
    except Exception as exc:
        return jsonify({"error": f"Error al consultar pronóstico: {exc}"}), 502

    import re
    m = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", str(hour_input).lower())
    target_hour = 17
    if m:
        h = int(m.group(1))
        ampm = m.group(3)
        if ampm == "pm" and h < 12:
            h += 12
        elif ampm == "am" and h == 12:
            h = 0
        target_hour = max(0, min(23, h))

    hourly_list = forecast_today.get("hourly", [])
    matched_slot = None
    for slot in hourly_list:
        if slot.get("hour", "").startswith(f"{target_hour:02d}:"):
            matched_slot = slot
            break

    if not matched_slot and hourly_list:
        matched_slot = hourly_list[0]

    matched_zone = None
    dest_clean = str(destination_input).lower().strip()
    for z in RISK_ZONES:
        if z["name"].lower() in dest_clean or dest_clean in z["name"].lower():
            matched_zone = z
            break

    base_risk = matched_zone["base_risk"] if matched_zone else 2
    precip_mm = matched_slot.get("precipitation_mm", 0.0) if matched_slot else 0.0
    prob = matched_slot.get("probability", 0) if matched_slot else 0

    if precip_mm >= 5.0 or (prob >= 70 and base_risk >= 3):
        risk_level = "Alto"
        risk_color = "#ef4444"
        recommendation = "Alta probabilidad de anegamientos. Evite transitar en vías bajas o estacionar en zonas inundables."
    elif precip_mm >= 1.0 or prob >= 50 or base_risk >= 2:
        risk_level = "Medio"
        risk_color = "#f59e0b"
        recommendation = "Probabilidad moderada de lluvia. Maneje con precaución ante posible encharcamiento."
    else:
        risk_level = "Bajo"
        risk_color = "#22c55e"
        recommendation = "Condiciones transitables favorables para el trayecto."

    return jsonify(
        {
            "fecha": forecast_today.get("date"),
            "fecha_formateada": forecast_today.get("date_formatted"),
            "hora_solicitada": hour_input,
            "hora_calculada": matched_slot.get("hour") if matched_slot else f"{target_hour:02d}:00",
            "etiqueta_hora": matched_slot.get("label") if matched_slot else f"{target_hour:02d}:00",
            "destino": matched_zone["name"] if matched_zone else destination_input,
            "lat": matched_zone["latitude"] if matched_zone else None,
            "lng": matched_zone["longitude"] if matched_zone else None,
            "probabilidad_lluvia": prob,
            "precipitacion_mm": precip_mm,
            "temperatura_c": matched_slot.get("temperature_c") if matched_slot else None,
            "condicion_clima": matched_slot.get("weather_desc") if matched_slot else "Variable",
            "nivel_riesgo": risk_level,
            "color_riesgo": risk_color,
            "recomendacion": recommendation,
        }
    )


@app.route("/api/reports", methods=["GET", "POST", "OPTIONS"])
def api_reports():
    if request.method == "OPTIONS":
        return "", 204

    if request.method == "GET":
        try:
            with REPORTS_LOCK:
                reports = read_reports()
        except (OSError, json.JSONDecodeError, ValueError):
            app.logger.exception("No se pudieron leer los reportes ciudadanos.")
            return jsonify({"error": "No se pudieron leer los reportes."}), 500
        return jsonify({"reports": reports})

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Envía un objeto JSON válido."}), 400

    street = data.get("calle", data.get("street"))
    report_type = data.get("tipo")
    description = data.get("descripcion", "")

    if not isinstance(street, str) or not street.strip():
        return jsonify({"error": "La calle es obligatoria."}), 400
    street = street.strip()
    if len(street) > 160:
        return jsonify({"error": "La calle no puede superar 160 caracteres."}), 400
    if not isinstance(report_type, str) or report_type not in REPORT_TYPES:
        return jsonify({"error": "Selecciona un tipo de reporte válido."}), 400
    if not isinstance(description, str):
        return jsonify({"error": "La descripción debe ser texto."}), 400
    description = description.strip()
    if len(description) > 1000:
        return jsonify({"error": "La descripción no puede superar 1000 caracteres."}), 400

    latitude = data.get("lat")
    longitude = data.get("lng")
    if (latitude is None) != (longitude is None):
        return jsonify({"error": "Envía ambas coordenadas (lat y lng), o ninguna."}), 400
    if latitude is not None:
        if (
            isinstance(latitude, bool)
            or isinstance(longitude, bool)
            or not isinstance(latitude, (int, float))
            or not isinstance(longitude, (int, float))
            or not -90 <= latitude <= 90
            or not -180 <= longitude <= 180
        ):
            return jsonify({"error": "Las coordenadas no son válidas."}), 400

    report = {
        "id": str(uuid.uuid4()),
        "calle": street,
        "tipo": report_type,
        "descripcion": description,
        "lat": latitude,
        "lng": longitude,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        with REPORTS_LOCK:
            reports = read_reports()
            reports.append(report)
            with REPORTS_FILE.open("w", encoding="utf-8") as reports_file:
                json.dump(reports, reports_file, ensure_ascii=False, indent=2)
                reports_file.write("\n")
    except (OSError, json.JSONDecodeError, ValueError):
        app.logger.exception("No se pudo guardar el reporte ciudadano.")
        return jsonify({"error": "No se pudo guardar el reporte."}), 500

    return jsonify({"message": "Reporte guardado.", "report": report}), 201


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    port = int(os.environ.get("PORT", 5000))
    print(f"=== INICIANDO OLARUTA - CIUDAD DEL CARMEN ===")
    print(f"Servidor activo en: http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
