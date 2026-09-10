from __future__ import annotations

from dataclasses import replace

from finality_ref.authority import ProtectedAuthority
from finality_ref.crypto import HMACAuthenticator
from finality_ref.effectors import EFFECTOR_TYPES
from finality_ref.evidence import EvidenceStore
from finality_ref.models import CandidateAct, SinkContext
from finality_ref.policy import Policy
from finality_ref.sink import FinalitySink
from finality_ref.state import InMemoryConsumptionStore, ProtectedState
from sovereignty_ref.authority_plane import AuthorityPlane, bind_governance_context
from sovereignty_ref.models import Approval, ComputeContext, JurisdictionEvidence
from sovereignty_ref.policy import SovereigntyPolicy
from sovereignty_ref.verification import PrincipalVerifierRegistry
from sovereignty_ref.scenarios import NOW

SECRET = b"digital-sovereignty-reference-key!!"


def default_evidence(jurisdiction: str):
    return (
        JurisdictionEvidence(
            evidence_id="je-gateway", evidence_type="gateway-attestation", asserted_jurisdiction=jurisdiction,
            issuer="national-trust-service", subject="finality-sink", observed_at_ns=NOW-1_000_000,
            expires_at_ns=NOW+60_000_000_000, trust_class="protected", value_digest="gateway-ok",
        ),
        JurisdictionEvidence(
            evidence_id="je-network", evidence_type="network-context", asserted_jurisdiction=jurisdiction,
            issuer="regulated-network", subject="effect-boundary", observed_at_ns=NOW-2_000_000,
            expires_at_ns=NOW+60_000_000_000, trust_class="network-derived", value_digest="network-ok",
        ),
    )


def default_compute(provider="global-ai-provider", jurisdiction="FOREIGN"):
    return ComputeContext(
        provider_id=provider, compute_jurisdiction=jurisdiction, workload_id="workload-1", model_id="model-1",
        runtime_evidence_digest="runtime-ok", session_id="session-1",
    )


def approvals_for(candidate: CandidateAct, roles=("policy-owner",)):
    from sovereignty_ref.models import governance_subject_digest
    return tuple(
        Approval(
            approver_id=f"approver-{idx}", role=role, candidate_digest=governance_subject_digest(candidate),
            policy_epoch=candidate.policy_epoch, approved_at_ns=NOW-1_000_000, expires_at_ns=NOW+60_000_000_000,
        )
        for idx, role in enumerate(roles, 1)
    )


def default_sovereignty_policy(candidate: CandidateAct, *, approval_roles=("policy-owner",), **overrides):
    base = dict(
        authority_jurisdiction=candidate.jurisdiction,
        policy_epoch=candidate.policy_epoch,
        allowed_compute_jurisdictions=frozenset({"FOREIGN", "US", "EU", "IN", "REGION-X", "REGION-Y"}),
        allowed_compute_providers=frozenset({"global-ai-provider", "regional-ai-provider", "foreign-medical-ai", "satellite-ai-provider", "external-benefit-ai"}),
        required_runtime_evidence_digest="runtime-ok",
        trusted_evidence_issuers=frozenset({"national-trust-service", "regulated-network", "facility-attestor"}),
        allowed_evidence_types=frozenset({"gateway-attestation", "network-context", "facility-attestation"}),
        min_evidence_items=2,
        min_independent_evidence_issuers=2,
        require_authority_jurisdiction_assertion=True,
        required_approval_roles=frozenset(approval_roles),
        approval_threshold=len(approval_roles),
    )
    base.update(overrides)
    return SovereigntyPolicy(**base)


def build_stack(candidate: CandidateAct, *, compute=None, evidence=None, approvals=None, sov_policy=None, state=None, consumption=None, authenticated=False):
    compute = compute or default_compute()
    evidence = default_evidence(candidate.jurisdiction) if evidence is None else tuple(evidence)
    approvals = approvals_for(candidate) if approvals is None else tuple(approvals)
    evidence_registry = None
    approval_registry = None
    if authenticated:
        evidence_registry = PrincipalVerifierRegistry()
        signed_evidence = []
        for idx, item in enumerate(evidence):
            signer = HMACAuthenticator(f"evidence-secret-{idx}-{item.issuer}".encode(), key_id=f"evidence-key-{idx}")
            evidence_registry.add(item.issuer, signer)
            unsigned = replace(item, key_id=signer.key_id, signature="")
            signed_evidence.append(replace(unsigned, signature=signer.sign(unsigned.unsigned())))
        evidence = tuple(signed_evidence)
        approval_registry = PrincipalVerifierRegistry()
        signed_approvals = []
        for idx, item in enumerate(approvals):
            signer = HMACAuthenticator(f"approval-secret-{idx}-{item.approver_id}".encode(), key_id=f"approval-key-{idx}")
            approval_registry.add(item.approver_id, signer)
            unsigned = replace(item, key_id=signer.key_id, signature="")
            signed_approvals.append(replace(unsigned, signature=signer.sign(unsigned.unsigned())))
        approvals = tuple(signed_approvals)

    candidate = bind_governance_context(candidate, compute=compute, evidence=evidence, approvals=approvals)
    sov_policy = sov_policy or default_sovereignty_policy(candidate)

    core_policy = Policy(
        policy_epoch=candidate.policy_epoch,
        allowed_purposes=frozenset({candidate.purpose}),
        allowed_jurisdictions=frozenset({candidate.jurisdiction}),
        allowed_sinks=frozenset({candidate.sink_id}),
        allowed_boundaries=frozenset({candidate.boundary_id}),
        allowed_effect_classes=frozenset({candidate.effect_class}),
        allowed_scopes=frozenset(candidate.scope),
        required_runtime_evidence_digest=compute.runtime_evidence_digest,
    )
    authn = HMACAuthenticator(SECRET)
    evidence_store = EvidenceStore(authn)
    state = state or ProtectedState(default_quota=1000, default_budget=1_000_000)
    protected_authority = ProtectedAuthority(
        authority_id=f"authority-{candidate.jurisdiction}", policy=core_policy, state=state,
        evidence_store=evidence_store, authenticator=authn, capability_ttl_ns=5_000_000_000, clock=lambda: NOW,
    )
    authority_plane = AuthorityPlane(
        policy=sov_policy, protected_authority=protected_authority, clock=lambda: NOW,
        jurisdiction_evidence_verifiers=evidence_registry, approval_verifiers=approval_registry,
        require_authenticated_evidence=authenticated, require_authenticated_approvals=authenticated,
    )
    effector = EFFECTOR_TYPES[candidate.effect_class]()
    sink = FinalitySink(
        context=SinkContext(candidate.sink_id, candidate.boundary_id, candidate.policy_epoch, frozenset(candidate.scope), candidate.effect_class),
        authenticator=authn, evidence_store=evidence_store, protected_state=state,
        consumption_store=consumption or InMemoryConsumptionStore(), effect_handle=effector.bind_for_sink(), clock=lambda: NOW,
    )
    return {
        "candidate": candidate, "compute": compute, "jurisdiction_evidence": evidence, "approvals": approvals,
        "sovereignty_policy": sov_policy, "authenticator": authn, "evidence_store": evidence_store,
        "state": state, "authority_plane": authority_plane, "effector": effector, "sink": sink,
    }
