from __future__ import annotations

import time
from dataclasses import replace
from typing import Callable

from finality_ref.authority import ProtectedAuthority
from finality_ref.errors import ValidationDenied
from finality_ref.models import CandidateAct, Capability

from .models import Approval, ComputeContext, GovernanceDecision, JurisdictionEvidence, approvals_digest, evidence_bundle_digest
from .policy import SovereigntyPolicy
from .verification import PrincipalVerifierRegistry

Clock = Callable[[], int]


def bind_governance_context(
    candidate: CandidateAct,
    *,
    compute: ComputeContext,
    evidence: tuple[JurisdictionEvidence, ...] = (),
    approvals: tuple[Approval, ...] = (),
) -> CandidateAct:
    """Bind compute/evidence/approval digests into the Candidate Act.

    Because the core capability binds candidate.digest(), mutation of any bound
    governance digest after authorization invalidates the capability at the sink.
    """
    ctx = dict(candidate.authority_context)
    ctx.update(
        {
            "compute_context_digest": compute.digest(),
            "jurisdiction_evidence_digest": evidence_bundle_digest(evidence),
            "approvals_digest": approvals_digest(approvals),
            "compute_provider_id": compute.provider_id,
            "compute_jurisdiction": compute.compute_jurisdiction,
        }
    )
    return replace(candidate, authority_context=ctx)


class AuthorityPlane:
    """Separately governed pre-effectuation authority layer.

    The wrapper validates sovereignty-specific context, confirms that the context is
    bound into the exact Candidate Act, and only then delegates to the core protected
    finality authority.
    """

    def __init__(
        self, *, policy: SovereigntyPolicy, protected_authority: ProtectedAuthority, clock: Clock = time.time_ns,
        jurisdiction_evidence_verifiers: PrincipalVerifierRegistry | None = None,
        approval_verifiers: PrincipalVerifierRegistry | None = None,
        require_authenticated_evidence: bool = False, require_authenticated_approvals: bool = False,
    ):
        self.policy = policy
        self.protected_authority = protected_authority
        self.clock = clock
        self.jurisdiction_evidence_verifiers = jurisdiction_evidence_verifiers
        self.approval_verifiers = approval_verifiers
        self.require_authenticated_evidence = require_authenticated_evidence
        self.require_authenticated_approvals = require_authenticated_approvals
        self.last_decision: GovernanceDecision | None = None

    def authorize(
        self,
        candidate: CandidateAct,
        *,
        compute: ComputeContext,
        evidence: tuple[JurisdictionEvidence, ...] = (),
        approvals: tuple[Approval, ...] = (),
        cost: int = 1,
        now_ns: int | None = None,
    ) -> Capability:
        now = self.clock() if now_ns is None else now_ns
        if self.require_authenticated_evidence:
            if self.jurisdiction_evidence_verifiers is None:
                raise ValidationDenied("jurisdiction_evidence_verifier_required")
            for item in evidence:
                if not self.jurisdiction_evidence_verifiers.verify(item.issuer, item.unsigned(), item.signature, item.key_id):
                    raise ValidationDenied("jurisdiction_evidence_signature_invalid")
        if self.require_authenticated_approvals:
            if self.approval_verifiers is None:
                raise ValidationDenied("approval_verifier_required")
            for approval in approvals:
                if not self.approval_verifiers.verify(approval.approver_id, approval.unsigned(), approval.signature, approval.key_id):
                    raise ValidationDenied("approval_signature_invalid")
        decision = self.policy.validate(candidate, compute, evidence, approvals, now)
        self.last_decision = decision
        if not decision.allowed:
            raise ValidationDenied(",".join(decision.reasons))

        ctx = candidate.authority_context
        required = {
            "compute_context_digest": decision.compute_context_digest,
            "jurisdiction_evidence_digest": decision.jurisdiction_evidence_digest,
            "approvals_digest": decision.approvals_digest,
            "compute_provider_id": compute.provider_id,
            "compute_jurisdiction": compute.compute_jurisdiction,
        }
        for key, expected in required.items():
            if ctx.get(key) != expected:
                raise ValidationDenied(f"governance_context_binding_mismatch:{key}")

        return self.protected_authority.authorize(candidate, cost=cost, now_ns=now)
