#!/usr/bin/env python3
"""
KAZENE-Sentinel v0.1.0
Reference Observation Validator

Validates observation records and protocol invariants.
Uses Python 3.11+ standard library only.

This validator does not perform network monitoring,
threat detection, or operational intervention.
"""

import copy
import json
import re
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = ROOT / "examples"

REQUIRED_FILES = {
    "normal.json": "NORMAL",
    "anomaly.json": "ANOMALY",
    "unknown.json": "UNKNOWN",
}

REQUIRED_FIELDS = {
    "observation_id",
    "timestamp",
    "source",
    "status",
    "reason",
    "evidence",
    "escalation_required",
    "execution_authorized",
}

VALID_STATES = {
    "NORMAL",
    "ANOMALY",
    "UNKNOWN",
}

TIMESTAMP_PATTERN = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}"
    r"T[0-9]{2}:[0-9]{2}:[0-9]{2}Z"
)


def is_nonempty_string(value):
    """Check for a non-empty, non-whitespace string."""
    return isinstance(value, str) and bool(value.strip())


def is_valid_timestamp(value):
    """Validate the supported UTC timestamp format."""
    if not isinstance(value, str):
        return False

    if not TIMESTAMP_PATTERN.fullmatch(value):
        return False

    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
        return True
    except ValueError:
        return False


def reject_duplicate_keys(pairs):
    """Reject duplicate JSON object keys."""
    result = {}

    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value

    return result


def reject_nonstandard_constant(value):
    """Reject non-standard JSON constants."""
    raise ValueError(f"Invalid JSON constant: {value}")


def load_json(path):
    """Load a strict JSON document."""
    with path.open("r", encoding="utf-8") as file:
        return json.load(
            file,
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_nonstandard_constant,
        )


def validate_observation(record):
    """Return a list of observation validation errors."""
    errors = []

    if not isinstance(record, dict):
        return ["Observation must be a JSON object."]

    fields = set(record)

    missing = REQUIRED_FIELDS - fields
    additional = fields - REQUIRED_FIELDS

    if missing:
        errors.append(
            f"Missing required fields: {', '.join(sorted(missing))}"
        )

    if additional:
        errors.append(
            f"Unexpected fields: {', '.join(sorted(additional))}"
        )

    for field in ("observation_id", "source", "reason"):
        if not is_nonempty_string(record.get(field)):
            errors.append(
                f"{field} must be a non-empty string."
            )

    if not is_valid_timestamp(record.get("timestamp")):
        errors.append(
            "timestamp must be a valid UTC timestamp "
            "in YYYY-MM-DDTHH:MM:SSZ format."
        )

    status = record.get("status")

    if not isinstance(status, str) or status not in VALID_STATES:
        errors.append(
            "status must be NORMAL, ANOMALY, or UNKNOWN."
        )

    evidence = record.get("evidence")

    if not isinstance(evidence, list):
        errors.append("evidence must be an array.")
    else:
        for index, reference in enumerate(evidence):
            if not is_nonempty_string(reference):
                errors.append(
                    f"evidence[{index}] must be a non-empty string."
                )

        if status in ("NORMAL", "ANOMALY") and not evidence:
            errors.append(
                f"{status} requires at least one evidence reference."
            )

    escalation = record.get("escalation_required")

    if type(escalation) is not bool:
        errors.append(
            "escalation_required must be a boolean."
        )

    if status == "NORMAL" and escalation is not False:
        errors.append(
            "NORMAL requires escalation_required=false."
        )

    if status == "ANOMALY" and escalation is not True:
        errors.append(
            "ANOMALY requires escalation_required=true."
        )

    # UNKNOWN allows either boolean escalation value.
    # External escalation policy verification is out of scope.

    if record.get("execution_authorized") is not False:
        errors.append(
            "execution_authorized must always be false."
        )

    return errors


def validate_dataset(records):
    """Validate records and dataset-level ID uniqueness."""
    results = {}
    seen_ids = set()

    for name, record in records.items():
        errors = validate_observation(record)

        if isinstance(record, dict):
            observation_id = record.get("observation_id")

            if is_nonempty_string(observation_id):
                if observation_id in seen_ids:
                    errors.append(
                        f"Duplicate observation_id: {observation_id}"
                    )
                else:
                    seen_ids.add(observation_id)

        results[name] = errors

    return results


def validate_examples():
    """Load and validate all example JSON files."""
    print("\n=== Example Validation ===")

    if not EXAMPLES_DIR.is_dir():
        print("[FAIL] examples directory not found.")
        return False

    records = {}
    success = True

    for filename in REQUIRED_FILES:
        if not (EXAMPLES_DIR / filename).is_file():
            print(f"[FAIL] Missing example: {filename}")
            success = False

    for path in sorted(EXAMPLES_DIR.rglob("*.json")):
        name = path.relative_to(EXAMPLES_DIR).as_posix()

        try:
            records[name] = load_json(path)
        except (OSError, ValueError) as error:
            print(f"[FAIL] {name}: {error}")
            success = False

    results = validate_dataset(records)

    for name, errors in results.items():
        record = records[name]
        expected_status = REQUIRED_FILES.get(name)

        if (
            expected_status is not None
            and isinstance(record, dict)
            and record.get("status") != expected_status
        ):
            errors.append(
                f"Expected status: {expected_status}"
            )

        if errors:
            success = False
            print(f"[FAIL] {name}")

            for error in errors:
                print(f"       - {error}")
        else:
            print(f"[PASS] {name}")

    return success


