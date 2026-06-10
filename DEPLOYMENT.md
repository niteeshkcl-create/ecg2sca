# Deployment & Environment Setup

This document explains how to create a reproducible environment, build the standalone binary, and run ECG2SCA on any machine.

## Recommended environment (tested)
- Python 3.9
- TensorFlow 2.12.1
- tensorflow-addons 0.19.0
- numpy, pandas, xmltodict, joblib, scikit-learn, biosppy, peakutils, h5py

## Quick setup (CPU)

```bash
# create venv
python3.9 -m venv ecg2sca_env
source ecg2sca_env/bin/activate
pip install --upgrade pip
# install from pinned requirements
pip install -r requirements.txt
# install editable package
pip install -e .
```

## Optional: GPU setup
If you have a CUDA-capable GPU, install the appropriate GPU TensorFlow package compatible with your CUDA/toolkit.

```bash
# example (may vary by system)
pip install tensorflow==2.12.1 tensorflow-addons==0.19.0
```

## Build standalone binary (optional)

```bash
# activate same venv used above
source ecg2sca_env/bin/activate
cd /path/to/ecg2sca
bash build_binary.sh
# output: ./dist/ecg2sca
```

Notes:
- If you plan to distribute a binary, add it to Git repository using Git LFS and track the file in `.gitattributes`.

## Model weights
The repository does not contain the trained VAE encoder or classifier bundle by default. You can either:

1. Copy the model files into the repository (recommended: use Git LFS for large files), or
2. Place them at a central filesystem path and provide those paths to the CLI via `--encoder_path` and `--bundle_path`.

Example usage:

```bash
ecg2sca --input_file /path/to/file.xml --output_csv /tmp/pred.csv \
  --encoder_path /path/to/encoder_median.h5 \
  --bundle_path /path/to/lasso_logreg_bundle.joblib
```

## Dependency lock
If you use `uv` to manage reproducible environments, generate a lock file:

```bash
pip install uv
uv lock
# commit uv.lock to the repository
```

If you don't use `uv`, `requirements.txt` is provided for a reproducible pip-based install.
