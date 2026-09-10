from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
# Reuse the environment capture used by the core benchmark so the result is self-describing.
sys.path.insert(0, str(ROOT / "scripts"))
from benchmark import environment_snapshot

from finality_ref.authority import ProtectedAuthority
from finality_ref.crypto import HMACAuthenticator
from finality_ref.effectors import PaymentEffector
from finality_ref.evidence import EvidenceStore
from finality_ref.models import CandidateAct, SinkContext
from finality_ref.policy import Policy
from finality_ref.sink import FinalitySink
from finality_ref.state import InMemoryConsumptionStore, ProtectedState
from sovereignty_ref.authority_plane import AuthorityPlane, bind_governance_context
from sovereignty_ref.models import Approval, ComputeContext, JurisdictionEvidence, governance_subject_digest
from sovereignty_ref.policy import SovereigntyPolicy
from sovereignty_ref.verification import PrincipalVerifierRegistry

NOW = 1_800_000_000_000_000_000


def percentile(values, p):
    v = sorted(values)
    idx = min(len(v) - 1, max(0, int(round((len(v) - 1) * p))))
    return v[idx] / 1000.0


def summary(ns_values):
    return {
        "n": len(ns_values),
        "mean_us": statistics.fmean(ns_values) / 1000.0,
        "p50_us": percentile(ns_values, .50),
        "p95_us": percentile(ns_values, .95),
        "p99_us": percentile(ns_values, .99),
        "min_us": min(ns_values) / 1000.0,
        "max_us": max(ns_values) / 1000.0,
    }


def make_candidate(i: int) -> CandidateAct:
    return CandidateAct(
        act_id=f"sov-bench-payment-{i}",
        act_class="public-benefit-payment",
        effect_class="payment-ledger",
        source="external-benefit-ai",
        destination="Domestic-Payment-Rail",
        purpose="Flood-Relief",
        jurisdiction="COUNTRY-C",
        policy_epoch=118,
        nonce=f"sov-bench-nonce-{i}",
        issued_at_ns=NOW,
        freshness_ns=30_000_000_000,
        sink_id="Treasury-Payment-Finality-Sink",
        boundary_id="Treasury-Settlement-Boundary",
        scope=("SETTLE",),
        payload={
            "recipient": "Applicant-472",
            "amount_minor": 25_000,
            "currency": "LCU",
            "program": "National-Relief-2026",
            "purpose": "Flood-Relief",
        },
        runtime_evidence_digest="runtime-ok",
        authority_context={},
    )


def sign_evidence(item: JurisdictionEvidence, signer: HMACAuthenticator) -> JurisdictionEvidence:
    unsigned = replace(item, key_id=signer.key_id, signature="")
    return replace(unsigned, signature=signer.sign(unsigned.unsigned()))


def sign_approval(item: Approval, signer: HMACAuthenticator) -> Approval:
    unsigned = replace(item, key_id=signer.key_id, signature="")
    return replace(unsigned, signature=signer.sign(unsigned.unsigned()))


