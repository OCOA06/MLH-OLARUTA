/**
 * SISTEMA DE ALERTA DE INUNDACIONES CARMEN (SALIC)
 * Controlador Frontend con Leaflet.js y APIs abiertas
 */

// Estado global de la aplicación
const state = {
  map: null,
  zonesLayer: null,
  reportsLayer: null,
  tempClickMarker: null,
  simulatedRain: null, // null = tiempo real
  selectedCoords: null,
  weather: null,
  zones: [],
  reports: [],
  historical: null
};

// Coordenadas centrales de Ciudad del Carmen, Campeche
const CARMEN_CENTER = [18.6496, -91.8239];

document.addEventListener("DOMContentLoaded", () => {
  initMap();
  initTabs();
  initSlider();
  initCitizenForm();
  initAiBulletin();
  initPitchModal();

  // Carga inicial de datos
  loadWeather();
  loadHistorical();
  loadZones();
  loadReports();
});

/* =========================================================
   INICIALIZACIÓN DEL MAPA LEAFLET
   ========================================================= */
function initMap() {
  state.map = L.map("map", {
    center: CARMEN_CENTER,
    zoom: 13,
    zoomControl: true
  });

  // Capa base: OpenStreetMap estándar
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(state.map);

  state.zonesLayer = L.layerGroup().addTo(state.map);
  state.reportsLayer = L.layerGroup().addTo(state.map);

  // Escuchar clics en el mapa para geo-reportar
  state.map.on("click", (e) => {
    const { lat, lng } = e.latlng;
    state.selectedCoords = [parseFloat(lat.toFixed(5)), parseFloat(lng.toFixed(5))];

    if (state.tempClickMarker) {
      state.map.removeLayer(state.tempClickMarker);
    }

    state.tempClickMarker = L.circleMarker([lat, lng], {
      radius: 9,
      fillColor: "#06b6d4",
      color: "#ffffff",
      weight: 2,
      fillOpacity: 0.9
    }).addTo(state.map);

    state.tempClickMarker.bindPopup(`<b>Punto seleccionado para reporte</b><br>Lat: ${state.selectedCoords[0]}<br>Lon: ${state.selectedCoords[1]}`).openPopup();

    // Actualizar texto en formulario
    const coordsText = document.getElementById("coordsText");
    if (coordsText) {
      coordsText.textContent = `${state.selectedCoords[0]}, ${state.selectedCoords[1]}`;
    }

    // Cambiar a la pestaña de reportes automáticamente si está en otra
    switchTab("tab-reports");
  });
}

/* =========================================================
   GESTIÓN DE PESTAÑAS
   ========================================================= */
function initTabs() {
  const tabButtons = document.querySelectorAll(".tab-btn");
  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetTab = btn.getAttribute("data-tab");
      switchTab(targetTab);
    });
  });
}

function switchTab(tabId) {
  document.querySelectorAll(".tab-btn").forEach(b => {
    b.classList.toggle("active", b.getAttribute("data-tab") === tabId);
  });
  document.querySelectorAll(".tab-pane").forEach(p => {
    p.classList.toggle("active", p.id === tabId);
  });
}

/* =========================================================
   CONSUMO DE APIS
   ========================================================= */

// 1. Clima en tiempo real (Open-Meteo)
async function loadWeather() {
  try {
    const res = await fetch("/api/weather");
    const data = await res.json();
    state.weather = data;

    // Actualizar cabecera
    const tempText = `${data.current_temperature}°C | ${data.expected_rain_24h_mm} mm 24h`;
    document.getElementById("currentWeatherText").textContent = tempText;
    document.getElementById("rainProbText").textContent = `${data.rain_probability_pct}%`;
  } catch (err) {
    console.error("Error al cargar clima:", err);
  }
}

// 2. Historial satelital (NASA POWER)
async function loadHistorical() {
  try {
    const res = await fetch("/api/historical");
    const data = await res.json();
    state.historical = data;

    if (data.stats) {
      document.getElementById("nasaAvg").textContent = `${data.stats.average_daily_mm} mm`;
      document.getElementById("nasaPeak").textContent = `${data.stats.historical_peak_day_mm} mm`;
    }

    renderNasaChart(data.data_points || []);
  } catch (err) {
    console.error("Error al cargar histórico NASA:", err);
  }
}

