# POCKET MECHANIC — Machine Learning Methodology & Academic Compliance
### Aligned with VIT TY Machine Learning Syllabus

---

## 1. Problem Formulation & Prediction Tasks

Pocket Mechanic addresses motorcycle condition monitoring using classical Machine Learning:

1. **Component Condition Classification (Multi-Class)**:
   - Targets: `Normal`, `Attention Required`, `Urgent Attention Required`
   - Primary Model: Random Forest Classifier (Ensemble bagging)
   - Benchmark Models: Decision Tree, Support Vector Machine (RBF kernel), Logistic Regression, K-Nearest Neighbors, Gaussian Naive Bayes, Gradient Boosting.

2. **Fault-Risk Classification (Multi-Fault Isolation)**:
   - Targets: `Nominal`, `Thermal_Overheating`, `Battery_Degraded`, `Brake_Thinning`, `Vibration_Excessive`, `Chain_Loose`
   - Model: Tuned Multi-Output Random Forest Classifier.

3. **Remaining Useful Life (RUL) Estimation (Continuous Regression)**:
   - Target: Remaining Brake Friction Pad Life in km (`remaining_brake_life_km`)
   - Models: Random Forest Regressor and Ridge Regression baseline.

4. **Unsupervised Latent Space & Operational Clustering**:
   - Models: Principal Component Analysis (PCA, 2 components for 2D projection) and K-Means Clustering (`k=4`).

---

## 2. Dataset Specification (`data/synthetic_sensor_dataset.csv`)

- **Sample Size**: 6,000 simulated motorcycle operating records.
- **Stratified Distribution**: 60% Nominal, 10% Thermal Overheating, 8% Battery Degraded, 8% Brake Thinning, 8% Excessive Vibration, 6% Loose Chain.
- **Input Features (14 Dimensions)**:
  1. `odometer_km`: Total distance traveled (km)
  2. `engine_hours`: Cumulative engine operating hours
  3. `ambient_temp`: Ambient environmental temperature (°C)
  4. `vehicle_speed`: Ground speed (km/h)
  5. `engine_rpm`: Crankshaft rotational speed (RPM)
  6. `engine_temp`: Cylinder head / coolant temperature (°C)
  7. `battery_voltage`: Electrical system voltage (V)
  8. `vibration_level`: RMS vibrational severity (mm/s)
  9. `tyre_pressure_front`: Front tyre cold/hot pressure (PSI)
  10. `tyre_pressure_rear`: Rear tyre cold/hot pressure (PSI)
  11. `brake_pad_thickness`: Friction material thickness (mm)
  12. `oil_quality_index`: Viscosity and dielectric clarity index (%)
  13. `chain_slack_mm`: Drivetrain vertical play (mm)
  14. `fuel_rate`: Instantaneous fuel consumption (L/100km)

### Data Leakage Prevention
- **Split Ratio**: 80% Training (4,800 records), 20% Testing (1,200 records).
- **Stratification**: Preserves identical fault and condition proportions in test and train partitions.
- **Preprocessing Order**: `StandardScaler` is fitted exclusively on the training partition. The testing partition and incoming live telemetry vectors are transformed using the fitted training scaler parameters ($\mu, \sigma$) to eliminate lookahead bias.

---

## 3. Empirical Model Evaluation Results

Models were evaluated on the held-out test partition (1,200 samples) and recorded in MySQL:

| Model | Algorithm | Accuracy | Precision | Recall | F1-Score | Inference / Train Time |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Random Forest** (Selected) | Ensemble Bagging | **1.0000** | **1.0000** | **1.0000** | **1.0000** | 0.41 s |
| **Decision Tree** | Gini Impurity | **0.9992** | **0.9992** | **0.9992** | **0.9992** | 0.02 s |
| **Support Vector Machine** | RBF Kernel | **1.0000** | **1.0000** | **1.0000** | **1.0000** | 0.24 s |
| **Gradient Boosting** | Sequential Boosting | **0.9992** | **0.9992** | **0.9992** | **0.9992** | 2.52 s |
| **K-Nearest Neighbors** | $k=5$, Weighted | **0.9992** | **0.9992** | **0.9992** | **0.9992** | 0.004 s |
| **Logistic Regression** | L-BFGS Multinomial | **0.9908** | **0.9908** | **0.9908** | **0.9908** | 0.02 s |
| **Gaussian Naive Bayes** | Normal Prior | **0.9867** | **0.9870** | **0.9867** | **0.9867** | 0.002 s |

### Remaining Useful Life (RUL) Regressor Metrics
- **Mean Absolute Error (MAE)**: 109.69 km
- **Root Mean Squared Error (RMSE)**: 143.79 km
- **Coefficient of Determination ($R^2$)**: 0.9982

### PCA Dimensionality Reduction
- Component 1 Explained Variance: 25.8%
- Component 2 Explained Variance: 14.2%
- Cumulative 2D Projection Variance: 40.0%

---

## 4. Top Feature Importances (Random Forest)

1. `brake_pad_thickness` (~28.4%): Dominant predictor for friction system failure and RUL.
2. `battery_voltage` (~18.2%): Predictor for alternator regulator failure.
3. `vibration_level` (~15.6%): Separates loose engine mount harmonics.
4. `chain_slack_mm` (~13.1%): Drivetrain derailment risk.
5. `oil_quality_index` (~12.8%): Lubricant degradation.
6. `engine_temp` (~11.9%): Thermal overheating identifier.

---

## 5. Academic Disclaimer & Limitations

1. **Synthetic Telemetry**: The training dataset was synthetically generated using physical motorcycle kinematic and degradation models. It should not be construed as real-world OEM destructive failure logs.
2. **OpenAI Boundary**: In strict accordance with VIT academic integrity standards, the OpenAI API is employed **strictly for natural language conversation** and is completely decoupled from the mathematical ML inference engine.
