"""
Integration tests: realistic AT government documents through the
full anonymization pipeline.

ML pipelines are mocked — these tests verify the deterministic pipeline
layers (normalizer, regex, Presidio-compat, ensemble, entity resolver,
channel formatting, quality check) across three realistic document
shapes and all three channels.
"""

from unittest.mock import MagicMock

import pytest

from anomyze.channels.govgpt import GovGPTResult
from anomyze.channels.ifg import IFGResult
from anomyze.channels.kapa import KAPAResult
from anomyze.config.settings import Settings
from anomyze.pipeline.orchestrator import PipelineOrchestrator


@pytest.fixture
def orch() -> PipelineOrchestrator:
    settings = Settings(
        use_anomaly_detection=False,
        use_gliner=False,
        device="cpu",
    )
    o = PipelineOrchestrator(settings)
    o.model_manager._pii_pipeline = MagicMock(return_value=[])
    o.model_manager._org_pipeline = MagicMock(return_value=[])
    o.model_manager._mlm_pipeline = MagicMock(return_value=[])
    o.model_manager._device = "cpu"
    o.model_manager._device_name = "CPU [test]"
    return o


# ---------------------------------------------------------------------------
# Sample AT documents (mixed PII)
# ---------------------------------------------------------------------------

BESCHEID = """
Aktenzahl: GZ 2024-BMI-1234

Sehr geehrte Frau Mag. Maria Huber,

zu Ihrer Anfrage vom 12.03.2024 teilen wir Ihnen mit, dass
die Ueberweisung auf das Konto AT61 1904 3002 3457 3201
erfolgt ist. Ihre Sozialversicherungsnummer 1237 010180
liegt dem Akt bei.

Kontakt: maria.huber@bmi.gv.at, Tel.: +43 1 5311 0.
KFZ W-12345 AB ist gesperrt.

Mit freundlichen Gruessen
Anomyze Testfinanz GmbH
"""


ANFRAGE = """
An das Bundesministerium fuer Inneres

Betrifft: Parlamentarische Anfrage (Zl 567/2024)

Der Abgeordnete Dr. Karl Gruber fragt in Bezug auf
das Verfahren gegen Herrn Josef Mayer (SVNR 1009 020280)
und seinen Bruder Mayer, ob die Akten GZ 2023-55 und
Az BMI-7/88/2023 freigegeben werden koennen.
"""


CLEAN = "Heute ist ein schoener Tag. Die Sonne scheint."


# ---------------------------------------------------------------------------
# GovGPT channel tests
# ---------------------------------------------------------------------------

class TestGovGPTIntegration:
    def test_bescheid_anonymizes_all_pii(self, orch) -> None:
        result = orch.process(BESCHEID, channel="govgpt")
        assert isinstance(result, GovGPTResult)
        # Raw PII must not remain in output
        assert "AT61 1904 3002 3457 3201" not in result.text
        assert "maria.huber@bmi.gv.at" not in result.text
        assert "1237 010180" not in result.text
        assert "W-12345" not in result.text
        # Placeholders present
        assert "[IBAN_1]" in result.text
        assert "[EMAIL_1]" in result.text
        assert "[SVNR_1]" in result.text

    def test_bescheid_mapping_is_reversible(self, orch) -> None:
        result = orch.process(BESCHEID, channel="govgpt")
        # Mapping contains at least some anonymized entries
        assert len(result.mapping) > 0
        # Each mapping key is a well-formed placeholder
        assert all(k.startswith("[") and k.endswith("]") for k in result.mapping)

    def test_quality_report_clean(self, orch) -> None:
        result = orch.process(BESCHEID, channel="govgpt")
        assert result.quality_report is not None
        # leak_count == 0 means no raw PII left in the output
        assert result.quality_report.leak_count == 0

    def test_clean_document_no_entities(self, orch) -> None:
        result = orch.process(CLEAN, channel="govgpt")
        assert result.entity_count == 0
        # Text passed through unchanged (modulo whitespace normalization)
        assert "Sonne scheint" in result.text


# ---------------------------------------------------------------------------
# IFG channel tests
# ---------------------------------------------------------------------------

class TestIFGIntegration:
    def test_ifg_irreversible_placeholders(self, orch) -> None:
        result = orch.process(BESCHEID, channel="ifg")
        assert isinstance(result, IFGResult)
        # IFG uses [GESCHWÄRZT:CATEGORY] without numbering
        assert "[GESCHWÄRZT:IBAN]" in result.text
        # No numbered placeholders in IFG
        assert "[IBAN_1]" not in result.text

    def test_ifg_no_mapping_exposed(self, orch) -> None:
        result = orch.process(BESCHEID, channel="ifg")
        # IFG returns no mapping (irreversible by design)
        assert not hasattr(result, "mapping") or not getattr(result, "mapping", None)

    def test_ifg_redaction_protocol_has_counts(self, orch) -> None:
        result = orch.process(BESCHEID, channel="ifg")
        assert len(result.redaction_protocol) > 0
        # Every category has a positive count
        for entry in result.redaction_protocol:
            assert entry.count > 0


# ---------------------------------------------------------------------------
# KAPA channel tests
# ---------------------------------------------------------------------------

class TestKAPAIntegration:
    def test_kapa_has_audit_entries(self, orch) -> None:
        result = orch.process(BESCHEID, channel="kapa")
        assert isinstance(result, KAPAResult)
        assert len(result.audit_entries) > 0
        # Each audit entry has required fields
        for entry in result.audit_entries:
            assert entry.timestamp
            assert entry.document_id
            assert entry.entity_group
            assert entry.action in ("anonymized", "flagged_for_review")

    def test_kapa_anonymizes_entities(self, orch) -> None:
        result = orch.process(BESCHEID, channel="kapa")
        assert "AT61 1904 3002 3457 3201" not in result.text
        assert "maria.huber@bmi.gv.at" not in result.text


# ---------------------------------------------------------------------------
# Cross-channel consistency
# ---------------------------------------------------------------------------

class TestCrossChannelConsistency:
    def test_all_channels_catch_same_regex_pii(self, orch) -> None:
        """All three channels must anonymize the same regex-detectable PII."""
        raw_pii = [
            "AT61 1904 3002 3457 3201",
            "maria.huber@bmi.gv.at",
            "1237 010180",
            "W-12345 AB",
        ]
        for channel in ("govgpt", "ifg", "kapa"):
            result = orch.process(BESCHEID, channel=channel)
            for pii in raw_pii:
                assert pii not in result.text, (
                    f"channel={channel}: {pii!r} leaked"
                )

    def test_entity_count_consistent_across_channels(self, orch) -> None:
        govgpt = orch.process(ANFRAGE, channel="govgpt")
        kapa = orch.process(ANFRAGE, channel="kapa")
        # Both channels see the same entities
        assert govgpt.entity_count == kapa.entity_count
