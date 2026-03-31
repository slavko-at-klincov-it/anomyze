"""
Mapping store for placeholder-to-original-value management.

Provides in-memory storage with optional JSON file persistence
for managing the reversible mapping between placeholders and
their original PII values.

Used by GovGPT and KAPA channels. The IFG channel never stores
mappings (irreversible by design).
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class MappingStore:
    """Store and retrieve placeholder-to-original-value mappings.

    Supports in-memory storage (default) and optional JSON file
    persistence for batch processing and API scenarios.

    Attributes:
        persist_path: Optional path for JSON file persistence.
            When set, mappings are saved to disk on every store() call.
    """

    def __init__(self, persist_path: Path | None = None):
        self._store: dict[str, dict[str, str]] = {}
        self.persist_path = persist_path

        # Load existing mappings from disk if available
        if persist_path and persist_path.exists():
            try:
                data = json.loads(persist_path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    self._store = data
                    logger.info("Loaded %d mappings from %s", len(data), persist_path)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Failed to load mappings from %s: %s", persist_path, exc)

    def store(self, document_id: str, mapping: dict[str, str]) -> None:
        """Store a mapping for a document.

        Args:
            document_id: Unique document identifier.
            mapping: Placeholder-to-original-value mapping.
        """
        self._store[document_id] = mapping
        self._persist()

    def retrieve(self, document_id: str) -> dict[str, str] | None:
        """Retrieve the mapping for a document.

        Args:
            document_id: Unique document identifier.

        Returns:
            The mapping dict, or None if not found.
        """
        return self._store.get(document_id)

    def delete(self, document_id: str) -> bool:
        """Delete the mapping for a document.

        Args:
            document_id: Unique document identifier.

        Returns:
            True if the mapping existed and was deleted.
        """
        if document_id in self._store:
            del self._store[document_id]
            self._persist()
            return True
        return False

    def list_documents(self) -> list[str]:
        """List all document IDs with stored mappings.

        Returns:
            List of document IDs.
        """
        return list(self._store.keys())

    def _persist(self) -> None:
        """Write the store to disk if persistence is configured."""
        if self.persist_path is not None:
            try:
                self.persist_path.parent.mkdir(parents=True, exist_ok=True)
                self.persist_path.write_text(
                    json.dumps(self._store, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
            except OSError as exc:
                logger.error("Failed to persist mappings to %s: %s", self.persist_path, exc)
