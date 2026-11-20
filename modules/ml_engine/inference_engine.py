import os
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List
from database.connection import get_db_connection

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODELS_DIR = os.path.join(BASE_DIR, "trained_models")

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

# Cache loaded models
_CACHE = {}

def get_loaded_artifact(filename: str):
    if filename not in _CACHE:
        path = os.path.join(MODELS_DIR, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model artifact not found: {path}. Run training_pipeline.py first.")
        _CACHE[filename] = joblib.load(path)
    return _CACHE[filename]

def run_ml_inference(raw_inputs: Dict[str, Any], model_name: str = "Random_Forest",
                     motorcycle_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Executes the full classical ML inference pipeline on input telemetry.
    Produces mathematical prediction, confidence score, remaining life regression,
    PCA projections, feature importances, and a live execution trace for UI rendering.
    """
    live_trace: List[Dict[str, str]] = []

    # Step 1: Feature Extraction
    live_trace.append({
        "stage": "Feature Extraction",
        "detail": f"Extracted {len(FEATURE_NAMES)} telemetry parameters from sensor packet."
    })

    # Prepare vector in fixed column order
    vector = []
    vector_dict = {}
    for feat in FEATURE_NAMES:
        val = float(raw_inputs.get(feat, 0.0))
        # Sensible fallbacks if omitted
        if feat == "ambient_temp" and val == 0.0:
            val = 28.0
        elif feat == "odometer_km" and val == 0.0:
            val = 8500.0
        elif feat == "engine_hours" and val == 0.0:
            val = round(float(raw_inputs.get("odometer_km", 8500.0)) / 38.0, 1)

        vector.append(val)
        vector_dict[feat] = val

    X_raw = np.array(vector).reshape(1, -1)

    # Step 2: Preprocessing & Scaling
    scaler = get_loaded_artifact("scaler.joblib")
    X_scaled = scaler.transform(X_raw)
    live_trace.append({
        "stage": "StandardScaler Preprocessing",
        "detail": f"Zero-mean unit-variance transformation applied across {len(FEATURE_NAMES)} input dimensions."
    })

    # Step 3: Latent Projections (PCA & K-Means)
    pca = get_loaded_artifact("pca_2d.joblib")
    pca_coords = pca.transform(X_scaled)[0].tolist()
    kmeans = get_loaded_artifact("kmeans_clusters.joblib")
    cluster_id = int(kmeans.predict(X_scaled)[0])
    live_trace.append({
        "stage": "Latent Space & Clustering",
        "detail": f"PCA Coordinates: [{pca_coords[0]:.3f}, {pca_coords[1]:.3f}], K-Means Operational Cluster #{cluster_id}"
    })

    # Step 4: Classifier Selection
    clean_model_name = model_name.replace(" ", "_")
    model_filename = f"{clean_model_name.lower()}_condition_v1.joblib"
    if not os.path.exists(os.path.join(MODELS_DIR, model_filename)):
        clean_model_name = "Random_Forest"
        model_filename = "random_forest_condition_v1.joblib"

    clf = get_loaded_artifact(model_filename)
    live_trace.append({
        "stage": "Model Inference",
        "detail": f"Executing trained classifier: {clean_model_name.replace('_', ' ')} (Joblib v1.0)"
    })

    # Inference: Condition
    predicted_condition = str(clf.predict(X_scaled)[0])

    confidence = 0.95
    probabilities = {}
    if hasattr(clf, "predict_proba"):
        probs = clf.predict_proba(X_scaled)[0]
        classes = clf.classes_
        confidence = float(np.max(probs))
        probabilities = {str(c): round(float(p), 4) for c, p in zip(classes, probs)}

    # Step 5: Dedicated Fault Risk Classification
    fault_clf = get_loaded_artifact("random_forest_fault_risk_v1.joblib")
    fault_label = str(fault_clf.predict(X_scaled)[0])
    live_trace.append({
        "stage": "Fault-Risk Diagnostics",
        "detail": f"Specific Fault Classifier isolated: {fault_label}"
    })

    # Step 6: Remaining Useful Life Regression
    rul_reg = get_loaded_artifact("random_forest_rul_regressor_v1.joblib")
    remaining_km = float(rul_reg.predict(X_scaled)[0])
    live_trace.append({
        "stage": "Remaining Life Regression",
        "detail": f"Estimated remaining brake friction life: {remaining_km:.0f} km"
    })

    # Step 7: Feature Importances
    feature_importance = {}
    if hasattr(clf, "feature_importances_"):
        raw_fi = clf.feature_importances_
        feature_importance = {f: round(float(w), 4) for f, w in zip(FEATURE_NAMES, raw_fi)}
        # Sort top 5 features
        feature_importance = dict(sorted(feature_importance.items(), key=lambda item: item[1], reverse=True)[:6])

    # Save prediction to MySQL if motorcycle_id provided
    if motorcycle_id:
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Find model_id
                cursor.execute("SELECT model_id FROM ml_models WHERE model_name=%s LIMIT 1", (clean_model_name,))
                m_row = cursor.fetchone()
                mid = m_row['model_id'] if m_row else 1
                cursor.execute(
                    """
                    INSERT INTO ml_predictions (model_id, motorcycle_id, input_features_json, predicted_class, probability, regression_value)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (mid, motorcycle_id, json.dumps(vector_dict), predicted_condition, confidence, remaining_km)
                )
        finally:
            conn.close()

    return {
        "model_used": clean_model_name.replace("_", " "),
        "predicted_condition": predicted_condition,
        "fault_label": fault_label,
        "confidence": round(confidence, 4),
        "confidence_pct": round(confidence * 100, 1),
        "probabilities": probabilities,
        "remaining_life_km": round(remaining_km, 0),
        "pca_coordinates": [round(pca_coords[0], 3), round(pca_coords[1], 3)],
        "cluster_id": cluster_id,
        "feature_importance": feature_importance,
        "live_trace": live_trace,
        "raw_inputs": vector_dict
    }
