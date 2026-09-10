from __future__ import annotations

from dataclasses import replace
import pytest

from finality_ref.errors import ValidationDenied
from sovereignty_ref.scenarios import healthcare_candidate
from .conftest import build_stack, default_compute, default_sovereignty_policy


@pytest.mark.parametrize("provider", ["unknown-provider","attacker","unregistered","shadow-cloud",""])
def test_unapproved_compute_provider_fails(provider):
    c=healthcare_candidate(); compute=default_compute(provider=provider); s=build_stack(c,compute=compute)
    with pytest.raises(ValidationDenied,match="compute_provider_not_allowed"):
        s["authority_plane"].authorize(s["candidate"],compute=s["compute"],evidence=s["jurisdiction_evidence"],approvals=s["approvals"])


@pytest.mark.parametrize("runtime", ["bad","stale","revoked","unknown",""])
def test_bad_runtime_evidence_fails(runtime):
    c=healthcare_candidate(runtime_evidence_digest=runtime); compute=replace(default_compute(),runtime_evidence_digest=runtime)
    policy=default_sovereignty_policy(c,required_runtime_evidence_digest="runtime-ok")
    s=build_stack(c,compute=compute,sov_policy=policy)
    with pytest.raises(ValidationDenied,match="compute_runtime_evidence_mismatch"):
        s["authority_plane"].authorize(s["candidate"],compute=s["compute"],evidence=s["jurisdiction_evidence"],approvals=s["approvals"])


def test_candidate_runtime_must_match_compute_runtime():
    c=healthcare_candidate(runtime_evidence_digest="candidate-runtime")
    compute=default_compute()
    policy=default_sovereignty_policy(c,required_runtime_evidence_digest=None)
    s=build_stack(c,compute=compute,sov_policy=policy)
    with pytest.raises(ValidationDenied,match="candidate_compute_runtime_binding_mismatch"):
        s["authority_plane"].authorize(s["candidate"],compute=s["compute"],evidence=s["jurisdiction_evidence"],approvals=s["approvals"])


@pytest.mark.parametrize("epoch", [0,1,72,183,185,2**31-1])
def test_sovereignty_policy_epoch_mismatch_fails(epoch):
    c=healthcare_candidate(); policy=default_sovereignty_policy(c,policy_epoch=epoch); s=build_stack(c,sov_policy=policy)
    if epoch==c.policy_epoch:
        assert s["authority_plane"].authorize(s["candidate"],compute=s["compute"],evidence=s["jurisdiction_evidence"],approvals=s["approvals"])
    else:
        with pytest.raises(ValidationDenied,match="sovereignty_policy_epoch_mismatch"):
            s["authority_plane"].authorize(s["candidate"],compute=s["compute"],evidence=s["jurisdiction_evidence"],approvals=s["approvals"])


def test_non_object_payload_fails_when_payload_constraints_exist():
    c=healthcare_candidate(payload="opaque")
    policy=default_sovereignty_policy(c,payload_required_fields=frozenset({"patient_id"}))
    s=build_stack(c,sov_policy=policy)
    with pytest.raises(ValidationDenied,match="payload_not_object"):
        s["authority_plane"].authorize(s["candidate"],compute=s["compute"],evidence=s["jurisdiction_evidence"],approvals=s["approvals"])