def build_stack():
    compute = ComputeContext(
        provider_id="global-ai-provider",
        compute_jurisdiction="FOREIGN",
        workload_id="workload-1",
        model_id="model-1",
        runtime_evidence_digest="runtime-ok",
        session_id="session-1",
    )

    ev1_signer = HMACAuthenticator(b"sov-bench-evidence-national", key_id="ev-national-v1")
    ev2_signer = HMACAuthenticator(b"sov-bench-evidence-network", key_id="ev-network-v1")
    ev1 = sign_evidence(JurisdictionEvidence(
        evidence_id="je-gateway", evidence_type="gateway-attestation", asserted_jurisdiction="COUNTRY-C",
        issuer="national-trust-service", subject="finality-sink", observed_at_ns=NOW-1_000_000,
        expires_at_ns=NOW+60_000_000_000, trust_class="protected", value_digest="gateway-ok",
    ), ev1_signer)
    ev2 = sign_evidence(JurisdictionEvidence(
        evidence_id="je-network", evidence_type="network-context", asserted_jurisdiction="COUNTRY-C",
        issuer="regulated-network", subject="effect-boundary", observed_at_ns=NOW-2_000_000,
        expires_at_ns=NOW+60_000_000_000, trust_class="network-derived", value_digest="network-ok",
    ), ev2_signer)
    evidence = (ev1, ev2)

    evidence_registry = PrincipalVerifierRegistry()
    evidence_registry.add("national-trust-service", ev1_signer)
    evidence_registry.add("regulated-network", ev2_signer)

    approval_signer = HMACAuthenticator(b"sov-bench-policy-owner", key_id="policy-owner-v1")
    approval_registry = PrincipalVerifierRegistry()
    approval_registry.add("policy-owner-1", approval_signer)

    sov_policy = SovereigntyPolicy(
        authority_jurisdiction="COUNTRY-C",
        policy_epoch=118,
        allowed_compute_jurisdictions=frozenset({"FOREIGN"}),
        allowed_compute_providers=frozenset({"global-ai-provider"}),
        required_runtime_evidence_digest="runtime-ok",
        trusted_evidence_issuers=frozenset({"national-trust-service", "regulated-network"}),
        allowed_evidence_types=frozenset({"gateway-attestation", "network-context"}),
        min_evidence_items=2,
        min_independent_evidence_issuers=2,
        require_authority_jurisdiction_assertion=True,
        required_approval_roles=frozenset({"policy-owner"}),
        approval_threshold=1,
        payload_required_fields=frozenset({"recipient", "amount_minor", "currency", "program", "purpose"}),
        payload_numeric_limits={"amount_minor": (1, 100_000)},
        payload_allowed_values={
            "currency": frozenset({"LCU"}),
            "program": frozenset({"National-Relief-2026"}),
            "purpose": frozenset({"Flood-Relief"}),
        },
    )

    core_auth = HMACAuthenticator(b"sov-benchmark-core-key", key_id="core-authority-v1")
    evidence_store = EvidenceStore(core_auth)
    state = ProtectedState(default_quota=1_000_000, default_budget=1_000_000)
    core_policy = Policy(
        policy_epoch=118,
        allowed_purposes=frozenset({"Flood-Relief"}),
        allowed_jurisdictions=frozenset({"COUNTRY-C"}),
        allowed_sinks=frozenset({"Treasury-Payment-Finality-Sink"}),
        allowed_boundaries=frozenset({"Treasury-Settlement-Boundary"}),
        allowed_effect_classes=frozenset({"payment-ledger"}),
        allowed_scopes=frozenset({"SETTLE"}),
        required_runtime_evidence_digest="runtime-ok",
    )
    protected_authority = ProtectedAuthority(
        authority_id="authority-COUNTRY-C",
        policy=core_policy,
        state=state,
        evidence_store=evidence_store,
        authenticator=core_auth,
        capability_ttl_ns=5_000_000_000,
        clock=lambda: NOW,
    )
    authority_plane = AuthorityPlane(
        policy=sov_policy,
        protected_authority=protected_authority,
        clock=lambda: NOW,
        jurisdiction_evidence_verifiers=evidence_registry,
        approval_verifiers=approval_registry,
        require_authenticated_evidence=True,
        require_authenticated_approvals=True,
    )
    effector = PaymentEffector()
    sink = FinalitySink(
        context=SinkContext(
            "Treasury-Payment-Finality-Sink", "Treasury-Settlement-Boundary", 118,
            frozenset({"SETTLE"}), "payment-ledger"
        ),
        authenticator=core_auth,
        evidence_store=evidence_store,
        protected_state=state,
        consumption_store=InMemoryConsumptionStore(),
        effect_handle=effector.bind_for_sink(),
        clock=lambda: NOW,
    )
    return {
        "compute": compute,
        "evidence": evidence,
        "approval_signer": approval_signer,
        "sov_policy": sov_policy,
        "authority_plane": authority_plane,
        "sink": sink,
    }


def prepare_case(stack, i: int):
    c = make_candidate(i)
    ap = Approval(
        approver_id="policy-owner-1",
        role="policy-owner",
        candidate_digest=governance_subject_digest(c),
        policy_epoch=118,
        approved_at_ns=NOW-1_000_000,
        expires_at_ns=NOW+60_000_000_000,
    )
    ap = sign_approval(ap, stack["approval_signer"])
    approvals = (ap,)
    bound = bind_governance_context(c, compute=stack["compute"], evidence=stack["evidence"], approvals=approvals)
    return bound, approvals


