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

    - Encoder: `/gscratch/cardss/nksp2/ecgml/ml4h/model_zoo/ECG_PheWAS/encoder_median.h5`
    - Classifier bundle: `/gscratch/cardss/nksp2/daklagwats/exp_1/lasso_logreg_bundle.joblib`

    You can provide local copies of these files and point the CLI to them using `--encoder_path` and `--bundle_path`.

- For reproducible installs, a `requirements.txt` is provided in the repo; optionally generate a `uv.lock` using `uv lock` if you use `uv` for environment management.

---

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
