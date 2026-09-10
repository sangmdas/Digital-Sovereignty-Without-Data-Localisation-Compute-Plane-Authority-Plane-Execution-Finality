# Digital-Sovereignty / Compute-Plane–Authority-Plane Test Matrix
## Granular test design, exact parameters, cross-language scope, latency measurements, legacy-feasibility checks, and non-claims

## 1. Verification summary

Clean reference run:

- Total Python tests: **741**
- Digital-sovereignty-specific tests: **260**
- Inherited execution-finality/core tests: **481**
- Measured Python source statements: **990**
- Statements missed: **0**
- Statement coverage: **100%**
- Core Node.js positive interoperability vectors: **20/20**
- Core Go positive interoperability vectors: **20/20**
- Node.js canonicalization conformance: **9/9**
- Go canonicalization conformance: **9/9**
- Node.js full Finality Sink baseline vector: **PASS**
- Node.js full Finality Sink Unicode vector: **PASS**
- Go full Finality Sink baseline vector: **PASS**
- Go full Finality Sink Unicode vector: **PASS**

The coverage number is statement coverage only. It is not proof of complete security, complete state-space coverage, or deployment non-bypassability.

## 2. Implementation languages and test responsibility

| Language | Version in recorded environment | What it verifies |
|---|---|---|
| Python | CPython 3.13.5 | Complete core + sovereignty layer, all 741 tests, concurrency, policy matrices, scenario tests |
| Node.js | 22.16.0 | Independent portable canonicalization and core finality verification vectors |
| Go | 1.23.2 | Independent portable canonicalization and core finality verification vectors |

Important scope boundary: the sovereignty-specific `ComputeContext`, `JurisdictionEvidence`, and `Approval` objects are presently implemented/tested in Python. Cross-language interoperability currently validates the common finality substrate, not a standardized sovereignty wire format.

## 3. Test framework and execution model

The Python suite uses `pytest 9.0.2`.

Parameterized cases are declared with `pytest.mark.parametrize`, allowing exact values to be enumerated and independently reported by the test collector.

Expected-denial cases use explicit exception assertions, primarily:

- `ValidationDenied` for pre-issuance policy/authentication failure;
- `VerificationFailed` for sink-side mismatch after authority issuance;
- `ReplayDetected` for repeated capability use;
- `EffectDenied` for direct-effect and post-consumption effect failures;
- `CanonicalizationError` for forbidden security-bound representations such as floats.

Concurrency tests use Python `ThreadPoolExecutor` so multiple workers race the same capability concurrently.

## 4. Deterministic clock parameters

The sovereignty scenario tests use:

`NOW = 1_800_000_000_000_000_000 ns`

Reference future-skew allowance:

`1,000,000,000 ns` = 1 s.

Default evidence expiry:

`NOW + 60,000,000,000 ns` = +60 s.

Default approval expiry:

`NOW + 60,000,000,000 ns` = +60 s.

Core capability TTL:

`5,000,000,000 ns` = 5 s.

The Candidate's own freshness can be shorter or longer; capability expiry is bounded by Candidate freshness.

## 5. Sovereignty-specific test distribution

| Module | Collected tests | Primary objective |
|---|---:|---|
| `test_authenticated_governance_inputs.py` | 13 | issuer/approver authentication, mutation after signature, missing verifier fail-closed |
| `test_compute_authority_separation.py` | 13 | foreign/global compute may propose; direct effect denied; post-authorization Candidate mutation rejected |
| `test_context_binding_attacks.py` | 18 | compute/evidence/approval digest substitution and post-authorization authority-context mutation |
| `test_cross_border_compute_matrix.py` | 35 | 5 authority jurisdictions × 6 compute jurisdictions plus blocked-location cases |
| `test_disaster_scenario.py` | 23 | public-warning constraints, hazard/severity combinations, region mutation |
| `test_fail_closed_and_policy.py` | 18 | provider allowlist, runtime evidence, epoch mismatch, payload type |
| `test_healthcare_scenario.py` | 22 | clinical payload requirements, purpose-bound operation, consent, patient/diagnosis mutation |
| `test_jurisdiction_evidence_matrix.py` | 36 | issuer/type/trust class, expiry/future time, evidence count, independent issuers, jurisdiction assertion |
| `test_multi_party_governance.py` | 21 | threshold matrix, required roles, stale/future/wrong-candidate approvals, duplicate approver |
| `test_public_benefit_payment.py` | 48 | amount range/type, recipient substitution, amount increase, currency/program binding, single-use replay |
| `test_replay_and_concurrency.py` | 10 | in-memory and SQLite concurrent single-use races with 2–32 workers |
| `test_small_helpers_and_branches.py` | 3 | helper determinism and remaining fail-closed branches |
| **Total** | **260** | |

