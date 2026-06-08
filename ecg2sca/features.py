import xmltodict

# Median/mean clinical fallback values for missing features from Surbhi's development cohort
CLINICAL_DEFAULTS = {
    "HeartRate": 70.0,
    "ECG_QTCCalculation": 420.0,
    "ECG_PRinterval": 160.0,
    "ECG_QTInterval": 400.0,
    "ECG_QRSDuration": 90.0,
}


def parse_clinical_features(xml_path: str) -> dict:
    """
    Extract time-domain ECG clinical measurements from GE MUSE XML metadata.
    Missing values are filled using cohort defaults.
    """
    with open(xml_path, "rb") as f:
        doc = xmltodict.parse(f.read().decode("utf-8"))

    measurements = doc.get("RestingECG", {}).get("RestingECGMeasurements", {})
    if measurements is None:
        measurements = {}

    # Map XML tag → feature base name
    tag_map = {
        "VentricularRate": "HeartRate",
        "ventricularrate": "HeartRate",
        "QTCorrected": "ECG_QTCCalculation",
        "qtcorrected": "ECG_QTCCalculation",
        "PRInterval": "ECG_PRinterval",
        "printerval": "ECG_PRinterval",
        "QTInterval": "ECG_QTInterval",
        "qtinterval": "ECG_QTInterval",
        "QRSDuration": "ECG_QRSDuration",
        "qrsduration": "ECG_QRSDuration",
    }

    # Extract raw values
    raw_values = {}
    for xml_tag, feature_base in tag_map.items():
        val = measurements.get(xml_tag)
        if val is not None:
            try:
                raw_values[feature_base] = float(val)
            except (ValueError, TypeError):
                pass

    # For a single ECG XML, Min, Max, and Mean are all equal
    features = {}
    for base_name, default_val in CLINICAL_DEFAULTS.items():
        val = raw_values.get(base_name, default_val)
        if base_name == "HeartRate":
            features["HeartRateMean"] = val
            features["HeartRateMin"] = val
            features["HeartRateMax"] = val
        else:
            features[f"{base_name}Min"] = val
            features[f"{base_name}Max"] = val
            features[f"{base_name}Mean"] = val

    return features
