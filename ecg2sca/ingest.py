import base64
import struct
import numpy as np
import xmltodict

# Standard 12 leads and order expected by models
LEAD_ORDER = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]
LEAD_INDEX = {name: idx for idx, name in enumerate(LEAD_ORDER)}


def decode_muse_waveform(raw_b64: str) -> np.ndarray:
    """Decode a base64-encoded GE MUSE waveform into a 1-D float32 array."""
    raw_bytes = base64.b64decode(raw_b64.encode("utf-8"))
    n_samples = len(raw_bytes) // 2
    samples = struct.unpack(f"<{n_samples}h", raw_bytes)
    return np.array(samples, dtype=np.float32)


def parse_xml_waveform(xml_path: str) -> np.ndarray:
    """
    Parse a GE MUSE XML file and return the 12-lead rhythm waveform
    as an array of shape (N, 12). Recomputes derived/augmented leads
    using Einthoven/Goldberger equations.
    """
    with open(xml_path, "rb") as f:
        doc = xmltodict.parse(f.read().decode("utf-8"))

    lead_data = {}

    # Locate waveform blocks
    waveforms = doc.get("RestingECG", {}).get("Waveform", [])
    if isinstance(waveforms, dict):
        waveforms = [waveforms]

    for waveform_group in waveforms:
        lead_entries = waveform_group.get("LeadData", [])
        if isinstance(lead_entries, dict):
            lead_entries = [lead_entries]

        for lead_entry in lead_entries:
            lead_id = lead_entry.get("LeadID")
            raw = lead_entry.get("WaveFormData")
            if lead_id and raw:
                decoded = decode_muse_waveform(raw)
                # Keep rhythm strip (typically 5000 samples at 500 Hz, or 2500 at 250 Hz)
                if len(decoded) >= 2500:
                    lead_data[lead_id] = decoded

        # We prefer Rhythm type waveforms
        wf_type = waveform_group.get("WaveformType", "")
        if wf_type == "Rhythm" and len(lead_data) >= 2:
            break

    if "I" not in lead_data or "II" not in lead_data:
        raise ValueError(f"Missing essential leads I or II in XML file: {xml_path}")

    # Standard Einthoven and Goldberger equations to recompute derived/augmented leads
    lead_data["III"] = lead_data["II"] - lead_data["I"]
    lead_data["aVR"] = -(lead_data["I"] + lead_data["II"]) / 2
    lead_data["aVL"] = lead_data["I"] - lead_data["III"] / 2
    lead_data["aVF"] = lead_data["II"] - lead_data["I"] / 2

    # Verify or resample to 5000 samples (500 Hz, 10s)
    sample_len = len(lead_data["I"])
    target_len = 5000
    
    # If the waveform is 250 Hz (2500 samples), resample to 500 Hz
    resample = sample_len != target_len
    
    ecg_array = np.zeros((target_len, 12), dtype=np.float32)
    for lead_name, idx in LEAD_INDEX.items():
        if lead_name in lead_data:
            arr = lead_data[lead_name]
            if resample:
                x_old = np.linspace(0, 1, len(arr))
                x_new = np.linspace(0, 1, target_len)
                arr = np.interp(x_new, x_old, arr)
            ecg_array[:, idx] = arr[:target_len]

    return ecg_array
