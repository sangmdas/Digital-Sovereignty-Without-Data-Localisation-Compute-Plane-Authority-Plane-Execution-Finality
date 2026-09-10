from __future__ import annotations

from dataclasses import replace
import pytest

from finality_ref.errors import ValidationDenied, VerificationFailed
from sovereignty_ref.authority_plane import bind_governance_context
from sovereignty_ref.models import Approval, ComputeContext, JurisdictionEvidence
from sovereignty_ref.scenarios import healthcare_candidate
from .conftest import approvals_for, build_stack, default_compute, default_evidence, default_sovereignty_policy


@pytest.mark.parametrize("key", [
    "compute_context_digest", "jurisdiction_evidence_digest", "approvals_digest", "compute_provider_id", "compute_jurisdiction"
])
def test_missing_or_wrong_governance_binding_rejected_before_capability(key):
    c = healthcare_candidate()
    compute = default_compute()
    ev = default_evidence(c.jurisdiction)
    aps = approvals_for(c)
    bound = bind_governance_context(c, compute=compute, evidence=ev, approvals=aps)
    ctx = dict(bound.authority_context); ctx[key] = "tampered"
    bad = replace(bound, authority_context=ctx)
    s = build_stack(c, compute=compute, evidence=ev, approvals=aps)
    # Reuse authority plane but deliberately submit candidate with mismatched binding.
    with pytest.raises(ValidationDenied, match="governance_context_binding_mismatch"):
        s["authority_plane"].authorize(bad, compute=compute, evidence=ev, approvals=aps)


@pytest.mark.parametrize("field,value", [
    ("provider_id","attacker-provider"),("compute_jurisdiction","UNKNOWN"),("workload_id","other-workload"),
    ("model_id","other-model"),("runtime_evidence_digest","bad-runtime"),("session_id","other-session")
])
def test_compute_context_substitution_after_binding_fails(field, value):
    c = healthcare_candidate()
    s = build_stack(c)
    altered = replace(s["compute"], **{field:value})
    with pytest.raises(ValidationDenied):
        s["authority_plane"].authorize(s["candidate"], compute=altered, evidence=s["jurisdiction_evidence"], approvals=s["approvals"])


def test_jurisdiction_evidence_substitution_after_binding_fails():
    c = healthcare_candidate(); s = build_stack(c)
    ev = list(s["jurisdiction_evidence"]); ev[0] = replace(ev[0], value_digest="changed")
    with pytest.raises(ValidationDenied, match="governance_context_binding_mismatch:jurisdiction_evidence_digest"):
        s["authority_plane"].authorize(s["candidate"], compute=s["compute"], evidence=tuple(ev), approvals=s["approvals"])


def test_approval_substitution_after_binding_fails():
    c = healthcare_candidate(); s = build_stack(c)
    aps = list(s["approvals"]); aps[0] = replace(aps[0], approver_id="different")
    with pytest.raises(ValidationDenied, match="governance_context_binding_mismatch:approvals_digest"):
        s["authority_plane"].authorize(s["candidate"], compute=s["compute"], evidence=s["jurisdiction_evidence"], approvals=tuple(aps))


@pytest.mark.parametrize("ctx_key", ["compute_context_digest","jurisdiction_evidence_digest","approvals_digest","compute_provider_id","compute_jurisdiction"])
def test_governance_context_mutation_after_authorization_fails_at_sink(ctx_key):
    s = build_stack(healthcare_candidate())
    cap = s["authority_plane"].authorize(s["candidate"], compute=s["compute"], evidence=s["jurisdiction_evidence"], approvals=s["approvals"])
    ctx = dict(s["candidate"].authority_context); ctx[ctx_key] = "post-auth-mutation"
    mutated = replace(s["candidate"], authority_context=ctx)
    with pytest.raises(VerificationFailed, match="candidate_digest_mismatch"):
        s["sink"].verify(mutated, cap)
