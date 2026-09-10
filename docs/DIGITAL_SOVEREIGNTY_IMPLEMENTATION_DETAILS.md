# Digital Sovereignty / Compute-Plane–Authority-Plane Reference Implementation
## Detailed implementation, test methodology, parameters, cross-language verification, latency model, legacy deployment feasibility, and limitations

## 1. Purpose and engineering question

This repository tests one narrow but operationally important architectural proposition: a workload may execute on foreign, regional, hyperscale, or otherwise externally operated compute while authority over selected externally effective acts remains independently governed.

The tested security invariant is:

> A Compute Plane may calculate, infer, transform, or propose a protected operation, but the modeled operation cannot become externally effective through the guarded path until a separately governed Authority Plane authorizes the exact Candidate Act and a Finality Sink independently verifies that authorization at the effectuation boundary.

The implementation does **not** assume that foreign compute is trustworthy, domestically controlled, legally subordinate to the authority jurisdiction, or physically located where metadata claims it is. The reference instead asks whether the **ability to compute** and the **ability to finalize a protected consequence** can be represented as different technical roles and tested as different trust boundaries.

## 2. Source architecture and implementation scope

The source Internet-Draft is preserved in:

`docs/source/draft-das-digital-sovereignty-finality-01.xml`

The executable implementation maps the following architectural elements into code:

- globally distributed Compute Plane;
- independently governed Authority Plane;
- Candidate Act;
- Non-Effective State;
- deployment-selected policy, jurisdiction, purpose, destination, runtime, freshness, revocation, replay, and approval predicates;
- protected state transition;
- protected validation evidence / LAVR-equivalent evidence object;
- scoped Finality Authority;
- Finality-Sink reconstruction and verification;
- consume/reserve-before-effect behavior;
- fail-closed error paths;
- anti-bypass deployment requirement;
- single- and multi-party governance;
- distinction between authenticated evidence and factual/geographic truth.

The reference does not attempt to decide which jurisdiction's law prevails or whether a particular cross-border transfer is lawful.

## 3. Repository architecture

The repository contains two Python packages and two independent non-Python verification implementations.

| Component | Language | Role |
|---|---|---|
| `src/finality_ref/` | Python | Complete execution-finality state machine, protected authority, state, evidence, capability, replay store, effectors, Finality Sink |
| `src/sovereignty_ref/` | Python | Compute Plane / Authority Plane separation, jurisdiction evidence, approvals, governance policy, national-use scenarios |
| `node/` | Node.js | Independent portable canonicalization and core finality-vector verification |
| `go/` | Go | Independent portable canonicalization and core finality-vector verification |

Python is currently the **complete executable reference** for the sovereignty-specific layer. Node.js and Go independently verify the common execution-finality substrate and canonicalization vectors. The sovereignty-specific object format is **not yet claimed as a standardized cross-language wire protocol**.

## 4. Tested runtime and tooling

The recorded reference stack uses:

| Item | Recorded version |
|---|---|
| Python | CPython 3.13.5 |
| pytest | 9.0.2 |
| pytest-cov | 7.0.0 |
| coverage.py | 7.13.3 |
| cryptography | 46.0.4 |
| setuptools | 82.0.1 |
| SQLite | 3.46.1 |
| OpenSSL | 3.5.5 |
| Node.js | 22.16.0 |
| Node Unicode data | 16.0 |
| Node ICU | 77.1 |
| Go | 1.23.2 linux/amd64 |
| Go Unicode data recorded | 15.0.0 |
| vendored `golang.org/x/text` | v0.16.0 |

The Python runtime has no mandatory third-party dependency for the basic HMAC reference path. `cryptography` is optional and is used for the Ed25519 adapter exercised by the inherited core tests.

## 5. Test harness determinism

Most sovereignty tests use a deterministic nanosecond clock:

`NOW = 1_800_000_000_000_000_000`

The fixed clock prevents wall-clock drift from changing expected freshness, expiry, and replay outcomes. Test objects are normally issued slightly before `NOW` and expire after deterministic offsets. When future-time behavior is under test, the exact offset from `NOW` is deliberately parameterized.

This design is intended to make failures reproducible across CI runs rather than dependent on scheduler timing.

## 6. Compute Plane representation

`ComputeContext` records the facts the policy chooses to bind about the environment that performed computation:

- `provider_id`;
- `compute_jurisdiction`;
- `workload_id`;
- `model_id`;
- `runtime_evidence_digest`;
- `session_id`.

A `ComputePlane` may call `propose()` to produce a Candidate Act. Calling `ComputePlane.effectuate()` raises:

`EffectDenied("compute_plane_has_no_effectuation_authority")`

This is an executable **software-model invariant**. It is not proof that a real cloud host, kernel, NIC, GPU, DMA engine, administrator, or alternative API cannot reach the underlying resource by another path.

## 7. Candidate Act representation

The inherited `CandidateAct` binds:

- act identifier;
- act class;
- effect class;
- source;
- destination;
- purpose;
- jurisdiction;
- policy epoch;
- nonce;
- issue time;
- freshness interval;
- sink identifier;
- effect boundary identifier;
- scope;
- payload;
- runtime-evidence digest;
- authority context;
- status.

The default status is `NON_EFFECTIVE`.

The Candidate digest is derived from deterministic canonical serialization. The capability later binds that complete digest. The Finality Sink recomputes the Candidate digest rather than accepting an upstream digest as sufficient evidence.

## 8. Governance-context binding

The sovereignty layer adds five load-bearing values to `candidate.authority_context`:

