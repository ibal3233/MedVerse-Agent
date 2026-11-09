# MedVerse-Agent
### Policy-Grounded Multi-Agent Institutional Coordination for Trustworthy Digital-Twin-Enabled Medical Metaverse Systems

**ITU AI for Good Sandbox Hackathon — United Arab Emirates · Healthcare / Medical Metaverse**

> ⚠️ Scenario-based modeled patient and workflow data are used for evaluation. No real patient records are included. Korean policy sources are drawn from publicly available laws, regulations and official guidance.

---

## Executive Summary

**The problem.** A Medical Metaverse can connect patients, sensors, Digital Twins, networks, hospitals, research platforms, privacy functions and regulators, but those institutions do not receive the same information or possess the same authority. A clinical concern may remain valid while telemetry becomes unreliable; a research request may arrive while Privacy and Research/IRB independently determine whether processing is permitted. Correct local decisions do not automatically form a correct joint workflow.

**The solution.** MedVerse-Agent coordinates five institutionally asymmetric agents — Hospital, Cyber/Network, Privacy, Research/IRB and Regulator — around a patient Digital Twin and a Republic-of-Korea policy knowledge base. It is a harmonizer, not a sixth institutional authority. Evidence retrieval, institutional reasoning, policy/mandate validation, workflow selection, commitment timing and audit receipts are separated.

**The design principle.** **Learning proposes; policy architecture disposes.** A semantically relevant policy passage is not itself execution permission, and valid institutional disagreement is not forced into consensus.

**The evidence.** The project contains component-level learning validation, a frozen B1–B5 architecture comparison, policy-retrieval tests, proposal-order studies, authorized-alternative selection, bounded commitment under partial information, and an inspectable HTTP/UI integration. Strong comparator ties and unfavorable cases are retained rather than tuned away.

**Submission links.** [Final report](Team_MedVerse_Final_Report_RC4.pdf) · [Demo video](demo/Team_MedVerse_Demo.mp4) · [Captions](demo/Team_MedVerse_Demo_Captions.srt) · [Repository README](../README.md)

---

## 1. Clinical Use Case

A modeled oncology patient is monitored through a Digital-Twin-enabled Medical Metaverse workspace. A patient-reported clinical concern arrives, part of the telemetry later becomes unreliable, and a research team requests access to associated monitoring information.

The five institutional roles must respond independently:

- **Hospital** — clinical review and healthcare-record responsibilities;
- **Cyber / Network** — telemetry, device/session and network integrity;
- **Privacy** — purpose limitation, disclosure, minimum necessity and pseudonymization;
- **Research / IRB** — research authorization, participant protection and review conditions;
- **Regulator** — modeled AI/digital-medical-product oversight and reserved human authority.

The correct result may include different simultaneous outcomes: clinical review continues, a suspect stream is isolated, a research disclosure remains conditional, additional evidence is requested, or a reserved decision is escalated.

---

## 2. Patient Digital Twin and Data Sources

The project-local `PatientDigitalTwin` is the current **evidence-bearing representation of the modeled patient episode**, not a perfect biological replica. It stores supplied observations and provenance and maintains quality metadata for freshness, integrity, completeness, provenance and uncertainty. Validity states are `VALID`, `DEGRADED` and `UNVERIFIED`.

An `UNVERIFIED` stream means that evidence should not be trusted without additional verification; it does not mean the patient is well.

Three evidence layers are kept separate:

1. **Patient / scenario observations** — modeled symptoms, supplied sensor readings, timestamps, telemetry and provenance.
2. **Korean oncology population context** — National Cancer Center cancer-incidence statistics for population-level context only; never used to infer patient-level facts.
3. **Korean policy evidence** — laws, regulations, official guidance and institutional-governance records used for role-bounded retrieval and action validation.

See [`../data/external/README_NCC_DATA.md`](../data/external/README_NCC_DATA.md) for the NCC data status and setup.

---

## 3. Korean Policy Knowledge Base

The current candidate corpus contains **44 curated records**, of which **42 are configured as retrieval-eligible**. Representative sources include the Medical Service Act, PIPA, Bioethics and Safety Act, Medical Devices Act, Digital Medical Products Act, AI Basic Act, relevant enforcement instruments, the Health & Medical Data Utilization Guideline and the Pseudonymized Information Processing Guideline.

### Processing pipeline

```text
Official Korean sources
  → source-controlled clause / section records
  → eligibility and recorded-version checks
  → KR jurisdiction
  → institutional agent-access filtering
  → lexical or multilingual semantic ranking
  → top-k source-linked evidence
  → institutional proposal
  → policy / mandate validation
  → cross-institution harmonization
```

