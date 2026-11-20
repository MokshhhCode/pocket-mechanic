# POCKET MECHANIC — 4-Person Project Contribution Split
### Academic Machine Learning Course Project (VIT TY ML)
**Project Title:** Pocket Mechanic — Intelligent Motorcycle Health Monitoring and Predictive Maintenance System (macOS Desktop Software)

---

## 1. Executive Summary & Philosophy of the Split

To fulfill the rigorous evaluation criteria of a university Machine Learning course project, the work is partitioned into **four equal, highly interdependent engineering roles**. 

Every single team member has **verifiable, mathematically sound Machine Learning responsibilities** alongside complementary engineering pillars (Dataset Engineering, Database Architecture, Systems/Backend, and Native Desktop/UI/UX):

```
+--------------------------------------------------------------------------------------------------+
|                                    PROJECT CONTRIBUTION SPLIT                                     |
+------------------------------------+------------------------------------+------------------------+
| Member                             | Core Machine Learning Pillar       | Engineering Pillar     |
+------------------------------------+------------------------------------+------------------------+
| Member 1 (Lead ML Architect)       | Supervised Classification & Tuning | Inference Integration  |
| Member 2 (ML Regr. & Data Lead)    | Continuous RUL, PCA & Clustering   | Kinematic Data Engine  |
| Member 3 (Data & Systems Lead)     | ML-DB Schema & Recommendation Eng. | MySQL & Security Tier  |
| Member 4 (Desktop & AI Lead)       | Explainable ML UI & Wrenchy Expert | macOS Desktop & UX     |
+------------------------------------+------------------------------------+------------------------+
```

---

## 2. Comprehensive Member Breakdown (Top to Bottom)

### 👤 MEMBER 1: Lead Machine Learning Engineer & Classification Architect
> **Primary Responsibility:** Supervised Condition Classification, Multi-Fault Isolation, Model Zoo Benchmarking, and Evaluation Metrics.

#### A. Machine Learning Contributions (100% ML Focused)
1. **Multi-Class Condition Classification**:
   - Formulated the 3-state component health problem: `Normal`, `Attention Required`, `Urgent Attention Required`.
   - Implemented, trained, and benchmarked a model zoo of **7 classical ML algorithms**:
     - **Random Forest (Selected Primary Classifier)**: Bagging ensemble with 100 estimators, Gini impurity criterion, handling non-linear cross-sensor interactions.
     - **Decision Tree**: Single tree baseline establishing interpretability boundaries.
     - **Support Vector Machine (SVM)**: Non-linear RBF kernel maximizing hyperplanes in high-dimensional telemetry space.
     - **Gradient Boosted Decision Trees (GBDT)**: Sequential boosting minimizing pseudo-residuals.
     - **K-Nearest Neighbors (KNN)**: Distance-weighted neighborhood voting ($k=5$).
     - **Multinomial Logistic Regression**: L-BFGS solver baseline for linear separability testing.
     - **Gaussian Naive Bayes**: Probabilistic classifier assuming conditional independence.
2. **Multi-Fault Risk Isolation**:
   - Built the multi-fault isolation model categorizing specific physical failure modes: `Nominal`, `Thermal_Overheating`, `Battery_Degraded`, `Brake_Thinning`, `Vibration_Excessive`, `Chain_Loose`.
3. **Rigorous Evaluation & Validation**:
   - Evaluated all 7 models across **Accuracy, Precision, Recall, F1-Score, ROC/AUC, and Inference Latency**.
   - Generated the empirical classification performance benchmark table (Random Forest achieving 100.0% accuracy on the test set).
   - Extracted and analyzed **Mean Decrease in Impurity (MDI) Feature Importances** (identifying `brake_pad_thickness` at 28.4%, `battery_voltage` at 18.2%, and `vibration_level` at 15.6% as primary discriminators).
4. **Model Serialization & Deployment**:
   - Built the serialization pipeline (`modules/ml_engine/training_pipeline.py`) utilizing `joblib` for persisting trained model artifacts in `trained_models/`.
   - Engineered the structured model metadata registry (`trained_models/model_metadata.json`).

#### B. Software Engineering & Integration
- Implemented `modules/ml_engine/inference_engine.py` connecting serialized `.joblib` models to live Flask requests.
- Integrated classification confidence scoring and probabilities in `modules/diagnostics/routes.py`.
- Authored test cases validating model inference bounds and classification output structures (`tests/test_ml_engine.py`, `tests/test_diagnostics.py`).

#### C. Codebase Files & Artifacts Owned
- `modules/ml_engine/training_pipeline.py` (Classifier training routines)
- `modules/ml_engine/inference_engine.py` (Inference execution & probability distribution)
- `trained_models/*.joblib` (Classifier model artifacts)
- `trained_models/model_metadata.json` (Hyperparameters & benchmark scores)
- `tests/test_ml_engine.py` (Automated classifier tests)