- `compute_context_digest`;
- `jurisdiction_evidence_digest`;
- `approvals_digest`;
- `compute_provider_id`;
- `compute_jurisdiction`.

The `AuthorityPlane` independently recomputes the expected values and refuses issuance if any field differs.

After capability issuance, modifying any of these fields changes the Candidate digest and is rejected by sink-side Candidate verification.

## 9. Approval-binding circularity and its resolution

Approvals need to bind to the intended Candidate, but the Candidate ultimately contains a digest of the approval set. Hashing the final Candidate into each approval would therefore create a circular dependency.

The implementation resolves this with `governance_subject_digest(candidate)`. It hashes the Candidate while excluding only the reserved governance-binding fields that are populated later. All ordinary Candidate fields and all non-governance authority-context fields remain covered.

The sequence is:

1. construct the ordinary Candidate;
2. compute the governance-subject digest;
3. bind approval(s) to that digest;
4. authenticate approval(s) when strict mode is used;
5. digest the final approval set;
6. bind compute/evidence/approval digests into the Candidate;
7. submit the fully bound Candidate to the Authority Plane;
8. issue the Finality Authority only if all bindings match.

## 10. Sovereignty policy surface

`SovereigntyPolicy` can validate:

- authority jurisdiction;
- policy epoch;
- compute-jurisdiction allowlist;
- compute-provider allowlist;
- required runtime-evidence digest;
- trusted jurisdiction-evidence issuers;
- allowed evidence types;
- minimum evidence count;
- minimum independent evidence-issuer count;
- requirement for an authority-jurisdiction assertion;
- allowed evidence trust classes;
- required approval roles;
- numerical approval threshold;
- maximum future clock skew;
- required payload fields;
- numeric payload ranges;
- allowed payload values.

These are reference parameters, not national policy recommendations.

## 11. Default compute-policy parameters used by the test harness

The common sovereignty fixture permits these compute-jurisdiction labels:

`FOREIGN`, `US`, `EU`, `IN`, `REGION-X`, `REGION-Y`

It permits these provider labels:

`global-ai-provider`, `regional-ai-provider`, `foreign-medical-ai`, `satellite-ai-provider`, `external-benefit-ai`

The required runtime-evidence digest is:

`runtime-ok`

Five explicitly disallowed/unregistered compute-location labels are also exercised:

`BLOCKED-1`, `BLOCKED-2`, `UNREGISTERED`, `UNKNOWN`, `SANCTIONED`

The labels are synthetic. They test state-machine separation and allowlisting, not real sanctions law or geography.

## 12. Cross-border matrix

Five authority jurisdictions are crossed with six permitted compute jurisdictions:

Authority labels:

`COUNTRY-A`, `COUNTRY-B`, `COUNTRY-C`, `COUNTRY-D`, `COUNTRY-E`

Compute labels:

`FOREIGN`, `US`, `EU`, `IN`, `REGION-X`, `REGION-Y`

This produces **30 allowed cross-product tests**.

The expected property is not that all such real-world transfers are lawful. The tested property is that the architecture can represent:

`compute jurisdiction != authority jurisdiction`

without automatically transferring final effectuation authority to the Compute Plane.

## 13. Jurisdiction-evidence object

Each `JurisdictionEvidence` object contains:

- evidence ID;
- evidence type;
- asserted jurisdiction;
- issuer;
- subject;
- observation time;
- expiration time;
- trust-class label;
- value digest;
- key ID;
- signature.

The object is intentionally an **assertion container**, not a claim of perfect location proof.

## 14. Default jurisdiction-evidence bundle

The default test bundle contains two independently named issuers:

1. `national-trust-service` / `gateway-attestation` / trust class `protected`;
2. `regulated-network` / `network-context` / trust class `network-derived`.

The default evidence times are approximately:

- first observation: `NOW - 1,000,000 ns`;
- second observation: `NOW - 2,000,000 ns`;
- expiration: `NOW + 60,000,000,000 ns`.

The default policy requires:

- at least 2 evidence items;
- at least 2 independent configured issuers;
- at least one assertion for the authority jurisdiction;
- allowed evidence type;
- allowed trust-class label;
- non-expired evidence;
- observation no more than 1 second into the future.

## 15. Negative evidence-issuer variants

The following issuer values are explicitly rejected in the negative matrix:

`unknown`, `self-asserted`, `untrusted-cloud`, `random-service`, `attacker`

This tests configured issuer trust, not global truth.

## 16. Negative evidence-type variants

The following evidence types are explicitly rejected by the reference allowlist:

`ip-only`, `gnss-unsigned`, `user-claim`, `free-text`, `dns-label`

This does not mean those signals can never be useful. It demonstrates that a deployment can refuse evidence classes that are not configured as sufficient for the protected decision.

## 17. Evidence freshness and future-skew parameters

Expired evidence is tested with expiration offsets of:

`1 ns`, `10 ns`, `1,000 ns`, `1,000,000 ns`, `10,000,000,000 ns`

into the past.

The policy allows a maximum future-clock skew of:

`1,000,000,000 ns` = 1 second.

Future observation offsets tested beyond the allowance are:

`1,000,000,001 ns`, `2,000,000,000 ns`, `5,000,000,000 ns`, `60,000,000,000 ns`.

## 18. Evidence-count and issuer-independence testing

Evidence counts `0` and `1` are tested against the default minimum of `2` and must fail.

Two evidence objects from the same issuer are also tested and fail the independent-issuer requirement.

Duplicate evidence IDs are separately rejected.

This distinguishes **number of records** from **number of independent configured principals**.

## 19. Evidence authentication

`PrincipalVerifierRegistry` maps configured issuer identities to authenticators.

