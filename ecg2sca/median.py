import logging
import numpy as np
import biosppy.signals.ecg

log = logging.getLogger("ecg2sca.median")


def stretch_ecg(x: np.ndarray, n: int = 0):
    """
    Stretch an ECG lead signal to a target BPM using R-peak detection.
    Reproduces the exact logic from ml4h/tensormap/ukb/ecg.py.
    """
    out = biosppy.signals.ecg.ecg(x.copy(), sampling_rate=500, show=False)
    # Heart rate may be missing if signal is too short or flat; default to 60 BPM
    try:
        hr = out["heart_rate"].mean() if hasattr(out, "_fields") else out[-1].mean()
    except Exception:
        log.warning("Unable to compute heart rate; defaulting to 60 BPM.")
        hr = 60.0
    t = np.arange(len(x))
    if n == 0 or hr == 0:
        tp = np.arange(len(x))
    else:
        tp = np.arange(len(x)) * n / hr
    stretched = np.interp(tp, t, x)
    out2 = biosppy.signals.ecg.ecg(stretched, show=False)
    rpeaks = out2["rpeaks"] if hasattr(out2, "_fields") else out2[2]
    return stretched, rpeaks


def make_biosspy_median(ecg_array: np.ndarray, channel_map: dict,
                        median_size: int = 600, bpm: int = 0) -> np.ndarray:
    """
    Generate median beat waveform from a 10-second ECG signal.
    Reproduces the exact logic from ml4h/tensormap/ukb/ecg.py.
    """
    medians = np.zeros((median_size, len(channel_map)))
    for lead, col_idx in channel_map.items():
        try:
            stretched, peaks = stretch_ecg(ecg_array[:, col_idx], bpm)

            waves = []
            for j, p0 in enumerate(peaks[:-2]):
                p1 = peaks[j + 1]
                middle = (p0 + p1) // 2
                if middle + median_size <= len(stretched):
                    waves.append(stretched[middle : middle + median_size])

            if len(waves) > 0:
                waves = np.array(waves)
                medians[:, col_idx] = np.median(waves, axis=0)
            else:
                log.warning(f"No valid beats detected for lead {lead}; using zeros.")
        except Exception as e:
            log.warning(f"Error computing median for lead {lead}: {e}; using zeros.")

    return medians
