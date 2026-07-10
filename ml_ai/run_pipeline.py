"""
ml_ai/run_pipeline.py -- End-to-End ML Pipeline Validation Script
================================================================
Demonstrates the complete ML pipeline from synthetic data generation
through anomaly detection with SHAP explainability and MLflow tracking.

Usage:
    cd AMR-NEXUS-BE
    python -m ml_ai.run_pipeline [--n-records 1000] [--train] [--validate-only]

This script:
    1. Generates synthetic AMR records
    2. Validates against literature benchmarks
    3. Engineers features from records
    4. Trains the anomaly detector (XGBoost + Isolation Forest)
    5. Runs inference and generates SHAP explanations
    6. Logs everything to MLflow
"""

from __future__ import annotations

import argparse
import io
import json
import logging
import os
import sys
from datetime import date
from pathlib import Path

# Fix Windows console encoding -- force UTF-8 output
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd

# -- Local imports -------------------------------------------------------------
from ml_ai.config import get_ml_config
from ml_ai.synthetic_data.generator import SyntheticAMRGenerator
from ml_ai.synthetic_data.validation_suite import SyntheticDataValidator
from ml_ai.feature_engineering import FeatureEngineer
from ml_ai.anomaly_detection import AnomalyDetector
from ml_ai.experiment_tracking import MLflowTracker

# -- Logging -------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("ml_ai.run_pipeline")


