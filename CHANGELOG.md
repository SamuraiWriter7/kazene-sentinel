# Changelog

All notable changes to KAZENE-Sentinel will be documented
in this file.

This project follows Semantic Versioning.

## [0.1.0] - 2026-11-24

### Added

- Initial specification of the KAZENE-Sentinel protocol.
- Observation-first architecture separating observation,
  reasoning, decision-making, and execution.
- Three-state observation classification:
  - NORMAL
  - ANOMALY
  - UNKNOWN
- Structured observation record format.
- JSON Schema based on JSON Schema Draft 2020-12.
- UTC timestamp validation.
- Observation identifier and evidence reference requirements.
- State-dependent escalation rules.
- Explicit prohibition of execution authorization.
- Three synthetic observation examples.
- Python standard-library reference validator.
- Dataset-level observation identifier uniqueness validation.
- Strict JSON parsing with duplicate key rejection.
- Twenty-two protocol self-tests.
- Automated validation through GitHub Actions.

### Architecture

Established four logically separated layers:

1. Observation Layer
2. Reasoning Layer
3. Decision Layer
4. Execution Layer

Sentinel operates exclusively within the Observation Layer.

Escalation requests do not grant execution authority.

### Observation States

| State | Evidence | Escalation | Execution |
| --- | --- | --- | --- |
| NORMAL | Required | No | Forbidden |
| ANOMALY | Required | Yes | Forbidden |
| UNKNOWN | Optional | Policy-dependent | Forbidden |

### Security Invariants

Established the following fundamental invariants:

- Observation does not imply authorization.
- Normal does not imply safety.
- Anomaly does not imply malicious intent.
- Unknown does not imply normality.
- Escalation does not imply execution.
- Sentinel must not expand its own authority.

The execution_authorized field must always be false.

### Validation

- GitHub Actions: PASSED
- Observation examples: 3/3 passed
- Protocol self-tests: 22/22 passed
- Total validation cases: 25/25 passed
- Python version: 3.11
- External Python dependencies: None

Validation includes:

- Required field verification.
- Field type verification.
- UTC timestamp verification.
- Observation state verification.
- Evidence reference verification.
- Escalation rule verification.
- Unauthorized execution rejection.
- Duplicate observation identifier rejection.
- Invalid record rejection.

Validation establishes structural and semantic
consistency of observation records.

It does not establish real-world threat detection accuracy,
runtime access control, or operational security.

### Scope

Version 0.1.0 intentionally excludes:

- Real-time network monitoring.
- Production intrusion detection.
- Autonomous threat response.
- Automated defensive intervention.
- Offensive security operations.
- Continuous LLM inference.
- Self-modifying observation policies.
- Cryptographic evidence verification.
- Notification delivery guarantees.

### Design Policy

Future extensions should be introduced only when justified
by demonstrated operational requirements.

The observation and execution authority boundary
must remain preserved in subsequent versions.

### Status

- Initial specification completed.
- Reference validation completed.
- GitHub Actions passed.
- Minimal protocol baseline established.
- Experimental protocol, not a production security product.

---

## Fundamental Principle

> Observe continuously.
> Reason when necessary.
> Act only when authorized.

**Sentinel observes.
Intelligence responds.
Authority remains bounded.**