def run_self_tests():
    """Verify that valid and invalid records are handled correctly."""
    print("\n=== Protocol Self-Tests ===")

    normal = {
        "observation_id": "TEST-001",
        "timestamp": "2026-11-24T00:00:00Z",
        "source": "synthetic-test",
        "status": "NORMAL",
        "reason": "Normal condition matched.",
        "evidence": ["test-evidence-001"],
        "escalation_required": False,
        "execution_authorized": False,
    }

    anomaly = {
        **normal,
        "observation_id": "TEST-002",
        "status": "ANOMALY",
        "reason": "Anomaly condition matched.",
        "escalation_required": True,
    }

    unknown = {
        **normal,
        "observation_id": "TEST-003",
        "status": "UNKNOWN",
        "reason": "Insufficient evidence.",
        "evidence": [],
        "escalation_required": True,
    }

    missing_field = copy.deepcopy(normal)
    del missing_field["reason"]

    cases = [
        ("Valid NORMAL", normal, True),
        ("Valid ANOMALY", anomaly, True),
        ("Valid UNKNOWN", unknown, True),
        (
            "UNKNOWN without escalation",
            {**unknown, "escalation_required": False},
            True,
        ),
        (
            "Invalid NORMAL escalation",
            {**normal, "escalation_required": True},
            False,
        ),
        (
            "Missing ANOMALY escalation",
            {**anomaly, "escalation_required": False},
            False,
        ),
        (
            "Unauthorized execution",
            {**anomaly, "execution_authorized": True},
            False,
        ),
        (
            "Unsupported observation state",
            {**normal, "status": "INVALID"},
            False,
        ),
        (
            "Missing NORMAL evidence",
            {**normal, "evidence": []},
            False,
        ),
        (
            "Missing ANOMALY evidence",
            {**anomaly, "evidence": []},
            False,
        ),
        (
            "Invalid calendar date",
            {**normal, "timestamp": "2026-02-30T00:00:00Z"},
            False,
        ),
        (
            "Invalid timestamp format",
            {**normal, "timestamp": "2026-11-24T09:00:00+09:00"},
            False,
        ),
        (
            "Non-boolean execution authority",
            {**normal, "execution_authorized": 0},
            False,
        ),
        (
            "Non-boolean escalation",
            {**normal, "escalation_required": 0},
            False,
        ),
        (
            "Missing required field",
            missing_field,
            False,
        ),
        (
            "Unexpected additional field",
            {**normal, "execute_command": "test"},
            False,
        ),
        (
            "Empty observation identifier",
            {**normal, "observation_id": "   "},
            False,
        ),
        (
            "Invalid evidence reference",
            {**normal, "evidence": [""]},
            False,
        ),
        (
            "Invalid observation state type",
            {**normal, "status": []},
            False,
        ),
        (
            "Invalid evidence type",
            {**normal, "evidence": "test-evidence"},
            False,
        ),
        (
            "Invalid record type",
            [],
            False,
        ),
    ]

    passed = 0
    total = len(cases) + 1

    for name, record, expected in cases:
        errors = validate_observation(record)
        actual = not errors

        if actual == expected:
            passed += 1
            outcome = "accepted" if actual else "rejected"
            print(f"[PASS] {name} ({outcome})")
        else:
            print(f"[FAIL] {name}")
            print(f"       Expected valid: {expected}")
            print(f"       Actual valid:   {actual}")

            for error in errors:
                print(f"       - {error}")

    duplicate_records = {
        "first.json": normal,
        "second.json": copy.deepcopy(normal),
    }

    duplicate_results = validate_dataset(duplicate_records)

    if (
        not duplicate_results["first.json"]
        and duplicate_results["second.json"]
    ):
        passed += 1
        print("[PASS] Duplicate observation ID (rejected)")
    else:
        print("[FAIL] Duplicate observation ID")

    print(f"\nSelf-tests: {passed}/{total} passed")

    return passed == total


def main():
    print("KAZENE-Sentinel v0.1.0")
    print("Reference Observation Validator")
    print("=" * 40)

    examples_ok = validate_examples()
    self_tests_ok = run_self_tests()

    print("\n=== Validation Summary ===")
    print(f"Examples:   {'PASS' if examples_ok else 'FAIL'}")
    print(f"Self-tests: {'PASS' if self_tests_ok else 'FAIL'}")

    if examples_ok and self_tests_ok:
        print("\nAll validation checks passed.")
        print("Observation and execution authority remain separated.")
        return 0

    print("\nValidation failed.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