def main() -> None:
    """Run the full AMR ML pipeline."""
    parser = argparse.ArgumentParser(description="AMR-Nexus ML Pipeline Runner")
    parser.add_argument(
        "--n-records", type=int, default=1000,
        help="Number of synthetic records to generate (default: 1000)",
    )
    parser.add_argument(
        "--validate-only", action="store_true",
        help="Only generate and validate data, skip model training",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for reproducibility",
    )
    parser.add_argument(
        "--output-dir", type=str, default="ml_artifacts",
        help="Directory for model artifacts",
    )
    args = parser.parse_args()

    config = get_ml_config()
    separator = "=" * 72

    print(f"\n{separator}")
    print("  AMR-Nexus AI/ML Pipeline -- End-to-End Validation")
    print(f"  Stack: Scikit-learn + XGBoost + Prophet + SHAP + MLflow")
    print(f"  Records: {args.n_records:,} | Seed: {args.seed}")
    print(f"{separator}\n")

    # -- Step 1: Generate Synthetic Data ---------------------------------------
    print("[STEP 1] Generating synthetic AMR records...")
    generator = SyntheticAMRGenerator(
        start_date=date(2024, 1, 1),
        end_date=date(2025, 12, 31),
        seed=args.seed,
    )
    records = generator.generate_records(
        n_records=args.n_records,
        inject_outbreaks=True,
        incomplete_reporting_rate=0.15,
    )
    print(f"  [OK] Generated {len(records):,} records")

    # Print sample record
    if records:
        print(f"\n  Sample record:")
        sample = records[0]
        for key, val in sample.items():
            print(f"    {key}: {val}")

    # Quick stats
    df_raw = pd.DataFrame(records)
    print(f"\n  Pathogens: {df_raw['pathogen_name'].nunique()}")
    print(f"  Counties: {df_raw['county'].nunique()}")
    print(f"  Sectors: {df_raw['sector'].value_counts().to_dict()}")
    print(f"  SIR Distribution: {df_raw['result_value'].value_counts().to_dict()}")

    genomic_count = df_raw["sequencing_platform"].notna().sum()
    print(f"  Genomic metadata: {genomic_count} ({genomic_count/len(records):.1%})")

    # -- Step 2: Validate Against Literature -----------------------------------
    print(f"\n{separator}")
    print("[STEP 2] Validating against Kenyan AMR literature...")
    validator = SyntheticDataValidator()
    validation_report = validator.validate_all(records)
    validator.print_report(validation_report)

    if not validation_report.overall_pass:
        logger.warning(
            "Validation FAILED -- data may not be suitable for training. "
            "Review failures above."
        )
    else:
        print("  [OK] All quality gates PASSED -- data approved for training.\n")

    if args.validate_only:
        print("  [--validate-only] Skipping model training.")
        return

    # -- Step 3: Feature Engineering -------------------------------------------
    print(f"{separator}")
    print("[STEP 3] Engineering features...")
    feature_engineer = FeatureEngineer()
    feature_df = feature_engineer.build_training_features(
        records, (date(2024, 1, 1), date(2025, 12, 31))
    )
    print(f"  [OK] Feature DataFrame: {feature_df.shape[0]} rows x {feature_df.shape[1]} columns")

    feature_cols = FeatureEngineer.get_feature_columns(feature_df)
    print(f"  Numeric feature columns ({len(feature_cols)}):")
    for col in feature_cols[:10]:
        print(f"    - {col}")
    if len(feature_cols) > 10:
        print(f"    ... and {len(feature_cols) - 10} more")

    # -- Step 4: Train Anomaly Detector ----------------------------------------
    print(f"\n{separator}")
    print("[STEP 4] Training anomaly detector (XGBoost + Isolation Forest)...")

    tracker = MLflowTracker(experiment_name="amr-nexus-pipeline-validation")
    detector = AnomalyDetector()

    metrics = None
    results = []
    anomalies = []

    with tracker.start_run(run_name="pipeline-validation-run"):
        try:
            metrics = detector.train(feature_df)
            print(f"  [OK] Training complete:")
            print(f"     F1 Score:   {metrics.f1:.4f}")
            print(f"     Precision:  {metrics.precision:.4f}")
            print(f"     Recall:     {metrics.recall:.4f}")
            print(f"     AUC-ROC:    {metrics.auc_roc:.4f}")
            print(f"     Support:    {metrics.support}")

            # Log to MLflow
            tracker.log_params({
                "n_records": args.n_records,
                "n_features": len(feature_cols),
                "seed": args.seed,
                "validation_passed": str(validation_report.overall_pass),
            })
            tracker.log_metrics({
                "f1": metrics.f1,
                "precision": metrics.precision,
                "recall": metrics.recall,
                "auc_roc": metrics.auc_roc,
            })
        except Exception as e:
            logger.error("Training failed: %s", e, exc_info=True)
            print(f"  [FAIL] Training failed: {e}")
            return

        # -- Step 5: Run Inference + SHAP ------------------------------------------
        print(f"\n{separator}")
        print("[STEP 5] Running anomaly detection with SHAP explanations...")

        results = detector.predict(feature_df)
        anomalies = [r for r in results if r.is_anomaly]

        print(f"  Total predictions: {len(results)}")
        print(f"  Anomalies flagged: {len(anomalies)}")
        if results:
            print(f"  Anomaly rate: {len(anomalies)/len(results):.1%}")

        if anomalies:
            print(f"\n  Top 5 anomalies:")
            for i, a in enumerate(sorted(anomalies, key=lambda x: x.score, reverse=True)[:5]):
                print(
                    f"    #{i+1} | Score: {a.score:.3f} | {a.pathogen} vs {a.drug_class} "
                    f"in {a.county} | Rate: {a.resistance_rate:.2%} (baseline: {a.baseline_rate:.2%})"
                )
                if a.contributing_features:
                    print(f"         Drivers: {[f.get('feature', 'N/A') for f in a.contributing_features[:3]]}")

    # -- Step 6: Save Model ----------------------------------------------------
    print(f"\n{separator}")
    print("[STEP 6] Saving model artifacts...")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    saved_path = detector.save(output_dir)
    print(f"  [OK] Model saved to: {saved_path}")

    # -- Summary ---------------------------------------------------------------
    print(f"\n{separator}")
    print("  PIPELINE COMPLETE")
    print(f"  [{'OK' if validation_report.overall_pass else 'WARN'}] Data Quality: {'PASSED' if validation_report.overall_pass else 'FAILED'}")
    if metrics:
        print(f"  [OK] Model F1: {metrics.f1:.4f}")
    print(f"  [OK] Anomalies: {len(anomalies)} flagged from {len(results)} predictions")
    print(f"  [OK] MLflow: Experiment logged to '{tracker._experiment_name}'")
    print(f"  [OK] Artifacts: {output_dir.resolve()}")
    print(f"{separator}\n")


if __name__ == "__main__":
    main()