## 6. Cross-border compute/authority matrix

Authority jurisdictions:

`COUNTRY-A`, `COUNTRY-B`, `COUNTRY-C`, `COUNTRY-D`, `COUNTRY-E`

Permitted compute jurisdictions:

`FOREIGN`, `US`, `EU`, `IN`, `REGION-X`, `REGION-Y`

Cross-product:

`5 × 6 = 30` allowed state-machine combinations.

Blocked/unregistered values:

`BLOCKED-1`, `BLOCKED-2`, `UNREGISTERED`, `UNKNOWN`, `SANCTIONED`

Expected property: the authority jurisdiction and compute jurisdiction may differ when configured policy permits it. The test does not determine whether any real cross-border transfer is lawful.

## 7. Compute-provider negative matrix

Rejected provider IDs:

`unknown-provider`, `attacker`, `unregistered`, `shadow-cloud`, empty string.

Expected failure:

`compute_provider_not_allowed`

## 8. Runtime-evidence negative matrix

Rejected runtime digest values:

`bad`, `stale`, `revoked`, `unknown`, empty string.

Expected failure when `runtime-ok` is required:

`compute_runtime_evidence_mismatch`

A separate test deliberately sets Candidate runtime evidence different from ComputeContext runtime evidence with no global required digest and expects:

`candidate_compute_runtime_binding_mismatch`

This verifies binding, not only allowlist lookup.

## 9. Policy-epoch matrix

Against healthcare Candidate epoch `184`, the test uses:

`0`, `1`, `72`, `183`, `185`, `2^31-1`.

All are expected to fail as `sovereignty_policy_epoch_mismatch`.

## 10. Jurisdiction-evidence baseline

Default bundle:

| Evidence | Issuer | Type | Trust class | Observed | Expires |
|---|---|---|---|---:|---:|
| gateway | `national-trust-service` | `gateway-attestation` | `protected` | NOW−1 ms | NOW+60 s |
| network | `regulated-network` | `network-context` | `network-derived` | NOW−2 ms | NOW+60 s |

Policy requirements:

- minimum 2 evidence items;
- minimum 2 independent issuers;
- an authority-jurisdiction assertion;
- allowed issuer;
- allowed type;
- allowed trust class;
- non-expired;
- not more than 1 s future-dated.

## 11. Evidence issuer negatives

Rejected issuers:

`unknown`, `self-asserted`, `untrusted-cloud`, `random-service`, `attacker`

Expected failure:

`untrusted_jurisdiction_evidence_issuer`

## 12. Evidence type negatives

Rejected types:

`ip-only`, `gnss-unsigned`, `user-claim`, `free-text`, `dns-label`

Expected failure:

`jurisdiction_evidence_type_not_allowed`

## 13. Evidence expiry variation

Evidence expiration is moved into the past by:

- 1 ns;
- 10 ns;
- 1,000 ns;
- 1,000,000 ns;
- 10,000,000,000 ns.

Expected failure:

`jurisdiction_evidence_expired`

## 14. Evidence future-time variation

With a 1-second allowed skew, the test sets observation time into the future by:

- 1,000,000,001 ns;
- 2,000,000,000 ns;
- 5,000,000,000 ns;
- 60,000,000,000 ns.

Expected failure:

`jurisdiction_evidence_from_future`

## 15. Evidence-count and independence variation

Evidence counts `0` and `1` fail the minimum of `2`.

Two objects with the same issuer fail:

`insufficient_independent_evidence_issuers`

Two objects with the same evidence ID fail:

`duplicate_jurisdiction_evidence`

## 16. Authority-jurisdiction assertion negatives

Both evidence records are rewritten to assert each of:

`COUNTRY-X`, `COUNTRY-Y`, `FOREIGN`, `NONE`, `UNKNOWN`

