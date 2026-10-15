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

WATER_LEVELS = {"bajo", "moderado", "alto"}


def get_current_weather() -> dict[str, Any]:
    """Return current precipitation and related weather observations."""
    response = requests.get(
        OPEN_METEO_URL,
        params={
            **CITY_COORDINATES,
            "current": "precipitation,temperature_2m,relative_humidity_2m,wind_speed_10m",
            "timezone": "America/Mexico_City",
        },
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json()
    current = payload.get("current")
    if (
        not isinstance(current, dict)
        or not isinstance(current.get("precipitation"), (int, float))
    ):
        raise ValueError("Open-Meteo no devolvió observaciones meteorológicas actuales.")

    return {
        "precipitation_mm": current["precipitation"],
        "temperature_c": current.get("temperature_2m"),
        "humidity_percent": current.get("relative_humidity_2m"),
        "wind_speed_kmh": current.get("wind_speed_10m"),
        "observed_at": current.get("time"),
    }


def get_risk_level(base_risk: int, precipitation_mm: float) -> tuple[str, str]:
    """Combine each zone's static risk with current precipitation."""
    if precipitation_mm >= 15 or base_risk >= 3:
        return "Rojo", "#ef4444"
    if precipitation_mm >= 5 or base_risk >= 2:
        return "Amarillo", "#f59e0b"
    return "Verde", "#22c55e"


def get_risk_zones(precipitation_mm: float) -> list[dict[str, Any]]:
    zones = []
    for zone in RISK_ZONES:
        level, color = get_risk_level(zone["base_risk"], precipitation_mm)
        zones.append(
            {
                "name": zone["name"],
                "latitude": zone["latitude"],
                "longitude": zone["longitude"],
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


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/status")
def api_status():
    try:
        weather = get_current_weather()
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

    precipitation = float(weather["precipitation_mm"])
    return jsonify(
        {
            "location": "Ciudad del Carmen",
            "weather": weather,
            "zones": get_risk_zones(precipitation),
        }
    )


@app.route("/api/reports", methods=["GET", "POST"])
def api_reports():
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

    street = data.get("street")
    water_level = data.get("water_level")
    if not isinstance(street, str) or not street.strip():
        return jsonify({"error": "La calle es obligatoria."}), 400
    street = street.strip()
    if len(street) > 160:
        return jsonify({"error": "La calle no puede superar 160 caracteres."}), 400
    if not isinstance(water_level, str) or water_level not in WATER_LEVELS:
        return jsonify({"error": "Selecciona un nivel de agua válido."}), 400

    report = {
        "id": str(uuid.uuid4()),
        "street": street,
        "water_level": water_level,
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
