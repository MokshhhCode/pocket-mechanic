"""
Pocket Mechanic: Classical Machine Learning Training Pipeline
Complies with VIT TY Machine Learning syllabus requirements:
- Supervised: Random Forest, Decision Tree, SVM, Logistic Regression, KNN, Naive Bayes, Gradient Boosting
- Regression: Random Forest Regressor, Ridge Regression
- Unsupervised: K-Means Clustering, PCA Dimensionality Reduction
- Comprehensive Metrics: Accuracy, Precision, Recall, F1, ROC-AUC, Confusion Matrix, MAE, RMSE, R2
- Model Persistence: Joblib serialization and MySQL Registry tracking
"""

import os
import time
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, mean_absolute_error, mean_squared_error, r2_score
)

# Classifiers
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestRegressor

from database.connection import get_db_connection
from modules.ml_engine.dataset_generator import generate_motorcycle_dataset

FEATURE_NAMES = [
    "odometer_km",
    "engine_hours",
    "ambient_temp",
    "vehicle_speed",
    "engine_rpm",
    "engine_temp",
    "battery_voltage",
    "vibration_level",
    "tyre_pressure_front",
    "tyre_pressure_rear",
    "brake_pad_thickness",
    "oil_quality_index",
    "chain_slack_mm",
    "fuel_rate"
]

