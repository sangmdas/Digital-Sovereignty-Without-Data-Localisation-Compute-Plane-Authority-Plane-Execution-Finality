from __future__ import annotations

from finality_ref.crypto import Authenticator


class PrincipalVerifierRegistry:
    """Maps a configured evidence issuer or approver identity to a verifier.

    The registry proves only that the configured principal authenticated the object;
    it does not make the underlying geographic, legal, medical, or policy assertion true.
    """
    def __init__(self):
        self._verifiers: dict[str, Authenticator] = {}

    def add(self, principal_id: str, verifier: Authenticator) -> None:
        self._verifiers[principal_id] = verifier

    def verify(self, principal_id: str, value, signature: str, key_id: str) -> bool:
        verifier = self._verifiers.get(principal_id)
        return bool(verifier and verifier.verify(value, signature, key_id))
