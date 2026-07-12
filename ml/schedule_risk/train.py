"""
Schedule Risk Model Training Pipeline.
Trains a LightGBM classifier (will_slip > 5 days) and regressor (expected delay days)
on synthetic data. Outputs model artifacts to ml/schedule_risk/.

Usage:
    python -m ml.schedule_risk.train
"""
import numpy as np
import json
import os
import pickle
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_synthetic_data(n_samples=1000):
    """Generate synthetic training data for schedule risk prediction."""
    np.random.seed(42)

    # Features
    lead_time_variance = np.random.exponential(5, n_samples)  # days behind
    upstream_slippage = np.random.exponential(3, n_samples)
    workforce_gap = np.random.uniform(0, 0.5, n_samples)
    weather_severity = np.random.uniform(0, 0.4, n_samples)
    vendor_otd_risk = np.random.uniform(0, 0.3, n_samples)
    progress_deficit = np.random.uniform(0, 0.6, n_samples)

    X = np.column_stack([
        lead_time_variance, upstream_slippage, workforce_gap,
        weather_severity, vendor_otd_risk, progress_deficit
    ])

    # Labels — will_slip is 1 if combined risk is high
    risk_score = (
        lead_time_variance * 0.30 +
        upstream_slippage * 0.25 +
        workforce_gap * 15 * 0.15 +
        weather_severity * 25 * 0.10 +
        vendor_otd_risk * 33 * 0.10 +
        progress_deficit * 17 * 0.10
    )
    will_slip = (risk_score > 5).astype(int)
    delay_days = np.maximum(risk_score * 1.5 + np.random.normal(0, 2, n_samples), 0)

    return X, will_slip, delay_days


def train_model():
    """Train and save model artifacts."""
    logger.info("Generating synthetic training data...")
    X, y_class, y_reg = generate_synthetic_data(2000)

    # Split
    split = int(0.8 * len(X))
    X_train, X_test = X[:split], X[split:]
    y_class_train, y_class_test = y_class[:split], y_class[split:]
    y_reg_train, y_reg_test = y_reg[:split], y_reg[split:]

    try:
        import lightgbm as lgb

        logger.info("Training LightGBM classifier (will_slip > 5 days)...")
        clf = lgb.LGBMClassifier(n_estimators=100, max_depth=5, learning_rate=0.1)
        clf.fit(X_train, y_class_train)
        acc = clf.score(X_test, y_class_test)
        logger.info(f"Classifier accuracy: {acc:.4f}")

        logger.info("Training LightGBM regressor (expected delay days)...")
        reg = lgb.LGBMRegressor(n_estimators=100, max_depth=5, learning_rate=0.1)
        reg.fit(X_train, y_reg_train)
        preds = reg.predict(X_test)
        mae = np.mean(np.abs(preds - y_reg_test))
        logger.info(f"Regressor MAE: {mae:.4f} days")

        # Save artifacts
        os.makedirs("ml/schedule_risk", exist_ok=True)
        with open("ml/schedule_risk/classifier.pkl", "wb") as f:
            pickle.dump(clf, f)
        with open("ml/schedule_risk/regressor.pkl", "wb") as f:
            pickle.dump(reg, f)

        # Save metrics
        metrics = {
            "classifier_accuracy": float(acc),
            "regressor_mae": float(mae),
            "n_train": split,
            "n_test": len(X) - split,
            "features": ["lead_time_variance", "upstream_slippage", "workforce_gap",
                         "weather_severity", "vendor_otd_risk", "progress_deficit"],
        }
        with open("ml/schedule_risk/metrics.json", "w") as f:
            json.dump(metrics, f, indent=2)

        logger.info("Model artifacts saved to ml/schedule_risk/")

    except ImportError:
        logger.warning("LightGBM not installed. Saving weighted-sum fallback model.")
        os.makedirs("ml/schedule_risk", exist_ok=True)

        # Save a simple weights file as fallback
        weights = {
            "model_type": "weighted_sum_fallback",
            "weights": {
                "lead_time_variance": 0.30,
                "upstream_slippage": 0.25,
                "workforce_gap": 0.15,
                "weather_severity": 0.10,
                "vendor_otd_risk": 0.10,
                "progress_deficit": 0.10,
            }
        }
        with open("ml/schedule_risk/model_weights.json", "w") as f:
            json.dump(weights, f, indent=2)
        logger.info("Fallback model weights saved to ml/schedule_risk/model_weights.json")


if __name__ == "__main__":
    train_model()
