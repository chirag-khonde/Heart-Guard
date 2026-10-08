"""HeartGuard Model Registry (Phase 16).

Provides safe, cached model loading with:
  - SHA-256 integrity verification against the model manifest.
  - Streamlit-compatible caching to prevent duplicate loads.
  - Safe fallback error reporting (no tracebacks to UI).
  - Version tracking and health reporting.

Usage:
    from src.ml.model_registry import ModelRegistry
    registry = ModelRegistry.get()
    model = registry.get_model("random_forest")
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Optional

from config.settings import MODEL_DIRECTORY
from src.utils.logger import get_logger

logger = get_logger(__name__)

_MANIFEST_PATH = MODEL_DIRECTORY / "model_manifest.json"
_METADATA_PATH = MODEL_DIRECTORY / "model_metadata.json"

_REQUIRED_MODELS = [
    "random_forest",
    "preprocessor",
]

_OPTIONAL_MODELS = [
    "xgboost",
    "neural_network",
    "logistic_regression",
    "feature_names",
]


def _compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_manifest() -> dict[str, Any]:
    """Load the model manifest file."""
    if not _MANIFEST_PATH.exists():
        logger.warning("Model manifest not found at %s", _MANIFEST_PATH)
        return {}
    try:
        with open(_MANIFEST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.error("Failed to parse model manifest: %s", type(exc).__name__)
        return {}


class ModelArtifact:
    """Represents a loaded model artifact with metadata."""

    def __init__(
        self,
        name: str,
        artifact: Any,
        version: str,
        file_path: Path,
        integrity_verified: bool,
    ) -> None:
        self.name = name
        self.artifact = artifact
        self.version = version
        self.file_path = file_path
        self.integrity_verified = integrity_verified

    def __repr__(self) -> str:
        return f"<ModelArtifact name={self.name!r} version={self.version!r} verified={self.integrity_verified}>"


class ModelIntegrityError(Exception):
    """Raised when model artifact checksum verification fails."""


class ModelRegistry:
    """Singleton model registry with integrity checking and caching."""

    _instance: Optional["ModelRegistry"] = None

    def __init__(self) -> None:
        self._artifacts: dict[str, ModelArtifact] = {}
        self._manifest: dict[str, Any] = _load_manifest()
        self._load_errors: dict[str, str] = {}
        self._loaded = False

    @classmethod
    def get(cls) -> "ModelRegistry":
        """Return the singleton registry, loading all models if not yet loaded."""
        if cls._instance is None:
            cls._instance = cls()
        if not cls._instance._loaded:
            cls._instance._load_all()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the registry (for testing). Do NOT call in production."""
        cls._instance = None

    def _load_all(self) -> None:
        """Load and verify all model artifacts."""
        import joblib

        manifest_models = self._manifest.get("models", {})
        model_files_to_load = {}

        # Discover all .pkl and .json model files
        for name, meta in manifest_models.items():
            fname = meta.get("file", "")
            fpath = MODEL_DIRECTORY / fname
            model_files_to_load[name] = (fpath, meta)

        for pkl in MODEL_DIRECTORY.glob("*.pkl"):
            name = pkl.stem
            if name not in model_files_to_load:
                model_files_to_load[name] = (pkl, {"version": "v1", "file": pkl.name})
        for jf in MODEL_DIRECTORY.glob("*.json"):
            name = jf.stem
            if name not in model_files_to_load and name != "model_manifest":
                model_files_to_load[name] = (jf, {"version": "v1", "file": jf.name})

        for name, (fpath, meta) in model_files_to_load.items():
            if not fpath.exists():
                msg = f"Model file not found: {fpath.name}"
                self._load_errors[name] = msg
                if name in _REQUIRED_MODELS:
                    logger.error("CRITICAL — required model missing: %s", fpath.name)
                else:
                    logger.warning("Optional model missing: %s", fpath.name)
                continue

            # Integrity check
            expected_sha = meta.get("sha256")
            try:
                if expected_sha:
                    actual_sha = _compute_sha256(fpath)
                    if actual_sha != expected_sha:
                        msg = f"Integrity check FAILED for {fpath.name}: expected {expected_sha[:12]}... got {actual_sha[:12]}..."
                        logger.error("Model integrity violation: %s", fpath.name)
                        self._load_errors[name] = msg
                        if name in _REQUIRED_MODELS:
                            raise ModelIntegrityError(msg)
                        continue
                    integrity_verified = True
                else:
                    integrity_verified = False
                    logger.warning("No checksum defined for model: %s", name)
            except ModelIntegrityError:
                raise
            except Exception as exc:
                logger.warning("Checksum computation failed for %s: %s", name, type(exc).__name__)
                integrity_verified = False

            # Load artifact
            try:
                if fpath.suffix == ".json":
                    with open(fpath, "r", encoding="utf-8") as f:
                        artifact = json.load(f)
                else:
                    artifact = joblib.load(str(fpath))

                self._artifacts[name] = ModelArtifact(
                    name=name,
                    artifact=artifact,
                    version=meta.get("version", "unknown"),
                    file_path=fpath,
                    integrity_verified=integrity_verified,
                )
                logger.info("Loaded model: %s v%s (verified=%s)", name, meta.get("version", "?"), integrity_verified)

            except Exception as exc:
                msg = f"Failed to load {fpath.name}: {type(exc).__name__}"
                logger.error("Model load error for %s: %s", name, type(exc).__name__)
                self._load_errors[name] = msg
                if name in _REQUIRED_MODELS:
                    logger.critical("Required model could not be loaded: %s", name)

        self._loaded = True
        logger.info(
            "ModelRegistry initialized: %d loaded, %d errors",
            len(self._artifacts),
            len(self._load_errors),
        )

    def get_model(self, name: str) -> Optional[Any]:
        """Return raw model artifact by name, or None if unavailable."""
        artifact = self._artifacts.get(name)
        return artifact.artifact if artifact else None

    def is_available(self, name: str) -> bool:
        """Check if a named model was successfully loaded."""
        return name in self._artifacts

    def get_health_status(self) -> dict[str, Any]:
        """Return a health summary of all models (no sensitive paths exposed)."""
        models_status = {}
        for name in list(self._artifacts.keys()) + list(self._load_errors.keys()):
            if name in self._artifacts:
                art = self._artifacts[name]
                models_status[name] = {
                    "status": "loaded",
                    "version": art.version,
                    "integrity_verified": art.integrity_verified,
                }
            else:
                models_status[name] = {
                    "status": "error",
                    "error": self._load_errors.get(name, "unknown"),
                }

        all_required_ok = all(
            self.is_available(m) for m in _REQUIRED_MODELS
        )
        return {
            "overall": "healthy" if all_required_ok else "degraded",
            "required_models_ok": all_required_ok,
            "loaded_count": len(self._artifacts),
            "error_count": len(self._load_errors),
            "models": models_status,
        }

    def get_versions(self) -> dict[str, str]:
        """Return name → version mapping for all loaded models."""
        return {
            name: art.version
            for name, art in self._artifacts.items()
        }


