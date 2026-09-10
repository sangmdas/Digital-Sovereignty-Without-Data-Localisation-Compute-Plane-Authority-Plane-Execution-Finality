# Digital Sovereignty Without Mandatory Data Localisation
## Compute Plane / Authority Plane Separation — Runnable Reference Implementation

This repository is a runnable reference implementation of the architecture described in `draft-das-digital-sovereignty-finality-01`.

The central proposition is deliberately narrow:

> **Access to computation and authority over consequential effects need not be controlled by the same entity.**

A globally distributed or foreign **Compute Plane** may perform inference, analysis, transformation, routing, simulation, or other computation. A separately governed **Authority Plane** determines whether a specific protected **Candidate Act** may become externally effective. The Candidate Act remains non-effective until policy and governance predicates are satisfied and a scoped Finality Authority is independently verified at the **Finality Sink**.

This repository extends the generic execution-finality core with a dedicated digital-sovereignty layer for:

- compute-provider and compute-jurisdiction context;
- independently governed authority-jurisdiction policy;
- jurisdiction/location evidence bundles;
- authenticated evidence issuers;
- multi-party or co-signed approval thresholds;
- exact Candidate-Act binding of governance context;
- healthcare, emergency-alert, and public-benefit/payment scenarios;
- cross-border compute/authority separation tests;
- fail-closed evidence, epoch, provider, approval, mutation, replay, and concurrency tests.

## Architecture

```text
External / Global Compute Plane
            |
            v
      Candidate Act
            |
            v
      NON-EFFECTIVE
            |
            v
Independently Governed Authority Plane
            |
            v
Policy + Jurisdiction Evidence + Runtime Evidence
+ Purpose + Destination + Epoch + Approvals
            |
            v
Protected Validation Evidence / LAVR
            |
            v
Scoped Finality Authority
            |
            v
Finality Sink Reconstruction + Verification
            |
            v
Consume / Reserve
            |
            v
External Effect
```

The Compute Plane is intentionally modeled as unable to effectuate protected actions directly. The guarded consequence boundary denies a direct effect path, and the Finality Sink is the only modeled path that can invoke the bound effect handle.

## Test status

The packaged reference was verified on 2026-09-10 with:

- **741 Python tests passed**
- **260 digital-sovereignty-specific tests**
- **481 inherited execution-finality/core tests**
- **990 measured Python statements, 0 missed, 100% statement coverage**
- existing Python/Node.js/Go interoperability and canonicalization checks retained from the hardened core

The 260 sovereignty-specific tests cover compute/authority separation, authenticated governance inputs, cross-border matrices, evidence quality/expiry/issuer checks, multi-party approvals, three concrete country-use scenarios, context substitution attacks, payment mutation, replay, and concurrent single-use enforcement.

These results demonstrate behavior of this reference implementation under the modeled conditions. They do **not** prove that an arbitrary real deployment is non-bypassable or that jurisdiction assertions are geographically true.

## Important distinction: cryptographic binding is not cryptographic geography

The reference can authenticate configured evidence issuers and cryptographically bind the exact evidence evaluated into the Candidate Act. It does not claim that a cloud-region label, network assertion, facility attestation, GNSS observation, or other location signal is inherently true merely because it is signed.

Evidence quality remains a deployment and trust-model question.

## Concrete scenarios

Three scenario families are included in the tests:

1. **Healthcare:** foreign medical AI proposes a clinical record operation; domestic/independently governed authority controls the EHR write boundary.
2. **Disaster response:** global AI or satellite analysis proposes a public warning; domestic authority controls the national alert gateway.
3. **Public-benefit payment:** external AI proposes a relief payment; domestic authority controls the treasury/payment finality boundary.

The examples are intentionally consequence-focused. They do not claim that the architecture supplies AI compute, solves model quality, removes foreign-provider dependence, overrides foreign law, or protects plaintext that a foreign compute environment is allowed to see.

## Repository layout

- `src/finality_ref/` — hardened execution-finality core
- `src/sovereignty_ref/` — Compute Plane / Authority Plane separation layer
- `tests/` — inherited core tests
- `tests/sovereignty/` — 260 sovereignty-specific tests
- `configs/sovereignty_profiles.json` — concrete scenario parameters
- `docs/DIGITAL_SOVEREIGNTY_IMPLEMENTATION_DETAILS.md` — detailed implementation methodology
- `docs/SOVEREIGNTY_TEST_MATRIX.md` — exact granular test breakdown
- `docs/SOURCE_MAPPING.md` — draft-to-code/test mapping
- `docs/source/draft-das-digital-sovereignty-finality-01.xml` — source Internet-Draft XML used for this implementation
- `docs/` — core threat model, canonicalization, deployment, limitations, benchmark notes, and attack matrix

## Run the complete test suite

```bash
python -m pytest -q
```

Coverage:

```bash
python -m pytest \
  --cov=src/finality_ref \
  --cov=src/sovereignty_ref \
  --cov-report=term-missing \
  -q
```

Sovereignty-specific tests only:

```bash
python -m pytest tests/sovereignty -q
```

## Security boundary

The software repository demonstrates a protocol/state-machine seam. Production non-bypassability still requires every protected consequence-bearing path to converge on a privileged Finality Sink or equivalent enforcement boundary. A root process, alternate socket, direct database credential, DMA path, secondary renderer, side channel, or other unmediated path can invalidate the real deployment guarantee if it can create the same protected external effect without finality verification.

## Non-goals

This implementation does not determine which jurisdiction's law prevails, decide whether a transfer is lawful, prove physical location, create domestic AI infrastructure, guarantee foreign-provider availability, solve semiconductor sovereignty, certify model correctness, or provide universal exactly-once semantics across arbitrary external systems.

See `docs/DIGITAL_SOVEREIGNTY_IMPLEMENTATION_DETAILS.md` and `docs/LIMITATIONS.md` before making deployment claims.

For the dedicated sovereignty validation plus combined statement coverage:

```bash
./scripts/run_sovereignty_checks.sh
```

`benchmarks/latest.json` contains the inherited core execution-finality Python benchmark. `benchmarks/sovereignty-python-local.json` contains a dedicated authenticated Authority-Plane + Finality-Sink reference benchmark. Both are user-space CPython measurements; neither includes remote evidence acquisition, WAN policy round trips, real TPM/TEE/GPU/RATS evidence acquisition, or production database/payment/network I/O.


Dedicated sovereignty benchmark:

```bash
python3 scripts/benchmark_sovereignty.py --iterations 3000 --warmup 1000 --output benchmarks/sovereignty-python-local.json
```