function renderNasaChart(points) {
  const container = document.getElementById("nasaChartPreview");
  if (!container || !points.length) return;

  container.innerHTML = "";
  const maxVal = Math.max(...points.map(p => p.precip_mm), 60);

  // Mostrar últimos 7 registros
  const slice = points.slice(-7);
  slice.forEach(p => {
    const heightPct = Math.max(6, Math.min(100, (p.precip_mm / maxVal) * 100));
    const col = document.createElement("div");
    col.className = "nasa-bar-col";
    col.title = `Fecha: ${p.date} - Lluvia: ${p.precip_mm} mm`;
    col.innerHTML = `
      <div class="nasa-bar" style="height: ${heightPct}%;"></div>
      <div class="nasa-bar-label">${p.date.slice(-4)}</div>
    `;
    container.appendChild(col);
  });
}

// 3. Zonas de riesgo y evaluación
async function loadZones() {
  try {
    let url = "/api/zones";
    if (state.simulatedRain !== null) {
      url += `?simulate_rain=${state.simulatedRain}`;
    }

    const res = await fetch(url);
    const data = await res.json();
    state.zones = data.zones || [];

    updateOverallRisk(data.summary);
    renderZonesList(state.zones);
    renderZonesOnMap(state.zones);
  } catch (err) {
    console.error("Error al cargar zonas:", err);
  }
}

function updateOverallRisk(summary) {
  if (!summary) return;

  const dot = document.getElementById("overallRiskDot");
  const text = document.getElementById("overallRiskText");
  const greenCount = document.getElementById("greenCount");
  const yellowCount = document.getElementById("yellowCount");
  const redCount = document.getElementById("redCount");
  const zonesCount = document.getElementById("zonesCount");

  dot.style.backgroundColor = summary.overall_color;
  dot.style.boxShadow = `0 0 10px ${summary.overall_color}`;
  text.textContent = summary.overall_level.toUpperCase();
  text.style.color = summary.overall_color;

  if (greenCount) greenCount.textContent = `${summary.green_count} Verdes`;
  if (yellowCount) yellowCount.textContent = `${summary.yellow_count} Amarillos`;
  if (redCount) redCount.textContent = `${summary.red_count} Rojos`;
  if (zonesCount) zonesCount.textContent = summary.total_zones;
}

function renderZonesList(zones) {
  const container = document.getElementById("zonesList");
  if (!container) return;

  container.innerHTML = "";
  zones.forEach(zone => {
    const card = document.createElement("div");
    card.className = `zone-card border-${zone.risk_level}`;
    card.innerHTML = `
      <div class="zone-header-row">
        <span class="zone-name">${zone.name}</span>
        <span class="zone-pill ${zone.risk_level}">${zone.risk_label}</span>
      </div>
      <div class="zone-meta">
        <span>📍 Elevación: <strong>${zone.elevation_masl}m</strong></span>
        <span>⚡ Vulnerabilidad: <strong>x${zone.vulnerability_factor}</strong></span>
        <span>💧 Índice: <strong>${zone.effective_rain_index}</strong></span>
      </div>
      <p class="zone-desc">${zone.description}</p>
      <div class="zone-action-box">
        <strong>Acción:</strong> ${zone.recommended_action}
      </div>
    `;

    card.addEventListener("click", () => {
      state.map.setView(zone.coords, 15);
      // Abrir popup de este marcador
      if (zone._marker) {
        zone._marker.openPopup();
      }
    });

    container.appendChild(card);
  });
}