The key rule is that **jurisdiction and institutional authority are constrained before similarity ranking**.

### Retrieval backends

The lightweight backend uses BM25 lexical ranking. The semantic backend uses `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` with 384-dimensional normalized embeddings and dot-product ranking, equivalent to cosine similarity for unit vectors. `top_k = 3`.

| Retrieval method | English Recall@3 | Korean Recall@3 |
|---|---:|---:|
| Lexical BM25 | 85% | 85% |
| Multilingual MiniLM | 95% | 75% |

These predefined-query results measure retrieval of target evidence, not legal applicability or universal multilingual capability.

---

## 4. ITU-T Y.3172 and AI Readiness Mapping

| Node | MedVerse-Agent function | Governance / readiness evidence |
|---|---|---|
| **SRC** | Clinical/scenario observations, DT/network evidence, Korean policy sources | Provenance, contextualization, lawful collection |
| **C** | Source IDs, timestamps and institution-bounded evidence capture | Evidence integrity and role separation |
| **PP** | Policy chunking, Korean/English representation, explicit missingness and normalization | Data governance and traceability |
| **M** | Institutional assessment and action proposal | Model provenance and domain-specific validation |
| **P** | KR retrieval, jurisdiction checks, mandate/purpose/evidence validation | Trust, policy application and human-authority boundaries |
| **D** | Distribution of permitted workflow outputs and scoped views | Minimum-necessary institutional exchange |
| **SINK** | Medical Metaverse operator workspace and audit receipt | Human collaboration and supervised execution |

MedVerse-Agent adds explicit machine-readable institutional mandate and action-authority context around the policy/decision path rather than treating one model output as sufficient authority.

---

## 5. Experimental Evaluation

### RQ1 — Are institutional decisions grounded in reliable evidence?

Privacy and Cyber/Network are the two fully audited learned components. Cyber prospective groups g5–g8 achieved action and assessment accuracy/macro-F1 of 1.0 across the frozen modeled generator-shift evaluation after TRAIN-fitted standardization and explicit missingness representation. Privacy’s final action head achieved accuracy/macro-F1/minimum recall of 1.0 on its bounded replication benchmark after semantic-leakage and low-support precedence diagnosis. These are finite modeled-policy results, not external clinical or security performance.

The DT/evidence bridge separately verifies that unobserved defaults are not converted into patient facts and that unrelated metadata cannot make old telemetry appear fresh.

### RQ2 — Does explicit institutional coordination improve the joint workflow?

Five frozen architectural configurations were evaluated:

| Configuration | Description |
|---|---|
| **B1 — Single Omniscient Agent** | Centralized architecture with access to all institutional information |
| **B2 — Unconstrained Multi-Agent** | Role-based agents without enforced observation/action/communication boundaries |
| **B3 — Consensus / Debate reference** | Institutional intents reduced through a consensus-style reference mechanism |
| **B4 — Policy Filter Only** | Independent policy filtering without cross-institution workflow harmonization |
| **B5 — MedVerse-Agent** | Mandate-aware agents with constrained evidence access, validated actions, harmonization and auditability |

Metrics: **IC** Institutional Correctness; **CQ** Coordination Quality; **EWM** Exact Workflow Match; **PVR** Policy Violation Rate; **UER** Unnecessary Escalation Rate; **IOR** Information Overexposure Rate; **UXR** Unsafe Execution Rate.

| Baseline | IC ↑ | CQ ↑ | EWM ↑ | PVR ↓ | UER ↓ | IOR ↓ | UXR ↓ |
|---|---:|---:|---:|---:|---:|---:|---:|
| B1 | 0.179 | 0.393 | 0.000 | 1.000 | 0.000 | 0.929 | 1.000 |
| B2 | 0.821 | 0.540 | 0.000 | 0.143 | 0.000 | 0.929 | 0.143 |
| B3 | 0.607 | 0.286 | 0.000 | 0.000 | 0.667 | 0.929 | 0.000 |
| B4 | 0.964 | 0.600 | 0.143 | 0.000 | 0.333 | 0.000 | 0.000 |
| **B5** | **1.000** | **1.000** | **1.000** | **0.000** | **0.000** | **0.000** | **0.000** |

The key observation is B4→B5: policy filtering alone does not reproduce the complete modeled joint workflow. This benchmark does not establish superiority over every possible planner or MAS implementation.

### RQ3 — What changes when information arrives progressively?

