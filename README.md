# ECG2SCA

**ECG2SCA** is a lightweight, installable Python CLI that predicts Sudden Cardiac Arrest (SCA) risk from GE MUSE XML files or raw 12‑lead CSV waveforms. It bundles the VAE encoder, feature extraction, and a calibrated logistic‑regression classifier from Surbhi's SCA study.

---

## 🚀 Quick start (one‑liner)

```bash
# 1️⃣ Create a fresh virtual environment (Python >= 3.8)
python3 -m venv ecg2sca_env
source ecg2sca_env/bin/activate

# 2️⃣ Install UV (optional but recommended for reproducible lock file)
pip install uv

# 3️⃣ Install the package from this repository (editable mode for development) 
#    If you have cloned the repo already, run from the repo root:
uv sync               # resolves dependencies from uv.lock (creates a venv automatically)
uv run ecg2sca --help # shows the usage
```

If you prefer classic pip:

```bash
pip install -e /path/to/ecg2sca_pkg   # installs the CLI entry point `ecg2sca`
```

---

## 🐣 Beginner Quickstart (step‑by‑step)

If you're new to this repo and want a minimal, copy‑paste set of commands that will get you from cloning to a working prediction, follow these exact steps.

1) Clone the repository and fetch LFS objects

```bash
git clone https://github.com/niteeshkcl-create/ecg2sca.git
cd ecg2sca
git lfs install         # one‑time per account on this machine
git lfs pull            # fetch large model and binary files tracked by LFS
```

2) Create and activate a Python virtual environment (Python 3.9 recommended)

```bash
python3.9 -m venv ecg2sca_env
source ecg2sca_env/bin/activate
python -m pip install --upgrade pip
```

3) Install dependencies and the package

```bash
pip install -r requirements.txt
pip install -e .
```

4) Verify models are present (repo‑local defaults)

```bash
ls -l models/encoder_median.h5 models/lasso_logreg_bundle.joblib
# If the files are absent, re-run `git lfs pull` or contact the repo owner
```

5) Run an example prediction (single XML)

```bash
ecg2sca --input_file /path/to/example.xml --output_csv /tmp/predictions.csv
# or use the included binary (no Python deps):
./bin/ecg2sca --input_file /path/to/example.xml --output_csv /tmp/predictions.csv
```

6) Inspect the output

```bash
head -n 5 /tmp/predictions.csv
```

If you see CSV with the columns described in this README, the pipeline worked.

---


## 📖 Usage examples

### Process a single XML file
```bash
ecg2sca \
    --input_file /path/to/file.xml \
    --output_csv /tmp/pred.xml.csv
```

### Process a directory of XML files (or mixed XML/CSV)
```bash
ecg2sca \
    --input_dir /path/to/folder \
    --output_csv predictions.csv
```

### Process a single CSV waveform file
```bash
ecg2sca \
    --input_file /path/to/waveform.csv \
    --output_csv /tmp/pred.csv
```

### Process a batch of CSV files
```bash
ecg2sca \
    --input_dir /path/to/csv_folder \
    --output_csv csv_predictions.csv
```

---

## 🛠️ What the CLI does under the hood
1. **Loads the VAE encoder** (`encoder_median.h5`).
2. **Computes a median beat** for each lead using `biosppy`.  If the signal is too short to estimate a heart‑rate, a fallback of 60 BPM is used and a warning is emitted.
3. **Extracts time‑domain ECG features** (heart‑rate, QTc, PR interval, etc.). Missing clinical values are filled with sensible defaults (HR = 70, QTc = 420 ms, …).
4. **Applies a calibrated logistic‑regression model** (`lasso_logreg_bundle.joblib`).
5. **Outputs a CSV** with columns:
   - `filename`
   - `patient_id`
   - `acquisition_datetime`
   - `sca_risk_score`
   - `flagged_<threshold_name>` for each of the four default thresholds.

---

## 📦 Dependency lock file (`uv.lock`)
We use **uv** to generate a reproducible lock file. The lock file is committed in the repo so that any lab member can install the exact same dependency versions with:

```bash
uv sync   # creates a virtual environment and installs everything from uv.lock
```

If you need to update dependencies, run:

```bash
uv add <package>   # e.g., uv add pandas==1.5.0
uv lock            # refresh the lock file
```

---

## 🏗️ Stand‑alone binary (Git LFS)

The compiled `ecg2sca` executable is stored in the repository via **Git LFS** at `bin/ecg2sca`. After cloning, ensure Git LFS is installed and run:

