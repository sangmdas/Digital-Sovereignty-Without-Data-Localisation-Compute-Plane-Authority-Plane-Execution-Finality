from __future__ import annotations

from dataclasses import replace

from finality_ref.models import CandidateAct

from .models import Approval, ComputeContext, JurisdictionEvidence, governance_subject_digest

NOW = 1_800_000_000_000_000_000


def compute_context(*, provider_id="global-ai-provider", compute_jurisdiction="FOREIGN", workload_id="workload-1", model_id="model-1", runtime_evidence_digest="runtime-ok", session_id="session-1") -> ComputeContext:
    return ComputeContext(provider_id, compute_jurisdiction, workload_id, model_id, runtime_evidence_digest, session_id)


def jurisdiction_evidence(*, evidence_id="je-1", evidence_type="gateway-attestation", asserted_jurisdiction="COUNTRY-A", issuer="national-trust-service", subject="finality-sink", observed_at_ns=NOW-1_000_000, expires_at_ns=NOW+60_000_000_000, trust_class="protected", value_digest="evidence-value-ok") -> JurisdictionEvidence:
    return JurisdictionEvidence(evidence_id, evidence_type, asserted_jurisdiction, issuer, subject, observed_at_ns, expires_at_ns, trust_class, value_digest)


def approval(candidate: CandidateAct, *, approver_id="approver-1", role="regulator", policy_epoch=None, approved_at_ns=NOW-1_000_000, expires_at_ns=NOW+60_000_000_000) -> Approval:
    return Approval(approver_id, role, governance_subject_digest(candidate), candidate.policy_epoch if policy_epoch is None else policy_epoch, approved_at_ns, expires_at_ns)


def healthcare_candidate(**overrides) -> CandidateAct:
    base = dict(
        act_id="health-act-1", act_class="clinical-record-update", effect_class="storage-write",
        source="foreign-medical-ai", destination="National-Hospital-EHR", purpose="Clinical-Treatment",
        jurisdiction="COUNTRY-A", policy_epoch=184, nonce="health-nonce-1", issued_at_ns=NOW-10_000,
        freshness_ns=10_000_000_000, sink_id="Hospital-EHR-Finality-Sink", boundary_id="Hospital-EHR-Write-Boundary",
        scope=("WRITE:/records",),
        payload={"patient_id":"patient-4821","operation":"append-diagnosis","diagnosis":"condition-X","clinician_id":"clinician-17","consent":"present"},
        runtime_evidence_digest="runtime-ok", authority_context={}
    )
    base.update(overrides)
    return CandidateAct(**base)


def disaster_candidate(**overrides) -> CandidateAct:
    base = dict(
        act_id="alert-act-1", act_class="public-warning", effect_class="network-egress",
        source="global-disaster-ai", destination="National-Telecom-Emergency-Gateway", purpose="Flood-Emergency-Warning",
        jurisdiction="COUNTRY-B", policy_epoch=73, nonce="alert-nonce-1", issued_at_ns=NOW-10_000,
        freshness_ns=600_000_000_000, sink_id="National-Alert-Finality-Sink", boundary_id="National-Alert-Dispatch-Boundary",
        scope=("SEND",),
        payload={"region":"Districts-A-B-C","hazard":"flood","severity":"severe","message_class":"public-warning"},
        runtime_evidence_digest="runtime-ok", authority_context={}
    )
    base.update(overrides)
    return CandidateAct(**base)


def payment_candidate(**overrides) -> CandidateAct:
    base = dict(
        act_id="payment-act-1", act_class="public-benefit-payment", effect_class="payment-ledger",
        source="external-benefit-ai", destination="Domestic-Payment-Rail", purpose="Flood-Relief",
        jurisdiction="COUNTRY-C", policy_epoch=118, nonce="payment-nonce-1", issued_at_ns=NOW-10_000,
        freshness_ns=30_000_000_000, sink_id="Treasury-Payment-Finality-Sink", boundary_id="Treasury-Settlement-Boundary",
        scope=("SETTLE",),
        payload={"recipient":"Applicant-472","amount_minor":25000,"currency":"LCU","program":"National-Relief-2026","purpose":"Flood-Relief"},
        runtime_evidence_digest="runtime-ok", authority_context={}
    )
    base.update(overrides)
    return CandidateAct(**base)
