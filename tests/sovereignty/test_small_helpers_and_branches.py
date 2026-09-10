from __future__ import annotations

import pytest
from finality_ref.errors import ValidationDenied
from sovereignty_ref.models import GovernanceDecision
from sovereignty_ref.scenarios import approval, compute_context, healthcare_candidate, jurisdiction_evidence
from .conftest import build_stack, default_sovereignty_policy


def test_governance_decision_digest_is_deterministic():
    d = GovernanceDecision(True, (), "a", "b", "c")
    assert d.digest() == d.digest()


def test_scenario_convenience_factories_construct_expected_types():
    c = healthcare_candidate()
    assert compute_context().provider_id == "global-ai-provider"
    assert jurisdiction_evidence().issuer == "national-trust-service"
    assert approval(c).candidate_digest


def test_authority_jurisdiction_mismatch_branch_fails_closed():
    c = healthcare_candidate()
    policy = default_sovereignty_policy(c, authority_jurisdiction="COUNTRY-Z")
    s = build_stack(c, sov_policy=policy)
    with pytest.raises(ValidationDenied, match="authority_jurisdiction_mismatch"):
        s["authority_plane"].authorize(s["candidate"], compute=s["compute"], evidence=s["jurisdiction_evidence"], approvals=s["approvals"])