function renderZonesOnMap(zones) {
  state.zonesLayer.clearLayers();

  zones.forEach(zone => {
    // 1. Círculo de área de influencia
    const circle = L.circle(zone.coords, {
      radius: zone.radius_meters,
      color: zone.risk_color,
      fillColor: zone.risk_color,
      fillOpacity: zone.risk_level === "rojo" ? 0.35 : (zone.risk_level === "amarillo" ? 0.25 : 0.15),
      weight: zone.risk_level === "rojo" ? 2.5 : 1.5
    });

    // 2. Marcador central con pin
    const centerMarker = L.circleMarker(zone.coords, {
      radius: zone.risk_level === "rojo" ? 10 : 7,
      fillColor: zone.risk_color,
      color: "#ffffff",
      weight: 2,
      fillOpacity: 1
    });

    const popupHtml = `
      <div class="popup-zone-title">${zone.name}</div>
      <div class="popup-zone-badge" style="background:${zone.risk_color}; color:#fff;">${zone.risk_label}</div>
      <div class="popup-detail"><strong>Cota:</strong> ${zone.elevation_masl} msnm | <strong>Vulnerabilidad:</strong> x${zone.vulnerability_factor}</div>
      <div class="popup-detail"><strong>Drenaje:</strong> ${zone.drainage_quality}</div>
      <div class="popup-action"><strong>Recomendación:</strong> ${zone.recommended_action}</div>
      <div class="popup-action" style="color:#a7f3d0; margin-top:4px;"><strong>Albergue asignado:</strong> ${zone.evacuation_center}</div>
    `;

    centerMarker.bindPopup(popupHtml);
    circle.bindPopup(popupHtml);

    // Guardar referencia en el objeto de zona para clics desde la lista
    zone._marker = centerMarker;

    state.zonesLayer.addLayer(circle);
    state.zonesLayer.addLayer(centerMarker);
  });
}

// 4. Reportes ciudadanos
async function loadReports() {
  try {
    const res = await fetch("/api/reports");
    const data = await res.json();
    state.reports = data.reports || [];

    const countElem = document.getElementById("reportsCount");
    if (countElem) countElem.textContent = state.reports.length;

    renderReportsList(state.reports);
    renderReportsOnMap(state.reports);
  } catch (err) {
    console.error("Error al cargar reportes:", err);
  }
}

function renderReportsList(reports) {
  const container = document.getElementById("reportsList");
  if (!container) return;

  container.innerHTML = "";
  if (!reports.length) {
    container.innerHTML = "<div class='loading-state'>No hay reportes recientes.</div>";
    return;
  }

  reports.forEach(rep => {
    const card = document.createElement("div");
    card.className = "report-card";
    const dateFormatted = new Date(rep.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    card.innerHTML = `
      <div class="report-header">
        <span class="report-loc">📍 ${rep.colonia}</span>
        <span class="report-badge ${rep.level_code}">${rep.water_level.split(" ")[0]}</span>
      </div>
      <div style="font-size:11px; color:#9ca3af; margin-bottom:4px;">${rep.street}</div>
      <p class="report-desc">"${rep.description}"</p>
      <div class="report-time">Por ${rep.author} · ${dateFormatted}</div>
    `;

    card.addEventListener("click", () => {
      if (rep.coords && rep.coords.length === 2) {
        state.map.setView(rep.coords, 16);
      }
    });

    container.appendChild(card);
  });
}

function renderReportsOnMap(reports) {
  state.reportsLayer.clearLayers();

  reports.forEach(rep => {
    if (!rep.coords || rep.coords.length !== 2) return;

    const colors = {
      bajo: "#10b981",
      medio: "#f59e0b",
      critico: "#ef4444"
    };
    const color = colors[rep.level_code] || "#06b6d4";

    const reportPin = L.circleMarker(rep.coords, {
      radius: 8,
      fillColor: color,
      color: "#ffffff",
      weight: 2,
      fillOpacity: 0.95
    });

    const popupHtml = `
      <div style="font-weight:700; color:#fff; font-size:13px;">📢 Reporte Comunitario</div>
      <div style="font-size:11px; color:#cbd5e1; margin-top:2px;"><strong>${rep.colonia}</strong> — ${rep.street}</div>
      <div style="font-size:11px; color:${color}; font-weight:700; margin:4px 0;">${rep.water_level}</div>
      <div style="font-size:11px; color:#e2e8f0; font-style:italic;">"${rep.description}"</div>
      <div style="font-size:10px; color:#94a3b8; margin-top:4px;">Reportado por ${rep.author}</div>
    `;

    reportPin.bindPopup(popupHtml);
    state.reportsLayer.addLayer(reportPin);
  });
}

/* =========================================================
   FORMULARIO DE REPORTE CIUDADANO
   ========================================================= */
function initCitizenForm() {
  const form = document.getElementById("citizenReportForm");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const colonia = document.getElementById("repColonia").value;
    const street = document.getElementById("repStreet").value;
    const water_level = document.getElementById("repWaterLevel").value;
    const author = document.getElementById("repAuthor").value || "Ciudadano Anónimo";
    const description = document.getElementById("repDescription").value;

    const payload = {
      colonia,
      street,
      water_level,
      author,
      description,
      coords: state.selectedCoords
    };

    const submitBtn = document.getElementById("btnSubmitReport");
    submitBtn.disabled = true;
    submitBtn.textContent = "Enviando reporte...";

    try {
      const res = await fetch("/api/reports", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (data.success) {
        alert("¡Reporte recibido con éxito! Ha sido agregado al mapa.");
        form.reset();
        state.selectedCoords = null;
        document.getElementById("coordsText").textContent = "Haz clic en el mapa o se usará el centro de la colonia";
        if (state.tempClickMarker) {
          state.map.removeLayer(state.tempClickMarker);
          state.tempClickMarker = null;
        }
        loadReports();
      } else {
        alert("Error: " + (data.error || "No se pudo registrar el reporte"));
      }
    } catch (err) {
      alert("Error de conexión al enviar reporte");
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Enviar Reporte Comunitario";
    }
  });
}