In strict authenticated mode the Authority Plane verifies each evidence object's signature before semantic policy validation.

The reference test harness uses distinct deterministic HMAC-SHA256 keys for configured issuers so one issuer's key is not reused as another issuer's key.

The authenticated mutation suite signs an evidence object and then modifies, without re-signing:

- asserted jurisdiction;
- subject;
- evidence-value digest;
- expiry;
- trust class.

Each case must fail before Finality Authority issuance.

## 20. What evidence authentication proves and does not prove

A successful signature check proves that the configured key authenticated the serialized assertion.

It does **not** prove:

- physical geography;
- legal jurisdiction;
- that a cloud-region label is accurate;
- that a facility attestation was generated honestly;
- that the issuer itself is uncompromised.

This is why the reference uses policy-defined evidence classes and issuer thresholds rather than treating a signature as "cryptographic geography."

## 21. Multi-party approval object

Each `Approval` contains:

- approver identity;
- approver role;
- Candidate governance-subject digest;
- policy epoch;
- approval time;
- expiry time;
- key ID;
- signature.

The policy can independently require a threshold and specific roles.

## 22. Approval threshold matrix

The following `(threshold, available approval count, expected result)` combinations are tested:

- `(0,0,allow)`;
- `(1,0,deny)`;
- `(1,1,allow)`;
- `(2,0,deny)`;
- `(2,1,deny)`;
- `(2,2,allow)`;
- `(3,2,deny)`;
- `(3,3,allow)`;
- `(4,3,deny)`;
- `(4,4,allow)`.

This tests exact boundary behavior rather than only a single 2-of-2 example.

## 23. Required-role matrix

The reference separately tests required roles so "any N signatures" is not treated as equivalent to "the required authorities signed."

Examples include:

- required `treasury`, present `treasury` -> allow;
- required `treasury + benefit-agency`, both present -> allow;
- required both, only one present -> deny;
- required `treasury + auditor`, present `treasury + benefit-agency` -> deny;
- no roles required, none present -> allow.

## 24. Duplicate-approver attack

Two approvals are created using the same `approver_id` but different roles. They do not count as two independent approvers.

The policy emits `duplicate_approver` and fails the threshold when two distinct principals are required.

## 25. Approval freshness and binding attacks

The semantic suite mutates approvals into:

- wrong Candidate digest;
- wrong policy epoch;
- expired approval;
- approval more than the 1-second future-skew allowance into the future.

The authenticated suite additionally mutates signed approval fields without re-signing and expects signature failure before semantic acceptance.

## 26. Why semantic and cryptographic tests are separated

Most policy-matrix tests operate on semantically constructed objects without requiring signatures so the test can reach and exercise the intended policy branch.

A separate authenticated suite validates signatures and mutation resistance.

This is intentional. If every negative object were corrupted at the signature layer, later semantic branches such as wrong role, threshold, or expiry would never be executed and code coverage would give a misleadingly shallow picture.

## 27. Protected Authority sequencing

After sovereignty-specific checks pass, the wrapper delegates to `ProtectedAuthority`.

The core sequence is:

1. build HCAD/descriptor;
2. validate core Candidate policy;
3. reserve nonce and advance protected state;
4. construct Validation Evidence;
5. sign Validation Evidence;
6. commit Validation Evidence;
7. construct scoped capability;
8. sign capability;
9. return capability.

The reference deliberately commits evidence before capability availability.

## 28. Protected state parameters

The normal sovereignty test stack constructs `ProtectedState` with:

- default quota: `1000`;
- default budget: `1,000,000`;
- authorization cost: normally `1`.

The benchmark stack uses much larger quotas to avoid exhausting state during thousands of iterations.

The state transition binds nonce, source, version change, quota change, budget change, policy epoch, and Candidate identity.

## 29. Capability parameters

The core Finality Authority binds:

- authority ID;
- Candidate digest;
- descriptor digest;
- sink;
- boundary;
- nonce;
- exact scope;
- policy epoch;
- validation-evidence ID;
- protected-state transition ID;
- issue time;
- expiry time;
- key ID;
- signature.

The test stack uses a capability TTL of:

`5,000,000,000 ns` = 5 seconds.

Actual expiry is clamped so the capability cannot outlive the Candidate's own freshness window.

## 30. Finality Sink verification sequence

The sink performs independent checks including:

1. Candidate remains `NON_EFFECTIVE`;
2. Candidate effect class matches sink-local effect class;
3. Candidate and capability sink IDs match sink-local identity;
4. Candidate and capability boundary IDs match sink-local boundary;
5. Candidate and capability policy epoch match local epoch;
6. Candidate scope equals capability scope;
7. capability scope is supported locally;
8. capability nonce equals Candidate nonce;
9. capability is not future-dated beyond allowed skew;
10. capability is not expired;
11. capability does not outlive Candidate freshness;
12. capability signature verifies;
13. strict PoP checks are performed if that profile is enabled;
14. Candidate digest is recomputed and matched;
15. HCAD is rebuilt using **sink-local** sink and boundary identity;
16. descriptor digest is matched;
17. committed validation evidence is retrieved;
18. validation-evidence signature verifies;
19. decision is ALLOW;
20. evidence authority/Candidate/descriptor/transition/epoch all match the capability;
21. protected-state transition verifies.

Only after verification can the effectuation function claim the capability and invoke the guarded effect handle.

## 31. Sink-local reconstruction

The sink does not trust an upstream caller to define which sink or boundary is being used. The sink supplies its own `sink_id` and `boundary_id` when reconstructing HCAD.

This directly tests sink-substitution and boundary-substitution attempts.

