# POCKET MECHANIC — Project & Agent Handoff Document
> **Purpose**: This document provides a complete technical briefing for any teammate, collaborator, or AI assistant (Antigravity, Claude Code, Cursor, etc.) picking up the Pocket Mechanic project. It allows anyone to clone the repo and immediately continue development with zero lost context.

---

## 1. Quick Repository & Environment Setup

- **GitHub Repository**: [https://github.com/MokshhhCode/pocket-mechanic.git](https://github.com/MokshhhCode/pocket-mechanic.git)
- **Primary Tech Stack**:
  - **Backend**: Python 3.11 + Flask (modular blueprints: Auth, Dashboard, Diagnostics, Telemetry, History, Wrenchy, Motorcycle)
  - **Machine Learning**: Scikit-Learn (`RandomForest`, `DecisionTree`, `SVC`, `GradientBoosting`, `KNeighbors`, `GaussianNB`, `LogisticRegression`, `Ridge`, `PCA`, `KMeans`)
  - **Database**: Offline Local MySQL 9.5 (Database: `pocket_mechanic_db`, 28 normalized tables)
  - **Frontend**: Local vendored Bootstrap 5.3.3 + Custom CSS design system (zero CDN dependencies)
  - **Desktop Runtime**: Native macOS Cocoa WebKit wrapper (`desktop/desktop_main.py` via `pywebview` / PyObjC)

### Quick Start Commands
```bash
# 1. Clone & enter repository
git clone https://github.com/MokshhhCode/pocket-mechanic.git
cd pocket-mechanic

# 2. Virtual environment setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Verify MySQL connection & seed database (if not already seeded)
python3 database/connection.py
python3 database/seed_data.py

# 4. Run automated test suite (All 21 unit tests should pass)
python3 -m unittest discover tests

# 5. Launch the application
./run_desktop.sh    # Launches native macOS desktop application
# OR
python3 run.py      # Launches local web server on http://127.0.0.1:5001/
```

---

## 2. Core Architecture & Design Decisions

1. **Strict 100% Offline-First Execution**:
   - Zero CDN dependencies (Bootstrap, SVGs, and fonts are locally vendored).
   - Local MySQL database stores rider profiles, vehicle specs, diagnostic history, and audit logs.
   - Wrenchy AI assistant features a hybrid architecture: calls Gemini/OpenAI if API keys exist, but has a deterministic local expert rules engine fallback when offline.
2. **Authentication Gate & Dashboard Lock**:
   - `/` renders the public Welcome/Landing screen (`templates/index.html`).
   - `/auth/login` and `/auth/register` handle rider authentication.
   - The entire dashboard (`.pm-app-shell` containing sidebar, topbar, and Wrenchy widget) is strictly locked behind authentication. Unauthenticated users see only `.pm-public-shell`.
   - Logging out clears credentials, purges `remember_token`, and safely redirects to `/`.
3. **Multi-Layer Theme Persistence**:
   - Dual attributes (`data-theme` and `data-bs-theme`) on the root `<html>` element.
   - Synchronized across:
     - Client: `<head>` pre-render guard script (zero flicker) + `localStorage.getItem('pm_theme')` + 1-year cookie (`pm_theme`).
     - Server: Flask `session['THEME_MODE']` + `@app.after_request` cookie header sync + MySQL `application_settings` sync.
   - Light mode persists across page reloads, navigations, login, registration, and logout.

---

## 3. Machine Learning Architecture & Dataset

### Dataset Specifications ([data/synthetic_sensor_dataset.csv](file:///Users/mokshsuthar/Desktop/VIT/TY/Semester%201/ML%20-%20Machine%20Learning/Course%20Project/Pocket%20Mechanic%20OG/data/synthetic_sensor_dataset.csv))
- **Shape**: 6,000 samples $\times$ 18 columns
- **14 Telemetry Feature Attributes**:
  `odometer_km`, `engine_hours`, `ambient_temp`, `vehicle_speed`, `engine_rpm`, `engine_temp`, `battery_voltage`, `vibration_level`, `tyre_pressure_front`, `tyre_pressure_rear`, `brake_pad_thickness`, `oil_quality_index`, `chain_slack_mm`, `fuel_rate`
- **4 Supervised Target Attributes**:
  1. `condition_label`: Multi-class health (`Normal`, `Attention Required`, `Urgent Attention Required`)
  2. `fault_label`: Root-cause failure mode (`Nominal`, `Thermal_Overheating`, `Battery_Degraded`, `Brake_Thinning`, `Vibration_Excessive`, `Chain_Loose`)
  3. `priority_label`: Triage urgency (`Low`, `Medium`, `High`, `Critical`)
  4. `remaining_brake_life_km`: Continuous Remaining Useful Life (RUL in km)

### Machine Learning Model Zoo ([trained_models/](file:///Users/mokshsuthar/Desktop/VIT/TY/Semester%201/ML%20-%20Machine%20Learning/Course%20Project/Pocket%20Mechanic%20OG/trained_models/))
- **Primary Health Classifier**: Random Forest (100 estimators, 100.0% accuracy on test set).
- **White-Box Diagnostic Model**: Decision Tree (CART Gini index, live decision path traversal).
- **Geometric Separation**: Kernel SVM with RBF kernel ($\gamma = 1/14$).
- **Instance Learning**: K-Nearest Neighbors ($k=5$, Euclidean distance to historical bikes).
- **Ensemble Boosting**: Gradient Boosted Decision Trees (GBDT).
- **Baselines**: Gaussian Naive Bayes & Multinomial Logistic Regression.
- **RUL Regression**: Random Forest Regressor & Ridge Regression ($R^2 = 0.9982$).
- **Unsupervised Geometry**: PCA (2D latent space explaining 40% variance) & K-Means ($k=4$ operational regimes).

---

## 4. Key File Map

| Purpose | Relevant Files |
|---|---|
| **App Entry & Server** | `app.py`, `config.py`, `run.py`, `run_desktop.sh`, `desktop/desktop_main.py` |
| **Authentication & Users** | `modules/auth/routes.py`, `templates/auth/login.html`, `templates/auth/register.html` |
| **Dashboard & Garage** | `modules/dashboard/routes.py`, `templates/index.html`, `templates/dashboard/home.html`, `templates/dashboard/settings.html` |
| **Diagnostics & ML Trace** | `modules/diagnostics/routes.py`, `static/js/diagnostics.js`, `templates/diagnostics/diagnose.html`, `templates/diagnostics/report.html` |
| **ML Engine & Models** | `modules/ml_engine/training_pipeline.py`, `modules/ml_engine/inference_engine.py`, `trained_models/` |
| **Telemetry & Sensors** | `modules/sensor/manager.py`, `modules/telemetry/routes.py`, `static/js/telemetry.js` |
| **Wrenchy AI Assistant** | `modules/wrenchy/service.py`, `modules/wrenchy/routes.py`, `static/js/wrenchy.js` |
| **Database & Models** | `database/connection.py`, `database/models.py`, `database/seed_data.py`, `database/schema.sql` |
| **Academic Deliverables** | `Pocket_Mechanic_Complete_Project_Report.pdf`, `Pocket_Mechanic_Contribution_Split.pdf`, `docs/CONTRIBUTION_SPLIT.md`, `docs/ARCHITECTURE.md` |

---

## 5. Active Context & Next Roadmap Items

1. **Patent Proposal**:
   - The user requested adding a diagram to their Patent Proposal.
   - Two formal patent figures have been designed with reference numerals (100, 102, 104...):
     - **FIG. 1**: System Architecture Block Diagram (System 100)
     - **FIG. 2**: Method / Process Flowchart (Process 200)
   - These are documented in the project conversation and ready to be compiled into `docs/PATENT_PROPOSAL.md`.
2. **Viva Defense & Presentation**:
   - Full 4-person academic contribution split is documented in `docs/CONTRIBUTION_SPLIT.md`.
   - Comprehensive university project report is generated in `Pocket_Mechanic_Complete_Project_Report.pdf`.
3. **Stage 2 Hardware Integration (Future)**:
   - Interface specification ready in `docs/STAGE2_HARDWARE_INTEGRATION.md` for physical ESP32 OBD-II microcontrollers.

---

## 6. Prompt to Give to Any New AI Assistant / Teammate

Copy and paste this exact prompt when starting a new session:

```text
Hello! I am continuing work on Pocket Mechanic (an offline-first intelligent motorcycle health monitoring and predictive diagnostics desktop application for macOS). 

Please read AGENT_HANDOFF.md in the root directory to bring yourself up to speed with the repository architecture, database setup (MySQL 9.5), machine learning pipeline, and current progress. 

Once you've reviewed AGENT_HANDOFF.md, let me know you're ready and we will proceed with the next task.
```