Expected failure when the policy requires an authority-jurisdiction assertion:

`authority_jurisdiction_evidence_missing`

## 17. Trust-class matrix

Accepted reference classes:

`declared`, `network-derived`, `protected`, `independently-verifiable`

Rejected classes:

`magically-certain`, `absolute-geography`, `unconfigured`, empty string.

This intentionally prevents a trust-class label from being treated as mathematical proof.

## 18. Authenticated evidence mutation tests

Strict mode uses separate deterministic HMAC-SHA256 authenticators per configured issuer.

A valid evidence object is signed, then one field is changed without re-signing:

- asserted jurisdiction;
- subject;
- value digest;
- expiry;
- trust class.

Expected result:

`jurisdiction_evidence_signature_invalid`

The suite also verifies fail-closed behavior when authenticated evidence is required but the verifier registry is missing.

## 19. Approval threshold matrix

Exact tested combinations:

| Threshold | Approvals present | Expected |
|---:|---:|---|
| 0 | 0 | allow |
| 1 | 0 | deny |
| 1 | 1 | allow |
| 2 | 0 | deny |
| 2 | 1 | deny |
| 2 | 2 | allow |
| 3 | 2 | deny |
| 3 | 3 | allow |
| 4 | 3 | deny |
| 4 | 4 | allow |

## 20. Required-role matrix

| Required roles | Present roles | Expected |
|---|---|---|
| treasury | treasury | allow |
| treasury + benefit-agency | treasury + benefit-agency | allow |
| treasury + benefit-agency | treasury | deny |
| treasury + benefit-agency | benefit-agency | deny |
| treasury + auditor | treasury + benefit-agency | deny |
| none | none | allow |

## 21. Approval semantic negatives

Mutations:

- wrong Candidate digest;
- wrong epoch;
- expired approval (`NOW−1`);
- future approval (`NOW+1,000,000,001 ns`).

Expected result: pre-issuance `ValidationDenied`.

## 22. Duplicate approver attack

Two approvals are created using identical approver identity `same-person` with roles `treasury` and `benefit-agency`.

A 2-of-N threshold does not count the same principal twice.

Expected failure:

`duplicate_approver`

## 23. Authenticated approval mutation tests

A valid approval is HMAC-authenticated and then modified without re-signing in fields including:

- role;
- Candidate digest;
- policy epoch;
- expiry;
- approval time.

Expected failure:

`approval_signature_invalid`

The suite separately verifies fail-closed behavior when authenticated approvals are required but the verifier registry is unavailable.

## 24. Governance-context pre-issuance substitution

The Authority Plane recomputes expected governance bindings. The suite mutates:

- compute context digest;
- jurisdiction evidence digest;
- approvals digest;
- compute provider ID;
- compute jurisdiction.

Expected failure before capability issuance:

`governance_context_binding_mismatch:<field>`

## 25. Compute-context semantic substitution

The suite changes individual ComputeContext fields including provider, jurisdiction, workload, model, runtime evidence, and session values.

Expected result is fail-closed when the Candidate's bound governance context no longer corresponds to the supplied ComputeContext or policy.

## 26. Post-authorization governance mutation

After capability issuance the Candidate authority context is modified in load-bearing governance fields.

Because the capability binds the complete Candidate digest, sink verification rejects the changed Candidate.

Expected failure:

`candidate_digest_mismatch`

## 27. Direct Compute Plane effectuation

The Compute Plane attempts to call its direct effectuation method.

Expected exception:

`EffectDenied("compute_plane_has_no_effectuation_authority")`

The generic guarded effector direct path is also tested and must deny with a Finality-Sink-required error.

## 28. Healthcare Candidate

| Field | Value |
|---|---|
| Jurisdiction | `COUNTRY-A` |
| Epoch | 184 |
| Effect | `storage-write` |
| Destination | `National-Hospital-EHR` |
| Purpose | `Clinical-Treatment` |
| Scope | `WRITE:/records` |
| Sink | `Hospital-EHR-Finality-Sink` |
| Boundary | `Hospital-EHR-Write-Boundary` |
| Freshness | 10 s |

Required payload:

`patient_id`, `operation`, `diagnosis`, `clinician_id`, `consent`

## 29. Healthcare missing-field matrix

