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
    this.poll();
    this.timer = setInterval(() => this.poll(), this.pollInterval);
  }

  poll() {
    fetch("/api/telemetry/live")
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