def run(iterations: int, warmup: int):
    stack = build_stack()
    c0, a0 = prepare_case(stack, -1)

    # Warm semantic policy and authorization/sink paths. Unique candidates are used
    # where protected nonce/state transitions are involved.
    for _ in range(warmup):
        stack["sov_policy"].validate(c0, stack["compute"], stack["evidence"], a0, NOW)
    for i in range(warmup):
        c, aps = prepare_case(stack, -10_000 - i)
        cap = stack["authority_plane"].authorize(c, compute=stack["compute"], evidence=stack["evidence"], approvals=aps)
        stack["sink"].effectuate(c, cap)

    policy_times = []
    for _ in range(iterations):
        t = time.perf_counter_ns()
        stack["sov_policy"].validate(c0, stack["compute"], stack["evidence"], a0, NOW)
        policy_times.append(time.perf_counter_ns() - t)

    issue_cases = [prepare_case(stack, 100_000 + i) for i in range(iterations)]
    issue_times = []
    issued = []
    for c, aps in issue_cases:
        t = time.perf_counter_ns()
        cap = stack["authority_plane"].authorize(c, compute=stack["compute"], evidence=stack["evidence"], approvals=aps)
        issue_times.append(time.perf_counter_ns() - t)
        issued.append((c, cap))

    # Verify-only uses one already-issued act/capability repeatedly so the measured
    # path excludes issuance and replay consumption.
    verify_candidate, verify_cap = issued[0]
    verify_times = []
    for _ in range(iterations):
        t = time.perf_counter_ns()
        stack["sink"].verify(verify_candidate, verify_cap)
        verify_times.append(time.perf_counter_ns() - t)

    full_cases = [prepare_case(stack, 200_000 + i) for i in range(iterations)]
    full_times = []
    for c, aps in full_cases:
        t = time.perf_counter_ns()
        cap = stack["authority_plane"].authorize(c, compute=stack["compute"], evidence=stack["evidence"], approvals=aps)
        stack["sink"].effectuate(c, cap)
        full_times.append(time.perf_counter_ns() - t)

    return {
        "schema": "digital-sovereignty-authority-plane-benchmark-v1",
        "environment": environment_snapshot(),
        "scenario": "public-benefit-country-c / authenticated governance inputs",
        "timing_boundary": (
            "Evidence collection, remote attestation acquisition, policy retrieval, issuer-side signing, "
            "and Candidate/approval construction are outside the timed authority/sink hot path. "
            "Authority-plane measurements include evidence/approval signature verification, sovereignty policy evaluation, "
            "governance-context binding verification, core protected authorization, protected state transition, "
            "validation-evidence commitment, and capability issuance. Full measurements additionally include "
            "Finality-Sink verification, in-memory single-use claim, guarded payment-effector commit, and receipt signing."
        ),
        "iterations": iterations,
        "warmup_iterations": warmup,
        "clock": "time.perf_counter_ns",
        "parameters": {
            "authority_jurisdiction": "COUNTRY-C",
            "compute_jurisdiction": "FOREIGN",
            "compute_provider": "global-ai-provider",
            "policy_epoch": 118,
            "evidence_items": 2,
            "independent_evidence_issuers": 2,
            "approval_threshold": 1,
            "required_approval_roles": ["policy-owner"],
            "authenticated_evidence": True,
            "authenticated_approvals": True,
            "candidate_freshness_ns": 30_000_000_000,
            "capability_ttl_ns": 5_000_000_000,
            "max_future_skew_ns": 1_000_000_000,
            "consumption_store": "InMemoryConsumptionStore",
            "reference_authentication": "HMAC-SHA256",
        },
        "measurements": {
            "sovereignty_policy_validate_only": summary(policy_times),
            "authenticated_authority_plane_issue": summary(issue_times),
            "sink_verify_only_after_sovereignty_issue": summary(verify_times),
            "authenticated_authority_plus_sink_effectuation": summary(full_times),
        },
        "warning": (
            "These are user-space CPython reference measurements, not certified or production latency guarantees. "
            "They do not include remote evidence acquisition, WAN round trips, real TPM/TEE/GPU/RATS verification, "
            "durable database/ledger commit latency, or production network/device I/O."
        ),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iterations", type=int, default=3000)
    ap.add_argument("--warmup", type=int, default=1000)
    ap.add_argument("--output", default="benchmarks/sovereignty-python-local.json")
    args = ap.parse_args()
    result = run(args.iterations, args.warmup)
    text = json.dumps(result, indent=2) + "\n"
    out = ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    print(text)


if __name__ == "__main__":
    main()
