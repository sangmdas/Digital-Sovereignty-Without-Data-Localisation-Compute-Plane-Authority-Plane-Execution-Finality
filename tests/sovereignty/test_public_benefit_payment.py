from __future__ import annotations

from dataclasses import replace
import pytest

from finality_ref.errors import ReplayDetected, ValidationDenied, VerificationFailed
from finality_ref.canonical import CanonicalizationError
from sovereignty_ref.scenarios import payment_candidate
from .conftest import build_stack, default_sovereignty_policy


def payment_policy(c):
    return default_sovereignty_policy(
        c,
        payload_required_fields=frozenset({"recipient","amount_minor","currency","program","purpose"}),
        payload_numeric_limits={"amount_minor":(1,100_000)},
        payload_allowed_values={"currency":frozenset({"LCU"}),"program":frozenset({"National-Relief-2026"}),"purpose":frozenset({"Flood-Relief"})},
    )


def test_payment_happy_path_and_single_use():
    c=payment_candidate(); s=build_stack(c,sov_policy=payment_policy(c)); cap=s["authority_plane"].authorize(s["candidate"],compute=s["compute"],evidence=s["jurisdiction_evidence"],approvals=s["approvals"])
    assert s["sink"].effectuate(s["candidate"],cap).effect_status=="EFFECTIVE"
    with pytest.raises(ReplayDetected):
        s["sink"].effectuate(s["candidate"],cap)


@pytest.mark.parametrize("amount", [1,2,100,999,1_000,25_000,50_000,99_999,100_000])
def test_payment_amount_boundary_allowed(amount):
    c=payment_candidate(payload={**payment_candidate().payload,"amount_minor":amount}); s=build_stack(c,sov_policy=payment_policy(c))
    assert s["authority_plane"].authorize(s["candidate"],compute=s["compute"],evidence=s["jurisdiction_evidence"],approvals=s["approvals"])


@pytest.mark.parametrize("amount", [-10,-1,0,100_001,250_000,1_000_000,2**31-1])
def test_payment_amount_out_of_policy_rejected(amount):
    c=payment_candidate(payload={**payment_candidate().payload,"amount_minor":amount}); s=build_stack(c,sov_policy=payment_policy(c))
    with pytest.raises(ValidationDenied,match="payload_numeric_out_of_range:amount_minor"):
        s["authority_plane"].authorize(s["candidate"],compute=s["compute"],evidence=s["jurisdiction_evidence"],approvals=s["approvals"])


@pytest.mark.parametrize("value", ["25000",None,True,[],{}])
def test_payment_amount_wrong_type_rejected(value):
    c=payment_candidate(payload={**payment_candidate().payload,"amount_minor":value}); s=build_stack(c,sov_policy=payment_policy(c))
    with pytest.raises(ValidationDenied,match="payload_numeric_invalid:amount_minor"):
        s["authority_plane"].authorize(s["candidate"],compute=s["compute"],evidence=s["jurisdiction_evidence"],approvals=s["approvals"])

def test_payment_float_is_rejected_even_before_policy_by_canonicalization():
    c=payment_candidate(payload={**payment_candidate().payload,"amount_minor":25.0})
    with pytest.raises(CanonicalizationError,match="floating point values are forbidden"):
        build_stack(c,sov_policy=payment_policy(c))


@pytest.mark.parametrize("recipient", ["Applicant-999","Applicant-001","Treasury","Foreign-Account","attacker"])
def test_recipient_substitution_after_authorization_fails(recipient):
    c=payment_candidate(); s=build_stack(c,sov_policy=payment_policy(c)); cap=s["authority_plane"].authorize(s["candidate"],compute=s["compute"],evidence=s["jurisdiction_evidence"],approvals=s["approvals"])
    p=dict(s["candidate"].payload); p["recipient"]=recipient
    with pytest.raises(VerificationFailed,match="candidate_digest_mismatch"):
        s["sink"].verify(replace(s["candidate"],payload=p),cap)


@pytest.mark.parametrize("amount", [25_001,30_000,50_000,100_000,250_000])
def test_amount_increase_after_authorization_fails_even_if_new_value_could_be_policy_valid(amount):
    c=payment_candidate(); s=build_stack(c,sov_policy=payment_policy(c)); cap=s["authority_plane"].authorize(s["candidate"],compute=s["compute"],evidence=s["jurisdiction_evidence"],approvals=s["approvals"])
    p=dict(s["candidate"].payload); p["amount_minor"]=amount
    with pytest.raises(VerificationFailed,match="candidate_digest_mismatch"):
        s["sink"].verify(replace(s["candidate"],payload=p),cap)


@pytest.mark.parametrize("currency", ["USD","EUR","INR","BTC",""])
def test_wrong_currency_rejected(currency):
    c=payment_candidate(payload={**payment_candidate().payload,"currency":currency}); s=build_stack(c,sov_policy=payment_policy(c))
    with pytest.raises(ValidationDenied,match="payload_value_not_allowed:currency"):
        s["authority_plane"].authorize(s["candidate"],compute=s["compute"],evidence=s["jurisdiction_evidence"],approvals=s["approvals"])


@pytest.mark.parametrize("program", ["General-Budget","Election-Fund","Unknown","National-Relief-2025",""])
def test_wrong_program_rejected(program):
    c=payment_candidate(payload={**payment_candidate().payload,"program":program}); s=build_stack(c,sov_policy=payment_policy(c))
    with pytest.raises(ValidationDenied,match="payload_value_not_allowed:program"):
        s["authority_plane"].authorize(s["candidate"],compute=s["compute"],evidence=s["jurisdiction_evidence"],approvals=s["approvals"])


@pytest.mark.parametrize("missing", ["recipient","amount_minor","currency","program","purpose"])
def test_missing_payment_field_rejected(missing):
    c=payment_candidate(); p=dict(c.payload); p.pop(missing); c=replace(c,payload=p); s=build_stack(c,sov_policy=payment_policy(c))
    with pytest.raises(ValidationDenied,match=f"payload_field_missing:{missing}"):
        s["authority_plane"].authorize(s["candidate"],compute=s["compute"],evidence=s["jurisdiction_evidence"],approvals=s["approvals"])
