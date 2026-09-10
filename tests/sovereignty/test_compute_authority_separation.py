from __future__ import annotations

import pytest
from dataclasses import replace

from finality_ref.errors import EffectDenied, VerificationFailed
from finality_ref.models import ActStatus
from sovereignty_ref.compute_plane import ComputePlane
from sovereignty_ref.scenarios import healthcare_candidate

from .conftest import build_stack, default_compute


def test_compute_plane_can_propose_but_not_effectuate():
    compute = ComputePlane(default_compute())
    candidate = compute.propose(healthcare_candidate())
    assert candidate.status == ActStatus.NON_EFFECTIVE
    with pytest.raises(EffectDenied, match="compute_plane_has_no_effectuation_authority"):
        compute.effectuate(candidate)


def test_guarded_effector_denies_direct_external_effect():
    s = build_stack(healthcare_candidate())
    with pytest.raises(EffectDenied, match="Finality Sink required"):
        s["effector"].direct_effect(s["candidate"])


def test_valid_authority_then_sink_allows_one_effect():
    s = build_stack(healthcare_candidate())
    cap = s["authority_plane"].authorize(s["candidate"], compute=s["compute"], evidence=s["jurisdiction_evidence"], approvals=s["approvals"])
    receipt = s["sink"].effectuate(s["candidate"], cap)
    assert receipt.effect_status == "EFFECTIVE"
    assert len(s["effector"].records) == 1


@pytest.mark.parametrize("field,new_value", [
    ("destination", "Foreign-EHR"), ("purpose", "Advertising"), ("jurisdiction", "OTHER"),
    ("sink_id", "Different-Sink"), ("boundary_id", "Different-Boundary"),
    ("policy_epoch", 185), ("nonce", "different-nonce"), ("source", "different-ai"),
    ("effect_class", "network-egress"), ("scope", ("SEND",)),
])
def test_post_authorization_candidate_mutation_cannot_inherit_authority(field, new_value):
    s = build_stack(healthcare_candidate())
    cap = s["authority_plane"].authorize(s["candidate"], compute=s["compute"], evidence=s["jurisdiction_evidence"], approvals=s["approvals"])
    mutated = replace(s["candidate"], **{field: new_value})
    with pytest.raises(VerificationFailed):
        s["sink"].verify(mutated, cap)