#### D. Academic Report & Viva Defense Topics
- *Report Section:* Mathematical foundations of Ensemble Bagging vs Boosting, Kernel SVM, Loss Functions, and Cross-Validation.
- *Viva Ready Questions:* "Why did Random Forest outperform Logistic Regression?", "How did you prevent overfitting in deep Decision Trees?", "Explain how Gini Impurity and Entropy differ in your model."

---

### 👤 MEMBER 2: ML Regression, Unsupervised Learning & Dataset Engineering Lead
> **Primary Responsibility:** Continuous Remaining Useful Life (RUL) Modeling, Dimensionality Reduction, Unsupervised Clustering, and Physics-Based Dataset Synthesis.

#### A. Machine Learning Contributions (100% ML Focused)
1. **Continuous Remaining Useful Life (RUL) Regression**:
   - Formulated the continuous degradation problem predicting residual brake friction material life in kilometers (`remaining_brake_life_km`).
   - Implemented and evaluated **Random Forest Regressor** against an $L_2$-regularized **Ridge Regression** baseline.
   - Evaluated regression performance using **Mean Absolute Error (MAE: 109.69 km)**, **Root Mean Squared Error (RMSE: 143.79 km)**, and **Coefficient of Determination ($R^2 = 0.9982$)**.
2. **Unsupervised Dimensionality Reduction & Latent Space**:
   - Implemented **Principal Component Analysis (PCA)** projecting 14-dimensional sensor vectors onto a 2D orthogonal latent plane (retaining 40.0% cumulative variance).
   - Created the 2D coordinate transformation allowing visual cluster separation of operating states without label supervision.
3. **Unsupervised Operational Regime Clustering**:
   - Implemented **K-Means Clustering** ($k=4$) to partition operational regimes (Idle, Highway Cruise, High-Load Thermal Stress, Mechanical Fault) without ground truth labels.
4. **Kinematic & Thermodynamic Dataset Generation**:
   - Engineered `modules/ml_engine/dataset_generator.py` producing 6,000 stratified, correlated telemetry samples (`data/synthetic_sensor_dataset.csv`).
   - Modeled physical kinematic laws: RPM-speed drivetrain ratios, Arrhenius-based thermal accumulation, alternator charging curves, and quadratic vibration-frequency scaling.
5. **Data Preprocessing & Anti-Leakage Pipeline**:
   - Enforced strict 80/20 train/test stratification.
   - Built the zero-lookahead preprocessing pipeline fitting `StandardScaler` strictly on training data and saving scaling parameters (`trained_models/scaler.joblib`) for runtime inference.

#### B. Software Engineering & Integration
- Implemented `modules/sensor/simulated_provider.py` delivering real-time correlated telemetry with 3 stress modes (Regular, Medium, Intense).
- Built sensor range validation and tolerance thresholds in `modules/telemetry/routes.py`.
- Authored automated tests for data generation, sensor ranges, and regression inference (`tests/test_simulation.py`).

#### C. Codebase Files & Artifacts Owned
- `modules/ml_engine/dataset_generator.py` (Physics-based synthetic generator)
- `data/synthetic_sensor_dataset.csv` (6,000-sample master dataset)
- `modules/sensor/simulated_provider.py` (Real-time telemetry stream engine)
- `trained_models/random_forest_rul_regressor_v1.joblib`
- `trained_models/ridge_rul_regressor_v1.joblib`
- `trained_models/pca_2d.joblib` & `trained_models/kmeans_clusters.joblib`
- `trained_models/scaler.joblib`
- `tests/test_simulation.py`

#### D. Academic Report & Viva Defense Topics
- *Report Section:* Dataset Generation Methodology, Covariance Matrices & Eigenvalues in PCA, K-Means Inertia / Elbow Method, Regression Loss Metrics ($R^2$, MAE, RMSE).
- *Viva Ready Questions:* "Why did you fit `StandardScaler` only on the training split?", "What do the first two principal components represent physically?", "Why use Random Forest Regressor over simple linear regression for brake pad life?"

---

### 👤 MEMBER 3: Data Architect, Backend Systems & Diagnostic Engine Engineer
> **Primary Responsibility:** Offline Relational Database Design, Cryptographic Data Security, Component Applicability Logic, and ML-Driven Recommendation Engine.

#### A. Machine Learning Contributions (Applied ML & Knowledge Engineering)
1. **ML Persistence & Audit Schema**:
   - Architected database tables (`ml_models`, `diagnostic_records`) designed to store model version history, accuracy metrics, inference logs, feature importance vectors, and prediction confidence scores.
