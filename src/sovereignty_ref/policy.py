from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from finality_ref.models import CandidateAct

from .models import Approval, ComputeContext, GovernanceDecision, JurisdictionEvidence, approvals_digest, evidence_bundle_digest, governance_subject_digest


@dataclass(frozen=True)
class SovereigntyPolicy:
    """Deployment-selected policy for separating compute from effectuation authority.

    The policy is intentionally jurisdiction-neutral. It validates configured facts;
    it does not decide which country's law prevails.
    """
    authority_jurisdiction: str
    policy_epoch: int
    allowed_compute_jurisdictions: frozenset[str] | None = None
    allowed_compute_providers: frozenset[str] | None = None
    required_runtime_evidence_digest: str | None = None
    trusted_evidence_issuers: frozenset[str] = field(default_factory=frozenset)
    allowed_evidence_types: frozenset[str] = field(default_factory=frozenset)
    min_evidence_items: int = 0
    min_independent_evidence_issuers: int = 0
    require_authority_jurisdiction_assertion: bool = False
    allowed_trust_classes: frozenset[str] = field(default_factory=lambda: frozenset({"declared", "network-derived", "protected", "independently-verifiable"}))
    required_approval_roles: frozenset[str] = field(default_factory=frozenset)
    approval_threshold: int = 0
    max_future_skew_ns: int = 1_000_000_000
    payload_required_fields: frozenset[str] = field(default_factory=frozenset)
    payload_numeric_limits: Mapping[str, tuple[int, int]] = field(default_factory=dict)
    payload_allowed_values: Mapping[str, frozenset[object]] = field(default_factory=dict)

    def validate(
        self,
        candidate: CandidateAct,
        compute: ComputeContext,
        evidence: tuple[JurisdictionEvidence, ...],
        approvals: tuple[Approval, ...],
        now_ns: int,
    ) -> GovernanceDecision:
        reasons: list[str] = []

        if candidate.jurisdiction != self.authority_jurisdiction:
            reasons.append("authority_jurisdiction_mismatch")
        if candidate.policy_epoch != self.policy_epoch:
            reasons.append("sovereignty_policy_epoch_mismatch")
        if self.allowed_compute_jurisdictions is not None and compute.compute_jurisdiction not in self.allowed_compute_jurisdictions:
            reasons.append("compute_jurisdiction_not_allowed")
        if self.allowed_compute_providers is not None and compute.provider_id not in self.allowed_compute_providers:
            reasons.append("compute_provider_not_allowed")
        if self.required_runtime_evidence_digest is not None and compute.runtime_evidence_digest != self.required_runtime_evidence_digest:
            reasons.append("compute_runtime_evidence_mismatch")
        if candidate.runtime_evidence_digest != compute.runtime_evidence_digest:
            reasons.append("candidate_compute_runtime_binding_mismatch")

        if len(evidence) < self.min_evidence_items:
            reasons.append("insufficient_jurisdiction_evidence")

        valid_issuers: set[str] = set()
        has_authority_jurisdiction = False
        seen_ids: set[str] = set()
        for item in evidence:
            if item.evidence_id in seen_ids:
                reasons.append("duplicate_jurisdiction_evidence")
            seen_ids.add(item.evidence_id)
            if self.trusted_evidence_issuers and item.issuer not in self.trusted_evidence_issuers:
                reasons.append("untrusted_jurisdiction_evidence_issuer")
            else:
                valid_issuers.add(item.issuer)
            if self.allowed_evidence_types and item.evidence_type not in self.allowed_evidence_types:
                reasons.append("jurisdiction_evidence_type_not_allowed")
            if item.trust_class not in self.allowed_trust_classes:
                reasons.append("jurisdiction_evidence_trust_class_not_allowed")
            if now_ns < item.observed_at_ns - self.max_future_skew_ns:
                reasons.append("jurisdiction_evidence_from_future")
            if now_ns > item.expires_at_ns:
                reasons.append("jurisdiction_evidence_expired")
            if item.asserted_jurisdiction == self.authority_jurisdiction:
                has_authority_jurisdiction = True

        if len(valid_issuers) < self.min_independent_evidence_issuers:
            reasons.append("insufficient_independent_evidence_issuers")
        if self.require_authority_jurisdiction_assertion and not has_authority_jurisdiction:
            reasons.append("authority_jurisdiction_evidence_missing")

        seen_approvers: set[str] = set()
        valid_approvals: list[Approval] = []
        for approval in approvals:
            if approval.approver_id in seen_approvers:
                reasons.append("duplicate_approver")
                continue
            seen_approvers.add(approval.approver_id)
            if approval.candidate_digest != governance_subject_digest(candidate):
                reasons.append("approval_candidate_mismatch")
            if approval.policy_epoch != self.policy_epoch:
                reasons.append("approval_policy_epoch_mismatch")
            if now_ns < approval.approved_at_ns - self.max_future_skew_ns:
                reasons.append("approval_from_future")
            if now_ns > approval.expires_at_ns:
                reasons.append("approval_expired")
            if (
                approval.candidate_digest == governance_subject_digest(candidate)
                and approval.policy_epoch == self.policy_epoch
                and now_ns >= approval.approved_at_ns - self.max_future_skew_ns
                and now_ns <= approval.expires_at_ns
            ):
                valid_approvals.append(approval)

        if self.approval_threshold and len(valid_approvals) < self.approval_threshold:
            reasons.append("approval_threshold_not_met")
        valid_roles = {a.role for a in valid_approvals}
        if not self.required_approval_roles.issubset(valid_roles):
            reasons.append("required_approval_role_missing")

        if not isinstance(candidate.payload, dict):
            if self.payload_required_fields or self.payload_numeric_limits or self.payload_allowed_values:
                reasons.append("payload_not_object")
        else:
            for name in self.payload_required_fields:
                if name not in candidate.payload:
                    reasons.append(f"payload_field_missing:{name}")
            for name, (minimum, maximum) in self.payload_numeric_limits.items():
                value = candidate.payload.get(name)
                if not isinstance(value, int) or isinstance(value, bool):
                    reasons.append(f"payload_numeric_invalid:{name}")
                elif value < minimum or value > maximum:
                    reasons.append(f"payload_numeric_out_of_range:{name}")
            for name, allowed in self.payload_allowed_values.items():
                if candidate.payload.get(name) not in allowed:
                    reasons.append(f"payload_value_not_allowed:{name}")

        return GovernanceDecision(
            allowed=not reasons,
            reasons=tuple(reasons),
            compute_context_digest=compute.digest(),
            jurisdiction_evidence_digest=evidence_bundle_digest(evidence),
            approvals_digest=approvals_digest(approvals),
        )
