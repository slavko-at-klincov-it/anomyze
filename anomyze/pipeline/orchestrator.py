"""
Pipeline orchestrator for Anomyze.

Central coordinator for filtering KI-generated output. The AI tools
work internally with full data — Anomyze scans the output for PII
before it leaves the system.

Responsibilities:
1. Owns model lifecycle (ModelManager)
2. Runs preprocessing (encoding fixes)
3. Dispatches to the 3-stage detection pipeline (Regex → NER → Context)
4. Delegates to output channels for formatting
"""

import logging
import re
import subprocess
from dataclasses import dataclass
from typing import Any

import torch
from transformers import pipeline as hf_pipeline

from anomyze.config.settings import Settings, get_settings
from anomyze.pipeline import DetectedEntity
from anomyze.pipeline.context_layer import ContextLayer
from anomyze.pipeline.ensemble import merge_entities
from anomyze.pipeline.ner_layer import NERLayer
from anomyze.pipeline.regex_layer import RegexLayer

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Encoding fixes for common transcription software issues
# ---------------------------------------------------------------------------
ENCODING_REPLACEMENTS = {
    # German umlauts (various broken encodings)
    '\u2030': 'ä', '\u0160': 'ä',
    '\u00f7': 'ö',
    '\u00b8': 'ü', '\u00b3': 'ü',
    '\u0192': 'ä',
    '\ufb02': 'ß', '\ufb01': 'ß', '\u00a7': 'ß',
    '\u00d0': 'Ä', '\u2044': 'Ü',
    # Common OCR/transcription errors
    '\u00b4': "'", '\u0060': "'",
    '\u2014': '-', '\u2013': '-',
    '\u2026': '...',
    '\u201c': '"', '\u201d': '"',
    '\u2018': "'", '\u2019': "'",
    '\u00a0': ' ',   # Non-breaking space
    '\ufeff': '',    # BOM
}


def fix_encoding(text: str) -> str:
    """Fix common encoding issues from transcription software.

    Args:
        text: Text with potential encoding issues.

    Returns:
        Text with encoding issues fixed.
    """
    for wrong, correct in ENCODING_REPLACEMENTS.items():
        text = text.replace(wrong, correct)
    return text


# ---------------------------------------------------------------------------
# Device detection
# ---------------------------------------------------------------------------
def get_device(settings: Settings | None = None) -> tuple[str, str]:
    """Detect the best available device for inference.

    Priority: MPS (Apple Silicon) > CUDA (NVIDIA) > CPU.

    Args:
        settings: Settings with optional device override.

    Returns:
        Tuple of (device_name, device_description).
    """
    if settings is None:
        settings = get_settings()

    if settings.device:
        device = settings.device
        if device == "mps":
            return "mps", "Apple Silicon GPU (MPS) [configured]"
        elif device == "cuda":
            return "cuda", "CUDA GPU [configured]"
        else:
            return "cpu", "CPU [configured]"

    if torch.backends.mps.is_available():
        return "mps", "Apple Silicon GPU (MPS)"
    elif torch.cuda.is_available():
        return "cuda", "CUDA GPU"
    else:
        return "cpu", "CPU"