Each field is removed independently:

`patient_id`, `operation`, `diagnosis`, `clinician_id`, `consent`

Expected failure:

`payload_field_missing:<field>`

## 30. Healthcare operation negatives

Rejected operation values:

`export-record`, `delete-record`, `advertising-export`, `bulk-download`, `share-external`, `overwrite-record`

Expected failure:

`payload_value_not_allowed:operation`

## 31. Healthcare consent negatives

Rejected values:

`missing`, `revoked`, `unknown`, `false`, empty string.

Expected failure:

`payload_value_not_allowed:consent`

## 32. Healthcare post-authorization mutation

After authority issuance, the test separately changes patient, diagnosis, clinician, operation, and consent.

Expected sink failure:

`candidate_digest_mismatch`

This proves act binding only; it does not prove the diagnosis is medically correct.

## 33. Disaster Candidate

| Field | Value |
|---|---|
| Jurisdiction | `COUNTRY-B` |
| Epoch | 73 |
| Effect | `network-egress` |
| Destination | `National-Telecom-Emergency-Gateway` |
| Purpose | `Flood-Emergency-Warning` |
| Scope | `SEND` |
| Sink | `National-Alert-Finality-Sink` |
| Boundary | `National-Alert-Dispatch-Boundary` |
| Freshness | 600 s |

## 34. Disaster hazard/severity cross-product

Allowed hazards:

`flood`, `cyclone`, `earthquake`, `wildfire`

Allowed severities:

`severe`, `extreme`

Cross-product:

`4 × 2 = 8` allowed combinations.

## 35. Disaster negative categories

Rejected hazards:

`marketing`, `political-message`, `routine-notice`, `unknown`, empty string.

Required payload fields are independently removed.

## 36. Disaster region-expansion attacks

A capability issued for the original region is presented with Candidate region changed to:

`Entire-Country`, `District-Z`, `District-A-B-C-D`, `Foreign-Region`, `*`

Expected sink failure:

`candidate_digest_mismatch`

## 37. Public-benefit/payment Candidate

| Field | Value |
|---|---|
| Jurisdiction | `COUNTRY-C` |
| Epoch | 118 |
| Effect | `payment-ledger` |
| Destination | `Domestic-Payment-Rail` |
| Purpose | `Flood-Relief` |
| Scope | `SETTLE` |
| Sink | `Treasury-Payment-Finality-Sink` |
| Boundary | `Treasury-Settlement-Boundary` |
| Freshness | 30 s |

Payload:

- recipient `Applicant-472`;
- amount `25,000` minor units;
- currency `LCU`;
- program `National-Relief-2026`;
- purpose `Flood-Relief`.

## 38. Payment amount policy

Range:

`1..100,000` minor units inclusive.

Allowed values tested:

`1`, `2`, `100`, `999`, `1,000`, `25,000`, `50,000`, `99,999`, `100,000`

Rejected numeric values:

`-10`, `-1`, `0`, `100,001`, `250,000`, `1,000,000`, `2^31−1`

## 39. Payment type matrix

Rejected wrong types:

- string `"25000"`;
- null;
- boolean;
- list;
- map;
- float `25.0`.

The float is rejected by the canonicalization layer before ordinary policy evaluation.

## 40. Recipient-substitution matrix

After issuance for `Applicant-472`, recipient is changed to:

`Applicant-999`, `Applicant-001`, `Treasury`, `Foreign-Account`, `attacker`

Expected failure:

`candidate_digest_mismatch`

## 41. Amount-escalation after authorization

Original authorized amount:

`25,000`

Changed values:

`25,001`, `30,000`, `50,000`, `100,000`, `250,000`

The first four are independently within the reference amount range, yet the old capability still fails. This verifies exact-act binding rather than "still policy-valid" substitution.

## 42. Currency and program negatives

Rejected currencies:

`USD`, `EUR`, `INR`, `BTC`, empty string.

Rejected programs:

`General-Budget`, `Election-Fund`, `Unknown`, `National-Relief-2025`, empty string.

Each required payment field is also independently removed.

## 43. Sequential replay

One valid payment capability is effectuated successfully once.

The exact same Candidate and capability are presented again.

Expected second result:

`ReplayDetected`

Expected guarded effector record count:

`1`

## 44. In-memory concurrent replay

