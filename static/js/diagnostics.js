/**
 * POCKET MECHANIC: Diagnostics & Live ML Execution Controller
 */

class DiagnosticsManager {
  constructor() {
    this.form = document.getElementById("diagForm");
    this.startBtn = document.getElementById("startDiagBtn");
    this.loaderCard = document.getElementById("diagLoaderCard");
    this.resultsCard = document.getElementById("diagResultsCard");
    this.statusText = document.getElementById("diagStatusText");
    this.progressBar = document.getElementById("diagProgressBar");
    this.flowBoxes = document.querySelectorAll(".pipeline-step-box");

    if (this.startBtn) {
      this.initEvents();
    }
  }

  initEvents() {
    this.startBtn.addEventListener("click", () => this.runDiagnosis());
  }

  async runDiagnosis() {
    const compSelect = document.getElementById("diagComponent");
    const catSelect = document.getElementById("diagCategory");
    const descInput = document.getElementById("diagDescription");
    const modelSelect = document.getElementById("diagModelSelect");

    const compCode = compSelect ? compSelect.value : "";
    const category = catSelect ? catSelect.value : "General Performance";
    const description = descInput ? descInput.value.trim() : "Routine scan";
    const modelName = modelSelect ? modelSelect.value : "Random_Forest";

    // Show loading state
    this.form.style.display = "none";
    if (this.resultsCard) this.resultsCard.style.display = "none";
    this.loaderCard.style.display = "block";

    const steps = [
      "Initializing diagnostic session...",
      "Loading motorcycle technical specifications...",
      "Checking component applicability...",
      "Activating simulated sensor source...",
      "Receiving sensor readings...",
      "Validating sensor data...",
      "Processing maintenance history...",
      "Extracting relevant features...",
      "Executing selected ML model...",
      "Evaluating component condition...",
      "Generating maintenance recommendations...",
      "Saving diagnostic report..."
    ];

    // Trigger backend execution
    const fetchPromise = fetch("/api/diagnostics/execute", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        component_code: compCode,
        problem_category: category,
        problem_description: description,
        model_name: modelName
      })
    }).then((r) => r.json());

    // Step-by-step synchronized loader transition
    for (let i = 0; i < steps.length; i++) {
      this.statusText.innerText = steps[i];
      const pct = Math.round(((i + 1) / steps.length) * 100);
      if (this.progressBar) this.progressBar.style.width = `${pct}%`;

      // Update connected pipeline flow boxes
      if (this.flowBoxes && this.flowBoxes[i]) {
        this.flowBoxes[i].classList.add("active");
        if (i > 0 && this.flowBoxes[i - 1]) {
          this.flowBoxes[i - 1].classList.remove("active");
          this.flowBoxes[i - 1].classList.add("completed");
        }
      }
      await new Promise((resolve) => setTimeout(resolve, 180));
    }

    try {
      const data = await fetchPromise;
      if (data.success) {
        this.renderResults(data);
      } else {
        alert("Diagnostic execution error: " + (data.error || "Unknown error"));
        this.resetForm();
      }
    } catch (err) {
      console.error("Diagnosis error:", err);
      alert("Communication error during diagnosis.");
      this.resetForm();
    }
  }

  renderResults(data) {
    this.loaderCard.style.display = "none";
    this.resultsCard.style.display = "block";

    // Ticket info
    document.getElementById("resTicketId").innerText = `#TICK-${data.ticket_id}`;
    document.getElementById("resTimestamp").innerText = data.timestamp;
    document.getElementById("resComponent").innerText = data.component_diagnosed;
    document.getElementById("resSymptoms").innerText = data.user_symptoms;

    // Condition badge
    const badge = document.getElementById("resConditionBadge");
    badge.innerText = data.predicted_condition;
    badge.className = `badge ${
      data.status_color === "red"
        ? "badge-red"
        : data.status_color === "yellow"
        ? "badge-yellow"
        : "badge-green"
    } px-3 py-2 fs-6`;

    // Severity & action
    document.getElementById("resSeverity").innerText = data.severity;
    document.getElementById("resAction").innerText = data.recommended_action;
    document.getElementById("resReason").innerText = data.supporting_reason;
    document.getElementById("resUrgentSummary").innerText = data.urgent_summary;

    // ML Engine Details
    const ml = data.ml_engine;
    document.getElementById("resMlModel").innerText = ml.model_selected;
    document.getElementById("resMlConfidence").innerText = `${ml.confidence_pct}%`;
    document.getElementById("resFaultLabel").innerText = ml.fault_label.replace("_", " ");
    document.getElementById("resPadRul").innerText = `${ml.remaining_pad_life_km} km`;

    // Report Link
    const reportLink = document.getElementById("resReportLink");
    if (reportLink) {
      reportLink.href = `/diagnostics/report/${data.ticket_id}`;
    }

    // Discuss with Wrenchy button
    const wrenchyBtn = document.getElementById("resDiscussWrenchyBtn");
    if (wrenchyBtn) {
      wrenchyBtn.onclick = () => {
        if (window.wrenchy) {
          window.wrenchy.toggleModal(true);
          window.wrenchy.input.value = `Can you explain diagnostic ticket #TICK-${data.ticket_id} regarding my ${data.component_diagnosed}?`;
          window.wrenchy.sendMessage();
        }
      };
    }

    // Populate live trace box if present
    const traceBox = document.getElementById("resTraceBox");
    if (traceBox && ml.live_trace) {
      traceBox.innerHTML = ml.live_trace
        .map(
          (t) =>
            `<div class="mb-1"><span class="text-cyan fw-bold">${t.stage}:</span> <span class="text-secondary">${t.detail}</span></div>`
        )
        .join("");
    }

    // Populate feature importances if present
    const fiBox = document.getElementById("resFeatureImportanceBox");
    if (fiBox && ml.feature_importance) {
      fiBox.innerHTML = Object.entries(ml.feature_importance)
        .map(
          ([k, v]) =>
            `<div class="d-flex justify-content-between py-1 border-bottom border-secondary text-secondary small">
              <span>${k.replace(/_/g, " ")}</span>
              <span class="text-primary font-monospace">${(v * 100).toFixed(1)}%</span>
            </div>`
        )
        .join("");
    }
  }

  resetForm() {
    this.loaderCard.style.display = "none";
    this.form.style.display = "block";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  window.diagManager = new DiagnosticsManager();
});