## 32. Consumption ordering and crash semantics

The reference uses:

`verify -> consume/claim -> effect`

rather than:

`verify -> effect -> consume`

The first ordering prevents a crash after an irreversible effect but before replay-state persistence from allowing the same capability to be used again.

The trade-off is that a crash after consumption but before external effect can leave:

`consumed / no effect`

The reference therefore provides **at-most-once authorization consumption**, not universal distributed exactly-once semantics.

## 33. Durable replay implementation

`SQLiteConsumptionStore` uses:

- SQLite WAL mode;
- capability ID as a uniqueness key;
- `BEGIN IMMEDIATE` for the claim transaction;
- a 30-second SQLite connection timeout in the core reference.

This provides a concrete durable single-use example rather than only an in-memory boolean.

## 34. Concurrent replay parameters

In-memory races use:

`2, 3, 4, 8, 16, 32` concurrent workers.

SQLite durable races use:

`2, 4, 8, 16` concurrent workers.

The workers are launched with Python `ThreadPoolExecutor` against the **same capability**.

Expected invariant:

- exactly one call returns success;
- all remaining attempts are replay failures;
- the guarded effector records exactly one effect.

## 35. Context-substitution attacks

Before capability issuance, the test suite substitutes:

- provider ID;
- compute jurisdiction;
- workload ID;
- model ID;
- runtime-evidence digest;
- session ID;
- evidence value;
- approval identity;
- governance digest fields.

After capability issuance, it mutates bound Candidate authority-context fields and expects sink-side `candidate_digest_mismatch` or equivalent fail-closed behavior.

## 36. Direct-effect bypass seam

Two separate application-level checks exist:

- `ComputePlane.effectuate()` always denies;
- the public `GuardedEffector.direct_effect()` path always denies.

The Finality Sink receives a bound effect handle and is the only modeled component permitted to call it.

This demonstrates the intended API seam. It does **not** establish process-, kernel-, hypervisor-, NIC-, DPU-, DMA-, or hardware-level non-bypassability.

## 37. Healthcare scenario parameters

The healthcare profile uses:

| Parameter | Value |
|---|---|
| Authority jurisdiction | `COUNTRY-A` |
| Policy epoch | `184` |
| Effect class | `storage-write` |
| Destination | `National-Hospital-EHR` |
| Purpose | `Clinical-Treatment` |
| Scope | `WRITE:/records` |
| Sink | `Hospital-EHR-Finality-Sink` |
| Boundary | `Hospital-EHR-Write-Boundary` |
| Candidate freshness | `10,000,000,000 ns` = 10 s |

Required payload fields:

`patient_id`, `operation`, `diagnosis`, `clinician_id`, `consent`

Allowed reference operation:

`append-diagnosis`

Allowed consent state:

`present`

## 38. Healthcare negative variations

Missing-field tests independently remove each required field.

Rejected operation values include:

`export-record`, `delete-record`, `advertising-export`, `bulk-download`, `share-external`, `overwrite-record`

Rejected consent values include:

`missing`, `revoked`, `unknown`, `false`, empty string.

Post-authorization mutations independently alter:

- patient;
- diagnosis;
- clinician;
- operation;
- consent.

The old capability must fail because the Candidate digest is no longer identical.

The test does not establish clinical correctness of the diagnosis.

## 39. Disaster-response scenario parameters

The disaster profile uses:

| Parameter | Value |
|---|---|
| Authority jurisdiction | `COUNTRY-B` |
| Policy epoch | `73` |
| Effect class | `network-egress` |
| Destination | `National-Telecom-Emergency-Gateway` |
| Purpose | `Flood-Emergency-Warning` |
| Scope | `SEND` |
| Sink | `National-Alert-Finality-Sink` |
| Boundary | `National-Alert-Dispatch-Boundary` |
| Candidate freshness | `600,000,000,000 ns` = 600 s |

Allowed hazards:

`flood`, `cyclone`, `earthquake`, `wildfire`

Allowed severities:

`severe`, `extreme`

Required message class:

`public-warning`

## 40. Disaster-response variation matrix

The happy-path hazard/severity cross-product is:

`4 hazards × 2 severities = 8` combinations.

Rejected hazard categories include:

`marketing`, `political-message`, `routine-notice`, `unknown`, empty string.

After authorization, the region is changed to:

`Entire-Country`, `District-Z`, `District-A-B-C-D`, `Foreign-Region`, `*`

and the original authority must fail.

Each required payload field is also independently removed.

## 41. Public-benefit/payment scenario parameters

The payment profile uses:

| Parameter | Value |
|---|---|
| Authority jurisdiction | `COUNTRY-C` |
| Policy epoch | `118` |
| Effect class | `payment-ledger` |
| Destination | `Domestic-Payment-Rail` |
| Purpose | `Flood-Relief` |
| Scope | `SETTLE` |
| Sink | `Treasury-Payment-Finality-Sink` |
| Boundary | `Treasury-Settlement-Boundary` |
| Candidate freshness | `30,000,000,000 ns` = 30 s |

Reference payload:

- recipient: `Applicant-472`;
- amount: `25,000` minor units;
- currency: `LCU`;
- program: `National-Relief-2026`;
- purpose: `Flood-Relief`.

## 42. Payment numeric boundary testing

Reference amount policy:

`1 <= amount_minor <= 100,000`

Allowed boundary and representative values:

`1`, `2`, `100`, `999`, `1,000`, `25,000`, `50,000`, `99,999`, `100,000`

Rejected numeric values:

`-10`, `-1`, `0`, `100,001`, `250,000`, `1,000,000`, `2^31-1`

Rejected wrong types:

string, null, boolean, list, map, float.

Float is rejected at canonicalization before ordinary payload-policy evaluation because floating-point values are forbidden in security-bound canonical material.

## 43. Payment substitution testing

After a valid capability has been issued for recipient `Applicant-472`, the recipient is changed to:

`Applicant-999`, `Applicant-001`, `Treasury`, `Foreign-Account`, `attacker`

The old capability must fail.

Amount escalation after authorization is separately tested with:

`25,001`, `30,000`, `50,000`, `100,000`, `250,000`

Some changed amounts remain independently policy-valid. They still fail because a policy-valid **new act** is not the **same act** that was authorized.

## 44. Other payment policy variants

Rejected currencies:

`USD`, `EUR`, `INR`, `BTC`, empty string.

Rejected program identifiers:

`General-Budget`, `Election-Fund`, `Unknown`, `National-Relief-2025`, empty string.

Each required payload field is independently removed and must fail.

## 45. Fail-closed provider and runtime tests

Rejected provider labels:

`unknown-provider`, `attacker`, `unregistered`, `shadow-cloud`, empty string.

Rejected runtime-evidence digests:

`bad`, `stale`, `revoked`, `unknown`, empty string.

A separate test verifies that Candidate runtime evidence must match ComputeContext runtime evidence even when no particular digest value is globally required by policy.

## 46. Policy-epoch negative values

The sovereignty epoch-mismatch suite uses:

`0`, `1`, `72`, `183`, `185`, `2^31-1`

against the healthcare reference epoch `184`.

This exercises both near-boundary and extreme integer mismatches.

## 47. Canonicalization profile

The inherited portable cross-language canonicalization profile supports:

- null;
- boolean;
- integers within ±(2^53−1);
- Unicode scalar strings;
- arrays;
- string-keyed maps.

It rejects:

- floating point;
- unsafe integers outside the portable range;
- non-string map keys;
- unpaired surrogate values;
- NFC-normalization key collisions.

Strings and keys are normalized using Unicode NFC before cryptographic binding.

## 48. Cross-language verification and its exact scope

The hardened core retains:

- **20/20 positive interoperability vectors**;
- **9/9 dedicated canonicalization-conformance cases**;
- baseline full Finality-Sink vector verified by Node.js and Go;
- decomposed-Unicode full Finality-Sink vector verified by Node.js and Go.

Node.js and Go independently canonicalize and verify the common finality objects rather than calling Python.

However, the current `sovereignty_ref` object model and its evidence/approval wire representation are tested only in Python. Therefore the repository does **not** claim multi-language protocol interoperability for sovereignty-specific objects yet.

For an IETF protocol realization, Candidate, ComputeContext, Evidence, Approval, Finality Authority, and Receipt should eventually have a normative representation and signature structure, for example using CBOR/CDDL/COSE or another explicitly specified encoding.

## 49. Unicode version limitation

The recorded runtimes use different Unicode data versions:

- Python: 15.1.0;
- Node: 16.0;
- Go runtime data: 15.0.0;
- vendored Go `x/text`: v0.16.0.

The included conformance repertoire behaves consistently, but the repository does not claim exhaustive equivalence for all future Unicode code points. A standards-track profile should pin normalization behavior or define one normative canonicalization profile.

## 50. Test count and measured coverage

Clean collection contains:

- **741 Python tests** total;
- **260 sovereignty-specific tests**;
- **481 inherited execution-finality tests**.

Coverage command:

```bash
pytest --cov=src/finality_ref --cov=src/sovereignty_ref --cov-report=term-missing -q
```

Recorded result:

- **990 source statements**;
- **0 missed**;
- **100% statement coverage**;
- **741 tests passed**.

Statement coverage means every measured Python statement executed. It is not proof of complete semantic state-space coverage or security completeness.

## 51. Sovereignty-specific test distribution

| Module | Tests |
|---|---:|
| Authenticated governance inputs | 13 |
| Compute Plane vs Authority Plane separation | 13 |
| Governance-context substitution attacks | 18 |
| Cross-border compute matrix | 35 |
| Disaster-response example | 23 |
| Fail-closed policy behavior | 18 |
| Healthcare example | 22 |
| Jurisdiction-evidence matrix | 36 |
| Multi-party governance | 21 |
| Public-benefit/payment example | 48 |
| Replay and concurrency | 10 |
| Helper/remaining defensive branches | 3 |
| **Total** | **260** |

## 52. Core benchmark methodology

The inherited benchmark uses:

- `time.perf_counter_ns()`;
- 1,000 warm-up iterations;
- 3,000 measured iterations in the checked-in latest run;
- mean, p50, p95, p99, minimum, maximum.

Measured paths are:

1. canonical SHA-256 binding;
2. sink verification only;
3. protected authority + sink + guarded effectuation.

The benchmark records the environment inside the JSON result rather than assuming the repository-level environment file always describes the same host.

## 53. Latest recorded core benchmark

`benchmarks/latest.json` currently records the following user-space CPython measurements:

| Path | Mean | p50 | p95 | p99 | Max |
|---|---:|---:|---:|---:|---:|
| Canonical SHA-256 | 14.42 µs | 9.37 µs | 15.00 µs | 136.14 µs | 2.352 ms |
| Sink verify only | 348.33 µs | 247.30 µs | 846.53 µs | 2.252 ms | 4.713 ms |
| Core authority + sink + effect | 1.724 ms | 1.392 ms | 3.190 ms | 5.218 ms | 11.345 ms |

The benchmark's own embedded environment for this run reports:

- CPython 3.13.5;
- Linux 6.18.35 x86_64 / glibc 2.41;
- visible CPU string: Intel Xeon Platinum 8573C;
- 5 visible logical CPUs, affinity 0–4;
- ~6.24 GB visible memory.

The separate repository `environment/reference-environment.json` was captured on a different container placement and reports a different CPU string. For latency interpretation, the environment embedded in the particular benchmark JSON is authoritative for that measurement.

## 54. Dedicated sovereignty-layer benchmark

The expanded package also includes:

`scripts/benchmark_sovereignty.py`

and recorded result:

`benchmarks/sovereignty-python-local.json`

The measured scenario is the authenticated public-benefit/payment profile with:

- authority jurisdiction `COUNTRY-C`;
- compute jurisdiction `FOREIGN`;
- provider `global-ai-provider`;
- policy epoch `118`;
- 2 jurisdiction-evidence objects;
- 2 independent evidence issuers;
- authenticated evidence enabled;
- 1 authenticated approval;
- approval threshold 1;
- required role `policy-owner`;
- Candidate freshness 30 seconds;
- capability TTL 5 seconds;
- future skew 1 second;
- HMAC-SHA256 reference authentication;
- in-memory consumption for the measured full path.

## 55. Sovereignty benchmark timing boundary

The timed Authority-Plane path includes:

- evidence signature verification;
- approval signature verification;
- sovereignty policy evaluation;
- exact governance-context binding verification;
- core Candidate policy validation;
- protected-state transition;
- validation-evidence creation and commitment;
- capability creation/signing.

The timed full path additionally includes:

- Finality-Sink verification;
- single-use in-memory claim;
- guarded payment-effector commit;
- sink receipt construction/signing.

The benchmark **does not** include:

- WAN round trip to a government or enterprise policy service;
- remote evidence collection;
- real TPM/TEE/GPU/RATS attestation acquisition;
- policy-bundle download;
- certificate-path construction from a network PKI;
- issuer-side signing time;
- durable real payment-ledger commit;
- production network/device I/O.

Those belong to either cold-path establishment or deployment-specific effect latency and must be measured separately.

## 56. Recorded sovereignty benchmark results

The checked-in user-space CPython result uses 1,000 warm-up iterations and 3,000 measured iterations:

| Path | Mean | p50 | p95 | p99 | Max |
|---|---:|---:|---:|---:|---:|
| Sovereignty policy validate only | 304.60 µs | 268.89 µs | 398.63 µs | 857.17 µs | 3.787 ms |
| Authenticated Authority Plane issue | 1.380 ms | 1.278 ms | 1.773 ms | 3.422 ms | 7.333 ms |
| Sink verify after sovereignty issuance | 319.23 µs | 286.23 µs | 426.25 µs | 801.71 µs | 4.533 ms |
| Authenticated Authority + sink + effect | 2.208 ms | 2.042 ms | 2.764 ms | 5.133 ms | 19.013 ms |

These are reference measurements, not certified production results.

## 57. Engineering latency targets

The repository retains the following deployment **targets** in `configs/system_profiles.json`:

| Profile | Target | Intended enforcement location |
|---|---:|---|
| Embedded control | 100 µs | MCU / secure element |
| Accelerator hot path | 500 µs | GPU / DPU / SmartNIC |
| UPF egress | 1 ms | UPF/N6 or SmartNIC |
| API gateway | 2 ms | reverse proxy / service-mesh gateway |
| Storage writer | 5 ms | transactional write boundary |
| Payment finality | 10 ms | payment terminal / ledger bridge |
| Cross-region governance | 20 ms | regional egress gateway |
| Audit-heavy output | 50 ms | model-output emitter |

These values are **engineering stress targets**, not standards requirements, vendor claims, or promises that the CPython implementation meets them.

## 58. Interpreting the target/measurement relationship

The current CPython results are useful mainly to identify which profiles clearly require a different implementation strategy.

Examples from the recorded run:

- 100 µs embedded target: the Python sink path itself is too slow; native/device-resident code is required.
- 500 µs accelerator target: Python sink p50 is below 500 µs, but tail latency substantially exceeds the target; this is not a reliable accelerator implementation.
- 1 ms UPF target: Python sink p50 is below 1 ms, but p99 is above 2 ms and the full authority + sink path is above 1 ms; a real UPF profile requires native/accelerated local verification and tighter tail-latency control.
- 2 ms API-gateway target: core full p50 is under 2 ms but p95/p99 are not; authenticated sovereignty full p50 is approximately 2.04 ms, so the CPython reference does not demonstrate a dependable 2 ms budget.
- 5 ms storage target: recorded p99 is slightly above 5 ms for both the core full path and the sovereignty full path; a 5 ms production budget therefore requires optimization and target-system measurement.
- 10 ms payment target: the recorded sovereignty full-path p99 is below 10 ms, but the observed maximum exceeds 10 ms and the benchmark excludes a real payment network/ledger commit. It therefore does **not** demonstrate a 10 ms end-to-end production payment guarantee.

The correct conclusion is that **local verification cost can be small enough to be engineering-relevant**, but target compliance must be measured on the actual enforcement hardware and effect system.

## 59. Cold path versus hot path

The architecture is not intended to put a remote sovereign-policy round trip into every packet or every model token.

### Cold path candidates

Operations that can often be amortized or pre-established include:

- remote attestation acquisition;
- certificate-chain validation;
- policy retrieval and signature verification;
- trust-anchor establishment;
- key provisioning/rotation;
- registration of authority domains and Finality Sinks;
- synchronization of revocation state;
- negotiation of cryptographic algorithms;
- synchronization of policy epoch;
- registration of jurisdiction-evidence issuers;
- creation of bounded protected local state.