def run_training_pipeline() -> Dict[str, Any]:
    print("=" * 70)
    print("POCKET MECHANIC: INITIATING MACHINE LEARNING TRAINING PIPELINE")
    print("=" * 70)

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(base_dir, "data")
    models_dir = os.path.join(base_dir, "trained_models")
    os.makedirs(models_dir, exist_ok=True)

    csv_path = os.path.join(data_dir, "synthetic_sensor_dataset.csv")
    if not os.path.exists(csv_path):
        print("Dataset not found. Generating fresh synthetic dataset...")
        csv_path = generate_motorcycle_dataset()

    print(f"Loading dataset: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"Dataset shape: {df.shape}")

    X = df[FEATURE_NAMES]
    y_cond = df["condition_label"]      # Normal, Attention Required, Urgent Attention Required
    y_fault = df["fault_label"]          # Nominal, Thermal_Overheating, etc.
    y_reg = df["remaining_brake_life_km"] # Continuous RUL in km

    # Train / Test Split (Stratified to prevent class imbalance leakage)
    X_train, X_test, y_train_cond, y_test_cond, y_train_fault, y_test_fault, y_train_reg, y_test_reg = train_test_split(
        X, y_cond, y_fault, y_reg, test_size=0.20, random_state=42, stratify=y_cond
    )
    print(f"Training set: {len(X_train)} samples | Testing set: {len(X_test)} samples")

    # Scaler
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Dimensionality Reduction: PCA (2 components for 2D visualization & 5 for latent features)
    pca_2d = PCA(n_components=2, random_state=42)
    X_train_pca = pca_2d.fit_transform(X_train_scaled)
    X_test_pca = pca_2d.transform(X_test_scaled)
    pca_explained_var = pca_2d.explained_variance_ratio_.tolist()
    print(f"PCA (2-Components) Explained Variance: {pca_explained_var}")

    # Unsupervised: K-Means Clustering on latent operational space
    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    kmeans.fit(X_train_scaled)

    # -------------------------------------------------------------------------
    # SUPERVISED CLASSIFIER MODEL ZOO (Condition & Fault Classification)
    # -------------------------------------------------------------------------
    classifiers = {
        "Random_Forest": RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42),
        "Decision_Tree": DecisionTreeClassifier(criterion="gini", max_depth=8, random_state=42),
        "Support_Vector_Machine": SVC(kernel="rbf", C=10.0, probability=True, random_state=42),
        "Logistic_Regression": LogisticRegression(max_iter=1000, random_state=42),
        "K_Nearest_Neighbors": KNeighborsClassifier(n_neighbors=5, weights="distance"),
        "Naive_Bayes": GaussianNB(),
        "Gradient_Boosting": GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, random_state=42)
    }

    results = {}
    best_model_name = "Random_Forest"
    best_f1 = -1.0

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Clear previous models to maintain clean registry
            cursor.execute("DELETE FROM ml_models")

            for name, clf in classifiers.items():
                print(f"--> Training {name} on Component Condition Task...")
                start_time = time.time()
                clf.fit(X_train_scaled, y_train_cond)
                duration = time.time() - start_time

                # Inference on test set
                y_pred = clf.predict(X_test_scaled)
                y_proba = clf.predict_proba(X_test_scaled) if hasattr(clf, "predict_proba") else None

                acc = float(accuracy_score(y_test_cond, y_pred))
                prec = float(precision_score(y_test_cond, y_pred, average="weighted", zero_division=0))
                rec = float(recall_score(y_test_cond, y_pred, average="weighted", zero_division=0))
                f1 = float(f1_score(y_test_cond, y_pred, average="weighted", zero_division=0))
                cm = confusion_matrix(y_test_cond, y_pred).tolist()

                # ROC-AUC (One-vs-Rest)
                roc_auc = None
                if y_proba is not None:
                    try:
                        roc_auc = float(roc_auc_score(pd.get_dummies(y_test_cond), y_proba, multi_class="ovr", average="weighted"))
                    except Exception:
                        roc_auc = None

                # Extract feature importance if available
                feat_importance = None
                if hasattr(clf, "feature_importances_"):
                    feat_importance = dict(zip(FEATURE_NAMES, [float(x) for x in clf.feature_importances_]))

                # Save model to disk
                model_filename = f"{name.lower()}_condition_v1.joblib"
                model_path = os.path.join(models_dir, model_filename)
                joblib.dump(clf, model_path)

                # Register in ml_models
                cursor.execute(
                    """
                    INSERT INTO ml_models (model_name, model_type, algorithm, version, filepath, is_active, target_component)
                    VALUES (%s, 'Classification', %s, 'v1.0.0', %s, %s, 'General Component Condition')
                    """,
                    (name, name.replace("_", " "), model_path, (name == "Random_Forest"))
                )
                model_id = cursor.lastrowid

                # Record training run
                cursor.execute(
                    """
                    INSERT INTO ml_training_runs (model_id, dataset_name, sample_count, feature_columns_json, hyperparameters_json, training_duration_sec)
                    VALUES (%s, 'synthetic_sensor_dataset.csv', %s, %s, %s, %s)
                    """,
                    (
                        model_id, len(df), json.dumps(FEATURE_NAMES),
                        json.dumps({k: str(v) for k, v in clf.get_params().items()}),
                        round(duration, 2)
                    )
                )
                run_id = cursor.lastrowid

                # Record evaluation metrics
                cursor.execute(
                    """
                    INSERT INTO ml_evaluation_metrics (run_id, accuracy, precision_score, recall, f1_score, roc_auc, confusion_matrix_json)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (run_id, acc, prec, rec, f1, roc_auc, json.dumps(cm))
                )

                results[name] = {
                    "accuracy": acc,
                    "precision": prec,
                    "recall": rec,
                    "f1_score": f1,
                    "roc_auc": roc_auc,
                    "duration_sec": round(duration, 2),
                    "feature_importance": feat_importance
                }
                print(f"    {name} -> Acc: {acc:.4f} | Prec: {prec:.4f} | Rec: {rec:.4f} | F1: {f1:.4f} (in {duration:.2f}s)")

                if f1 > best_f1:
                    best_f1 = f1
                    best_model_name = name

            # -----------------------------------------------------------------
            # FAULT-RISK CLASSIFIER (Specific failure diagnosis: Thermal, Battery, etc.)
            # -----------------------------------------------------------------
            print("--> Training Dedicated Fault-Risk Classifier (Random Forest Multi-Fault)...")
            fault_clf = RandomForestClassifier(n_estimators=100, max_depth=14, random_state=42)
            fault_clf.fit(X_train_scaled, y_train_fault)
            fault_pred = fault_clf.predict(X_test_scaled)
            fault_acc = float(accuracy_score(y_test_fault, fault_pred))
            fault_f1 = float(f1_score(y_test_fault, fault_pred, average="weighted"))
            joblib.dump(fault_clf, os.path.join(models_dir, "random_forest_fault_risk_v1.joblib"))

            # -----------------------------------------------------------------
            # REGRESSION ENGINE (Remaining Useful Life Estimation)
            # -----------------------------------------------------------------
            print("--> Training Remaining Useful Life (RUL) Regressors...")
            rf_reg = RandomForestRegressor(n_estimators=80, max_depth=10, random_state=42)
            rf_reg.fit(X_train_scaled, y_train_reg)
            reg_pred = rf_reg.predict(X_test_scaled)

            mae = float(mean_absolute_error(y_test_reg, reg_pred))
            rmse = float(np.sqrt(mean_squared_error(y_test_reg, reg_pred)))
            r2 = float(r2_score(y_test_reg, reg_pred))
            joblib.dump(rf_reg, os.path.join(models_dir, "random_forest_rul_regressor_v1.joblib"))
            print(f"    RUL Regressor -> MAE: {mae:.2f} km | RMSE: {rmse:.2f} km | R²: {r2:.4f}")

            # Baseline Ridge Regression
            ridge_reg = Ridge(alpha=1.0)
            ridge_reg.fit(X_train_scaled, y_train_reg)
            joblib.dump(ridge_reg, os.path.join(models_dir, "ridge_rul_regressor_v1.joblib"))

            # Save Scaler, PCA, KMeans, and Metadata bundle
            joblib.dump(scaler, os.path.join(models_dir, "scaler.joblib"))
            joblib.dump(pca_2d, os.path.join(models_dir, "pca_2d.joblib"))
            joblib.dump(kmeans, os.path.join(models_dir, "kmeans_clusters.joblib"))

            meta = {
                "trained_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "feature_names": FEATURE_NAMES,
                "best_classifier": best_model_name,
                "best_f1": best_f1,
                "results": results,
                "pca_explained_variance": pca_explained_var,
                "rul_metrics": {"mae": mae, "rmse": rmse, "r2": r2}
            }
            with open(os.path.join(models_dir, "model_metadata.json"), "w") as f:
                json.dump(meta, f, indent=2)

            print("=" * 70)
            print(f"MACHINE LEARNING TRAINING PIPELINE COMPLETED SUCCESSFULLY!")
            print(f"Selected Primary Model: {best_model_name} (F1: {best_f1:.4f})")
            print("=" * 70)

            return meta
    finally:
        conn.close()

if __name__ == "__main__":
    run_training_pipeline()
