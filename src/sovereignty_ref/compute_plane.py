from __future__ import annotations

from dataclasses import replace
from typing import Any

from finality_ref.errors import EffectDenied
from finality_ref.models import CandidateAct

from .models import ComputeContext


class ComputePlane:
    """Reference compute-plane role: may propose Candidate Acts, never effectuate them."""
    def __init__(self, context: ComputeContext):
        self.context = context

    def propose(self, template: CandidateAct, *, payload: Any | None = None) -> CandidateAct:
        return replace(template, payload=template.payload if payload is None else payload, runtime_evidence_digest=self.context.runtime_evidence_digest)

    def effectuate(self, candidate: CandidateAct):
        raise EffectDenied("compute_plane_has_no_effectuation_authority")
