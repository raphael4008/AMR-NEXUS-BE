"""
ml_ai/experiment_tracking.py — MLflow Experiment Tracking & Model Registry
=============================================================================
Production-grade wrapper around MLflow for the AMR-Nexus One Health
Antimicrobial Resistance Intelligence Platform.

Provides:
    - ``MLflowTracker``: Full lifecycle management — experiments, runs,
      artifact logging, model registration, and model loading.
    - ``@track_experiment``: Decorator that auto-instruments training
      functions with parameter/metric/model logging.
    - ``generate_run_name`` / ``format_metrics_table``: Helpers for
      consistent naming and human-readable metric reports.

**Graceful degradation**: If MLflow is not installed the module exposes
``HAS_MLFLOW = False`` and every public method becomes a logged no-op.
The platform will never crash due to a missing tracking dependency — it
simply loses provenance capture until MLflow is provisioned.

Design notes:
    * Targets low-resource, unreliable East African infrastructure.
    * All operations tolerate network timeouts and fall back to warnings.
    * Config sourced from ``ml_ai.config.get_ml_config().mlflow``.

Authors: Gavinta Tipape & Jesse Ng'eno — AMR-Nexus AI/ML Team
"""

from __future__ import annotations

import functools
import logging
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Generator, List, Optional, TypeVar, cast

from ml_ai.config import get_ml_config

# ── Standard logger ──────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)

# ── Graceful MLflow import ───────────────────────────────────────────────────
try:
    import mlflow
    import mlflow.sklearn
    import mlflow.xgboost
    from mlflow.tracking import MlflowClient
    from mlflow.entities import ViewType

    HAS_MLFLOW = True
    logger.info("MLflow %s loaded — experiment tracking enabled.", mlflow.__version__)
except ImportError:
    HAS_MLFLOW = False
    mlflow = None  # type: ignore[assignment]
    MlflowClient = None  # type: ignore[assignment,misc]
    ViewType = None  # type: ignore[assignment,misc]
    logger.warning(
        "MLflow is NOT installed.  All tracking calls will be no-ops.  "
        "Install with:  pip install mlflow"
    )

# ── Type helpers ─────────────────────────────────────────────────────────────
F = TypeVar("F", bound=Callable[..., Any])


# ═══════════════════════════════════════════════════════════════════════════════
# Helper functions
# ═══════════════════════════════════════════════════════════════════════════════

def generate_run_name(model_type: str, dataset_version: Optional[str] = None) -> str:
    """Generate a deterministic, sortable MLflow run name.

    Args:
        model_type: Short identifier for the model, e.g. ``"xgb"``,
            ``"iforest"``, ``"prophet"``.
        dataset_version: Optional dataset version tag.  When *None* the
            current UTC date is used (``vYYYYMMDD``).

    Returns:
        A run name like ``"anomaly-detection-xgb-v20260607"``.
    """
    cfg = get_ml_config()
    experiment_prefix = cfg.mlflow.experiment_name.split("-")[-1]  # e.g. "detection"
    if dataset_version is None:
        dataset_version = f"v{datetime.now(timezone.utc).strftime('%Y%m%d')}"
    return f"{experiment_prefix}-{model_type}-{dataset_version}"


def format_metrics_table(metrics: Dict[str, float]) -> str:
    """Pretty-print a metrics dictionary as an aligned ASCII table.

    Args:
        metrics: Mapping of metric name → numeric value.

    Returns:
        Multi-line string suitable for logging or console output.

    Example::

        ┌──────────────────────┬────────────┐
        │ Metric               │ Value      │
        ├──────────────────────┼────────────┤
        │ accuracy             │     0.9412 │
        │ f1_score             │     0.8837 │
        └──────────────────────┴────────────┘
    """
    if not metrics:
        return "(no metrics to display)"

    name_width = max(len(k) for k in metrics) + 2
    val_width = 12

    top    = f"┌{'─' * name_width}┬{'─' * val_width}┐"
    header = f"│ {'Metric':<{name_width - 2}} │ {'Value':>{val_width - 2}} │"
    sep    = f"├{'─' * name_width}┼{'─' * val_width}┤"
    bottom = f"└{'─' * name_width}┴{'─' * val_width}┘"

    rows: list[str] = []
    for name, value in sorted(metrics.items()):
        formatted = f"{value:>{val_width - 2}.4f}" if isinstance(value, float) else f"{value:>{val_width - 2}}"
        rows.append(f"│ {name:<{name_width - 2}} │ {formatted} │")

    return "\n".join([top, header, sep, *rows, bottom])