Concurrent worker counts:

`2`, `3`, `4`, `8`, `16`, `32`

All workers race the same capability through `FinalitySink.effectuate()`.

Expected invariant for every worker count:

- exactly one `ok`;
- all remaining calls replay;
- exactly one effect record.

## 45. SQLite durable concurrent replay

Worker counts:

`2`, `4`, `8`, `16`

`SQLiteConsumptionStore` is backed by a temporary database for each parameterized test.

The store uses a unique capability key and transactional claim.

Expected invariant:

- exactly one successful effect;
- every other concurrent attempt is replay;
- exactly one effect record.

## 46. Inherited binding/adversarial tests

The 481 inherited tests additionally exercise:

- Candidate field mutation;
- HCAD/descriptor mutation;
- purpose/destination/scope/sink/boundary substitution;
- stale/future capability;
- policy epoch mismatch;
- evidence substitution;
- state transition mismatch;
- strict proof-of-possession/non-bearer presentation;
- fail-closed fault injection;
- multiple effect channels;
- deterministic fuzz mutations;
- Unicode canonicalization;
- cross-language vectors.

## 47. Cross-language canonicalization cases

The portable profile tests valid and invalid cases including:

- NFC decomposition/recomposition;
- decomposed Unicode object keys;
- normalized-key collision;
- supplementary-plane versus BMP key ordering;
- control characters;
- `<`, `>`, `&`;
- U+2028/U+2029;
- float rejection;
- unsafe integer rejection.

## 48. Unicode scope limitation

Runtime Unicode data versions differ:

- Python 15.1;
- Node 16.0;
- Go 15.0 runtime data.

The included vectors pass across all three, but the repository does not claim exhaustive behavior over all future Unicode assignments.

## 49. Core latency benchmark method

`benchmarks/latest.json` is produced with:

- clock: `time.perf_counter_ns`;
- warm-up: 1,000 iterations;
- measured: 3,000 iterations;
- reported statistics: mean, p50, p95, p99, minimum, maximum.

Measured core paths:

- canonical SHA-256;
- sink verification only;
- core authority + sink + guarded effectuation.

## 50. Core recorded latency

| Path | Mean | p50 | p95 | p99 | Max |
|---|---:|---:|---:|---:|---:|
| Canonical SHA-256 | 14.42 µs | 9.37 µs | 15.00 µs | 136.14 µs | 2.352 ms |
| Sink verify only | 348.33 µs | 247.30 µs | 846.53 µs | 2.252 ms | 4.713 ms |
| Authority + sink + effect | 1.724 ms | 1.392 ms | 3.190 ms | 5.218 ms | 11.345 ms |

These are user-space Python results, not certified platform performance.

## 51. Dedicated sovereignty benchmark method

`benchmarks/sovereignty-python-local.json` is produced by:

`scripts/benchmark_sovereignty.py`

Parameters:

| Parameter | Value |
|---|---|
| Scenario | public-benefit/payment |
| Authority jurisdiction | `COUNTRY-C` |
| Compute jurisdiction | `FOREIGN` |
| Compute provider | `global-ai-provider` |
| Policy epoch | 118 |
| Evidence items | 2 |
| Independent evidence issuers | 2 |
| Evidence authentication | enabled |
| Approval authentication | enabled |
| Approval threshold | 1 |
| Required role | `policy-owner` |
| Candidate freshness | 30 s |
| Capability TTL | 5 s |
| Future skew | 1 s |
| Reference authenticator | HMAC-SHA256 |
| Consumption store | in-memory for timed full path |
| Warm-up | 1,000 |
| Measured iterations | 3,000 |

## 52. Sovereignty benchmark timing boundary

Included in authenticated Authority Plane issuance timing:

- evidence signature verification;
- approval signature verification;
- sovereignty policy evaluation;
- governance-context binding verification;
- core protected authorization;
- state transition;
- validation-evidence commit;
- capability generation/signing.

Included in full timing in addition:

- sink verification;
- single-use claim;
- guarded payment effect;
- receipt signing.

Excluded:

- remote evidence acquisition;
- WAN policy service round trip;
- real TPM/TEE/GPU/RATS evidence acquisition;
- remote certificate-path building;
- issuer-side signing;
- real ledger/database/network commit latency.

