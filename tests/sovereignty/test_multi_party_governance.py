from __future__ import annotations

from dataclasses import replace
import itertools
import pytest

from finality_ref.errors import ValidationDenied
from sovereignty_ref.models import Approval, governance_subject_digest
from sovereignty_ref.scenarios import NOW, payment_candidate
from .conftest import approvals_for, build_stack, default_sovereignty_policy


@pytest.mark.parametrize("threshold,count,allowed", [
    (0,0,True),(1,0,False),(1,1,True),(2,0,False),(2,1,False),(2,2,True),(3,2,False),(3,3,True),(4,3,False),(4,4,True)
])
def test_approval_threshold_matrix(threshold, count, allowed):
    c = payment_candidate()
    roles = tuple(f"role-{i}" for i in range(max(count, threshold, 1)))
    aps = approvals_for(c, roles=roles[:count])
    policy = default_sovereignty_policy(c, approval_roles=(), approval_threshold=threshold, required_approval_roles=frozenset())
    s = build_stack(c, approvals=aps, sov_policy=policy)
    if allowed:
        assert s["authority_plane"].authorize(s["candidate"], compute=s["compute"], evidence=s["jurisdiction_evidence"], approvals=s["approvals"])
    else:
        with pytest.raises(ValidationDenied, match="approval_threshold_not_met"):
            s["authority_plane"].authorize(s["candidate"], compute=s["compute"], evidence=s["jurisdiction_evidence"], approvals=s["approvals"])


@pytest.mark.parametrize("required_roles,present_roles,allowed", [
    (("treasury",), ("treasury",), True),
    (("treasury","benefit-agency"), ("treasury","benefit-agency"), True),
    (("treasury","benefit-agency"), ("treasury",), False),
    (("treasury","benefit-agency"), ("benefit-agency",), False),
    (("treasury","auditor"), ("treasury","benefit-agency"), False),
    ((), (), True),
])
def test_required_role_matrix(required_roles, present_roles, allowed):
    c = payment_candidate()
    aps = approvals_for(c, roles=present_roles)
    policy = default_sovereignty_policy(c, approval_roles=(), approval_threshold=len(present_roles), required_approval_roles=frozenset(required_roles))
    s = build_stack(c, approvals=aps, sov_policy=policy)
    if allowed:
        assert s["authority_plane"].authorize(s["candidate"], compute=s["compute"], evidence=s["jurisdiction_evidence"], approvals=s["approvals"])
    else:
        with pytest.raises(ValidationDenied, match="required_approval_role_missing"):
            s["authority_plane"].authorize(s["candidate"], compute=s["compute"], evidence=s["jurisdiction_evidence"], approvals=s["approvals"])


@pytest.mark.parametrize("mutation", ["candidate","epoch","expired","future"])
def test_invalid_approval_semantics_fail(mutation):
    c = payment_candidate()
    ap = approvals_for(c, roles=("treasury",))[0]
    if mutation == "candidate": ap = replace(ap, candidate_digest="00"*32)
    if mutation == "epoch": ap = replace(ap, policy_epoch=c.policy_epoch+1)
    if mutation == "expired": ap = replace(ap, expires_at_ns=NOW-1)
    if mutation == "future": ap = replace(ap, approved_at_ns=NOW+1_000_000_001)
    policy = default_sovereignty_policy(c, approval_roles=("treasury",))
    s = build_stack(c, approvals=(ap,), sov_policy=policy)
    with pytest.raises(ValidationDenied):
        s["authority_plane"].authorize(s["candidate"], compute=s["compute"], evidence=s["jurisdiction_evidence"], approvals=s["approvals"])


def test_duplicate_approver_does_not_count_twice():
    c = payment_candidate()
    d = governance_subject_digest(c)
    ap1 = Approval("same-person","treasury",d,c.policy_epoch,NOW-1,NOW+10_000_000_000)
    ap2 = Approval("same-person","benefit-agency",d,c.policy_epoch,NOW-1,NOW+10_000_000_000)
    policy = default_sovereignty_policy(c, approval_roles=(), approval_threshold=2, required_approval_roles=frozenset())
    s = build_stack(c, approvals=(ap1,ap2), sov_policy=policy)
    with pytest.raises(ValidationDenied, match="duplicate_approver"):
        s["authority_plane"].authorize(s["candidate"], compute=s["compute"], evidence=s["jurisdiction_evidence"], approvals=s["approvals"])