# ═══════════════════════════════════════════════════════════════════════════════
# MLflowTracker
# ═══════════════════════════════════════════════════════════════════════════════

class MLflowTracker:
    """Full-lifecycle MLflow experiment tracking and model registry wrapper.

    All public methods degrade gracefully when ``HAS_MLFLOW`` is *False*:
    they emit a warning and return a sensible default instead of raising.

    Usage::

        tracker = MLflowTracker()
        with tracker.start_run("training-run-001"):
            tracker.log_params({"max_depth": 6, "lr": 0.1})
            model = train(...)
            tracker.log_metrics({"f1": 0.88, "auc": 0.93})
            tracker.log_model(model, "anomaly-detector", feature_cols)

    Args:
        experiment_name: MLflow experiment name.  Defaults to config value.
        tracking_uri: MLflow tracking server URI.  Defaults to config value
            (local ``mlruns`` directory for single-node deployments).
    """

    def __init__(
        self,
        experiment_name: Optional[str] = None,
        tracking_uri: Optional[str] = None,
    ) -> None:
        cfg = get_ml_config()
        self._experiment_name = experiment_name or cfg.mlflow.experiment_name
        self._tracking_uri = tracking_uri or cfg.mlflow.tracking_uri
        self._active_run: Any = None  # mlflow.ActiveRun | None
        self._client: Any = None      # MlflowClient | None
        self._experiment_id: Optional[str] = None

        if not HAS_MLFLOW:
            logger.warning(
                "MLflowTracker initialised WITHOUT MLflow — all calls are no-ops."
            )
            return

        try:
            mlflow.set_tracking_uri(self._tracking_uri)
            self._client = MlflowClient(tracking_uri=self._tracking_uri)

            # Create or retrieve experiment
            experiment = mlflow.get_experiment_by_name(self._experiment_name)
            if experiment is None:
                self._experiment_id = mlflow.create_experiment(
                    self._experiment_name,
                    artifact_location=cfg.mlflow.artifact_location,
                )
                logger.info(
                    "Created MLflow experiment '%s' (id=%s).",
                    self._experiment_name,
                    self._experiment_id,
                )
            else:
                self._experiment_id = experiment.experiment_id
                logger.info(
                    "Using existing MLflow experiment '%s' (id=%s).",
                    self._experiment_name,
                    self._experiment_id,
                )
        except Exception:
            logger.exception(
                "Failed to initialise MLflow tracking at '%s'.  "
                "Continuing in degraded mode.",
                self._tracking_uri,
            )
            self._client = None
            self._experiment_id = None

    # ── Run lifecycle ────────────────────────────────────────────────────

    @contextmanager
    def start_run(
        self,
        run_name: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> Generator[Any, None, None]:
        """Context manager that opens (and auto-closes) an MLflow run.

        Args:
            run_name: Human-readable run name.  Auto-generated if *None*.
            tags: Optional key/value tags attached to the run.

        Yields:
            The ``mlflow.ActiveRun`` object, or *None* when MLflow is absent.
        """
        if not HAS_MLFLOW or self._experiment_id is None:
            logger.warning("start_run skipped — MLflow unavailable.")
            yield None
            return

        run_name = run_name or generate_run_name("run")
        merged_tags = {
            "platform": "amr-nexus",
            "environment": "production",
        }
        if tags:
            merged_tags.update(tags)

        try:
            self._active_run = mlflow.start_run(
                experiment_id=self._experiment_id,
                run_name=run_name,
                tags=merged_tags,
            )
            logger.info("MLflow run started: %s (id=%s).", run_name, self._active_run.info.run_id)
            yield self._active_run
        except Exception:
            logger.exception("Error during MLflow run '%s'.", run_name)
            yield None
        finally:
            self.end_run()

    def end_run(self) -> None:
        """End the currently active MLflow run, if any."""
        if not HAS_MLFLOW:
            return
        try:
            if self._active_run is not None:
                mlflow.end_run()
                logger.info(
                    "MLflow run ended: %s.",
                    self._active_run.info.run_id,
                )
                self._active_run = None
        except Exception:
            logger.exception("Error ending MLflow run.")
            self._active_run = None

    # ── Logging methods ──────────────────────────────────────────────────

    def log_params(self, params: Dict[str, Any]) -> None:
        """Log a dictionary of hyper-parameters to the active run.

        Args:
            params: Mapping of parameter name → value.  Values are
                automatically cast to strings for MLflow compatibility.
        """
        if not HAS_MLFLOW or self._active_run is None:
            logger.warning("log_params skipped — no active MLflow run.")
            return
        try:
            # MLflow has a 100-param batch limit; chunk if needed.
            items = list(params.items())
            batch_size = 100
            for i in range(0, len(items), batch_size):
                batch = {k: str(v) for k, v in items[i : i + batch_size]}
                mlflow.log_params(batch)
            logger.debug("Logged %d params to MLflow.", len(params))
        except Exception:
            logger.exception("Failed to log params to MLflow.")

    def log_metrics(
        self,
        metrics: Dict[str, float],
        step: Optional[int] = None,
    ) -> None:
        """Log evaluation metrics to the active run.

        Args:
            metrics: Mapping of metric name → numeric value.
            step: Optional training step / epoch number.
        """
        if not HAS_MLFLOW or self._active_run is None:
            logger.warning("log_metrics skipped — no active MLflow run.")
            return
        try:
            for name, value in metrics.items():
                mlflow.log_metric(name, float(value), step=step)
            logger.debug("Logged %d metrics to MLflow.", len(metrics))
        except Exception:
            logger.exception("Failed to log metrics to MLflow.")

    def log_model(
        self,
        model: Any,
        model_name: str,
        feature_columns: Optional[List[str]] = None,
    ) -> None:
        """Log a trained scikit-learn or XGBoost model as an artifact.

        The method inspects the model type to pick the correct MLflow
        flavour (``mlflow.sklearn`` vs ``mlflow.xgboost``).

        Args:
            model: A fitted estimator (sklearn or xgboost).
            model_name: Artifact path / display name for the model.
            feature_columns: Optional list of feature names used during
                training — stored as a run tag for reproducibility.
        """
        if not HAS_MLFLOW or self._active_run is None:
            logger.warning("log_model skipped — no active MLflow run.")
            return
        try:
            # Determine the correct MLflow flavour
            model_class = type(model).__module__
            if "xgboost" in model_class:
                mlflow.xgboost.log_model(model, artifact_path=model_name)
                logger.info("Logged XGBoost model '%s' to MLflow.", model_name)
            else:
                # Default to sklearn flavour for sklearn, IsolationForest, etc.
                mlflow.sklearn.log_model(model, artifact_path=model_name)
                logger.info("Logged sklearn model '%s' to MLflow.", model_name)

            if feature_columns:
                mlflow.set_tag(
                    "feature_columns",
                    ",".join(feature_columns[:200]),  # Tag value cap
                )
        except Exception:
            logger.exception("Failed to log model '%s' to MLflow.", model_name)

    def log_artifact(self, filepath: str) -> None:
        """Log an arbitrary file artifact to the active run.

        Args:
            filepath: Absolute or relative path to the file to log.
        """
        if not HAS_MLFLOW or self._active_run is None:
            logger.warning("log_artifact skipped — no active MLflow run.")
            return
        try:
            mlflow.log_artifact(filepath)
            logger.debug("Logged artifact '%s' to MLflow.", filepath)
        except Exception:
            logger.exception("Failed to log artifact '%s'.", filepath)

    def log_dataset_info(
        self,
        n_records: int,
        date_range: tuple[str, str],
        pathogens: List[str],
        counties: List[str],
    ) -> None:
        """Record dataset provenance as run parameters.

        This captures *what data* went into a training run so that auditors
        and researchers can reproduce or inspect results.

        Args:
            n_records: Total number of AMR records used.
            date_range: ``(start_date, end_date)`` strings in ISO-8601.
            pathogens: List of pathogen names included.
            counties: List of Kenya county codes or names included.
        """
        if not HAS_MLFLOW or self._active_run is None:
            logger.warning("log_dataset_info skipped — no active MLflow run.")
            return
        try:
            provenance = {
                "dataset.n_records": str(n_records),
                "dataset.date_start": date_range[0],
                "dataset.date_end": date_range[1],
                "dataset.n_pathogens": str(len(pathogens)),
                "dataset.pathogens": ",".join(pathogens[:50]),
                "dataset.n_counties": str(len(counties)),
                "dataset.counties": ",".join(counties[:60]),
            }
            mlflow.log_params(provenance)
            logger.info(
                "Dataset provenance logged: %d records, %d pathogens, %d counties.",
                n_records,
                len(pathogens),
                len(counties),
            )
        except Exception:
            logger.exception("Failed to log dataset info to MLflow.")

    # ── Model Registry ───────────────────────────────────────────────────

    def register_model(
        self,
        run_id: str,
        model_name: str,
        stage: str = "Staging",
    ) -> Optional[Any]:
        """Register a logged model artifact in the MLflow Model Registry.

        Args:
            run_id: The MLflow run ID that contains the model artifact.
            model_name: Registered model name in the registry.
            stage: Target stage — ``"Staging"`` or ``"Production"``.

        Returns:
            The ``ModelVersion`` object, or *None* on failure / no MLflow.
        """
        if not HAS_MLFLOW or self._client is None:
            logger.warning("register_model skipped — MLflow unavailable.")
            return None
        try:
            model_uri = f"runs:/{run_id}/{model_name}"
            result = mlflow.register_model(model_uri, model_name)
            version = result.version

            # Transition to requested stage
            self._client.transition_model_version_stage(
                name=model_name,
                version=version,
                stage=stage,
                archive_existing_versions=(stage == "Production"),
            )
            logger.info(
                "Registered model '%s' v%s → stage '%s'.",
                model_name,
                version,
                stage,
            )
            return result
        except Exception:
            logger.exception(
                "Failed to register model '%s' from run %s.",
                model_name,
                run_id,
            )
            return None

    # ── Model Loading ────────────────────────────────────────────────────

    def load_production_model(self, model_name: str) -> Any:
        """Load the current Production-stage model from the registry.

        Args:
            model_name: Registered model name.

        Returns:
            The deserialised model object, or *None* if loading fails.
        """
        if not HAS_MLFLOW:
            logger.warning("load_production_model skipped — MLflow unavailable.")
            return None
        try:
            model_uri = f"models:/{model_name}/Production"
            model = mlflow.pyfunc.load_model(model_uri)
            logger.info("Loaded Production model '%s'.", model_name)
            return model
        except Exception:
            logger.exception(
                "Failed to load Production model '%s'.  "
                "Verify a Production-stage version exists.",
                model_name,
            )
            return None

    def load_model_by_version(self, model_name: str, version: int) -> Any:
        """Load a specific version of a registered model.

        Args:
            model_name: Registered model name.
            version: Integer model version number.

        Returns:
            The deserialised model object, or *None* if loading fails.
        """
        if not HAS_MLFLOW:
            logger.warning("load_model_by_version skipped — MLflow unavailable.")
            return None
        try:
            model_uri = f"models:/{model_name}/{version}"
            model = mlflow.pyfunc.load_model(model_uri)
            logger.info("Loaded model '%s' version %d.", model_name, version)
            return model
        except Exception:
            logger.exception(
                "Failed to load model '%s' version %d.",
                model_name,
                version,
            )
            return None

    # ── Query helpers ────────────────────────────────────────────────────

    def get_best_run(
        self,
        metric_name: str,
        maximize: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Find the run with the best value for a given metric.

        Args:
            metric_name: The metric to optimise (e.g. ``"f1_score"``).
            maximize: If *True* the highest value wins; otherwise lowest.

        Returns:
            A dict with ``run_id``, ``metric_value``, ``params``, and
            ``tags``; or *None* if no qualifying run exists.
        """
        if not HAS_MLFLOW or self._client is None or self._experiment_id is None:
            logger.warning("get_best_run skipped — MLflow unavailable.")
            return None
        try:
            order = "DESC" if maximize else "ASC"
            runs = self._client.search_runs(
                experiment_ids=[self._experiment_id],
                order_by=[f"metrics.{metric_name} {order}"],
                max_results=1,
                run_view_type=ViewType.ACTIVE_ONLY,
            )
            if not runs:
                logger.info(
                    "No runs found with metric '%s' in experiment '%s'.",
                    metric_name,
                    self._experiment_name,
                )
                return None

            best = runs[0]
            result: Dict[str, Any] = {
                "run_id": best.info.run_id,
                "run_name": best.info.run_name,
                "metric_value": best.data.metrics.get(metric_name),
                "params": dict(best.data.params),
                "tags": dict(best.data.tags),
                "start_time": best.info.start_time,
            }
            logger.info(
                "Best run for '%s' (%s): %s = %s.",
                metric_name,
                "max" if maximize else "min",
                best.info.run_id,
                result["metric_value"],
            )
            return result
        except Exception:
            logger.exception(
                "Failed to query best run for metric '%s'.",
                metric_name,
            )
            return None


# ═══════════════════════════════════════════════════════════════════════════════
# Decorator: @track_experiment
# ═══════════════════════════════════════════════════════════════════════════════

def track_experiment(
    experiment_name: Optional[str] = None,
    tracking_uri: Optional[str] = None,
    run_name: Optional[str] = None,
    log_model_artifact: bool = True,
) -> Callable[[F], F]:
    """Decorator that auto-instruments a training function with MLflow logging.

    The decorated function **must** return a dictionary with (at minimum)
    the following keys:

    - ``"model"``: the trained model object
    - ``"metrics"``: ``dict[str, float]`` of evaluation metrics
    - ``"params"``: ``dict[str, Any]`` of hyper-parameters
    - ``"feature_columns"`` *(optional)*: ``list[str]`` of feature names
    - ``"model_name"`` *(optional)*: artifact path, defaults to
      ``"model"``

    Example::

        @track_experiment(experiment_name="anomaly-detection")
        def train_anomaly_model(X, y, **kwargs):
            model = XGBClassifier(**kwargs)
            model.fit(X, y)
            return {
                "model": model,
                "params": kwargs,
                "metrics": {"f1": 0.88, "auc": 0.93},
                "feature_columns": list(X.columns),
            }

    Args:
        experiment_name: MLflow experiment.  Defaults to config value.
        tracking_uri: MLflow tracking URI.  Defaults to config value.
        run_name: Explicit run name; auto-generated when *None*.
        log_model_artifact: Whether to log the model binary. Set to
            *False* for quick validation runs.

    Returns:
        The wrapped function (transparent — same signature & return value).
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            tracker = MLflowTracker(
                experiment_name=experiment_name,
                tracking_uri=tracking_uri,
            )

            effective_run_name = run_name or generate_run_name(
                func.__name__
            )

            with tracker.start_run(
                run_name=effective_run_name,
                tags={
                    "training_function": func.__qualname__,
                    "invocation_time": datetime.now(timezone.utc).isoformat(),
                },
            ):
                start_ts = time.monotonic()
                result = func(*args, **kwargs)
                elapsed = time.monotonic() - start_ts

                if not isinstance(result, dict):
                    logger.warning(
                        "@track_experiment: '%s' did not return a dict.  "
                        "Skipping auto-logging.",
                        func.__name__,
                    )
                    return result

                # ── Log parameters ───────────────────────────────────
                params = result.get("params", {})
                if params:
                    tracker.log_params(params)

                # ── Log metrics ──────────────────────────────────────
                metrics = result.get("metrics", {})
                metrics["training_duration_seconds"] = round(elapsed, 3)
                if metrics:
                    tracker.log_metrics(metrics)
                    logger.info(
                        "Training complete (%s):\n%s",
                        func.__name__,
                        format_metrics_table(metrics),
                    )

                # ── Log model ────────────────────────────────────────
                model = result.get("model")
                model_name = result.get("model_name", "model")
                feature_columns = result.get("feature_columns")
                if model is not None and log_model_artifact:
                    tracker.log_model(model, model_name, feature_columns)

            return result

        return cast(F, wrapper)

    return decorator
