from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import pytest

from finality_ref.errors import ReplayDetected
from finality_ref.state import InMemoryConsumptionStore, SQLiteConsumptionStore
from sovereignty_ref.scenarios import payment_candidate
from .conftest import build_stack, default_sovereignty_policy
from .test_public_benefit_payment import payment_policy


@pytest.mark.parametrize("workers", [2,3,4,8,16,32])
def test_in_memory_single_use_under_concurrent_payment_effectuation(workers):
    s=build_stack(payment_candidate(),sov_policy=payment_policy(payment_candidate()))
    cap=s["authority_plane"].authorize(s["candidate"],compute=s["compute"],evidence=s["jurisdiction_evidence"],approvals=s["approvals"])
    def call():
        try:
            s["sink"].effectuate(s["candidate"],cap); return "ok"
        except ReplayDetected:
            return "replay"
    with ThreadPoolExecutor(max_workers=workers) as ex:
        results=list(ex.map(lambda _:call(),range(workers)))
    assert results.count("ok")==1
    assert len(s["effector"].records)==1


@pytest.mark.parametrize("workers", [2,4,8,16])
def test_sqlite_single_use_under_concurrent_payment_effectuation(tmp_path, workers):
    store=SQLiteConsumptionStore(tmp_path/f"consumed-{workers}.db")
    c=payment_candidate(); s=build_stack(c,sov_policy=payment_policy(c),consumption=store)
    cap=s["authority_plane"].authorize(s["candidate"],compute=s["compute"],evidence=s["jurisdiction_evidence"],approvals=s["approvals"])
    def call():
        try:
            s["sink"].effectuate(s["candidate"],cap); return "ok"
        except ReplayDetected:
            return "replay"
    with ThreadPoolExecutor(max_workers=workers) as ex:
        results=list(ex.map(lambda _:call(),range(workers)))
    assert results.count("ok")==1
    assert len(s["effector"].records)==1