# ---------------------------------------------------------------------------
# Model management
# ---------------------------------------------------------------------------
class ModelManager:
    """Manages model loading and caching.

    Lazily loads HuggingFace pipelines on first access and caches them
    for subsequent calls. Supports PII, NER/ORG, and MLM models.
    """

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._pii_pipeline: Any = None
        self._org_pipeline: Any = None
        self._mlm_pipeline: Any = None
        self._gliner_model: Any = None
        self._device: str | None = None
        self._device_name: str | None = None

    def _ensure_device(self) -> None:
        if self._device is None:
            self._device, self._device_name = get_device(self.settings)

    @property
    def device(self) -> str:
        """Get the compute device (lazily detected)."""
        self._ensure_device()
        assert self._device is not None
        return self._device

    @property
    def device_name(self) -> str:
        """Get the human-readable device description."""
        self._ensure_device()
        assert self._device_name is not None
        return self._device_name

    def load_pii_pipeline(self, verbose: bool = True) -> Any:
        """Load the PII detection pipeline."""
        if self._pii_pipeline is None:
            if verbose:
                print("Loading PII model...")
            self._pii_pipeline = hf_pipeline(
                "token-classification",
                model=self.settings.pii_model,
                aggregation_strategy="simple",
                device=self.device,
            )
        return self._pii_pipeline

    def load_org_pipeline(self, verbose: bool = True) -> Any:
        """Load the organization/NER detection pipeline."""
        if self._org_pipeline is None:
            if verbose:
                print("Loading NER model...")
            self._org_pipeline = hf_pipeline(
                "token-classification",
                model=self.settings.org_model,
                aggregation_strategy="simple",
                device=self.device,
            )
        return self._org_pipeline

    def load_mlm_pipeline(self, verbose: bool = True) -> Any:
        """Load the masked language model pipeline for anomaly detection."""
        if self._mlm_pipeline is None:
            if verbose:
                print("Loading anomaly detection model...")
            self._mlm_pipeline = hf_pipeline(
                "fill-mask",
                model=self.settings.mlm_model,
                device=self.device,
                top_k=50,
            )
        return self._mlm_pipeline

    def load_gliner_model(self, verbose: bool = True) -> Any:
        """Load the GLiNER zero-shot NER model."""
        if self._gliner_model is None and self.settings.use_gliner:
            try:
                from gliner import GLiNER
                if verbose:
                    print("Loading GLiNER model...")
                self._gliner_model = GLiNER.from_pretrained(
                    self.settings.gliner_model
                )
            except ImportError:
                logger.warning("GLiNER not installed, skipping zero-shot NER")
            except Exception:
                logger.warning("Failed to load GLiNER model", exc_info=True)
        return self._gliner_model

    def load_all(self, verbose: bool = True) -> tuple[Any, Any, Any]:
        """Load all pipelines.

        Returns:
            Tuple of (pii_pipeline, org_pipeline, mlm_pipeline).
        """
        pii = self.load_pii_pipeline(verbose)
        org = self.load_org_pipeline(verbose)
        mlm = self.load_mlm_pipeline(verbose)
        if self.settings.use_gliner:
            self.load_gliner_model(verbose)
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
_model_manager: ModelManager | None = None


def get_model_manager(settings: Settings | None = None) -> ModelManager:
    """Get the global model manager instance."""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager(settings)
    return _model_manager


def load_models(
    device: str | None = None,
    verbose: bool = True,
    settings: Settings | None = None,
) -> tuple[Any, Any, Any]:
    """Load all detection models.

    Convenience function for backwards compatibility.

    Args:
        device: Device to use (auto-detected if None).
        verbose: Print loading progress.
        settings: Settings instance (uses global if None).

    Returns:
        Tuple of (pii_pipeline, org_pipeline, mlm_pipeline).
    """
    if settings is None:
        settings = get_settings()

    if device:
        settings.device = device

    manager = get_model_manager(settings)

    if verbose:
        print(f"Device: {manager.device_name}\n")

    return manager.load_all(verbose)


