/**
 * POCKET MECHANIC: Live Telemetry & Gauge Controller
 */

class TelemetryMonitor {
  constructor() {
    this.pollInterval = 3000;
    this.timer = null;
    this.historyBuffer = {};
    this.init();
  }

  init() {
    this.initIntensityControl();
    this.poll();
    this.timer = setInterval(() => this.poll(), this.pollInterval);
  }

  initIntensityControl() {
    const sel = document.getElementById("telemetryIntensitySelect");
    if (sel) {
      sel.addEventListener("change", (e) => {
        const newInt = e.target.value;
        const disp = document.getElementById("telemetryIntensityDisplay");
        if (disp) {
          disp.innerText = newInt.charAt(0).toUpperCase() + newInt.slice(1).toLowerCase();
        }

        // Persist to user settings via API
        fetch("/api/settings/update", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ key: "SIMULATION_INTENSITY", value: newInt })
        })
          .then((r) => r.json())
          .then(() => {
            // Immediately re-poll to update gauges without waiting for next timer interval
            this.poll();
          })
          .catch((err) => console.error("Failed to update simulation intensity:", err));
      });
    }
  }

  poll() {
    const sel = document.getElementById("telemetryIntensitySelect");
    const intensityQuery = sel ? `?intensity=${sel.value}` : "";
    fetch(`/api/telemetry/live${intensityQuery}`)
      .then((r) => r.json())
      .then((packet) => {
        if (packet.readings) {
          this.updateDisplay(packet);
        } else if (packet.status === "DISCONNECTED") {
          this.showHardwareOffline(packet.error);
        }
      })
      .catch((err) => console.error("Telemetry poll error:", err));
  }

  updateDisplay(packet) {
    const readings = packet.readings;
    const anomalies = new Set(packet.anomalies || []);

    document.querySelectorAll("[data-sensor-code]").forEach((card) => {
      const code = card.getAttribute("data-sensor-code");
      const val = readings[code];
      if (val !== undefined) {
        const valElem = card.querySelector(".sensor-value");
        if (valElem) valElem.innerText = val;

        const dot = card.querySelector(".indicator-dot");
        const statusBadge = card.querySelector(".sensor-health-badge");
        const isAnom = anomalies.has(code);

        if (dot) {
          dot.className = `indicator-dot ${isAnom ? "indicator-red" : "indicator-green"}`;
        }
        if (statusBadge) {
          statusBadge.innerText = isAnom ? "Warning" : "Nominal";
          statusBadge.className = `badge ${isAnom ? "badge-red" : "badge-green"}`;
        }
      }
    });

    const statusBadge = document.getElementById("telemetryOverallStatus");
    if (statusBadge) {
      statusBadge.innerText = packet.status;
      statusBadge.className = `badge ${
        packet.status === "ONLINE" ? "badge-green" : packet.status === "ATTENTION_REQUIRED" ? "badge-yellow" : "badge-red"
      }`;
    }
  }

  showHardwareOffline(msg) {
    const banner = document.getElementById("telemetryOfflineBanner");
    if (banner) {
      banner.style.display = "block";
      banner.innerText = msg || "Hardware Sensor Unit Not Detected.";
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("telemetryGrid")) {
    window.telemetryMonitor = new TelemetryMonitor();
  }
});
