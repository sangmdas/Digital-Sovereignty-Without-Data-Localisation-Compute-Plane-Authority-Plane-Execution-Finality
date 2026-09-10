from __future__ import annotations

import pytest

from sovereignty_ref.scenarios import healthcare_candidate
from .conftest import build_stack, default_compute, default_sovereignty_policy

AUTHORITY_JURISDICTIONS = ["COUNTRY-A", "COUNTRY-B", "COUNTRY-C", "COUNTRY-D", "COUNTRY-E"]
COMPUTE_JURISDICTIONS = ["FOREIGN", "US", "EU", "IN", "REGION-X", "REGION-Y"]


@pytest.mark.parametrize("authority_jurisdiction", AUTHORITY_JURISDICTIONS)
@pytest.mark.parametrize("compute_jurisdiction", COMPUTE_JURISDICTIONS)
def test_compute_location_can_differ_from_authority_location(authority_jurisdiction, compute_jurisdiction):
    candidate = healthcare_candidate(jurisdiction=authority_jurisdiction, policy_epoch=101)
    compute = default_compute(jurisdiction=compute_jurisdiction)
    policy = default_sovereignty_policy(candidate, allowed_compute_jurisdictions=frozenset(COMPUTE_JURISDICTIONS))
    s = build_stack(candidate, compute=compute, sov_policy=policy)
    cap = s["authority_plane"].authorize(s["candidate"], compute=s["compute"], evidence=s["jurisdiction_evidence"], approvals=s["approvals"])
    assert cap.candidate_digest == s["candidate"].digest()


@pytest.mark.parametrize("blocked", ["BLOCKED-1", "BLOCKED-2", "UNREGISTERED", "UNKNOWN", "SANCTIONED"])
def test_policy_can_restrict_compute_location_without_changing_finality_model(blocked):
    candidate = healthcare_candidate()
    compute = default_compute(jurisdiction=blocked)
    policy = default_sovereignty_policy(candidate, allowed_compute_jurisdictions=frozenset({"FOREIGN", "US"}))
    s = build_stack(candidate, compute=compute, sov_policy=policy)
    with pytest.raises(Exception, match="compute_jurisdiction_not_allowed"):
        s["authority_plane"].authorize(s["candidate"], compute=s["compute"], evidence=s["jurisdiction_evidence"], approvals=s["approvals"])
