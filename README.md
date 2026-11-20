# POCKET MECHANIC (macOS Desktop Edition)
### Intelligent Motorcycle Health Monitoring and Predictive Maintenance System
> **Tagline:** *Your Motorcycle's Personal Mechanic*  
> **AI Assistant:** *Wrenchy AI*  
> **Course:** VIT TY Machine Learning Course Project

---

## 1. System Overview

**Pocket Mechanic** is an automotive-grade desktop application for motorcycle owners and certified technicians. It operates locally on macOS as a standalone native desktop software application, backed by an offline local **MySQL 9.5 Community Server** database and a **classical Machine Learning engine** (Scikit-Learn, Pandas, NumPy, SciPy).

The platform eliminates the need for a web browser or remote cloud hosting, providing:
- **Native macOS Desktop Window**: Launched via `Pocket Mechanic.app` or `./run_desktop.sh`, featuring a native Cocoa WebKit runtime (`pyobjc-framework-WebKit`), custom app icon (`PocketMechanic.icns`), traffic-light window controls, zoom, and resize behavior.
- **Notion-Inspired Design System**: Calm, restrained aesthetic built on an Obsidian neutral base (`#191919`), persistent left sidebar (`#202020`), crisp cards (`#252525`), and intentional condition highlights (Emerald, Amber, Crimson). Zero neon glows or distracting gimmicks.
- **Persistent Left-Hand Sidebar**:
  1. **Workspace**: Overview Dashboard & Garage / Fleet Management.
  2. **Monitoring & Diagnostics**: Classical ML Diagnostics Suite & Live Telemetry Monitor.
  3. **Maintenance & Logs**: Service History Logbook & Maintenance Schedule / Inspection Checklists.
  4. **Intelligence**: Wrenchy AI Assistant.
  5. **System & Profile**: Local MySQL Status & Data Management (`/settings`).
- **Local-First & Zero Forced Login**: Automatically loads your local rider profile and active motorcycle upon launch. No forced sign-in or cloud accounts required.
- **100% Offline & Self-Contained**: Bootstrap 5.3.3 vendored locally (`static/vendor/`), local SVG icons, and authentic Wrenchy 3D character artwork. Zero remote CDN or internet dependencies.
- **Offline MySQL Database**: 28 normalized relational entities with user isolation and AES-256 Fernet encryption at rest for sensitive data.
- **28 Verified OEMs**: Complete master specifications database of major Indian and international motorcycle manufacturers (KTM, Royal Enfield, Yamaha, Honda, Kawasaki, Ducati, BMW Motorrad, etc.).
- **Classical ML Engine**: Supervised multi-class ensemble (Random Forest, Decision Tree, GBDT, SVM, KNN, Naive Bayes), remaining useful life (RUL) regression, and PCA failure clustering.
- **Wrenchy AI**: Context-aware assistant knowing your active motorcycle's exact OEM specifications and telemetry readings, with an offline deterministic diagnostic expert fallback.

---

## 2. Desktop Architecture & Native Wrapper Choice

```
+-------------------------------------------------------------+
|                Pocket Mechanic macOS Desktop                |
|  (Native Cocoa WKWebView / PyObjC Window, PocketMechanic.icns) |
+-------------------------------------------------------------+
                               |
                Local Loopback IPC (127.0.0.1)
                               v
+-------------------------------------------------------------+
|             Embedded Flask Application Server               |
|      (Modular Blueprints, Flask-Login, Context Engine)      |
+-------------------------------------------------------------+
          |                                       |
          v                                       v
+-----------------------+              +----------------------+
|   Classical ML Engine |              | Local MySQL Database |
| (Scikit-Learn, Joblib)|              | (28 Normalized Tables|
| Ensembles & Regressors|              | 100% Offline Storage)|
+-----------------------+              +----------------------+
```

### Why PyObjC Native WebKit over Electron?
1. **Lightweight & Instant Startup**: Uses macOS's native `WKWebView` via `pyobjc-framework-WebKit`. Zero Chromium bloat, saving over 150MB of memory and launching instantly.
2. **Native macOS Integration**: Native Cocoa window controls, native traffic-light buttons, macOS menu bar, and proper dock icon handling.
3. **Unified Python Runtime**: Both the desktop window lifecycle and the classical machine learning backend run under the same Python 3.11 environment.

---

## 3. Quick Start & Launching the Desktop Application

### Option A: Double-Click the macOS App Bundle
Open `Pocket Mechanic.app` located in the project directory:
```bash
open "Pocket Mechanic.app"
```

### Option B: Terminal Desktop Launcher
Run the shell launcher:
```bash
./run_desktop.sh
```
Or directly with Python:
```bash
python3 desktop/desktop_main.py
```

### Option C: Browser Fallback (CLI Mode)
If you prefer running a local server for browser testing:
```bash
python3 run.py
# Open http://127.0.0.1:5001/dashboard
```

---

## 4. Key Functional Areas

| Screen / Area | Endpoint | Purpose |
| :--- | :--- | :--- |
| **Overview** | `/dashboard` | System health summary, active urgent work panel, condition breakdown, and quick action bar. |
| **Garage & Fleet** | `/garage` | Full fleet switcher, 50+ OEM specifications (bore, stroke, power, torque, oil, tyres), and component applicability rules. |
| **Diagnostics Suite** | `/diagnostics` | Classical ML multi-class classification, symptom input, live tolerance checks, and generated diagnostic reports. |
| **Live Telemetry** | `/telemetry` | Real-time sensor stream with tolerance thresholds, simulator intensity controls (Regular/Medium/Intense), and hardware mode. |
| **Service History** | `/history` | Chronological digital logbook, diagnostic ticket resolution lifecycle, parts replaced, and costs. |
| **Maintenance Schedule** | `/schedule` | Inspection checklists (Pre-ride, Weekly, Periodic) with instant one-click logging to MySQL service records. |
| **Wrenchy AI Assistant** | `/wrenchy` | Contextual motorcycle assistant with chat history, OEM spec handoff, and deterministic fallback. |
| **Settings & Local Data** | `/settings` | Offline MySQL health monitor, table record counts, rider profile switcher, and full JSON data backup export. |

---

## 5. Offline Data Backup & Export

Pocket Mechanic stores 100% of your records locally in MySQL (`pocket_mechanic_db`). You can export a comprehensive JSON backup of your entire fleet, history, and tickets at any time:
- Via UI: Go to **Settings & Local Data** &rarr; Click **Export JSON Backup**.
- Via API: `GET /api/data/export` (downloads `pocket_mechanic_backup_<timestamp>.json`).

---

## 6. Verification & Automated Test Suite

Run the complete test suite (21 automated unit and integration tests):
```bash
python3 -m unittest discover tests
```
All 21 tests cover:
- End-to-end user registration and motorcycle enrollment
- Component applicability rules (air vs liquid, disc vs drum)
- ML model inference and RUL regressions
- Diagnostics ticket lifecycle and report generation
- Desktop routes (`/garage`, `/settings`, `/schedule`, `/api/data/export`)
- Health check probe (`/health`)
- AES-Fernet encryption and decryption verification

---

## 7. Project Metadata

- **Author:** Moksh Suthar
- **Platform:** macOS Sonoma / Sequoia (Apple Silicon & Intel)
- **Status:** Stage 1 Software-Only Predictive Diagnostics Platform (Complete & Verified)