2. **Component Applicability Inference Rules**:
   - Built motorcycle architecture validation rules ensuring ML features and diagnostic routines adapt to motorcycle physical variants (e.g., suppressing coolant temperature checks on air-cooled engines, adapting brake telemetry for drum vs disc configurations).
3. **ML-to-Action Prescriptive Maintenance Engine**:
   - Designed `modules/recommendations/engine.py`, an algorithmic translation layer taking ML condition classifications, fault risks, and RUL predictions and mapping them to actionable maintenance directives, urgency rankings, parts requirement lists, and cost estimates.

#### B. Software Engineering & Systems Integration
1. **Offline MySQL Relational Database**:
   - Engineered the normalized 28-table database schema in local MySQL (`database/schema.sql`, `database/models.py`).
   - Implemented connection pooling, transaction handling, and relational foreign-key cascades (`database/connection.py`).
2. **Master OEM Specifications Database**:
   - Created the seed dataset (`database/seed_data.py`) containing 28 verified motorcycle manufacturers and 50+ granular OEM specifications (bore, stroke, power, oil viscosity, tyre pressures).
3. **Data Security & Cryptography**:
   - Built the AES-256 Fernet cryptographic layer ensuring user profile data and maintenance records remain encrypted at rest.
4. **Logbook, Service History & Backup APIs**:
   - Engineered the maintenance logbook, diagnostic ticket resolution lifecycle (`modules/history/routes.py`), and full JSON backup export system (`/api/data/export`).

#### C. Codebase Files & Artifacts Owned
- `database/schema.sql` (28 normalized tables)
- `database/models.py` (Relational data models)
- `database/connection.py` (MySQL connection pool & transaction manager)
- `database/seed_data.py` (28 OEM motorcycle master catalog)
- `modules/recommendations/engine.py` (Prescriptive recommendation algorithm)
- `modules/history/routes.py` (Logbook & ticketing engine)
- `tests/test_auth.py`, `tests/test_motorcycle.py`, `tests/test_recommendations.py`

#### D. Academic Report & Viva Defense Topics
- *Report Section:* Relational Database ERD, Data Normalization (3NF/BCNF), Cryptographic Architecture (AES-256 Fernet), Rule-Based Expert Prescriptive Mapping.
- *Viva Ready Questions:* "How does the system ensure ACID compliance during diagnostic ticket creation?", "How are ML prediction outputs stored and audited in the database?", "How does the component applicability engine prevent false alarms on air-cooled engines?"

---

### 👤 MEMBER 4: Desktop Application Architect, UI/UX Lead & AI Diagnostic Assistant
> **Primary Responsibility:** Native macOS Desktop Application, Notion-Inspired Product Design System, Real-Time ML Visualizations, and Context-Aware Wrenchy AI.

#### A. Machine Learning Contributions (ML Visualization & Explainable AI)
1. **Explainable ML Interface & Visual Telemetry**:
   - Designed the front-end ML Diagnostic Console (`templates/diagnostics/diagnose.html`, `static/js/diagnostics.js`), surfacing real-time model confidence percentages, multi-class condition pills, and feature breakdown cards.
   - Built visual diagnostic report generator (`templates/diagnostics/report.html`) presenting ML prediction summaries, recommended technical procedures, and risk levels.
   - Implemented real-time interactive telemetry gauge cards (`templates/telemetry/live.html`, `static/js/telemetry.js`) with dynamic color thresholds (Emerald/Amber/Crimson) reflecting ML anomaly boundaries.
2. **Context-Aware Wrenchy AI Integration**:
   - Engineered `modules/wrenchy/service.py` integrating conversational AI with the ML pipeline:
     - Extracts the active motorcycle's live telemetry, ML condition prediction, and OEM specs, feeding them into the AI prompt context.
     - Built the **100% offline deterministic diagnostic expert fallback** generating structured troubleshooting guides when running without an internet connection or OpenAI API key.

#### B. Software Engineering & Systems Integration
1. **Native macOS Desktop Application Packaging**:
   - Built `Pocket Mechanic.app` native macOS app bundle with custom Apple ICNS icon, `Info.plist`, and `pocket_mechanic_launcher` shell binary.
   - Implemented desktop wrapper `desktop/desktop_main.py` utilizing native Cocoa `WKWebView` (`pywebview`) with traffic light controls, smooth window resizing, and keyboard shortcuts.
2. **Notion-Inspired Design System & Responsive UI**:
   - Created obsidian-themed design system in `static/css/style.css` and `templates/base.html` featuring persistent left-hand navigation sidebar, crisp cards, and fluid animations.
   - Implemented high-contrast dark/light mode toggle with dual `data-theme` and `data-bs-theme` synchronization.
   - Vendored all dependencies locally (Bootstrap 5.3.3, SVG icons, animated Wrenchy SVG logo) ensuring 100% offline self-contained operation.

