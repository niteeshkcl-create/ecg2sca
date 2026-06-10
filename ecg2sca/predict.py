import os
import logging
import numpy as np
import pandas as pd
import joblib

from .ingest import parse_xml_waveform, LEAD_INDEX
from .median import make_biosspy_median
from .features import parse_clinical_features

log = logging.getLogger("ecg2sca.predict")


def load_encoder(encoder_path: str):
    import tensorflow as tf
    from tensorflow.keras.models import load_model
    # Provide a Mish activation mapping so legacy HDF5 models that reference
    # Addons>mish or Mish can be deserialized even if tensorflow_addons
    # is not installed on the host. Prefer the tfa implementation when
    # available, otherwise provide a lightweight local fallback.
    custom_objects = {}
    try:
        import tensorflow_addons as tfa
        mish_impl = tfa.activations.mish
        log.info("tensorflow_addons available; using tfa.activations.mish")
    except Exception:
        import tensorflow as _tf
        log.warning("tensorflow_addons not found; using local Mish fallback.")
        def mish_impl(x):
            return x * _tf.math.tanh(_tf.math.softplus(x))

    # map common identifiers saved in older models to the implementation
    custom_objects["Addons>mish"] = mish_impl
    custom_objects["Mish"] = mish_impl
    custom_objects["mish"] = mish_impl
    # Limit TF threading to avoid pthread creation failures on constrained nodes
    tf.config.threading.set_intra_op_parallelism_threads(1)
    tf.config.threading.set_inter_op_parallelism_threads(1)
    # Force CPU only (no GPU) to avoid GPU init on headless nodes
    try:
        tf.config.set_visible_devices([], 'GPU')
    except Exception:
        pass

    # Load model with custom_objects to ensure deserialization succeeds
    try:
        encoder = load_model(encoder_path, custom_objects=custom_objects)
    except Exception as e:
        log.error(f"Failed to load encoder with custom_objects: {e}")
        # Last resort: try loading without custom objects to surface original error
        encoder = load_model(encoder_path)
    log.info(f"Encoder loaded: input={encoder.input_shape}, output={encoder.output_shape}")
    return encoder


def load_classifier(bundle_path: str):
    bundle = joblib.load(bundle_path)
    for key in ["model", "scaler", "feature_names", "thresholds"]:
        if key not in bundle:
            raise ValueError(f"Bundle is missing required key: '{key}'")
    log.info(
        f"Classifier loaded: {len(bundle['feature_names'])} features, thresholds={list(bundle['thresholds'].keys())}"
    )
    return bundle["model"], bundle["scaler"], bundle["feature_names"], bundle["thresholds"]


def predict_single_xml(xml_path: str, encoder, model, scaler, feature_names) -> dict:
    filename = os.path.basename(xml_path)
    # Metadata extraction
    patient_id = "unknown"
    acq_datetime = "unknown"
    try:
        import xmltodict
        with open(xml_path, "rb") as f:
            doc = xmltodict.parse(f.read().decode("utf-8"))
        patient_id = doc["RestingECG"]["PatientDemographics"]["PatientID"]
        acq_date = doc["RestingECG"]["TestDemographics"]["AcquisitionDate"]
        acq_time = doc["RestingECG"]["TestDemographics"]["AcquisitionTime"]
        acq_datetime = f"{acq_date}_{acq_time}"
    except Exception:
        pass

    ecg_array = parse_xml_waveform(xml_path)
    median_beat = make_biosspy_median(ecg_array, LEAD_INDEX, median_size=600, bpm=0)
    median_input = median_beat.copy()
    median_input -= np.mean(median_input)
    std = np.std(median_input)
    if std > 1e-7:
        median_input /= std
    embedding = encoder.predict(np.expand_dims(median_input, axis=0), verbose=0).flatten()
    clinical = parse_clinical_features(xml_path)
    feature_dict = {f"latent_{i}": embedding[i] for i in range(256)}
    feature_dict.update(clinical)
    df_features = pd.DataFrame([feature_dict])
    for col in feature_names:
        if col not in df_features:
            df_features[col] = 0.0
    df_features = df_features[feature_names]
    X_scaled = scaler.transform(df_features.values)
    prob = model.predict_proba(X_scaled)[0, 1]
    return {
        "filename": filename,
        "patient_id": patient_id,
        "acquisition_datetime": acq_datetime,
        "sca_risk_score": float(prob),
    }


