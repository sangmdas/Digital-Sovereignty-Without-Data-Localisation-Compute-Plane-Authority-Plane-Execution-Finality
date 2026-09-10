from __future__ import annotations

from dataclasses import replace
import pytest

from finality_ref.errors import ValidationDenied
from sovereignty_ref.models import JurisdictionEvidence
from sovereignty_ref.scenarios import NOW, healthcare_candidate
from .conftest import build_stack, default_evidence, default_sovereignty_policy


@pytest.mark.parametrize("bad_issuer", ["unknown", "self-asserted", "untrusted-cloud", "random-service", "attacker"])
def test_untrusted_evidence_issuer_fails_closed(bad_issuer):
    c = healthcare_candidate()
    ev = list(default_evidence(c.jurisdiction))
    ev[0] = replace(ev[0], issuer=bad_issuer)
    s = build_stack(c, evidence=ev)
    with pytest.raises(ValidationDenied, match="untrusted_jurisdiction_evidence_issuer"):
        s["authority_plane"].authorize(s["candidate"], compute=s["compute"], evidence=s["jurisdiction_evidence"], approvals=s["approvals"])


@pytest.mark.parametrize("bad_type", ["ip-only", "gnss-unsigned", "user-claim", "free-text", "dns-label"])
def test_unconfigured_evidence_type_fails_closed(bad_type):
    c = healthcare_candidate()
    ev = list(default_evidence(c.jurisdiction))
    ev[0] = replace(ev[0], evidence_type=bad_type)
    s = build_stack(c, evidence=ev)
    with pytest.raises(ValidationDenied, match="jurisdiction_evidence_type_not_allowed"):
        s["authority_plane"].authorize(s["candidate"], compute=s["compute"], evidence=s["jurisdiction_evidence"], approvals=s["approvals"])


@pytest.mark.parametrize("delta", [1, 10, 1_000, 1_000_000, 10_000_000_000])
def test_expired_evidence_rejected(delta):
    c = healthcare_candidate()
    ev = list(default_evidence(c.jurisdiction))
    ev[0] = replace(ev[0], expires_at_ns=NOW-delta)
    s = build_stack(c, evidence=ev)
    with pytest.raises(ValidationDenied, match="jurisdiction_evidence_expired"):
        s["authority_plane"].authorize(s["candidate"], compute=s["compute"], evidence=s["jurisdiction_evidence"], approvals=s["approvals"])


@pytest.mark.parametrize("future_delta", [1_000_000_001, 2_000_000_000, 5_000_000_000, 60_000_000_000])
def test_evidence_too_far_from_future_rejected(future_delta):
    c = healthcare_candidate()
    ev = list(default_evidence(c.jurisdiction))
    ev[0] = replace(ev[0], observed_at_ns=NOW+future_delta)
    s = build_stack(c, evidence=ev)
    with pytest.raises(ValidationDenied, match="jurisdiction_evidence_from_future"):
        s["authority_plane"].authorize(s["candidate"], compute=s["compute"], evidence=s["jurisdiction_evidence"], approvals=s["approvals"])


@pytest.mark.parametrize("count", [0, 1])
def test_minimum_evidence_count_enforced(count):
    c = healthcare_candidate()
    ev = default_evidence(c.jurisdiction)[:count]
    s = build_stack(c, evidence=ev)
    with pytest.raises(ValidationDenied, match="insufficient_jurisdiction_evidence"):
        s["authority_plane"].authorize(s["candidate"], compute=s["compute"], evidence=s["jurisdiction_evidence"], approvals=s["approvals"])


def test_two_items_from_same_issuer_do_not_satisfy_independence():
    c = healthcare_candidate()
    ev = list(default_evidence(c.jurisdiction))
    ev[1] = replace(ev[1], issuer=ev[0].issuer)
    s = build_stack(c, evidence=ev)
    with pytest.raises(ValidationDenied, match="insufficient_independent_evidence_issuers"):
        s["authority_plane"].authorize(s["candidate"], compute=s["compute"], evidence=s["jurisdiction_evidence"], approvals=s["approvals"])


def test_duplicate_evidence_id_rejected():
    c = healthcare_candidate()
    ev = list(default_evidence(c.jurisdiction))
    ev[1] = replace(ev[1], evidence_id=ev[0].evidence_id)
    s = build_stack(c, evidence=ev)
    with pytest.raises(ValidationDenied, match="duplicate_jurisdiction_evidence"):
        s["authority_plane"].authorize(s["candidate"], compute=s["compute"], evidence=s["jurisdiction_evidence"], approvals=s["approvals"])


@pytest.mark.parametrize("wrong", ["COUNTRY-X", "COUNTRY-Y", "FOREIGN", "NONE", "UNKNOWN"])
def test_policy_can_require_evidence_for_authority_jurisdiction(wrong):
    c = healthcare_candidate()
    ev = tuple(replace(e, asserted_jurisdiction=wrong) for e in default_evidence(c.jurisdiction))
    s = build_stack(c, evidence=ev)
    with pytest.raises(ValidationDenied, match="authority_jurisdiction_evidence_missing"):
        s["authority_plane"].authorize(s["candidate"], compute=s["compute"], evidence=s["jurisdiction_evidence"], approvals=s["approvals"])


@pytest.mark.parametrize("trust_class", ["declared", "network-derived", "protected", "independently-verifiable"])
def test_configured_trust_classes_are_labels_not_claims_of_truth(trust_class):
    c = healthcare_candidate()
    ev = list(default_evidence(c.jurisdiction))
    ev[0] = replace(ev[0], trust_class=trust_class)
    s = build_stack(c, evidence=ev)
    cap = s["authority_plane"].authorize(s["candidate"], compute=s["compute"], evidence=s["jurisdiction_evidence"], approvals=s["approvals"])
    assert cap


@pytest.mark.parametrize("trust_class", ["magically-certain", "absolute-geography", "unconfigured", ""])
def test_unconfigured_trust_class_rejected(trust_class):
    c = healthcare_candidate()
    ev = list(default_evidence(c.jurisdiction))
    ev[0] = replace(ev[0], trust_class=trust_class)
    s = build_stack(c, evidence=ev)
    with pytest.raises(ValidationDenied, match="jurisdiction_evidence_trust_class_not_allowed"):
        s["authority_plane"].authorize(s["candidate"], compute=s["compute"], evidence=s["jurisdiction_evidence"], approvals=s["approvals"])
