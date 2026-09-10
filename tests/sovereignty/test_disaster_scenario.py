from __future__ import annotations

from dataclasses import replace
import pytest

from finality_ref.errors import ValidationDenied, VerificationFailed
from sovereignty_ref.scenarios import disaster_candidate
from .conftest import build_stack, default_sovereignty_policy


def disaster_policy(c):
    return default_sovereignty_policy(
        c,
        payload_required_fields=frozenset({"region","hazard","severity","message_class"}),
        payload_allowed_values={
            "hazard": frozenset({"flood","cyclone","earthquake","wildfire"}),
            "severity": frozenset({"severe","extreme"}),
            "message_class": frozenset({"public-warning"}),
        },
    )


def test_disaster_happy_path():
    c=disaster_candidate(); s=build_stack(c,sov_policy=disaster_policy(c))
    cap=s["authority_plane"].authorize(s["candidate"],compute=s["compute"],evidence=s["jurisdiction_evidence"],approvals=s["approvals"])
    assert s["sink"].effectuate(s["candidate"],cap).effect_status=="EFFECTIVE"


@pytest.mark.parametrize("hazard", ["flood","cyclone","earthquake","wildfire"])
@pytest.mark.parametrize("severity", ["severe","extreme"])
def test_configured_hazard_severity_matrix(hazard,severity):
    payload={**disaster_candidate().payload,"hazard":hazard,"severity":severity}
    c=disaster_candidate(payload=payload); s=build_stack(c,sov_policy=disaster_policy(c))
    assert s["authority_plane"].authorize(s["candidate"],compute=s["compute"],evidence=s["jurisdiction_evidence"],approvals=s["approvals"])


@pytest.mark.parametrize("hazard", ["marketing","political-message","routine-notice","unknown",""])
def test_unapproved_alert_class_rejected(hazard):
    payload={**disaster_candidate().payload,"hazard":hazard}; c=disaster_candidate(payload=payload); s=build_stack(c,sov_policy=disaster_policy(c))
    with pytest.raises(ValidationDenied,match="payload_value_not_allowed:hazard"):
        s["authority_plane"].authorize(s["candidate"],compute=s["compute"],evidence=s["jurisdiction_evidence"],approvals=s["approvals"])


@pytest.mark.parametrize("region", ["Entire-Country","District-Z","District-A-B-C-D","Foreign-Region","*"])
def test_region_change_after_authorization_requires_new_authority(region):
    c=disaster_candidate(); s=build_stack(c,sov_policy=disaster_policy(c)); cap=s["authority_plane"].authorize(s["candidate"],compute=s["compute"],evidence=s["jurisdiction_evidence"],approvals=s["approvals"])
    payload=dict(s["candidate"].payload); payload["region"]=region
    with pytest.raises(VerificationFailed,match="candidate_digest_mismatch"):
        s["sink"].verify(replace(s["candidate"],payload=payload),cap)


@pytest.mark.parametrize("field", ["region","hazard","severity","message_class"])
def test_missing_disaster_field_fails(field):
    c=disaster_candidate(); p=dict(c.payload); p.pop(field); c=replace(c,payload=p); s=build_stack(c,sov_policy=disaster_policy(c))
    with pytest.raises(ValidationDenied,match=f"payload_field_missing:{field}"):
        s["authority_plane"].authorize(s["candidate"],compute=s["compute"],evidence=s["jurisdiction_evidence"],approvals=s["approvals"])