### Hot path candidates

Immediately before effectuation, the intended local path is closer to:

- canonicalize/reconstruct load-bearing Candidate attributes;
- calculate/verify compact digests;
- verify bounded authority/evidence binding;
- compare sink, boundary, destination, purpose, jurisdiction, epoch, scope;
- check local freshness/revocation/replay state;
- consume/reserve capability;
- commit the effect.

Moving expensive trust establishment off the hot path is an optimization. Moving the final act-to-effect binding away from the effectuation boundary would weaken the intended property.

## 60. Legacy-system feasibility: design objective

The architecture does **not** require every existing application to be rewritten before any useful deployment is possible.

A legacy system can participate when the protected consequence can be forced through a controllable gateway, writer, proxy, broker, or other mediation point.

The key question is not "was the legacy application modified?" The key question is:

> Can every path capable of producing the protected effect be made to converge on the same enforcing boundary?

## 61. Legacy HTTP/API integration

A legacy application that currently sends external HTTP/API calls can use a reverse proxy, egress gateway, service-mesh gateway, or privileged sidecar as a Finality Sink if direct egress is prevented.

A Candidate can bind, for example:

- HTTP method;
- normalized authority/host;
- path/resource;
- body or body digest;
- purpose;
- tenant/workload identity;
- jurisdiction context;
- policy epoch;
- destination gateway;
- allowed scope.

Feasibility depends on removing alternate sockets, alternate proxy credentials, direct NAT paths, and administrative bypasses for the protected workload.

## 62. Legacy database/storage integration

A legacy application can stage a mutation while a privileged database writer or storage proxy owns the only credential capable of committing the protected write.

Possible binding fields include:

- database/table or object namespace;
- operation class;
- primary key/object ID;
- content digest/version;
- purpose;
- tenant;
- policy epoch;
- idempotency/capability ID.

If the legacy process retains an unrestricted direct database credential, the software Finality Sink does not provide complete mediation.

## 63. Legacy payment integration

A payment system can place the Finality Sink at a payment gateway, HSM-protected signing service, settlement adapter, or ledger bridge.

For safety, the downstream transaction should consume or persist `capability_id` as an idempotency/transaction key where possible.

A software-only pre-payment gateway can demonstrate binding and replay protection, but high-assurance deployments should integrate consumption with the actual settlement primitive rather than relying on a separate best-effort log.

## 64. Legacy telecom integration

Existing telecom deployments can place enforcement at an already privileged control/egress point such as:

- UPF/N6 boundary;
- policy enforcement gateway;
- SmartNIC/DPU adjacent to egress;
- radio-control gateway for selected commands;
- SMS/emergency-alert gateway.

The architecture does not imply per-packet remote authorization. A protected Candidate may represent creation of a flow, release of a data class, dispatch of an emergency alert, or another bounded effect that then permits ordinary transport under the authorized constraint.

## 65. Legacy AI/agent integration

An existing agent framework can continue generating tool calls normally if the generated call remains non-effective until intercepted by a controlling tool gateway or resource-side sink.

For a legacy deployment, the practical migration can be:

`agent -> structured tool intent -> finality gateway -> existing API`

The finality gateway must be privileged relative to the agent. If the agent still possesses direct credentials or a second tool path to the same consequence, the deployment remains bypassable.

## 66. Suggested legacy assurance levels

A useful engineering classification is:

| Level | Example | Assurance |
|---|---|---|
| L0 - Observe | log/audit only | no pre-effect prevention |
| L1 - Software gateway | reverse proxy, sidecar, DB proxy | useful binding/replay controls; privileged host may bypass |
| L2 - Host/hypervisor enforced | host firewall, hypervisor, protected service, isolated credentials | stronger path control |
| L3 - Hardware/I/O assisted | TEE/HSM, DPU/SmartNIC, IOMMU/device boundary, secure controller | stronger anti-bypass and key/state protection |

These are descriptive deployment profiles, not formal IETF conformance levels.

## 67. Legacy deployment failure modes

A legacy integration should be considered incomplete if any of the following remains available to the protected workload for the same consequence:

- raw socket bypass;
- direct DB/storage credential;
- alternate broker credential;
- unguarded admin API;
- secondary renderer/export path;
- DMA or peer-to-peer release path;
- debug channel carrying protected output;
- alternate payment signing key;
- alternate telecom gateway;
- file/clipboard/IPC path that produces the same protected external effect.

## 68. Benchmarking legacy systems

For legacy feasibility testing, report at minimum:

- baseline effect latency without finality;
- finality verification-only latency;
- consume/reserve latency;
- downstream effect latency;
- total incremental overhead;
- p50/p95/p99/max;
- throughput at realistic concurrency;
- failure/retry behavior;
- whether durability is synchronous;
- whether attestation or certificate validation occurs on hot or cold path;
- CPU affinity/isolation and runtime environment;
- Candidate size and payload-digest strategy;
- location of keys and protected state;
- whether the effect path is actually exclusive.

A benchmark that reports only average cryptographic time is insufficient for an effectuation-boundary design.

## 69. Large payload handling

The Finality Sink need not necessarily rehash a multi-gigabyte object immediately before release if a protected storage or processing path already maintains a trustworthy content commitment.

The Candidate can bind to:

- immutable object version;
- protected content digest;
- Merkle root;
- authenticated manifest;
- protected storage identifier.

The security requirement is that the object presented at finality cannot be substituted after the commitment was authorized.

## 70. Reference cryptography

The dependency-free reference uses HMAC-SHA256 for deterministic tests and vectors.

