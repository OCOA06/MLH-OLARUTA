# 🌊 OlaRuta — Sistema de Monitoreo Ciudadano de Inundaciones
### Proyecto para Hackathon MLH OLARUTA · Ciudad del Carmen, Campeche

> *"Sistema de alerta temprana y monitoreo ciudadano en tiempo real ante inundaciones y anegamientos en Ciudad del Carmen, Campeche. Integra pronósticos meteorológicos satelitales en vivo de Open-Meteo, cálculo de niveles de riesgo por zona y un módulo participativo para reportes comunitarios geolocalizados."*

---

## 📌 1. El Problema en Ciudad del Carmen
Ciudad del Carmen es una isla de barrera entre el Golfo de México y la Laguna de Términos con una altitud promedio de solo **0.5 a 2.0 metros sobre el nivel del mar**. 

Ante episodios de precipitación continua combinados con marea alta (pleamar) o frentes fríos ("nortes"), el drenaje pluvial se satura con facilidad. **OlaRuta** proporciona una herramienta pública, ligera y accesible para que los habitantes y autoridades conozcan el nivel de riesgo en su colonia y reporten anegamientos al momento.

---

## 🏛️ 2. Arquitectura de la Aplicación

- **Frontend Moderno y Ligero**:
  - HTML5 semántico + Tailwind CSS (diseño limpio, responsivo y adaptado para móviles).
  - **Leaflet.js + OpenStreetMap**: Visualización cartográfica interactiva sin requerir API keys de pago, con marcadores coloreados por nivel de riesgo (*Verde, Amarillo, Rojo*).
- **Backend en Python (Flask)**:
  - Servidor ligero y robusto en `app.py`.
  - Integración en tiempo real con la API de **Open-Meteo** (precipitación actual en mm, temperatura, humedad y velocidad del viento).
  - Algoritmo de ponderación de riesgo dinámico (cruce entre precipitación en tiempo real y susceptibilidad base de cada zona).
  - Almacenamiento local concurrente y seguro (`reports.json` con thread lock) para reportes ciudadanos.

---

## 🚀 3. Instrucciones de Ejecución

### Prerrequisitos
- Python 3.10 o superior

### Instalación y arranque
```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Iniciar el servidor
python app.py
```

Abre tu navegador en:  
👉 **`http://localhost:5000`** o **`http://127.0.0.1:5000`**

---

## 🔌 4. Endpoints de la API

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/` | Carga el centro de monitoreo interactivo de OlaRuta |
| `GET` | `/api/status` | Condiciones meteorológicas en tiempo real (Open-Meteo) y semáforo de riesgo por colonia |
| `GET` | `/api/reports` | Consulta la lista de reportes ciudadanos recientes |
| `POST` | `/api/reports` | Registra un nuevo reporte ciudadano de nivel de agua (`street`, `water_level`) |

---

## 👥 Equipo OlaRuta
Desarrollado para el Hackathon **MLH OLARUTA**.
