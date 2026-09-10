# Source-Draft to Implementation Mapping

This repository is grounded in `docs/source/draft-das-digital-sovereignty-finality-01.xml`. The mapping below records where major architectural propositions are represented in code and tests. It is not a claim that every sentence of the Internet-Draft is a normative implementation requirement.

| Draft concept | Implementation | Representative tests |
|---|---|---|
| Compute Plane may be globally distributed | `sovereignty_ref.models.ComputeContext`, `ComputePlane` | `test_cross_border_compute_matrix.py` |
| Compute is not authority | `ComputePlane.effectuate()` always denies | `test_compute_authority_separation.py` |
| Authority Plane independently governed | `sovereignty_ref.authority_plane.AuthorityPlane` | core + context-binding tests |
| Candidate Act remains Non-Effective | `finality_ref.models.CandidateAct`, `ActStatus.NON_EFFECTIVE` | inherited core tests + separation tests |
| Jurisdiction/location evidence is deployment-selected | `JurisdictionEvidence`, `SovereigntyPolicy` | `test_jurisdiction_evidence_matrix.py` |
| Cryptography binds evidence but does not prove geography | `PrincipalVerifierRegistry` + evidence digests | authenticated-governance tests; documented limitation |
| Multi-party/co-signed deployment | `Approval`, approval threshold, required roles | `test_multi_party_governance.py` |
| Protected validation evidence / LAVR | `finality_ref.ValidationEvidence`, `EvidenceStore` | inherited evidence/fail-closed tests |
| Scoped Finality Authority | `finality_ref.Capability` | inherited binding-integrity tests |
| Sink reconstructs load-bearing Candidate | `FinalitySink.verify()` + `build_hcad()` | inherited sink adversarial tests + scenario mutation tests |
| Replay/consumption before effect | `InMemoryConsumptionStore`, `SQLiteConsumptionStore` | `test_replay_and_concurrency.py` + inherited concurrency tests |
| Anti-bypass closure | `GuardedEffector`, deployment surface model | inherited channel and wide-channel tests |
| Existing IAM/OAuth/RATS can be inputs | modeled as context/evidence inputs, not replaced | documentation; no protocol conformance claim |
| Country need not operate every processor | compute/authority jurisdiction matrix | 30 cross-border allow cases |
| Foreign compute can propose but not complete protected action | scenario factories + guarded sinks | healthcare, disaster, payment scenario suites |

## Deliberately not implemented as factual truth

The reference does not decide legal jurisdiction, resolve conflicts of law, determine whether a country should trust an issuer, prove physical location, verify a particular vendor's remote-attestation format, or determine whether an AI output is correct. Those are deployment inputs or separate protocol/assurance problems.