## 53. Sovereignty recorded latency

| Path | Mean | p50 | p95 | p99 | Max |
|---|---:|---:|---:|---:|---:|
| Sovereignty policy validate only | 304.60 µs | 268.89 µs | 398.63 µs | 857.17 µs | 3.787 ms |
| Authenticated Authority Plane issue | 1.380 ms | 1.278 ms | 1.773 ms | 3.422 ms | 7.333 ms |
| Sink verify after sovereignty issuance | 319.23 µs | 286.23 µs | 426.25 µs | 801.71 µs | 4.533 ms |
| Authenticated Authority + sink + effect | 2.208 ms | 2.042 ms | 2.764 ms | 5.133 ms | 19.013 ms |

## 54. Latency target profiles

| Profile | Target | Reference placement |
|---|---:|---|
| Embedded control | 100 µs | MCU / secure element |
| Accelerator hot path | 500 µs | GPU / DPU / SmartNIC |
| UPF egress | 1 ms | UPF/N6 or SmartNIC |
| API gateway | 2 ms | reverse proxy / service mesh |
| Storage writer | 5 ms | transactional writer |
| Payment finality | 10 ms | payment/ledger bridge |
| Cross-region governance | 20 ms | regional egress gateway |
| Audit-heavy | 50 ms | model-output emitter |

These are engineering stress targets, not protocol requirements.

## 55. Target interpretation

The CPython implementation is a correctness reference.

It should **not** be presented as satisfying 100 µs embedded or 500 µs accelerator targets merely because some individual samples fall below them.

For high-rate profiles, the expected implementation strategy is native/device-resident code, pre-established trust, compact local state, and hardware-assisted key/state operations.

The 10 ms payment target is particularly important to interpret correctly: the recorded sovereignty full-path p99 is below 10 ms, but the observed maximum exceeds 10 ms and the measurement excludes a real payment rail or durable settlement operation. It is therefore not a 10 ms end-to-end payment claim.

## 56. Hot-path/cold-path testing model

The benchmark intentionally excludes remote trust-establishment operations from the measured hot path.

Cold-path candidates:

- remote attestation acquisition;
- policy retrieval;
- certificate-chain validation;
- trust-anchor establishment;
- key provisioning;
- issuer registration;
- policy epoch synchronization;
- revocation synchronization.

Hot-path candidates:

- Candidate reconstruction;
- digest/signature verification;
- local epoch/state check;
- replay lookup;
- consume/reserve;
- effect commit.

A deployment that requires a WAN approval round trip for every protected effect should benchmark that round trip separately; it is not hidden in the reference numbers.

## 57. Legacy HTTP/API feasibility checks

Reference deployment assumption:

`legacy app -> privileged egress/finality gateway -> external API`

For the security claim to hold, direct raw sockets, alternate proxies, and direct destination credentials must be blocked for the protected workload.

Candidate binding should include the exact method/resource/destination/body or body digest, purpose, policy epoch, and scope.

## 58. Legacy database/storage feasibility checks

Reference deployment assumption:

`legacy app -> staged mutation -> privileged DB writer/finality proxy -> database`

The protected writer must own the only credential capable of the covered write, or equivalent host/hypervisor enforcement must prevent direct access.

For exactly-once-like behavior, pass `capability_id` into the database transaction/idempotency mechanism.

## 59. Legacy payment feasibility checks

Reference deployment assumption:

`AI/legacy app -> Candidate payment -> treasury/payment gateway -> settlement system`

The gateway can verify Candidate bindings without replacing the entire upstream AI application.

A production system should integrate capability consumption with the actual downstream ledger/idempotency transaction. A separate software log is not enough for strong exactly-once claims.

## 60. Legacy telecom feasibility checks

Candidate finality can be applied at a UPF/N6, SmartNIC/DPU, emergency-alert gateway, or other already privileged network boundary.

The architecture does not require a sovereign service call per packet. The Candidate can represent establishment or release of a protected flow or message class.

## 61. Legacy agent feasibility checks

A legacy agent can continue producing tool calls if:

- the tool call is initially a Candidate Act;
- direct tool credentials are removed from the agent;
- the finality gateway/resource side owns the real effect credential;
- alternate effect paths are blocked.

A wrapper that calls `FinalitySink.verify()` but leaves the agent's original direct credential intact is not a non-bypassable deployment.

