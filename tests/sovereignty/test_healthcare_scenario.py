from __future__ import annotations

from dataclasses import replace
import pytest

from finality_ref.errors import ValidationDenied, VerificationFailed
from sovereignty_ref.scenarios import healthcare_candidate
from .conftest import build_stack, default_sovereignty_policy


def healthcare_policy(c):
    return default_sovereignty_policy(
        c,
        payload_required_fields=frozenset({"patient_id","operation","diagnosis","clinician_id","consent"}),
        payload_allowed_values={"operation": frozenset({"append-diagnosis"}), "consent": frozenset({"present"})},
    )


def test_healthcare_happy_path():
    c = healthcare_candidate(); s = build_stack(c, sov_policy=healthcare_policy(c))
    cap = s["authority_plane"].authorize(s["candidate"], compute=s["compute"], evidence=s["jurisdiction_evidence"], approvals=s["approvals"])
    receipt = s["sink"].effectuate(s["candidate"], cap)
    assert receipt.effect_status == "EFFECTIVE"


@pytest.mark.parametrize("missing", ["patient_id","operation","diagnosis","clinician_id","consent"])
def test_healthcare_required_payload_fields(missing):
    c = healthcare_candidate(); payload=dict(c.payload); payload.pop(missing)
    c=replace(c,payload=payload); s=build_stack(c,sov_policy=healthcare_policy(c))
    with pytest.raises(ValidationDenied, match=f"payload_field_missing:{missing}"):
        s["authority_plane"].authorize(s["candidate"], compute=s["compute"], evidence=s["jurisdiction_evidence"], approvals=s["approvals"])


@pytest.mark.parametrize("operation", ["export-record","delete-record","advertising-export","bulk-download","share-external","overwrite-record"])
def test_healthcare_unapproved_operation_rejected(operation):
    c=healthcare_candidate(payload={**healthcare_candidate().payload,"operation":operation}); s=build_stack(c,sov_policy=healthcare_policy(c))
    with pytest.raises(ValidationDenied, match="payload_value_not_allowed:operation"):
        s["authority_plane"].authorize(s["candidate"], compute=s["compute"], evidence=s["jurisdiction_evidence"], approvals=s["approvals"])


@pytest.mark.parametrize("consent", ["missing","revoked","unknown","false",""])
def test_healthcare_consent_policy_rejects_non_present(consent):
    c=healthcare_candidate(payload={**healthcare_candidate().payload,"consent":consent}); s=build_stack(c,sov_policy=healthcare_policy(c))
    with pytest.raises(ValidationDenied, match="payload_value_not_allowed:consent"):
        s["authority_plane"].authorize(s["candidate"], compute=s["compute"], evidence=s["jurisdiction_evidence"], approvals=s["approvals"])


@pytest.mark.parametrize("field,value", [
    ("patient_id","patient-9999"),("diagnosis","condition-Y"),("clinician_id","clinician-99"),
    ("operation","delete-record"),("consent","revoked")
])
def test_healthcare_payload_mutation_after_authority_fails_at_sink(field,value):
    c=healthcare_candidate(); s=build_stack(c,sov_policy=healthcare_policy(c))
    cap=s["authority_plane"].authorize(s["candidate"],compute=s["compute"],evidence=s["jurisdiction_evidence"],approvals=s["approvals"])
    payload=dict(s["candidate"].payload); payload[field]=value
    with pytest.raises(VerificationFailed, match="candidate_digest_mismatch"):
        s["sink"].verify(replace(s["candidate"],payload=payload),cap)
