/**
 * POCKET MECHANIC: Global Application Controller
 * Handles Developer Toolbar controls, Theme Switcher,
 * Motorcycle Switcher & Registration Modal, and Flash Alerts.
 */

document.addEventListener("DOMContentLoaded", function () {
  initDeveloperToolbar();
  initThemeToggle();
  initMotorcycleSwitcher();
  initAddBikeModal();
});

function initDeveloperToolbar() {
  const modeSelect = document.getElementById("devDataSourceMode");
  const intensitySelect = document.getElementById("devSimulationIntensity");
  const themeToggle = document.getElementById("devThemeToggle");
  const liveMlToggle = document.getElementById("devLiveMlToggle");

  if (modeSelect) {
    modeSelect.addEventListener("change", function () {
      updateSetting("DATA_SOURCE_MODE", this.value, () => {
        location.reload();
      });
    });
  }

  if (intensitySelect) {
    intensitySelect.addEventListener("change", function () {
      updateSetting("SIMULATION_INTENSITY", this.value, () => {
        console.log("Simulation intensity updated to:", this.value);
      });
    });
  }

  if (themeToggle) {
    themeToggle.addEventListener("change", function () {
      const newTheme = this.checked ? "light" : "dark";
      if (typeof window.setPocketMechanicTheme === 'function') {
        window.setPocketMechanicTheme(newTheme);
      } else {
        document.documentElement.setAttribute("data-theme", newTheme);
        document.documentElement.setAttribute("data-bs-theme", newTheme);
        try { localStorage.setItem('pm_theme', newTheme); } catch (e) {}
        document.cookie = 'pm_theme=' + newTheme + '; path=/; max-age=31536000; SameSite=Lax';
        updateSetting("THEME_MODE", newTheme.toUpperCase());
      }
    });
  }

  if (liveMlToggle) {
    liveMlToggle.addEventListener("change", function () {
      const state = this.checked ? "ON" : "OFF";
      updateSetting("LIVE_ML_DIAGNOSTICS", state, () => {
        const livePanel = document.getElementById("liveMlPanel");
        if (livePanel) {
          livePanel.style.display = state === "ON" ? "block" : "none";
        }
      });
    });
  }
}

function updateSetting(key, value, callback) {
  fetch("/api/settings/update", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ key: key, value: value })
  })
    .then((r) => r.json())
    .then((data) => {
      if (data.success && callback) callback(data);
    })
    .catch((err) => console.error("Setting update error:", err));
}

function initThemeToggle() {
  let savedTheme = null;
  try {
    savedTheme = localStorage.getItem('pm_theme');
  } catch (e) {}
  if (!savedTheme) {
    const m = document.cookie.match(/(?:^|;\s*)pm_theme=([^;]+)/);
    if (m) savedTheme = m[1];
  }
  if (!savedTheme) {
    savedTheme = document.documentElement.getAttribute("data-theme") || "dark";
  }
  savedTheme = savedTheme.toLowerCase();
  document.documentElement.setAttribute("data-theme", savedTheme);
  document.documentElement.setAttribute("data-bs-theme", savedTheme);
  try {
    localStorage.setItem('pm_theme', savedTheme);
  } catch (e) {}
  const devToggle = document.getElementById("devThemeToggle");
  if (devToggle) devToggle.checked = (savedTheme === "light");
}

function initMotorcycleSwitcher() {
  const switchBtns = document.querySelectorAll("[data-switch-bike-id]");
  switchBtns.forEach((btn) => {
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      const bikeId = this.getAttribute("data-switch-bike-id");
      fetch(`/api/motorcycles/switch/${bikeId}`, { method: "POST" })
        .then((r) => r.json())
        .then((data) => {
          if (data.success) {
            location.reload();
          }
        });
    });
  });
}

function initAddBikeModal() {
  const modalEl = document.getElementById("addBikeModal");
  if (!modalEl) return;

  const mfgSelect = document.getElementById("newBikeMfg");
  const modelSelect = document.getElementById("newBikeModel");
  const saveBtn = document.getElementById("saveNewBikeBtn");

  // Load manufacturers when modal opens or on page load
  let manufacturersLoaded = false;
  function loadManufacturers() {
    if (manufacturersLoaded || !mfgSelect) return;
    fetch("/api/motorcycles/manufacturers")
      .then((res) => res.json())
      .then((mfgs) => {
        manufacturersLoaded = true;
        mfgSelect.innerHTML = '<option value="">Select Manufacturer...</option>';
        mfgs.forEach((m) => {
          const opt = document.createElement("option");
          opt.value = m.manufacturer_id;
          opt.textContent = `${m.name} (${m.country})`;
          mfgSelect.appendChild(opt);
        });
      })
      .catch((err) => console.error("Error loading manufacturers:", err));
  }

  modalEl.addEventListener("show.bs.modal", loadManufacturers);
  loadManufacturers();

  if (mfgSelect) {
    mfgSelect.addEventListener("change", function () {
      const mfgId = this.value;
      if (!mfgId) {
        modelSelect.innerHTML = '<option value="">Choose manufacturer first...</option>';
        modelSelect.disabled = true;
        return;
      }

      modelSelect.disabled = false;
      modelSelect.innerHTML = '<option value="">Loading models...</option>';

      fetch(`/api/motorcycles/models/${mfgId}`)
        .then((res) => res.json())
        .then((models) => {
          modelSelect.innerHTML = '<option value="">Select Motorcycle Model...</option>';
          models.forEach((mod) => {
            const opt = document.createElement("option");
            opt.value = mod.model_id;
            opt.textContent = `${mod.name} [${mod.category || "Standard"}]`;
            modelSelect.appendChild(opt);
          });
        })
        .catch((err) => {
          modelSelect.innerHTML = '<option value="">Error loading models</option>';
        });
    });
  }

  if (saveBtn) {
    saveBtn.addEventListener("click", function () {
      const modelId = modelSelect ? modelSelect.value : "";
      const year = document.getElementById("newBikeYear") ? document.getElementById("newBikeYear").value : 2023;
      const colour = document.getElementById("newBikeColour") ? document.getElementById("newBikeColour").value.trim() : "Black";
      const reg = document.getElementById("newBikeReg") ? document.getElementById("newBikeReg").value.trim().toUpperCase() : "";

      if (!modelId) {
        alert("Please select a motorcycle model.");
        return;
      }
      if (!reg) {
        alert("Please enter a valid registration number.");
        return;
      }

      saveBtn.disabled = true;
      saveBtn.textContent = "Saving...";

      fetch("/api/motorcycles/register-another", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model_id: parseInt(modelId, 10),
          year: parseInt(year, 10),
          colour: colour || "Black",
          registration_number: reg
        })
      })
        .then((r) => r.json())
        .then((data) => {
          if (data.success) {
            location.reload();
          } else {
            alert(data.error || "Failed to save motorcycle.");
            saveBtn.disabled = false;
            saveBtn.textContent = "Save Motorcycle";
          }
        })
        .catch((err) => {
          alert("Communication error saving motorcycle.");
          saveBtn.disabled = false;
          saveBtn.textContent = "Save Motorcycle";
        });
    });
  }
}
