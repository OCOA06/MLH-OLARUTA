# OlaRuta — Sistema de Monitoreo Ciudadano ante Inundaciones
### Proyecto para Hackathon MLH OlaRuta · Ciudad del Carmen, Campeche

Sistema de alerta temprana y monitoreo ciudadano orientado a la prevención y respuesta ante contingencias pluviales y afectaciones viales en Ciudad del Carmen, Campeche. La plataforma integra observaciones meteorológicas en tiempo real, estimación de niveles de riesgo por zona y un módulo participativo para la generación y consulta de reportes comunitarios georreferenciados.

---

## 1. Contexto y Problemática

Ciudad del Carmen se ubica en una isla de barrera entre el Golfo de México y la Laguna de Términos, con una altitud promedio de entre 0.5 y 2.0 metros sobre el nivel del mar.

Debido a su ubicación geográfica y características topográficas, las precipitaciones intensas, en combinación con fenómenos de marea alta y frentes fríos, ocasionan saturación recurrente en la red de drenaje pluvial. OlaRuta surge como una solución accesible para la ciudadanía y los cuerpos de apoyo, facilitando la visualización del riesgo por sectores, la consulta del pronóstico de lluvias del día y el registro oportuno de incidentes viales y anegamientos sobre el mapa.

---

## 2. Características Principales

- **Módulo de Reporte Ciudadano:**
  Permite a los usuarios notificar incidentes en su ubicación seleccionando entre las categorías principales: Accidentes, Inundaciones y Cierres o Bloqueos viales. La captura de ubicación se realiza directamente mediante interacción con el mapa cartográfico.

- **Pronóstico Meteorológico y Predicción del Día:**
  Conexión automatizada con servicios meteorológicos satelitales (Open-Meteo) para obtener las condiciones del momento y el pronóstico de precipitaciones hora por hora. Incluye un módulo de consulta personalizada para verificar la probabilidad de lluvia y el nivel de riesgo estimado según la hora y el destino dentro de la isla.

- **Mapa Cartográfico Interactivo:**
  Visualización geoespacial desarrollada con OpenStreetMap y Leaflet, diseñada para señalar reportes recientes, zonas con susceptibilidad pluvial y puntos de referencia de la ciudad.

- **Arquitectura Ligera y Confiable:**
  Desarrollado con un servidor ligero en Python (Flask) y almacenamiento concurrente de reportes. Cuenta con soporte de respaldo para operar en entornos locales de servidor web o directamente desde el navegador.

---

## 3. Instrucciones de Instalación y Uso

### Requisitos previos
- Python 3.10 o versión superior.
- Navegador web moderno con soporte para JavaScript.

### Puesta en marcha

1. Instalar las dependencias del proyecto:
```bash
pip install -r requirements.txt
```

2. Iniciar el servidor local:
```bash
python app.py
```

3. Acceder al sistema desde el navegador web:
- `http://localhost:5000` o `http://127.0.0.1:5000`

Nota: La aplicación también puede ser visualizada en modo estático abriendo directamente el archivo `index.html` en el navegador.

---

## 4. Servicios y Endpoints Disponibles

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` | Interfaz principal de monitoreo y consulta |
| GET | `/api/status` | Condiciones del clima en tiempo real, pronóstico del día y niveles de riesgo por zona |
| GET | `/api/predict` | Consulta de probabilidad de lluvia y riesgo por hora y destino específico |
| GET | `/api/reports` | Consulta del listado de reportes ciudadanos registrados |
| POST | `/api/reports` | Registro de un nuevo reporte ciudadano georreferenciado |

---

## 5. Equipo de Desarrollo

Proyecto desarrollado para el Hackathon MLH OlaRuta:

- Jossie Arianna Peraza Castro
- Sara Victoria Rojas Gonzalez
- Roger de Jesus Sanchez Peñate
- Ángel Jaret Pérez Rodríguez
- Miguel Ángel Guerrero Damas

---

## 6. Información del Proyecto

- Versión: 1.0.0
- Estado: Operativo y verificado
- Repositorio oficial: https://github.com/OCOA06/MLH-OLARUTA