# ---------------------------------------------------------------------------
# Text smoothing (optional post-processing)
# ---------------------------------------------------------------------------
def smooth_text_with_ollama(
    text: str,
    model: str = "qwen2.5:14b",
    timeout: int = 120,
) -> str:
    """Smooth/rewrite text using local Ollama LLM.

    Protects placeholders like [ORG_1] during processing.

    Args:
        text: Text with placeholders to smooth.
        model: Ollama model name.
        timeout: Timeout in seconds for Ollama call.

    Returns:
        Smoothed text with placeholders preserved.
    """
    # Step 1: Protect placeholders by replacing with unique tokens
    placeholder_pattern = r'\[([A-Z_]+_\d+)\]'
    placeholders = re.findall(placeholder_pattern, text)
    protected_text = text

    placeholder_map = {}
    for i, ph in enumerate(set(placeholders)):
        token = f"\u00a7\u00a7\u00a7PLACEHOLDER{i}\u00a7\u00a7\u00a7"
        placeholder_map[token] = f"[{ph}]"
        protected_text = protected_text.replace(f"[{ph}]", token)

    # Step 2: Create prompt for smoothing
    prompt = (
        "Du bist ein Texteditor. Glätte den folgenden deutschen Text:\n\n"
        "REGELN:\n"
        "- Entferne Füllwörter (ähm, also, halt, ja, mhm, etc.)\n"
        "- Korrigiere Grammatik und mache Sätze flüssiger\n"
        "- Behalte die Bedeutung und alle Fakten exakt bei\n"
        "- WICHTIG: Alle §§§PLACEHOLDER...§§§ Tokens MÜSSEN exakt unverändert bleiben!\n"
        "- Entferne keine Informationen\n"
        "- Behalte Zeitstempel und Sprechernamen\n\n"
        f"TEXT:\n{protected_text}\n\n"
        "GEGLÄTTETER TEXT:"
    )

    # Step 3: Call Ollama
    try:
        result = subprocess.run(
            ["ollama", "run", model, prompt],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if result.returncode != 0:
            logger.warning("Ollama error: %s", result.stderr)
            return text

        smoothed = result.stdout.strip()

        # Step 4: Restore placeholders
        for token, original in placeholder_map.items():
            smoothed = smoothed.replace(token, original)

        return smoothed

    except subprocess.TimeoutExpired:
        logger.warning("Ollama timeout - Text zu lang oder Model zu langsam")
        return text
    except FileNotFoundError:
        logger.warning("Ollama nicht gefunden. Bitte installieren: https://ollama.ai")
        return text


# ---------------------------------------------------------------------------
# AnonymizeResult (backwards compatibility)
# ---------------------------------------------------------------------------
@dataclass
class AnonymizeResult:
    """Result of an anonymization operation.

    Attributes:
        text: The anonymized text with placeholders.
        mapping: Placeholder-to-original-value mapping.
        entities: List of all detected entities.
        original_text: The original input text before anonymization.
    """

    text: str
    mapping: dict[str, str]
    entities: list[DetectedEntity]
    original_text: str = ""

    @property
    def entity_count(self) -> int:
        """Total number of detected entities."""
        return len(self.entities)

    @property
    def unique_entity_count(self) -> int:
        """Number of unique entities (by placeholder)."""
        return len(self.mapping)


# ---------------------------------------------------------------------------
# Pipeline Orchestrator
# ---------------------------------------------------------------------------
class PipelineOrchestrator:
    """Central coordinator for the 3-stage anonymization pipeline.

    Manages the full lifecycle: model loading → preprocessing →
    detection (Regex → NER → Context) → channel formatting.
    """

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.model_manager = ModelManager(self.settings)
        self.regex_layer = RegexLayer()
        self.ner_layer = NERLayer()
        self.context_layer = ContextLayer()
        self._gliner_layer: Any = None

    def load_models(self, verbose: bool = True) -> tuple[Any, Any, Any]:
        """Load all detection models.

        Args:
            verbose: Print loading progress.

        Returns:
            Tuple of (pii_pipeline, org_pipeline, mlm_pipeline).
        """
        if verbose:
            print(f"Device: {self.model_manager.device_name}\n")
        return self.model_manager.load_all(verbose)

    def detect(self, text: str) -> tuple[str, list[DetectedEntity]]:
        """Run all 3 pipeline stages and return detected entities.

        This method runs preprocessing and all detection layers but
        does NOT apply any channel formatting.

        Args:
            text: The input text to analyze.

        Returns:
            Tuple of (preprocessed_text, sorted_entities).
        """
        # Preprocessing: fix encoding issues
        if self.settings.fix_encoding:
            text = fix_encoding(text)

        raw_entities: list[DetectedEntity] = []

        # Stage 1: Regex-based detection
        if self.settings.use_regex_fallback:
            raw_entities.extend(self.regex_layer.process(text))

        # Stage 2: NER model detection
        pii = self.model_manager.load_pii_pipeline(verbose=False)
        org = self.model_manager.load_org_pipeline(verbose=False)
        raw_entities.extend(
            self.ner_layer.process(text, pii, org, self.settings)
        )

        # Stage 2b: GLiNER zero-shot NER
        if self.settings.use_gliner:
            from anomyze.pipeline.gliner_layer import GLiNERLayer
            if self._gliner_layer is None:
                self._gliner_layer = GLiNERLayer()
            gliner_model = self.model_manager.load_gliner_model(verbose=False)
            raw_entities.extend(
                self._gliner_layer.process(text, gliner_model, self.settings)
            )

        # Ensemble: merge overlapping entities from all sources
        entities = merge_entities(raw_entities, text)

        # Stage 3: Context/anomaly detection (uses merged entities)
        if self.settings.use_anomaly_detection:
            mlm = self.model_manager.load_mlm_pipeline(verbose=False)
            context_entities = self.context_layer.process(
                text, entities, mlm, self.settings
            )
            entities.extend(context_entities)

        # Sort by position
        entities.sort(key=lambda e: e.start)
        return text, entities

    def process(self, text: str, channel: str = "govgpt") -> Any:
        """Full pipeline: detect entities and format via output channel.

        Args:
            text: The input text to anonymize.
            channel: Output channel name ("govgpt", "ifg", "kapa").

        Returns:
            Channel-specific result object.

        Raises:
            ValueError: If the channel name is unknown.
        """
        from anomyze.channels import GovGPTChannel, IFGChannel, KAPAChannel
        from anomyze.channels.base import BaseChannel

        original_text = text
        text, entities = self.detect(text)

        channels: dict[str, type[BaseChannel]] = {
            "govgpt": GovGPTChannel,
            "ifg": IFGChannel,
            "kapa": KAPAChannel,
        }

        channel_cls = channels.get(channel)
        if channel_cls is None:
            raise ValueError(
                f"Unknown channel: '{channel}'. Must be one of: {', '.join(channels)}"
            )

        channel_impl = channel_cls()  # type: ignore[abstract]
        return channel_impl.format_output(text, entities, self.settings, original_text)


# ---------------------------------------------------------------------------
# Backwards-compatible anonymize() function
# ---------------------------------------------------------------------------
def anonymize(
    text: str,
    pii_pipeline: Any,
    org_pipeline: Any,
    mlm_pipeline: Any,
    settings: Settings | None = None,
) -> AnonymizeResult:
    """Main anonymization function combining all detection methods.

    This function maintains backwards compatibility with v1.x.
    For new code, prefer using PipelineOrchestrator directly.

    Args:
        text: Text to anonymize.
        pii_pipeline: PII detection pipeline.
        org_pipeline: Organization/NER detection pipeline.
        mlm_pipeline: MLM pipeline for anomaly detection.
        settings: Settings instance (uses global if None).

    Returns:
        AnonymizeResult with anonymized text, mapping, and entities.
    """
    if settings is None:
        settings = get_settings()

    original_text = text

    # Preprocessing
    if settings.fix_encoding:
        text = fix_encoding(text)

    raw_entities: list[DetectedEntity] = []

    # Stage 1: Regex
    if settings.use_regex_fallback:
        regex_layer = RegexLayer()
        raw_entities.extend(regex_layer.process(text))

    # Stage 2: NER
    ner_layer = NERLayer()
    raw_entities.extend(
        ner_layer.process(text, pii_pipeline, org_pipeline, settings)
    )

    # Ensemble: merge overlapping entities
    all_entities = merge_entities(raw_entities, text)

    # Stage 3: Context
    if settings.use_anomaly_detection:
        context_layer = ContextLayer()
        context_entities = context_layer.process(text, all_entities, mlm_pipeline, settings)
        all_entities.extend(context_entities)

    if not all_entities:
        return AnonymizeResult(
            text=text,
            mapping={},
            entities=[],
            original_text=original_text,
        )

    # Use GovGPT channel for backwards-compatible output
    from anomyze.channels.govgpt import GovGPTChannel
    channel = GovGPTChannel()
    result = channel.format_output(text, all_entities, settings, original_text)
    return AnonymizeResult(
        text=result.text,
        mapping=result.mapping,
        entities=result.entities,
        original_text=result.original_text,
    )