def predict_single_csv(csv_path: str, encoder, model, scaler, feature_names) -> dict:
    """Process a CSV containing a raw 12‑lead waveform (rows=timesteps)."""
    filename = os.path.basename(csv_path)
    # Load waveform – first column is an index we drop
    # Load waveform – first column may be an index; we ignore it
    df = pd.read_csv(csv_path)
    # Expected 12 leads (standard order)
    expected_leads = ["I", "II", "III", "aVR", "aVL", "aVF",
                     "V1", "V2", "V3", "V4", "V5", "V6"]
    # Identify which leads are present (case‑insensitive)
    present = [col for col in df.columns if col.strip() in expected_leads]
    missing = [lead for lead in expected_leads if lead not in present]
    # Fill missing leads with zeros (same length as existing rows)
    for lead in missing:
        df[lead] = 0.0
    # Ensure column order matches expected leads
    df = df[expected_leads]
    ecg_array = df.values.astype(np.float32)
    median_beat = make_biosspy_median(ecg_array, LEAD_INDEX, median_size=600, bpm=0)
    median_input = median_beat.copy()
    median_input -= np.mean(median_input)
    std = np.std(median_input)
    if std > 1e-7:
        median_input /= std
    embedding = encoder.predict(np.expand_dims(median_input, axis=0), verbose=0).flatten()
    # CSV files lack clinical metadata – use defaults
    clinical = {}
    for base_name, default_val in {
        "HeartRate": 70.0,
        "ECG_QTCCalculation": 420.0,
        "ECG_PRinterval": 160.0,
        "ECG_QTInterval": 400.0,
        "ECG_QRSDuration": 90.0,
    }.items():
        if base_name == "HeartRate":
            clinical["HeartRateMean"] = clinical["HeartRateMin"] = clinical["HeartRateMax"] = default_val
        else:
            clinical[f"{base_name}Min"] = clinical[f"{base_name}Max"] = clinical[f"{base_name}Mean"] = default_val
    feature_dict = {f"latent_{i}": embedding[i] for i in range(256)}
    feature_dict.update(clinical)
    df_features = pd.DataFrame([feature_dict])
    for col in feature_names:
        if col not in df_features:
            df_features[col] = 0.0
    df_features = df_features[feature_names]
    X_scaled = scaler.transform(df_features.values)
    prob = model.predict_proba(X_scaled)[0, 1]
    return {
        "filename": filename,
        "patient_id": "unknown",
        "acquisition_datetime": "unknown",
        "sca_risk_score": float(prob),
    }


def run_batch(xml_paths: list, encoder, model, scaler, feature_names, thresholds) -> pd.DataFrame:
    """Run inference on a list of XML files."""
    results = []
    total = len(xml_paths)
    for i, path in enumerate(xml_paths, 1):
        log.info(f"Processing XML [{i}/{total}]: {os.path.basename(path)}")
        try:
            results.append(predict_single_xml(path, encoder, model, scaler, feature_names))
        except Exception as e:
            log.error(f"XML FAILED: {e}")
            results.append({
                "filename": os.path.basename(path),
                "patient_id": "ERROR",
                "acquisition_datetime": "ERROR",
                "sca_risk_score": np.nan,
            })
    return pd.DataFrame(results)


def run_batch_csv(csv_paths: list, encoder, model, scaler, feature_names, thresholds) -> pd.DataFrame:
    """Run inference on a list of CSV waveform files."""
    results = []
    total = len(csv_paths)
    for i, path in enumerate(csv_paths, 1):
        log.info(f"Processing CSV [{i}/{total}]: {os.path.basename(path)}")
        try:
            results.append(predict_single_csv(path, encoder, model, scaler, feature_names))
        except Exception as e:
            log.error(f"CSV FAILED: {e}")
            results.append({
                "filename": os.path.basename(path),
                "patient_id": "ERROR",
                "acquisition_datetime": "ERROR",
                "sca_risk_score": np.nan,
            })
    return pd.DataFrame(results)