## 62. Legacy migration assurance levels

| Level | Example | Primary residual risk |
|---|---|---|
| L0 observe | log/audit | no prevention |
| L1 software gateway | proxy/sidecar/DB writer | privileged host bypass |
| L2 host/hypervisor | isolated service, host firewall, protected credentials | TCB compromise |
| L3 hardware/I/O assisted | TEE/HSM/DPU/IOMMU/device boundary | hardware/firmware/root-of-trust compromise |

These are engineering descriptions, not protocol conformance levels.

## 63. Legacy bypass cases that must remain explicit

A deployment is incomplete if the same protected effect remains reachable through:

- raw socket;
- direct DB credential;
- alternate broker;
- secondary API gateway;
- DMA mapping;
- peer-to-peer accelerator release;
- debug output;
- alternate renderer;
- admin API;
- alternate payment key;
- unguarded file/clipboard/IPC path.

## 64. What the latency tests do not measure

They do not measure:

- real HSM latency;
- real TEE transition cost;
- GPU/DPU/NIC firmware cost;
- network RTT;
- DNS/TLS connection establishment;
- remote attestation collection;
- certificate-chain path building;
- real database fsync;
- real payment settlement;
- telecom control-plane propagation;
- device actuation latency.

These must be benchmarked on the actual deployment stack.

## 65. What these tests do not prove

They do not prove:

- physical geography from metadata;
- legal validity of a jurisdictional rule;
- correctness of an AI diagnosis, alert, fraud score, or benefit recommendation;
- confidentiality of plaintext supplied to foreign compute;
- non-bypassability of a real host, kernel, NIC, GPU, DMA path, payment rail, or telecom network;
- absence of side/covert channels;
- resistance to a fully compromised Authority Plane or Finality Sink;
- availability of foreign AI infrastructure;
- semiconductor or model sovereignty;
- universal distributed exactly-once execution;
- that HMAC is the correct production trust model;
- that the sovereignty object format is already an interoperable multi-language IETF wire protocol;
- absence of unknown vulnerabilities.

## 66. Falsification-oriented review questions

An engineer reviewing a deployment should try to answer:

1. Can the workload create the same external effect without the Finality Sink?
2. Can an old capability authorize a changed Candidate?
3. Can one issuer masquerade as two independent evidence sources?
4. Can one approver count twice?
5. Can stale or future evidence pass?
6. Can Candidate/provider/jurisdiction context be swapped after authorization?
7. Can replay create two effects under concurrency?
8. Is the sink's local identity independent of caller input?
9. Is protected state rollback-resistant enough for the claimed assurance level?
10. Is the actual effect transaction tied to capability consumption?
11. Are cold-path trust inputs fresh enough for the hot-path decision?
12. Does the measured p99/max latency satisfy the actual deployment budget under realistic load?

## 67. Reproduction commands

Sovereignty-specific tests:

```bash
pytest tests/sovereignty -q
```

All Python tests:

```bash
pytest -q
```

Combined coverage:

```bash
pytest --cov=src/finality_ref --cov=src/sovereignty_ref --cov-report=term-missing -q
```

All core cross-language checks:

```bash
./scripts/run_all.sh
```

Sovereignty verification wrapper:

```bash
./scripts/run_sovereignty_checks.sh
```

Core benchmark:

```bash
python3 scripts/benchmark.py --iterations 3000 --output benchmarks/latest.json
```

Sovereignty benchmark:

```bash
python3 scripts/benchmark_sovereignty.py \
  --iterations 3000 \
  --warmup 1000 \
  --output benchmarks/sovereignty-python-local.json
```

## 68. Interpretation

The test suite demonstrates a concrete, falsifiable separation between computation and protected effectuation authority under the modeled conditions. It does not convert the reference implementation into a proof of national sovereignty, physical location, legal compliance, or universal non-bypassability.

For an IETF-oriented review, the strongest evidence in this package is not the raw test count. It is the combination of exact Candidate binding, independently configurable authority/compute jurisdictions, authenticated and thresholded governance inputs, sink-local reconstruction, replay races, explicit failure cases, reproducible latency measurements, multi-language verification of the common finality substrate, and clearly stated deployment conditions that can invalidate the claimed property.
