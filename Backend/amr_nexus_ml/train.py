import sys
import joblib
from pathlib import Path
import pandas as pd
import numpy as np
import click
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
import xgboost as xgb
from sklearn.ensemble import IsolationForest
import shap
import warnings
warnings.filterwarnings('ignore')

from src.core.config import settings
from src.utils.logger import logger

try:
    import mlflow
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    logger.warning("MLflow not installed. Experiment tracking disabled.")

FRONTEND_FEATURES = [
    'sector', 'sub_sector', 'pathogen_code', 'specimen_type',
    'county', 'antibiotic_class', 'test_method', 'sample_month',
    'prior_antibiotic_exposure'
]

COLUMN_MAPPING = {
    'pathogen': 'pathogen_code',
    'antibiotic': 'antibiotic_class',
    'prior_antibiotic_use': 'prior_antibiotic_exposure',
    'facility': 'facility',
    'sample_type': 'specimen_type',
    'month': 'sample_month',
}


class DataLoader:
    @staticmethod
    def from_csv(file_path: str = None, target_col: str = None, threshold: float = None, limit: int = None, encoding: str = None):
        if file_path is None:
            file_path = settings.DATA_FILE_PATH
        logger.info(f"Loading data from: {file_path}")

        df = None

        try:
            df = pd.read_excel(file_path, engine='openpyxl')
            logger.info("Successfully read as Excel file.")
        except Exception as e:
            logger.warning(f"Failed to read as Excel: {e}. Trying CSV...")
            encodings = [encoding] if encoding else ['utf-8', 'latin-1', 'cp1252', 'utf-8-sig']
            delimiters = [',', ';', '\t', '|']
            last_error = None
            for enc in encodings:
                for delim in delimiters:
                    try:
                        df = pd.read_csv(
                            file_path,
                            encoding=enc,
                            delimiter=delim,
                            engine='python',
                            on_bad_lines='skip',
                            quotechar='"',
                            quoting=1
                        )
                        if df is not None and not df.empty:
                            logger.info(f"Successfully read CSV with encoding: {enc}, delimiter: {repr(delim)}")
                            break
                    except Exception as e:
                        last_error = e
                        continue
                if df is not None and not df.empty:
                    break

        if df is None or df.empty:
            raise ValueError(f"Could not read file with any method. Last error: {last_error}")

        logger.info(f"Loaded {len(df)} records.")
        if limit:
            df = df.head(limit)
            logger.info(f"Limited to {len(df)} records.")
        if df.empty:
            raise ValueError("File is empty or not found.")

        df.rename(columns=COLUMN_MAPPING, inplace=True)

        columns_to_keep = FRONTEND_FEATURES + ['classification', 'resistance_percent', 'mdr_flag']
        available_columns = [c for c in columns_to_keep if c in df.columns]
        df = df[available_columns]

        if target_col is None:
            if 'mdr_flag' in df.columns:
                target_col = 'mdr_flag'
                logger.info("Using 'mdr_flag' as target column.")
            elif 'classification' in df.columns:
                target_col = 'classification'
                logger.info("Using 'classification' as target column.")
            elif 'resistance_percent' in df.columns:
                target_col = 'resistance_percent'
                logger.info("Using 'resistance_percent' as target column.")
            else:
                raise KeyError("No suitable target column found. Please specify with --target-col.")

        if target_col not in df.columns:
            raise KeyError(f"Target column '{target_col}' not found. Available: {list(df.columns)}")

        if df[target_col].dtype == 'object':
            positive_keywords = ['resistant', 'mdr', 'positive', 'yes', '1']
            def map_to_binary(val):
                if isinstance(val, str):
                    val_lower = val.lower()
                    if any(kw in val_lower for kw in positive_keywords):
                        return 1
                    else:
                        return 0
                return int(val) if pd.notna(val) else 0
            df[target_col] = df[target_col].apply(map_to_binary)
            logger.info(f"Converted '{target_col}' to binary.")
        elif df[target_col].dtype in ['float64', 'int64']:
            if threshold is None:
                threshold = df[target_col].median()
                logger.info(f"No threshold provided. Using median={threshold} as cutoff.")
            df[target_col] = (df[target_col] > threshold).astype(int)
            logger.info(f"Binarized '{target_col}' with threshold={threshold}.")

        return df, target_col


class PreprocessorBuilder:
    @staticmethod
    def build(df: pd.DataFrame, target_col: str) -> ColumnTransformer:
        X = df.drop(columns=[target_col])
        features = [f for f in FRONTEND_FEATURES if f in X.columns]
        X = X[features]

        numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = X.select_dtypes(include=['object', 'category']).columns.tolist()

        numeric_transformer = Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())
        ])

        categorical_transformer = Pipeline([
            ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
            ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
        ])

        preprocessor = ColumnTransformer([
            ('num', numeric_transformer, numeric_cols) if numeric_cols else ('num', 'passthrough', []),
            ('cat', categorical_transformer, categorical_cols) if categorical_cols else ('cat', 'passthrough', [])
        ])

        return preprocessor