```bash
git lfs install                # one‑time per user
git pull                       # fetch the binary
chmod +x bin/ecg2sca

---

## Deployment notes

- CPU vs GPU: The CLI runs on CPU by default and is fully functional (but slower). If a GPU is available, install GPU-enabled TensorFlow and run on GPU for much faster inference. Example (recommended for GPU machines):

    ```bash
    pip install tensorflow==2.12.1 tensorflow-addons==0.19.0
    ```

    If you prefer CPU-only usage (works on any machine):

    ```bash
    pip install tensorflow==2.12.1 tensorflow-addons==0.19.0
    ```

- Model weights: The repository does not contain the trained VAE encoder or classifier weights by default. In our environment the models used during testing were located at:

 - Model weights: You can now store the trained VAE encoder and classifier bundle inside the repository under the `models/` directory. When present, the CLI will default to these paths:

     - Encoder: `models/encoder_median.h5`
     - Classifier bundle: `models/lasso_logreg_bundle.joblib`

     If you prefer to use models from another location, pass `--encoder_path` and `--bundle_path` to the CLI.

- For reproducible installs, a `requirements.txt` is provided in the repo; optionally generate a `uv.lock` using `uv lock` if you use `uv` for environment management.

### Required versions (recommended)

To avoid Keras/TensorFlow deserialization and CPU incompatibility issues, we recommend the following versions for most users:

```
Python==3.9.*
tensorflow==2.12.1
tensorflow-addons==0.19.0   # optional but recommended (Mish activation)
pandas==1.5.*
scikit-learn==1.2.*
biosppy
xmltodict
joblib
uv    # optional, for lockfiles
```

If you're using macOS/Apple Silicon, install TensorFlow following the official instructions for your platform (or use `conda` to simplify binary compatibility).

---

## Quick Install & Usage (for any computer)

These steps make the package easy to use on another machine. Two main options are provided: install from source (recommended for development) or use the included standalone binary (recommended for simple deployments).

1) Install from source (editable)

```bash
# create & activate virtualenv (Python >=3.9 recommended)
python3.9 -m venv ecg2sca_env
source ecg2sca_env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

2) Use the prebuilt binary (no Python dependencies)

```bash
# After cloning the repository and fetching LFS objects
git lfs install
git pull
chmod +x bin/ecg2sca
./bin/ecg2sca --help
```

## Models included in this repository

The repository contains a `models/` directory with the VAE encoder and classifier bundle tracked via Git LFS:

- `models/encoder_median.h5` — VAE encoder (256-dim embedding)
- `models/lasso_logreg_bundle.joblib` — classifier bundle (scaler, feature names, thresholds)

By default the CLI will use these repo-local paths. To explicitly point to model files elsewhere, pass `--encoder_path` and `--bundle_path`.

## Example: Run prediction on a single XML file (using repo-local weights)

```bash
# using the installed Python package
ecg2sca --input_file /path/to/file.xml --output_csv /tmp/predictions.csv

# or using the bundled binary
./bin/ecg2sca --input_file /path/to/file.xml --output_csv /tmp/predictions.csv
```

If you want to explicitly reference the repo-local models, use:

```bash
ecg2sca \
    --input_file /path/to/file.xml \
    --output_csv /tmp/predictions.csv \
    --encoder_path models/encoder_median.h5 \
    --bundle_path models/lasso_logreg_bundle.joblib
```

## Example: Run predictions on a directory of XML files

```bash
ecg2sca --input_dir /path/to/xml_folder --output_csv /tmp/predictions_batch.csv
```

## Expected runtimes

- CPU (single core): ~10–25 minutes per 12-lead XML file on a typical lab CPU (median observed ≈ 15–20 minutes). This includes median-beat extraction + encoder inference.
- GPU: ~1–5 seconds per file (depends on GPU model). If a CUDA-capable GPU is present and you install the GPU build of TensorFlow, inference will be orders of magnitude faster.

If you expect to process large batches, run jobs in parallel or use a GPU-enabled machine.

## Git LFS and large files

The models and the compiled binary are large files and are tracked with Git LFS in this repository. After cloning, fetch LFS objects with:

```bash
git lfs install
git pull
```

If you plan to add/replace model weights or the binary, use Git LFS to track the file types (e.g., `*.h5`, `*.joblib`, and binary `bin/ecg2sca`).

## Troubleshooting

- If you see `Illegal instruction` or similar errors when importing TensorFlow, rebuild the virtual environment on that host and install the TensorFlow wheel compatible with the CPU/GPU of that machine.
- If the models are missing after cloning, ensure you fetched LFS objects (`git lfs pull`) and that your Git client has LFS enabled.

Common error: "Could not interpret activation function identifier: Addons>mish"

- Cause: The saved encoder HDF5 references the Mish activation from `tensorflow_addons`. If `tensorflow_addons` is not installed or the Keras/TensorFlow versions mismatch, deserialization can fail with this message.
- Quick fixes:

```bash
# Preferred: install the matching addon package
pip install tensorflow-addons==0.19.0

# Use the CLI self-test to inspect your environment without loading the full encoder
ecg2sca --self_test

# To attempt loading the encoder (may be slow) during self-test
ecg2sca --self_test --run_encoder_load
```

Notes: The code includes a fallback that maps `Addons>mish` to a local Mish implementation when `tensorflow_addons` is absent. Installing the addon with the recommended versions is still the most robust solution.

Other TF/Keras incompatibilities

- If you see errors related to Keras 3 or TensorFlow 2.20 when loading `.h5` models, use `tensorflow==2.12.1` as the safest version for deserializing legacy HDF5 model artifacts included here.

./bin/ecg2sca --help
```

If you prefer to build the binary yourself, you can still use PyInstaller:

```bash
# 1️⃣ Activate the virtual environment where ECG2SCA is installed
source ecg2sca_env/bin/activate

# 2️⃣ Install PyInstaller (if not already)
pip install pyinstaller

# 3️⃣ Build the executable
pyinstaller --onefile -n ecg2sca run_ecg2sca.py
# The binary will appear in ./dist/ecg2sca
```

The LFS‑tracked binary is the recommended way for distribution, as it avoids the GitHub file‑size limit and provides an immediate ready‑to‑run `ecg2sca`.

---

## 🤝 Contributing
Feel free to open merge requests on the internal GitLab repo.  Please keep the lock file up‑to‑date and follow the existing coding style.


Happy predicting! 🎉