/* =========================================================
   SIMULADOR INTERACTIVO DE LLUVIA (PARA JURADOS)
   ========================================================= */
function initSlider() {
  const slider = document.getElementById("rainSlider");
  const valueDisplay = document.getElementById("simRainValue");
  const presetButtons = document.querySelectorAll(".btn-preset");

  if (!slider) return;

  slider.addEventListener("input", (e) => {
    const val = parseFloat(e.target.value);
    presetButtons.forEach(b => b.classList.remove("active"));
    
    if (val === 0) {
      state.simulatedRain = null;
      valueDisplay.textContent = "Tiempo Real (API)";
    } else {
      state.simulatedRain = val;
      valueDisplay.textContent = `${val} mm`;
    }
    loadZones();
  });

  presetButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      presetButtons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");

      const preset = btn.getAttribute("data-rain");
      if (preset === "real") {
        slider.value = 0;
        state.simulatedRain = null;
        valueDisplay.textContent = "Tiempo Real (API)";
      } else {
        const num = parseFloat(preset);
        slider.value = num;
        state.simulatedRain = num;
        valueDisplay.textContent = `${num} mm`;
      }
      loadZones();
    });
  });
}

/* =========================================================
   CAPA DE IA: BOLETÍN GEMMA / PROTECCIÓN CIVIL
   ========================================================= */
function initAiBulletin() {
  const btn = document.getElementById("btnGenerateAi");
  const textElem = document.getElementById("aiBulletinText");
  const tagElem = document.getElementById("aiRiskTag");

  if (!btn) return;

  btn.addEventListener("click", async () => {
    btn.disabled = true;
    btn.innerHTML = "<span>⏳</span> Sintetizando con IA...";
    textElem.textContent = "Analizando precipitaciones, topografía insular y estado de pleamar en Ciudad del Carmen...";

    try {
      let url = "/api/ai-bulletin";
      if (state.simulatedRain !== null) {
        url += `?rain_mm=${state.simulatedRain}`;
      }

      const res = await fetch(url);
      const data = await res.json();

      if (data.success) {
        textElem.textContent = data.bulletin;
        tagElem.textContent = `Nivel: ${data.risk_level.toUpperCase()} (${data.forecast_mm} mm)`;
        tagElem.style.color = data.risk_level === "rojo" ? "#ef4444" : (data.risk_level === "amarillo" ? "#f59e0b" : "#10b981");
      } else {
        textElem.textContent = "No se pudo generar el boletín. Inténtalo nuevamente.";
      }
    } catch (err) {
      textElem.textContent = "Error al conectar con el servicio de IA.";
    } finally {
      btn.disabled = false;
      btn.innerHTML = "<span>✨</span> Actualizar Boletín Oficial de Protección Civil";
    }
  });
}

/* =========================================================
   MODAL DE PITCH Y ARQUITECTURA
   ========================================================= */
function initPitchModal() {
  const openBtn = document.getElementById("openPitchBtn");
  const closeBtn = document.getElementById("closePitchBtn");
  const modal = document.getElementById("pitchModal");

  if (!openBtn || !modal) return;

  openBtn.addEventListener("click", () => modal.classList.add("open"));
  if (closeBtn) closeBtn.addEventListener("click", () => modal.classList.remove("open"));

  modal.addEventListener("click", (e) => {
    if (e.target === modal) modal.classList.remove("open");
  });
}