This choice provides reproducibility and simple cross-language verification. It is **not** a recommendation to share symmetric secrets among countries, cloud providers, evidence issuers, approvers, and sinks.

Production deployments should normally use separated cryptographic roles and protected key storage, potentially including asymmetric signatures, HSM/TEE/device-backed keys, PKI or workload-identity trust chains, revocation, and rotation.

## 71. Optional Ed25519

The inherited core includes an optional Ed25519 adapter using `cryptography` and exercises it with dedicated tests.

This demonstrates algorithm abstraction but does not define a standards cryptographic suite. A future protocol profile would need algorithm identifiers, key discovery, trust-chain rules, revocation, algorithm agility, and downgrade behavior.

## 72. Runtime evidence limitation

The sovereignty layer binds and compares a runtime-evidence digest. It does not parse a real TPM quote, EAT, RATS Evidence/Attestation Result, confidential-VM report, GPU attestation report, or cloud attestation document.

Such systems can supply upstream evidence, but their verification semantics are outside the current reference.

## 73. Evidence-truth limitation

A valid signature authenticates an assertion; it does not establish the factual truth of physical location, legal status, patient state, disaster severity, benefit eligibility, or model correctness.

## 74. Foreign-compute confidentiality limitation

Compute/authority separation does not stop a foreign Compute Plane from reading plaintext intentionally supplied to it.

Confidential computing, encryption, data minimization, PETs, protected key release, split processing, or other controls may be necessary.

## 75. Foreign-provider availability limitation

The architecture does not create accelerators, models, data centers, electricity, connectivity, software support, or contractual access.

A country can remain dependent on an external provider for computation even while retaining independent effectuation authority.

## 76. Foreign-law limitation

The architecture cannot override foreign law, resolve conflicts of law, or compel an external provider to continue service.

## 77. Model-quality limitation

An AI system can generate an incorrect diagnosis, flood forecast, fraud score, or eligibility recommendation.

Execution finality governs whether a proposed consequence may become effective; it does not establish the correctness of the underlying recommendation.

## 78. Anti-bypass limitation

The strongest deployment condition is complete mediation of the protected consequence.

If the same effect can be produced through a raw socket, direct database credential, DMA mapping, alternate renderer, secondary gateway, administrative API, debug port, alternate payment key, or other unmediated path, the real deployment does not satisfy the intended property for that effect.

## 79. Protected-state limitation

The Python protected state is a synchronized state machine, not hardware rollback-resistant storage.

High-assurance deployment requires a durable and rollback-resistant state mechanism appropriate to the threat model.

## 80. Exactly-once limitation

The reference chooses at-most-once capability consumption before effectuation.

Exactly-once external semantics require co-design with the downstream transaction, ledger, idempotency, reservation, device, or database mechanism.

## 81. Side/covert-channel limitation

The repository does not attempt to eliminate side channels, covert channels, timing leakage, cache leakage, RF leakage, power analysis, or all information flows available to a compromised privileged platform.

## 82. Fully compromised authority or sink

A completely compromised Authority Plane or Finality Sink is within the trusted-computing-base failure model. The protocol cannot cryptographically force a fully compromised component to execute its own verification code honestly.

Mitigations can include smaller TCBs, attestation, isolated keys, multi-party approval, independent receipts, hardware enforcement, and operational separation.

## 83. Performance limitation

All reported latency values are user-space reference measurements. They are not certified performance for national infrastructure, hospitals, payment rails, GPUs, DPUs, SmartNICs, UPFs, TEEs, or production cloud deployments.

Target hardware and effect systems require independent benchmarks under realistic load.

## 84. Falsifiability criterion

A claimed deployment should be considered incomplete if:

- the protected effect can occur without finality verification;
- a different Candidate can reuse authority for the original Candidate;
- sink identity is supplied entirely by the untrusted caller;
- evidence/approval substitution is accepted without rebinding;
- replay creates more than one effect;
- fail-open behavior permits effect when required evidence is unavailable;
- an alternate consequence path bypasses the enforcing boundary.

The repository is intended to make those claims testable rather than rhetorical.

## 85. Reproduction commands

Run all Python tests:

```bash
pytest -q
```

Run sovereignty-specific tests:

```bash
pytest tests/sovereignty -q
```

Run combined statement coverage:

```bash
pytest --cov=src/finality_ref --cov=src/sovereignty_ref --cov-report=term-missing -q
```

Run all inherited Python/Node/Go verification:

```bash
./scripts/run_all.sh
```

Run the dedicated sovereignty verification wrapper:

```bash
./scripts/run_sovereignty_checks.sh
```

Run the core benchmark:

```bash
python3 scripts/benchmark.py --iterations 3000 --output benchmarks/latest.json
```

Run the sovereignty-layer benchmark:

```bash
python3 scripts/benchmark_sovereignty.py \
  --iterations 3000 \
  --warmup 1000 \
  --output benchmarks/sovereignty-python-local.json
```

## 86. Correct interpretation

The defensible conclusion from this implementation is:

> The Compute Plane and Authority Plane can be represented as separate executable roles; compute context, evidence, approvals, Candidate identity, protected state, scoped authority, sink identity, replay state, and consequence boundary can be made load-bearing in a fail-closed reference flow; and the modeled separation survives the included policy variations, signature mutations, Candidate substitutions, cross-border matrices, replay races, and sink-side verification tests.

The repository does **not** prove that every national, cloud, telecom, payment, medical, or AI deployment automatically obtains those properties. Real assurance depends on evidence quality, key management, privileged enforcement, anti-bypass closure, protected state, downstream transaction semantics, and the actual deployment topology.