**Proposal order.** Snapshot-once and sequential-once processing are order-sensitive. Fair stateful retry and dependency ordering both reach 100% macro completion across the tested known families. Dependency ordering saves only about 1.03% of validator calls versus fair retry, so the strong-control tie is retained.

**Alternative workflow selection.** When the originally requested path cannot proceed, fair stateful selection, an independently implemented constraint planner and MedVerse-Agent all complete the ten reference-feasible confirmation workflows; the requested-path-only scope control completes 1/10. This supports functional alternative selection, not unique planning superiority.

**Bounded commitment.** An action may be authorized now but committing immediately can prevent a later compatible workflow. The commitment study therefore makes `COMMIT`, bounded `WAIT`, authorized `PREPARE`, and `BLOCK / ESCALATE` explicit.

| Controller | Complete | Clinical obligation on time when feasible | Wait steps | Invalid commits |
|---|---:|---:|---:|---:|
| Eager commitment | 14/32 | 28/30 | 0 | 0 |
| Fair bounded wait | **15/32** | **29/30** | 38 | 0 |
| **MedVerse commitment** | **15/32** | **29/30** | 38 | **0** |

Relative to eager commitment, bounded waiting improves four continuations and loses three earlier authorized opportunities; MedVerse ties the capable bounded-wait comparator. Waiting is therefore a controlled trade-off, not a universal improvement.

---

## 6. Auditability and Interface

Every consequential modeled action can be traced through:

```text
released event
  → institution and authorized observations
  → source-linked evidence
  → actual proposal ID
  → policy / mandate verdict
  → coordination selection
  → commitment disposition
  → final revalidation
  → modeled side effect and receipt
```

The operator interface exposes institutional role views, proposal status, DT/evidence context, receipts, policy searches and selected measured plots. Role panels are operator inspection views, not evidence of authenticated remote multi-tenant isolation.

---

## 7. Policy and Standards Findings

| ITU work | Existing focus | Coordination / standardization opportunity identified |
|---|---|---|
| **Y.3172** | ML pipeline and orchestration | Institutional identity, mandate, jurisdiction and action-authority context between output and execution |
| **Y.3060 / Y.3061** | Trust and autonomous-network architecture | Extend trust to evidence provenance and institution-owned authority across legitimate controllers |
| **Y.3090 / Y.4239 / Y.4240** | DT architecture, metaverse integration and synchronization | Healthcare-specific exchange profile carrying validity, purpose, recipient, provenance and authority context |
| **FG-MV** | Confidence, cyber risk, PII and interoperability | Minimum-necessary institutional messaging and policy-aware cross-platform coordination |
| **FG-AI4H** | Ethics, regulation, data, testing and clinical evaluation | Runtime mandate validation, reserved human authority and auditable institutional workflows |
| **X.2014** | DT-supported security decisions | Prevent technical-security actions from implicitly overriding clinical authority |

Proposed reusable artifacts include an **Institutional Agent Descriptor**, **Action Authority Descriptor**, **Digital Twin Context Envelope**, and an interoperable coordination-state vocabulary.

---

## 8. Cross-Domain Reuse

The coordination interfaces, validators, workflow selector, commitment controller and receipts are reusable. Domain transfer still requires new policy sources, institutional mandates, observations, actions, authority records and evaluation cases. Merely swapping the knowledge base is not validated cross-domain transfer.

---

## 9. Quick Start

### BM25 demo

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -B run_presenter_sandbox.py --open --backend bm25
```

Open `http://127.0.0.1:8765`.

### Dense multilingual retrieval

```bash
pip install -r requirements-gate31.txt
python -B run_presenter_sandbox.py --open --backend dense
```

Key routes: `/` commitment workspace · `/foundation` Digital Twin workspace · `/presentation` selected results.

---

## 10. Limitations

The prototype demonstrates policy-grounded institutional coordination under controlled scenario-modeling assumptions. It does not establish clinical safety, legal-compliance certification, complete Korean-law coverage, arbitrary-language independence, production identity/security, universal planning superiority or full ITU conformance. The patient Digital Twin represents supplied observations and evidence quality; it is not a patient-specific physiological simulator. NCC population statistics remain contextual and are never used to infer patient-level facts.

---

## Team MedVerse

**Chonnam National University · Republic of Korea**

- **Team leader:** Aliyu Ibrahim
- **Team members:** Jeremiah Isuwa · Abubakar Isah · Kim Jinsul
- **Contact:** ibal2010@yahoo.com

> **Coordinate the workflow. Preserve institutional authority.**