# ---------------------------------------------------------------------------
# Backward-compatible module-level functions
# These map the old API to the new singleton registry.
# ---------------------------------------------------------------------------

def load_model(name: str) -> Optional[Any]:
    """Load a model artifact by name (backward-compatible wrapper)."""
    registry = ModelRegistry.get()
    return registry.get_model(name)


def get_available_models() -> dict[str, bool]:
    """Return dict of model names and their availability status."""
    registry = ModelRegistry.get()
    all_names = list(registry._artifacts.keys()) + list(registry._load_errors.keys())
    return {name: registry.is_available(name) for name in all_names}


def get_best_model_name() -> str:
    """Return the name of the best-performing model from best_model.json."""
    best_model_path = MODEL_DIRECTORY.parent / "reports" / "best_model.json"
    try:
        if best_model_path.exists():
            with open(best_model_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("best_model", "logistic_regression")
    except Exception:
        pass
    return "logistic_regression"


def register_model(name: str, file_path: Any = None, artifact: Any = None, version: str = "v1") -> None:
    """Register a model in the registry (for training pipelines)."""
    registry = ModelRegistry.get()
    fpath = file_path if isinstance(file_path, Path) else (MODEL_DIRECTORY / f"{name}.pkl")
    art = artifact if artifact is not None else file_path
    registry._artifacts[name] = ModelArtifact(
        name=name,
        artifact=art,
        version=version,
        file_path=fpath,
        integrity_verified=False,
    )


def get_model_path(name: str) -> Optional[Path]:
    """Return the file path for a named model artifact."""
    registry = ModelRegistry.get()
    artifact = registry._artifacts.get(name)
    return artifact.file_path if artifact else None


def save_model(name: Any, artifact: Any = None, file_path: Path | None = None, version: str = "v1") -> None:
    """Save a model artifact to disk and register it (for training pipelines)."""
    import joblib
    from config.settings import MODEL_DIRECTORY

    if isinstance(name, str):
        model_name = name
        model_artifact = artifact
    else:
        # Called as save_model(model, name)
        model_name = str(artifact)
        model_artifact = name

    if file_path is None:
        file_path = MODEL_DIRECTORY / f"{model_name}.pkl"
    else:
        file_path = Path(file_path)

    file_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model_artifact, str(file_path))
    register_model(model_name, file_path, model_artifact, version)
