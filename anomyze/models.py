"""
Model loading and management for Anomyze.

Handles:
- Device detection (MPS, CUDA, CPU)
- Model loading with caching
- Pipeline creation
"""

from typing import Tuple, Optional, Any
import torch
from transformers import pipeline

from anomyze.config import get_settings, Settings


def get_device(settings: Optional[Settings] = None) -> Tuple[str, str]:
    """
    Detect the best available device for inference.

    Returns:
        Tuple of (device_name, device_description)
    """
    if settings is None:
        settings = get_settings()

    # Allow override via settings
    if settings.device:
        device = settings.device
        if device == "mps":
            return "mps", "Apple Silicon GPU (MPS) [configured]"
        elif device == "cuda":
            return "cuda", "CUDA GPU [configured]"
        else:
            return "cpu", "CPU [configured]"

    # Auto-detect
    if torch.backends.mps.is_available():
        return "mps", "Apple Silicon GPU (MPS)"
    elif torch.cuda.is_available():
        return "cuda", "CUDA GPU"
    else:
        return "cpu", "CPU"


class ModelManager:
    """Manages model loading and caching."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self._pii_pipeline = None
        self._org_pipeline = None
        self._mlm_pipeline = None
        self._device = None
        self._device_name = None

    @property
    def device(self) -> str:
        if self._device is None:
            self._device, self._device_name = get_device(self.settings)
        return self._device

    @property
    def device_name(self) -> str:
        if self._device_name is None:
            self._device, self._device_name = get_device(self.settings)
        return self._device_name

    def load_pii_pipeline(self, verbose: bool = True) -> Any:
        """Load the PII detection pipeline."""
        if self._pii_pipeline is None:
            if verbose:
                print(f"Loading PII model...")
            self._pii_pipeline = pipeline(
                "token-classification",
                model=self.settings.pii_model,
                aggregation_strategy="simple",
                device=self.device
            )
        return self._pii_pipeline

    def load_org_pipeline(self, verbose: bool = True) -> Any:
        """Load the organization/NER detection pipeline."""
        if self._org_pipeline is None:
            if verbose:
                print(f"Loading NER model...")
            self._org_pipeline = pipeline(
                "token-classification",
                model=self.settings.org_model,
                aggregation_strategy="simple",
                device=self.device
            )
        return self._org_pipeline

    def load_mlm_pipeline(self, verbose: bool = True) -> Any:
        """Load the masked language model pipeline for anomaly detection."""
        if self._mlm_pipeline is None:
            if verbose:
                print(f"Loading anomaly detection model...")
            self._mlm_pipeline = pipeline(
                "fill-mask",
                model=self.settings.mlm_model,
                device=self.device,
                top_k=50
            )
        return self._mlm_pipeline

    def load_all(self, verbose: bool = True) -> Tuple[Any, Any, Any]:
        """Load all three pipelines."""
        pii = self.load_pii_pipeline(verbose)
        org = self.load_org_pipeline(verbose)
        mlm = self.load_mlm_pipeline(verbose)
        if verbose:
            print("All models loaded.\n")
        return pii, org, mlm

    def is_loaded(self) -> bool:
        """Check if all models are loaded."""
        return all([
            self._pii_pipeline is not None,
            self._org_pipeline is not None,
            self._mlm_pipeline is not None,
        ])


# Global model manager instance
_model_manager: Optional[ModelManager] = None


def get_model_manager(settings: Optional[Settings] = None) -> ModelManager:
    """Get the global model manager instance."""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager(settings)
    return _model_manager


def load_models(
    device: Optional[str] = None,
    verbose: bool = True,
    settings: Optional[Settings] = None
) -> Tuple[Any, Any, Any]:
    """
    Load all detection models.

    Args:
        device: Device to use (auto-detected if None)
        verbose: Print loading progress
        settings: Settings instance (uses global if None)

    Returns:
        Tuple of (pii_pipeline, org_pipeline, mlm_pipeline)
    """
    if settings is None:
        settings = get_settings()

    if device:
        settings.device = device

    manager = get_model_manager(settings)

    if verbose:
        print(f"Device: {manager.device_name}\n")

    return manager.load_all(verbose)
