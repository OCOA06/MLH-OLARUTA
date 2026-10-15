# 🌊 OlaRuta — Sistema de Monitoreo Ciudadano de Inundaciones
### Proyecto para Hackathon MLH OLARUTA · Ciudad del Carmen, Campeche

> *"Sistema de alerta temprana y monitoreo ciudadano en tiempo real ante inundaciones y eventualidades viales en Ciudad del Carmen, Campeche. Integra pronósticos meteorológicos satelitales en vivo de Open-Meteo, cálculo de niveles de riesgo por zona y un módulo participativo para reportes comunitarios georreferenciados en el mapa."*

---

## 📌 1. El Problema en Ciudad del Carmen
Ciudad del Carmen es una isla de barrera entre el Golfo de México y la Laguna de Términos con una altitud promedio de solo **0.5 a 2.0 metros sobre el nivel del mar**. 

Ante episodios de precipitación continua combinados con marea alta (pleamar) o frentes fríos ("nortes"), el drenaje pluvial se satura con facilidad. **OlaRuta** proporciona una herramienta pública, ligera y accesible para que los habitantes y autoridades conozcan el nivel de riesgo en su colonia, reporten anegamientos, obras viales y accidentes directamente marcando el punto en el mapa.

---

## 🏛️ 2. Arquitectura de la Aplicación

- **Frontend Moderno y Fiel a los Diseños Oficiales (Mockups OlaRuta)**:
  - Interfaz visual basada en la identidad oficial: navbar navy (`#07162c`), icono circular glowing `icon.png` y logo oficial `logo.png`.
  - Favicon oficial integrado para pestañas de navegador.
  - **Pantalla 1: Reporte Ciudadano** ("¿Qué está pasando en tu ubicación?") con tarjetas interactivas de categoría con sus respectivos recursos:
    - 💥 **Accidente** (`accidente.png`)
    - 🌊 **Inundación** (`inundaciones.png`)
    - 🚧 **Cierre / Bloqueo** (`bloqueos.png`)
    - Botones píldora oficiales: **Reportar**, **Predicciones** y **Regresar**.
  - **Pantalla 2: Modal de Predicción** ("HORA", "A DONDE VAS", botón **PREDICCIÓN** en azul cielo).
  - **Pantalla 3: Pronóstico y Riesgo** ("¿Por dónde lloverá hoy?") con píldoras de lluvia (`pronosticolluvia.png`), semáforo de riesgo por colonia (Alto, Medio, Bajo) y observaciones meteorológicas en vivo de Open-Meteo.
  - **Leaflet.js + OpenStreetMap**: Visualización cartográfica interactiva con pin personalizado estilo mockup, marcadores de incidentes y zonas de riesgo.
  - **Georreferenciación con un clic**: Haz clic sobre cualquier punto del mapa para asignar automáticamente las coordenadas `lat` y `lng` al reporte.
- **Backend en Python (Flask)**:
  - Servidor ligero y robusto en `app.py`.
  - Integración en tiempo real con la API de **Open-Meteo** (precipitación actual en mm, temperatura, humedad y velocidad del viento).
  - Algoritmo de ponderación de riesgo dinámico (cruce entre precipitación en tiempo real y susceptibilidad base de cada zona).
  - Almacenamiento local concurrente y seguro (`reports.json` con thread lock) para reportes ciudadanos.
  - Soporte completo para CORS (permite ejecución tanto con Flask como con Live Server).

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

*(También puedes abrir `index.html` directamente o con Live Server sin necesidad de ejecutar Flask gracias al modo de respaldo directo con Open-Meteo).*

---

## 🔌 4. Endpoints de la API

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/` | Carga el centro de monitoreo interactivo de OlaRuta |
| `GET` | `/api/status` | Condiciones meteorológicas en tiempo real (Open-Meteo) y semáforo de riesgo por colonia |
| `GET` | `/api/reports` | Consulta la lista de reportes ciudadanos recientes georreferenciados |
| `POST` | `/api/reports` | Registra un nuevo reporte ciudadano (`calle`, `tipo`, `descripcion`, `lat`, `lng`) |

---

## 👥 Equipo OlaRuta
Desarrollado con ❤️ para el Hackathon **MLH OLARUTA**:

- **Jossie Arianna Peraza Castro**
- **Sara Victoria Rojas Gonzalez**
- **Roger de Jesus Sanchez Peñate**
- **Ángel Jaret Pérez Rodríguez**
- **Miguel Ángel Guerrero Damas**

---

## 🏆 Entrega Final
- **Versión**: 1.0.0 — Entrega Final
- **Estado**: Completo, verificado y operativo (Soporte dual: Backend Flask y modo estático / Live Server)
- **Repositorio oficial**: [https://github.com/OCOA06/MLH-OLARUTA](https://github.com/OCOA06/MLH-OLARUTA)