class ModelTrainer:
    @staticmethod
    def train_xgboost_default(X_train, y_train, X_val, y_val):
        logger.info("Training XGBoost with default parameters...")
        model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=1.0,
            early_stopping_rounds=10,
            eval_metric='logloss',
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
        return model, {}

    @staticmethod
    def train_isolation_forest(X_train_numeric, contamination=0.05):
        logger.info("Training Isolation Forest...")
        model = IsolationForest(contamination=contamination, random_state=42)
        model.fit(X_train_numeric)
        return model

    @staticmethod
    def build_shap_explainer(model, X_sample):
        logger.info("Building SHAP explainer...")
        return shap.TreeExplainer(model)


class ArtifactSaver:
    @staticmethod
    def save_all(model, anomaly_model, preprocessor, feature_names, numeric_indices, shap_explainer):
        model_dir = Path(settings.MODEL_DIR)
        model_dir.mkdir(parents=True, exist_ok=True)

        joblib.dump(model, model_dir / 'mdr_xgb.pkl')
        joblib.dump(anomaly_model, model_dir / 'anomaly_iso.pkl')
        joblib.dump(preprocessor, model_dir / 'preprocessor.pkl')
        joblib.dump(feature_names, model_dir / 'feature_names.pkl')
        joblib.dump(numeric_indices, model_dir / 'numeric_indices.pkl')
        joblib.dump(shap_explainer, model_dir / 'shap_explainer.pkl')

        logger.info(f"All artifacts saved to {model_dir}")


def run_pipeline(csv_path: str = None, target_col: str = None, threshold: float = None, limit: int = None, split_by_time: bool = False, encoding: str = None):
    mlflow_enabled = MLFLOW_AVAILABLE
    if mlflow_enabled:
        try:
            mlflow.set_experiment("amr_mdr_classifier")
            mlflow.start_run()
            logger.info("MLflow tracking active.")
        except Exception as e:
            logger.warning(f"MLflow start failed: {e}. Continuing without tracking.")
            mlflow_enabled = False

    logger.info("Starting AMR model training pipeline...")

    df, target_col = DataLoader.from_csv(
        file_path=csv_path,
        target_col=target_col,
        threshold=threshold,
        limit=limit,
        encoding=encoding
    )

    feature_cols = [f for f in FRONTEND_FEATURES if f in df.columns]
    df = df[feature_cols + [target_col]]

    X = df.drop(columns=[target_col])
    y = df[target_col].astype(int)

    if split_by_time and 'created_at' in df.columns:
        df_sorted = df.sort_values('created_at')
        split_idx = int(0.8 * len(df_sorted))
        X_train = X.iloc[:split_idx]
        X_val = X.iloc[split_idx:]
        y_train = y.iloc[:split_idx]
        y_val = y.iloc[split_idx:]
    else:
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

    preprocessor = PreprocessorBuilder.build(df, target_col=target_col)
    preprocessor.fit(X_train)

    X_train_processed = preprocessor.transform(X_train)
    X_val_processed = preprocessor.transform(X_val)

    xgb_model, _ = ModelTrainer.train_xgboost_default(
        X_train_processed, y_train, X_val_processed, y_val
    )

    y_pred = xgb_model.predict(X_val_processed)
    y_proba = xgb_model.predict_proba(X_val_processed)[:, 1]
    roc_auc = roc_auc_score(y_val, y_proba)

    logger.info(f"Validation ROC-AUC: {roc_auc:.4f}")
    logger.info("\n" + classification_report(y_val, y_pred))

    if mlflow_enabled:
        mlflow.log_metric("roc_auc", roc_auc)
        mlflow.log_params(xgb_model.get_params())

    shap_explainer = ModelTrainer.build_shap_explainer(xgb_model, X_train_processed[:100])

    feature_names = list(preprocessor.get_feature_names_out())
    numeric_cols = X_train.select_dtypes(include=[np.number]).columns.tolist()
    numeric_indices = [i for i, name in enumerate(feature_names) if any(col in name for col in numeric_cols)]

    
    if len(numeric_indices) == 0:
        logger.warning("No numeric features found. Using all features for Isolation Forest.")
        if hasattr(X_train_processed, "toarray"):
            X_train_numeric = X_train_processed.toarray()
        else:
            X_train_numeric = X_train_processed
    else:
        X_train_numeric = X_train_processed[:, numeric_indices]

    iso_model = ModelTrainer.train_isolation_forest(X_train_numeric)

    ArtifactSaver.save_all(
        xgb_model, iso_model, preprocessor,
        feature_names, numeric_indices, shap_explainer
    )

    if mlflow_enabled:
        mlflow.end_run()

    logger.info("Training pipeline completed successfully.")


@click.command()
@click.option('--csv-path', type=str, default=None, help='Path to CSV file (defaults to DATA_FILE_PATH in .env).')
@click.option('--target-col', type=str, default=None, help='Name of the target column. If not set, auto-detects.')
@click.option('--threshold', type=float, default=None, help='Threshold for numeric target columns.')
@click.option('--limit', type=int, default=None, help='Limit records for debugging.')
@click.option('--split-by-time', is_flag=True, help='Split data chronologically.')
@click.option('--encoding', type=str, default=None, help='CSV encoding. If not set, auto-detects.')
def cli(csv_path, target_col, threshold, limit, split_by_time, encoding):
    try:
        run_pipeline(csv_path=csv_path, target_col=target_col, threshold=threshold, limit=limit, split_by_time=split_by_time, encoding=encoding)
    except Exception as e:
        logger.exception(f"Pipeline failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    cli()