from __future__ import annotations

from dataclasses import replace
import pytest

from finality_ref.errors import ValidationDenied
from sovereignty_ref.authority_plane import bind_governance_context
from sovereignty_ref.scenarios import healthcare_candidate
from .conftest import build_stack


def test_authenticated_evidence_and_approvals_allow_when_signatures_are_valid():
    s = build_stack(healthcare_candidate(), authenticated=True)
    cap = s["authority_plane"].authorize(
        s["candidate"], compute=s["compute"], evidence=s["jurisdiction_evidence"], approvals=s["approvals"]
    )
    assert cap


@pytest.mark.parametrize("field,value", [
    ("asserted_jurisdiction","COUNTRY-X"),("subject","other-sink"),("value_digest","tampered"),
    ("expires_at_ns",1),("trust_class","declared")
])
def test_evidence_signature_detects_post_signature_mutation(field,value):
    s = build_stack(healthcare_candidate(), authenticated=True)
    evidence = list(s["jurisdiction_evidence"])
    evidence[0] = replace(evidence[0], **{field:value})
    candidate = bind_governance_context(s["candidate"], compute=s["compute"], evidence=tuple(evidence), approvals=s["approvals"])
    with pytest.raises(ValidationDenied, match="jurisdiction_evidence_signature_invalid"):
        s["authority_plane"].authorize(candidate, compute=s["compute"], evidence=tuple(evidence), approvals=s["approvals"])


@pytest.mark.parametrize("field,value", [
    ("role","other-role"),("candidate_digest","00"*32),("policy_epoch",999),
    ("expires_at_ns",1),("approved_at_ns",9_999_999_999_999_999_999)
])
def test_approval_signature_detects_post_signature_mutation(field,value):
    s = build_stack(healthcare_candidate(), authenticated=True)
    approvals = list(s["approvals"])
    approvals[0] = replace(approvals[0], **{field:value})
    candidate = bind_governance_context(s["candidate"], compute=s["compute"], evidence=s["jurisdiction_evidence"], approvals=tuple(approvals))
    with pytest.raises(ValidationDenied, match="approval_signature_invalid"):
        s["authority_plane"].authorize(candidate, compute=s["compute"], evidence=s["jurisdiction_evidence"], approvals=tuple(approvals))


def test_missing_evidence_verifier_fails_closed_when_authentication_required():
    s = build_stack(healthcare_candidate())
    s["authority_plane"].require_authenticated_evidence = True
    with pytest.raises(ValidationDenied, match="jurisdiction_evidence_verifier_required"):
        s["authority_plane"].authorize(s["candidate"], compute=s["compute"], evidence=s["jurisdiction_evidence"], approvals=s["approvals"])


def test_missing_approval_verifier_fails_closed_when_authentication_required():
    s = build_stack(healthcare_candidate())
    s["authority_plane"].require_authenticated_approvals = True
    with pytest.raises(ValidationDenied, match="approval_verifier_required"):
        s["authority_plane"].authorize(s["candidate"], compute=s["compute"], evidence=s["jurisdiction_evidence"], approvals=s["approvals"])
