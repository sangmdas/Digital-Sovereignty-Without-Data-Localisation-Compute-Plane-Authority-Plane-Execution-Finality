from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Mapping

from finality_ref.canonical import sha256_hex
from finality_ref.models import CandidateAct


@dataclass(frozen=True)
class ComputeContext:
    """Facts about the environment that performed the computation.

    These facts describe compute; they do not themselves grant effectuation authority.
    """
    provider_id: str
    compute_jurisdiction: str
    workload_id: str
    model_id: str
    runtime_evidence_digest: str
    session_id: str

    def digest(self) -> str:
        return sha256_hex(self)


@dataclass(frozen=True)
class JurisdictionEvidence:
    """One deployment-selected assertion relevant to jurisdiction or location.

    Cryptographic binding can protect this assertion; the class does not claim that
    the assertion is geographically true. Trust remains bounded by evidence quality.
    """
    evidence_id: str
    evidence_type: str
    asserted_jurisdiction: str
    issuer: str
    subject: str
    observed_at_ns: int
    expires_at_ns: int
    trust_class: str
    value_digest: str
    key_id: str = ""
    signature: str = ""

    def unsigned(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id, "evidence_type": self.evidence_type,
            "asserted_jurisdiction": self.asserted_jurisdiction, "issuer": self.issuer,
            "subject": self.subject, "observed_at_ns": self.observed_at_ns,
            "expires_at_ns": self.expires_at_ns, "trust_class": self.trust_class,
            "value_digest": self.value_digest, "key_id": self.key_id,
        }

    def digest(self) -> str:
        return sha256_hex(self)


@dataclass(frozen=True)
class Approval:
    """A policy-owner approval bound to one exact Candidate Act digest."""
    approver_id: str
    role: str
    candidate_digest: str
    policy_epoch: int
    approved_at_ns: int
    expires_at_ns: int
    key_id: str = ""
    signature: str = ""

    def unsigned(self) -> dict[str, Any]:
        return {
            "approver_id": self.approver_id, "role": self.role,
            "candidate_digest": self.candidate_digest, "policy_epoch": self.policy_epoch,
            "approved_at_ns": self.approved_at_ns, "expires_at_ns": self.expires_at_ns,
            "key_id": self.key_id,
        }

    def digest(self) -> str:
        return sha256_hex(self)


@dataclass(frozen=True)
class GovernanceDecision:
    allowed: bool
    reasons: tuple[str, ...]
    compute_context_digest: str
    jurisdiction_evidence_digest: str
    approvals_digest: str

    def digest(self) -> str:
        return sha256_hex(self)


def evidence_bundle_digest(items: tuple[JurisdictionEvidence, ...]) -> str:
    return sha256_hex(tuple(sorted((i.digest() for i in items))))


def approvals_digest(items: tuple[Approval, ...]) -> str:
    return sha256_hex(tuple(sorted((i.digest() for i in items))))


_GOVERNANCE_KEYS = frozenset({
    "compute_context_digest", "jurisdiction_evidence_digest", "approvals_digest",
    "compute_provider_id", "compute_jurisdiction",
})

def governance_subject_digest(candidate: CandidateAct) -> str:
    """Digest of the Candidate Act before governance-binding metadata is attached.

    This avoids a circular dependency when approvals themselves are later bound into
    candidate.authority_context. All ordinary Candidate fields and non-governance
    authority_context entries remain covered.
    """
    ctx = {k: v for k, v in candidate.authority_context.items() if k not in _GOVERNANCE_KEYS}
    return replace(candidate, authority_context=ctx).digest()
