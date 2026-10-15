# 🌊 ALERTA CARMEN — Sistema de Alerta Temprana de Inundaciones
### Proyecto para Hackathon MLH OLARUTA · Ciudad del Carmen, Campeche

> *"Nuestra arquitectura es simple: un frontend ligero con Leaflet, un backend mínimo que consume datos abiertos de Open-Meteo y NASA POWER, y una capa de IA que cruza el pronóstico con el historial de inundaciones de Carmen para generar alertas tempranas. Todo corre en el navegador, sin bases de datos pesadas, y se puede desplegar en cualquier servidor."*

---

## 📌 1. El Problema en Ciudad del Carmen
Ciudad del Carmen es una isla de barrera entre el Golfo de México y la Laguna de Términos, con una altitud promedio de solo **0.5 a 2.0 metros sobre el nivel medio del mar**. 

Históricamente, eventos de lluvia de más de **35-40 mm** combinados con marea alta (pleamar) o vientos del "Norte" saturan por completo los drenes naturales, incomunicando colonias como **La Manigua, El Caracol, Caleta, Arroyo de los Franceses y Tierra y Libertad**.

---

## 🏛️ 2. Arquitectura del Proyecto

```
┌──────────────────────────────────────────────────────────┐
│                 CAPA DE PRESENTACIÓN                     │
│  HTML5 + CSS3 + Vanilla JS + Leaflet.js (OpenStreetMap)  │
│  • Mapa interactivo con zonas de riesgo coloreadas       │
│  • Semáforo de riesgo por colonia (Verde/Amarillo/Rojo)  │
│  • Formulario de reporte ciudadano georreferenciado      │
│  • Modo Simulador para evaluación del jurado             │
└────────────────────────────┬─────────────────────────────┘
                             │ REST JSON
┌────────────────────────────▼─────────────────────────────┐
│                 CAPA DE LÓGICA (BACKEND)                 │
│                 Python 3 + Flask (app.py)                │
│  • Consumo y caché de Open-Meteo y NASA POWER            │
│  • Cruce hidrológico: Precipitación x Factor de Riesgo   │
│  • Persistencia ligera en archivos JSON locales          │
│  • Generador de boletines de Protección Civil            │
└────────────────────────────┬─────────────────────────────┘
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
┌───────────────────────────┐   ┌──────────────────────────┐
│    FUENTES DE DATOS       │   │      CAPA DE IA          │
│  • Open-Meteo (24h en vivo)│  │  • Gemma / Gemini API    │
│  • NASA POWER (Histórico) │   │  • Síntesis de alerta    │
│  • OpenStreetMap (Tiles)  │   │  • Recomendaciones civil │
└───────────────────────────┘   └──────────────────────────┘
```

---

## 🚀 3. Instrucciones de Ejecución

### Prerrequisitos
- Python 3.10 o superior (Flask y Requests)

### Instalación y arranque
```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Iniciar el servidor
python app.py
```

Abre tu navegador en:  
👉 **`http://localhost:5000`** o **`http://127.0.0.1:5000`**

### Variables de Entorno Opcionales
- `GEMINI_API_KEY`: Si deseas que la generación de boletines se realice vía Gemini 1.5/2.0 Flash o Gemma en vivo con tu API Key. *(Si no se proporciona, el sistema cuenta con un motor algorítmico local de Protección Civil que funciona al 100% sin conexión ni API keys).*

---

## 🔌 4. Endpoints de la API

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/` | Carga la interfaz interactiva |
| `GET` | `/api/weather` | Pronóstico de precipitación y clima en vivo de Ciudad del Carmen vía Open-Meteo |
| `GET` | `/api/historical` | Historial satelital de lluvias de la NASA POWER y umbrales de anegación |
| `GET` | `/api/zones` | Lista de colonias con semáforo calculado en tiempo real (admite `?simulate_rain=35`) |
| `GET` | `/api/reports` | Consulta de reportes ciudadanos registrados |
| `POST`| `/api/reports` | Envío de reporte de inundación comunitaria |
| `GET` | `/api/ai-bulletin` | Emisión de boletín preventivo con IA / Gemma |

---

## 💡 5. Modo Pitch para el Jurado del Hackathon
1. **Abrir la aplicación**: Mostrar el mapa de Ciudad del Carmen con las colonias en tiempo real.
2. **Explicar la arquitectura**: Clic en el botón **🎯 Pitch** en la esquina superior derecha para proyectar la frase y estructura.
3. **Demostración en vivo del simulador**: Mover el deslizador superior a **65 mm (Tormenta Tropical)**:
   - Ver cómo las colonias de **La Manigua, El Caracol y Playón** se tornan rojas en el mapa y la lista.
   - Ir a la pestaña **🤖 Boletín IA (Gemma)** y pulsar *Generar Boletín*: La IA redacta el comunicado oficial con albergues habilitados y números de emergencia (911 y Protección Civil Carmen).
4. **Reporte ciudadano**: Hacer clic sobre una calle del mapa para abrir el reporte rápido y enviarlo.
