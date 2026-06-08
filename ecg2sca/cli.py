import os
import sys
import argparse
import logging
import warnings
import numpy as np
import pandas as pd

from .predict import (
    load_encoder,
    load_classifier,
    run_batch,
    run_batch_csv,
)

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
warnings.filterwarnings("ignore")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("ecg2sca")

DEFAULT_ENCODER_PATH = (
    "/gscratch/cardss/nksp2/ecgml/ml4h/model_zoo/ECG_PheWAS/encoder_median.h5"
)
DEFAULT_BUNDLE_PATH = (
    "/gscratch/cardss/nksp2/daklagwats/exp_1/lasso_logreg_bundle.joblib"
)


def main():
    parser = argparse.ArgumentParser(
        description="ECG2SCA: Predict SCA risk from GE MUSE XML or raw CSV ECG files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a directory of XMLs
  ecg2sca --input_dir /path/to/xmls --output_csv predictions.csv

  # Process a directory of CSV waveforms
  ecg2sca --input_dir /path/to/csvs --output_csv predictions.csv

  # Process a single file (XML or CSV)
  ecg2sca --input_file /path/to/file.xml --output_csv pred.csv
        """,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input_dir", type=str, help="Directory containing ECG files (XML or CSV)")
    group.add_argument("--input_file", type=str, help="Path to a single ECG file (XML or CSV)")

    parser.add_argument("--output_csv", type=str, required=True, help="Output CSV path for predictions")
    parser.add_argument("--encoder_path", type=str, default=DEFAULT_ENCODER_PATH, help="Path to encoder_median.h5")
    parser.add_argument("--bundle_path", type=str, default=DEFAULT_BUNDLE_PATH, help="Path to lasso_logreg_bundle.joblib")

    args = parser.parse_args()

    # Resolve file list
    if args.input_file:
        if not os.path.isfile(args.input_file):
            log.error(f"File not found: {args.input_file}")
            sys.exit(1)
        paths = [args.input_file]
    else:
        if not os.path.isdir(args.input_dir):
            log.error(f"Directory not found: {args.input_dir}")
            sys.exit(1)
        paths = sorted([
            os.path.join(args.input_dir, f)
            for f in os.listdir(args.input_dir)
            if f.lower().endswith(".xml") or f.lower().endswith(".csv")
        ])

    if not paths:
        log.error("No ECG XML or CSV files found.")
        sys.exit(1)

    log.info(f"Found {len(paths)} file(s) to process.")

    # Load models
    log.info("Loading VAE encoder …")
    encoder = load_encoder(args.encoder_path)
    log.info("Loading classifier bundle …")
    model, scaler, feature_names, thresholds = load_classifier(args.bundle_path)

    # Split by extension
    xml_paths = [p for p in paths if p.lower().endswith('.xml')]
    csv_paths = [p for p in paths if p.lower().endswith('.csv')]

    df_results = pd.DataFrame()
    if xml_paths:
        log.info(f"Running inference on {len(xml_paths)} XML file(s) …")
        df_xml = run_batch(xml_paths, encoder, model, scaler, feature_names, thresholds)
        df_results = pd.concat([df_results, df_xml], ignore_index=True)
    if csv_paths:
        log.info(f"Running inference on {len(csv_paths)} CSV file(s) …")
        df_csv = run_batch_csv(csv_paths, encoder, model, scaler, feature_names, thresholds)
        df_results = pd.concat([df_results, df_csv], ignore_index=True)

    # Save results
    output_dir = os.path.dirname(os.path.abspath(args.output_csv))
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    df_results.to_csv(args.output_csv, index=False)
    log.info(f"Results saved to {args.output_csv}")

    # Summary output
    print("\n" + "=" * 60)
    print("  ECG2SCA — Prediction Summary")
    print("=" * 60)
    print(f"  Total files processed : {len(df_results)}")
    print(f"  Successful predictions: {df_results['sca_risk_score'].notna().sum()}")
    print(f"  Failed predictions    : {df_results['sca_risk_score'].isna().sum()}")
    if df_results["sca_risk_score"].notna().any():
        print(f"\n  Risk score statistics:")
        print(f"    Mean : {df_results['sca_risk_score'].mean():.4f}")
        print(f"    Min  : {df_results['sca_risk_score'].min():.4f}")
        print(f"    Max  : {df_results['sca_risk_score'].max():.4f}")
        for thr_name, thr_val in thresholds.items():
            col = f"flagged_{thr_name.replace(' ', '_').lower()}"
            if col in df_results.columns:
                flagged = df_results[col].sum()
                print(f"\n  Threshold '{thr_name}' (≥{thr_val:.4f}): {flagged}/{len(df_results)} flagged")
    print("=" * 60)