#### C. Codebase Files & Artifacts Owned
- `Pocket Mechanic.app/` (Native macOS bundle)
- `desktop/desktop_main.py` (Native WebKit desktop runner)
- `run_desktop.sh`, `launcher.py` (Desktop execution scripts)
- `modules/wrenchy/service.py` & `modules/wrenchy/routes.py` (AI Assistant & Offline Expert)
- `templates/` (All Notion-style HTML views)
- `static/css/style.css`, `static/css/wrenchy.css` (Full design system)
- `static/js/*.js` (Client-side telemetry streams & async diagnostics)
- `tests/test_desktop_and_new_features.py`, `tests/test_e2e_flow.py`

#### D. Academic Report & Viva Defense Topics
- *Report Section:* Human-Computer Interaction (HCI) in Automotive Telemetry, Native Desktop vs Web Architectures, Explainable AI (XAI) UI Design, Contextual Prompt Engineering & Offline Expert Systems.
- *Viva Ready Questions:* "How does the UI explain ML model predictions to a non-technical rider?", "How does Wrenchy AI function when there is no internet connection?", "What architectural advantages did native Cocoa WebKit provide over Electron?"

---

## 3. Contribution Matrix Across Project Dimensions

| Project Dimension | Member 1 (ML Classification) | Member 2 (ML Regr. & Data) | Member 3 (Data & Systems) | Member 4 (Desktop & UX) |
| :--- | :---: | :---: | :---: | :---: |
| **Supervised Classification (7 Models)** | **Lead (100%)** | Supporting (Validation) | Schema Storage | UI Integration |
| **RUL Regression (RF & Ridge)** | Benchmark Review | **Lead (100%)** | Audit Logging | UI Gauge Display |
| **Unsupervised Learning (PCA & K-Means)** | Feature Analysis | **Lead (100%)** | Cluster DB Records | Visual Latent Plots |
| **Kinematic Dataset Generation (6k rows)** | Feature Scoping | **Lead (100%)** | Ingestion & Seeding | Telemetry Controls |
| **Relational Database (MySQL 28 tables)** | ML Model Tables | Sensor Data Logging | **Lead (100%)** | Settings View |
| **Component Applicability Logic** | Target Mapping | Feature Boundaries | **Lead (100%)** | Garage Fleet Filter |
| **Prescriptive Maintenance Engine** | Class Inputs | Degradation Metrics | **Lead (100%)** | Action Checklist UI |
| **Native macOS App (`.app` / WebKit)** | CLI Verification | Script Testing | Service Launching | **Lead (100%)** |
| **Notion UI Design & Light/Dark Theme** | Feedback | Feedback | Data Binding | **Lead (100%)** |
| **Wrenchy AI & Offline Expert System** | Inference API | Sensor Prompt Context | Spec Data Injection | **Lead (100%)** |
| **Automated Test Suite (21 Unit Tests)** | ML Tests (5) | Simulation Tests (3) | Auth/DB Tests (7) | Desktop/E2E Tests (6) |
| **Project Report Documentation** | ML Methodology | Dataset & Math | Database & Security | UI/UX & System Intro |

---

## 4. Academic Report "Author Contribution Statement" (Ready to Paste)

```markdown
### Author Contribution Statement

- **Member 1 (Roll No: [Insert Roll No]):** Formulated the supervised component health classification problem. Designed, trained, tuned, and evaluated the 7-model machine learning benchmark zoo (Random Forest, Decision Tree, SVM, GBDT, KNN, Logistic Regression, Gaussian Naive Bayes). Conducted hyperparameter optimization, confusion matrix analysis, and feature importance evaluation. Built the inference engine and classifier unit test suite.
- **Member 2 (Roll No: [Insert Roll No]):** Formulated the continuous predictive maintenance remaining useful life (RUL) regression task using Random Forest and Ridge Regression ($R^2 = 0.9982$). Implemented unsupervised latent space modeling using PCA and K-Means operational clustering. Developed the 14-dimensional physics-based synthetic sensor dataset generator and engineered anti-leakage train/test preprocessing pipelines.
- **Member 3 (Roll No: [Insert Roll No]):** Designed and normalized the 28-entity offline MySQL database schema and created the 28-OEM master vehicle catalog. Implemented AES-256 Fernet encryption at rest for user data. Developed the motorcycle component applicability rule engine and the prescriptive maintenance recommendation engine mapping ML outputs to prioritized servicing tasks and costs.
- **Member 4 (Roll No: [Insert Roll No]):** Architected the native macOS desktop application bundle and Cocoa WebKit wrapper. Designed the Notion-inspired automotive UI/UX design system with synchronized dark/light mode and 100% offline vendored assets. Built the explainable ML diagnostics interface, live telemetry dashboards, and the context-aware Wrenchy AI assistant with offline deterministic fallback.
```
