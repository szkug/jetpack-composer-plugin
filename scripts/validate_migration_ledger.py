#!/usr/bin/env python3
"""Validate code-led XML/DataBinding-to-Compose migration evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

EVIDENCE_RE = re.compile(r"^(.+):(\d+)$")
PLACEHOLDERS = {"", "todo", "tbd", "unknown", "n/a", "none"}
ITEM_KINDS = {
    "state", "visibility", "event", "side-effect", "navigation", "list",
    "binding-expression", "binding-adapter", "analytics", "accessibility",
    "lifecycle", "resource", "layout",
}
BEHAVIOR_KINDS = ITEM_KINDS - {"resource", "layout"}
TERMINAL_KINDS = {"event", "side-effect", "navigation", "analytics"}
STATE_KINDS = {"state", "visibility", "list", "binding-expression", "binding-adapter"}
SURFACE_KINDS = {"screen", "page", "surface", "component"}
FINAL_STATUSES = {"mapped", "intentionally-removed"}
BASELINE_LEVELS = {"runtime", "reference", "source", "unresolved"}
SLICE_GATES = {
    "realData", "appearance", "behavior", "preview", "compile",
    "coordinatorReview",
}


def load(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"cannot read {path}: {exc}") from exc


def text_ok(value: object, minimum: int = 8) -> bool:
    text = str(value or "").strip()
    return text.lower() not in PLACEHOLDERS and len(text) >= minimum


def check_evidence(repo: Path, value: object, label: str, errors: list[str]) -> None:
    match = EVIDENCE_RE.match(str(value or ""))
    if not match:
        errors.append(f"{label}: expected repo-relative path:line")
        return
    source = (repo / match.group(1)).resolve()
    try:
        source.relative_to(repo)
    except ValueError:
        errors.append(f"{label}: evidence escapes repository")
        return
    if not source.is_file():
        errors.append(f"{label}: evidence file missing: {value}")
        return
    line = int(match.group(2))
    with source.open(errors="ignore") as stream:
        count = sum(1 for _ in stream)
    if line < 1 or line > count:
        errors.append(f"{label}: line {line} is outside file ({count} lines)")


def check_evidence_list(repo: Path, values: object, label: str, errors: list[str]) -> list[str]:
    if not isinstance(values, list) or not values:
        errors.append(f"{label} must be a non-empty array")
        return []
    for value in values:
        check_evidence(repo, value, label, errors)
    return [str(value) for value in values]


def inventory_items(inventory: dict) -> dict[str, str]:
    result: dict[str, str] = {}
    for collection in ("views", "bindingVariables", "bindingExpressions"):
        for item in inventory.get(collection, []):
            item_id = str(item.get("inventoryId", "")).strip()
            if item_id:
                result[item_id] = str(item.get("evidence", "")).strip()
    return result


def read_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False,
    )
    if result.returncode:
        return ""
    return result.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--inventory", required=True, type=Path)
    parser.add_argument("--ledger", required=True, type=Path)
    args = parser.parse_args()

    repo = args.repo.resolve()
    evidence_dir = args.ledger.resolve().parent
    inventory = load(args.inventory)
    ledger = load(args.ledger)
    errors: list[str] = []

    if inventory.get("schemaVersion") != 2:
        errors.append("legacy-inventory.schemaVersion must be 2")
    if ledger.get("schemaVersion") != 9:
        errors.append("migration-ledger.schemaVersion must be 9")

    scope_path = evidence_dir / "scope-contract.json"
    scope = load(scope_path) if scope_path.is_file() else {}
    if not scope:
        errors.append("scope-contract.json must exist beside migration-ledger.json")
    elif scope.get("schemaVersion") != 4:
        errors.append("scope-contract.schemaVersion must be 4")

    baseline_path = evidence_dir / "baseline-assessment.json"
    baseline = load(baseline_path) if baseline_path.is_file() else {}
    if ledger.get("baselineAssessment") != "baseline-assessment.json":
        errors.append("ledger.baselineAssessment must be 'baseline-assessment.json'")
    if not baseline:
        errors.append("baseline-assessment.json must exist beside migration-ledger.json")
    elif baseline.get("schemaVersion") != 1:
        errors.append("baseline-assessment.schemaVersion must be 1")

    slices_path = evidence_dir / "migration-slices.json"
    slices_doc = load(slices_path) if slices_path.is_file() else {}
    if ledger.get("migrationSlices") != "migration-slices.json":
        errors.append("ledger.migrationSlices must be 'migration-slices.json'")
    if not slices_doc:
        errors.append("migration-slices.json must exist beside migration-ledger.json")
    elif slices_doc.get("schemaVersion") != 1:
        errors.append("migration-slices.schemaVersion must be 1")

    frozen_fields = (
        "baselineRevision", "allowedChangePrefixes", "replacementBoundary",
        "targetEntries", "preservedSharedEntries", "migrationRootLayouts",
    )
    ledger_scope = ledger.get("scope") or {}
    for field in frozen_fields:
        if scope.get(field) != ledger_scope.get(field):
            errors.append(f"ledger.scope.{field} must exactly match scope-contract.json")

    if not re.fullmatch(r"[0-9a-fA-F]{7,64}", str(scope.get("baselineRevision", ""))):
        errors.append("scope-contract.baselineRevision must be an immutable git revision")
    prefixes = scope.get("allowedChangePrefixes")
    if not isinstance(prefixes, list) or not prefixes or any(not text_ok(p, 2) for p in prefixes):
        errors.append("scope-contract.allowedChangePrefixes must contain narrow paths")
    if not text_ok(scope.get("replacementBoundary"), 12):
        errors.append("scope-contract.replacementBoundary must be concrete")
    if not isinstance(scope.get("acceptanceStates"), list) or not scope.get("acceptanceStates"):
        errors.append("scope-contract.acceptanceStates must be non-empty")

    baseline_state_names: set[str] = set()
    for index, state in enumerate(baseline.get("states") or []):
        label = f"baseline.states[{index}]"
        name = str(state.get("name", "")).strip()
        if not name or name in baseline_state_names:
            errors.append(f"{label}.name must be non-empty and unique")
        baseline_state_names.add(name)
        level = state.get("level")
        if level not in BASELINE_LEVELS:
            errors.append(f"{label}.level must be one of {sorted(BASELINE_LEVELS)}")
        appearance = state.get("appearanceEvidence")
        if level == "source":
            check_evidence_list(repo, appearance, f"{label}.appearanceEvidence", errors)
        elif appearance is not None and not isinstance(appearance, list):
            errors.append(f"{label}.appearanceEvidence must be an array")
        elif isinstance(appearance, list):
            for evidence in appearance:
                check_evidence(repo, evidence, f"{label}.appearanceEvidence", errors)
        for field in ("dataEvidence", "behaviorEvidence"):
            values = state.get(field)
            if level != "unresolved":
                check_evidence_list(repo, values, f"{label}.{field}", errors)
            elif values is not None and not isinstance(values, list):
                errors.append(f"{label}.{field} must be an array")
        artifacts = state.get("referenceArtifacts")
        if not isinstance(artifacts, list):
            errors.append(f"{label}.referenceArtifacts must be an array")
        else:
            for artifact in artifacts:
                path = (evidence_dir / str(artifact)).resolve()
                try:
                    path.relative_to(evidence_dir.resolve())
                except ValueError:
                    errors.append(f"{label}.referenceArtifacts escapes evidence directory")
                    continue
                if not path.is_file():
                    errors.append(f"{label}.referenceArtifacts is missing: {artifact}")
        if level in {"runtime", "reference"} and not artifacts:
            errors.append(f"{label}.referenceArtifacts must support {level} evidence")
        if not isinstance(state.get("uncertainties"), list):
            errors.append(f"{label}.uncertainties must be an array")
    if baseline_state_names != set(scope.get("acceptanceStates") or []):
        errors.append("baseline states must exactly match scope-contract.acceptanceStates")

    attempts = baseline.get("captureAttempts")
    if not isinstance(attempts, list):
        errors.append("baseline.captureAttempts must be an array")
    for index, attempt in enumerate(attempts or []):
        if not text_ok(attempt.get("kind"), 3) or not text_ok(attempt.get("result"), 3):
            errors.append(f"baseline.captureAttempts[{index}] must name kind and result")
        if attempt.get("result") != "available" and not text_ok(attempt.get("reason"), 12):
            errors.append(f"baseline.captureAttempts[{index}].reason must explain fallback")
    for group in ("targetEntries", "preservedSharedEntries"):
        entries = scope.get(group)
        if group == "targetEntries" and (not isinstance(entries, list) or not entries):
            errors.append("scope-contract.targetEntries must be non-empty")
            continue
        if not isinstance(entries, list):
            errors.append(f"scope-contract.{group} must be an array")
            continue
        for index, entry in enumerate(entries):
            label = f"scope-contract.{group}[{index}]"
            if not text_ok(entry.get("name")) or not text_ok(entry.get("condition"), 12):
                errors.append(f"{label} must name a concrete runtime condition")
            check_evidence_list(repo, entry.get("entryEvidence"), f"{label}.entryEvidence", errors)

    roots = set(inventory.get("rootLayouts") or [])
    layouts = set(inventory.get("layouts") or [])
    if set(scope.get("migrationRootLayouts") or []) != roots:
        errors.append("scope-contract.migrationRootLayouts must equal inventory.rootLayouts")
    if not layouts.issubset(set(ledger_scope.get("legacyLayouts") or [])):
        errors.append("ledger.scope.legacyLayouts omits recursive inventoried layouts")
    compose_roots = ledger_scope.get("productionComposeRoots")
    if not isinstance(compose_roots, list) or not compose_roots:
        errors.append("ledger.scope.productionComposeRoots must be non-empty")

    frozen_inventory = inventory_items(inventory)
    ledger_ids: set[str] = set()
    state_item_ids: set[str] = set()
    for index, item in enumerate(ledger.get("items") or []):
        label = f"items[{index}]"
        item_id = str(item.get("id", "")).strip()
        if not item_id or item_id in ledger_ids:
            errors.append(f"{label}.id must be non-empty and unique")
        ledger_ids.add(item_id)
        kind = item.get("kind")
        status = item.get("status")
        if kind not in ITEM_KINDS:
            errors.append(f"{label}.kind is invalid")
        if kind in STATE_KINDS:
            state_item_ids.add(item_id)
        if status not in FINAL_STATUSES:
            errors.append(f"{label}.status must be final")
        if not text_ok(item.get("notes"), 20):
            errors.append(f"{label}.notes must explain the mapping")
        legacy = check_evidence_list(repo, item.get("legacyEvidence"), f"{label}.legacyEvidence", errors)
        expected = frozen_inventory.get(item_id)
        if expected and expected not in legacy:
            errors.append(f"{label}.legacyEvidence must include frozen evidence {expected}")
        field = "composeEvidence" if status == "mapped" else "removalEvidence"
        check_evidence_list(repo, item.get(field), f"{label}.{field}", errors)
        if status == "mapped" and kind in BEHAVIOR_KINDS:
            tests = check_evidence_list(repo, item.get("verificationEvidence"), f"{label}.verificationEvidence", errors)
            for test in tests:
                if "/src/test/" not in test and "/src/androidTest/" not in test:
                    errors.append(f"{label}.verificationEvidence must point to executable test source")
        if status == "mapped" and kind in STATE_KINDS:
            check_evidence_list(repo, item.get("producerEvidence"), f"{label}.producerEvidence", errors)
            check_evidence_list(repo, item.get("mappingEvidence"), f"{label}.mappingEvidence", errors)
    missing = sorted(set(frozen_inventory) - ledger_ids)
    if missing:
        errors.append("inventory entries missing from ledger: " + ", ".join(missing))

    contracts = ledger.get("behaviorContracts")
    if not isinstance(contracts, list) or not contracts:
        errors.append("behaviorContracts must be non-empty")
    seen_contracts: set[str] = set()
    for index, contract in enumerate(contracts or []):
        label = f"behaviorContracts[{index}]"
        contract_id = str(contract.get("id", "")).strip()
        if not contract_id or contract_id in seen_contracts:
            errors.append(f"{label}.id must be non-empty and unique")
        seen_contracts.add(contract_id)
        kind = contract.get("kind")
        if kind not in BEHAVIOR_KINDS:
            errors.append(f"{label}.kind must be behavioral")
        if not text_ok(contract.get("notes"), 20):
            errors.append(f"{label}.notes must explain terminal parity")
        for field in ("legacyEvidence", "composeEvidence", "verificationEvidence"):
            values = check_evidence_list(repo, contract.get(field), f"{label}.{field}", errors)
            if field == "verificationEvidence":
                for value in values:
                    if "/src/test/" not in value and "/src/androidTest/" not in value:
                        errors.append(f"{label}.{field} must point to executable test source")
        if kind in TERMINAL_KINDS:
            check_evidence_list(repo, contract.get("terminalEffectEvidence"), f"{label}.terminalEffectEvidence", errors)

    slices = slices_doc.get("slices")
    if not isinstance(slices, list) or not slices:
        errors.append("migration-slices.slices must be a non-empty array")
    slice_ids: set[str] = set()
    sliced_ledger_ids: list[str] = []
    sliced_contract_ids: list[str] = []
    orders: list[int] = []
    representative_count = 0
    for index, item in enumerate(slices or []):
        label = f"migration-slices.slices[{index}]"
        slice_id = str(item.get("id", "")).strip()
        if not slice_id or slice_id in slice_ids:
            errors.append(f"{label}.id must be non-empty and unique")
        slice_ids.add(slice_id)
        if not text_ok(item.get("name"), 5):
            errors.append(f"{label}.name must be concrete")
        order = item.get("order")
        if not isinstance(order, int) or order < 1:
            errors.append(f"{label}.order must be a positive integer")
        else:
            orders.append(order)
        if item.get("representative") is True:
            representative_count += 1
        sliced_ledger_ids.extend(str(v) for v in item.get("ledgerItemIds") or [])
        sliced_contract_ids.extend(str(v) for v in item.get("behaviorContractIds") or [])
        if not set(item.get("acceptanceStates") or []).issubset(set(scope.get("acceptanceStates") or [])):
            errors.append(f"{label}.acceptanceStates contains unknown states")
        if item.get("status") != "passed":
            errors.append(f"{label}.status must be 'passed' for final validation")
        gates = item.get("gates") or {}
        if set(gates) != SLICE_GATES or any(value != "pass" for value in gates.values()):
            errors.append(f"{label}.gates must contain exactly the six passing slice gates")
        if not text_ok(item.get("reviewNotes"), 30):
            errors.append(f"{label}.reviewNotes must record coordinator review")
    if orders and sorted(orders) != list(range(1, len(orders) + 1)):
        errors.append("migration slice order must be contiguous starting at 1")
    if representative_count != 1:
        errors.append("migration slices must identify exactly one representative slice")
    if set(sliced_ledger_ids) != ledger_ids or len(sliced_ledger_ids) != len(set(sliced_ledger_ids)):
        errors.append("every ledger item must belong to exactly one migration slice")
    if set(sliced_contract_ids) != seen_contracts or len(sliced_contract_ids) != len(set(sliced_contract_ids)):
        errors.append("every behavior contract must belong to exactly one migration slice")

    for name in ("convergence-review.md", "verification-summary.md"):
        path = evidence_dir / name
        if not path.is_file() or not text_ok(path.read_text(errors="ignore"), 80):
            errors.append(f"{name} must exist and contain a substantive review")

    artifact_names = {
        "previewCatalog": "preview-catalog.json",
        "previewSummary": "preview-summary.json",
        "performanceAudit": "performance-audit.json",
    }
    artifacts: dict[str, dict] = {}
    for field, expected_name in artifact_names.items():
        if ledger.get(field) != expected_name:
            errors.append(f"ledger.{field} must be {expected_name!r}")
        path = evidence_dir / expected_name
        if not path.is_file():
            errors.append(f"{expected_name} is missing")
            artifacts[field] = {}
        else:
            artifacts[field] = load(path)

    catalog = artifacts.get("previewCatalog", {})
    if catalog.get("schemaVersion") != 3:
        errors.append("preview-catalog.schemaVersion must be 3")
    check_evidence_list(repo, catalog.get("productionScreenEvidence"), "preview.productionScreenEvidence", errors)
    check_evidence_list(repo, catalog.get("fixtureFactoryEvidence"), "preview.fixtureFactoryEvidence", errors)
    if not isinstance(catalog.get("requiredCoverage"), list) or not catalog.get("requiredCoverage"):
        errors.append("preview.requiredCoverage must be non-empty")
    if not isinstance(catalog.get("notApplicable"), list):
        errors.append("preview.notApplicable must be an array")

    scenario_names: set[str] = set()
    acceptance_covered: list[str] = []
    scenarios = catalog.get("scenarios") or []
    for index, scenario in enumerate(scenarios):
        label = f"preview.scenarios[{index}]"
        name = str(scenario.get("name", "")).strip()
        if not name or name in scenario_names:
            errors.append(f"{label}.name must be non-empty and unique")
        scenario_names.add(name)
        check_evidence(repo, scenario.get("previewEvidence"), f"{label}.previewEvidence", errors)
        check_evidence(repo, scenario.get("productionScreenCallEvidence"), f"{label}.productionScreenCallEvidence", errors)
        image = evidence_dir / str(scenario.get("previewImage", ""))
        if not image.is_file():
            errors.append(f"{label}.previewImage is missing")
        if not scenario.get("surfaceIds") or not scenario.get("coverage"):
            errors.append(f"{label} must cover surfaces and cases")
        acceptance = str(scenario.get("acceptanceStateName", "")).strip()
        if acceptance:
            acceptance_covered.append(acceptance)
    if set(acceptance_covered) != set(scope.get("acceptanceStates") or []):
        errors.append("Preview scenarios must cover every acceptance state exactly by name")

    surface_ids: set[str] = set()
    preview_ledger_ids: set[str] = set()
    for index, surface in enumerate(catalog.get("surfaces") or []):
        label = f"preview.surfaces[{index}]"
        surface_id = str(surface.get("id", "")).strip()
        if not surface_id or surface_id in surface_ids:
            errors.append(f"{label}.id must be non-empty and unique")
        surface_ids.add(surface_id)
        if surface.get("kind") not in SURFACE_KINDS:
            errors.append(f"{label}.kind is invalid")
        check_evidence_list(repo, surface.get("productionEvidence"), f"{label}.productionEvidence", errors)
        preview_ledger_ids.update(surface.get("ledgerItemIds") or [])
        if not set(surface.get("scenarioNames") or []).issubset(scenario_names):
            errors.append(f"{label}.scenarioNames contains unknown scenarios")
    if ledger_ids - preview_ledger_ids:
        errors.append("ledger items missing Preview surface coverage: " + ", ".join(sorted(ledger_ids - preview_ledger_ids)))

    for index, excluded in enumerate(catalog.get("excludedComposables") or []):
        label = f"preview.excludedComposables[{index}]"
        check_evidence(repo, excluded.get("productionEvidence"), f"{label}.productionEvidence", errors)
        if not text_ok(excluded.get("rationale"), 30):
            errors.append(f"{label}.rationale must prove parent-only coverage")

    field_paths: set[str] = set()
    field_ledger_ids: set[str] = set()
    for index, field in enumerate(catalog.get("stateFields") or []):
        label = f"preview.stateFields[{index}]"
        path = str(field.get("path", "")).strip()
        if not path or path in field_paths:
            errors.append(f"{label}.path must be non-empty and unique")
        field_paths.add(path)
        if not text_ok(field.get("type"), 2):
            errors.append(f"{label}.type is required")
        check_evidence_list(repo, field.get("productionEvidence"), f"{label}.productionEvidence", errors)
        field_ledger_ids.update(field.get("ledgerItemIds") or [])
        cases = field.get("cases")
        if not isinstance(cases, list) or not cases:
            errors.append(f"{label}.cases must be non-empty")
        for case_index, case in enumerate(cases or []):
            case_label = f"{label}.cases[{case_index}]"
            if not text_ok(case.get("valueClass"), 2):
                errors.append(f"{case_label}.valueClass is required")
            if not set(case.get("scenarioNames") or []).issubset(scenario_names) or not case.get("scenarioNames"):
                errors.append(f"{case_label}.scenarioNames must reference scenarios")
    if state_item_ids - field_ledger_ids:
        errors.append("state-like ledger items missing state-field coverage: " + ", ".join(sorted(state_item_ids - field_ledger_ids)))

    for index, scenario in enumerate(scenarios):
        unknown = set(scenario.get("surfaceIds") or []) - surface_ids
        if unknown:
            errors.append(f"preview.scenarios[{index}] references unknown surfaces: {sorted(unknown)}")

    summary = artifacts.get("previewSummary", {})
    if summary.get("status") != "passed" or summary.get("compiled") is not True:
        errors.append("preview-summary must be compiled and passed")
    if set(summary.get("renderedScenarioNames") or []) != scenario_names:
        errors.append("preview-summary rendered scenarios must exactly match catalog")
    if set(summary.get("coveredSurfaceIds") or []) != surface_ids:
        errors.append("preview-summary covered surfaces must exactly match catalog")
    if set(summary.get("coveredStateFieldPaths") or []) != field_paths:
        errors.append("preview-summary covered state fields must exactly match catalog")
    if summary.get("usesSharedProductionComponents") is not True or summary.get("containsPreviewOnlyUi") is not False:
        errors.append("preview-summary must prove shared production UI with no Preview-only fork")
    if summary.get("visualReview") != "pass":
        errors.append("preview-summary.visualReview must be pass")

    audit = artifacts.get("performanceAudit", {})
    if audit.get("schemaVersion") != 1 or audit.get("status") != "pass":
        errors.append("performance-audit must be schema 1 with pass status")
    audit_surface_ids: set[str] = set()
    policy_fields = (
        "stateReadOwnership", "recompositionBoundary", "stabilityContract",
        "collectionPolicy", "mediaPolicy", "effectAnimationPolicy", "expensiveWorkPolicy",
    )
    for index, surface in enumerate(audit.get("surfaces") or []):
        label = f"performance.surfaces[{index}]"
        surface_id = str(surface.get("surfaceId", "")).strip()
        audit_surface_ids.add(surface_id)
        check_evidence_list(repo, surface.get("productionEvidence"), f"{label}.productionEvidence", errors)
        for field in policy_fields:
            if not text_ok(surface.get(field), 20):
                errors.append(f"{label}.{field} must record a concrete decision")
        stress = set(surface.get("stressScenarioNames") or [])
        if not stress or not stress.issubset(scenario_names):
            errors.append(f"{label}.stressScenarioNames must reference Preview scenarios")
    if audit_surface_ids != surface_ids:
        errors.append("performance-audit surfaces must exactly match Preview surfaces")
    handoff = audit.get("measurementHandoff")
    if not isinstance(handoff, list) or not handoff:
        errors.append("performance-audit.measurementHandoff must name coordinator measurements")
    for index, item in enumerate(handoff or []):
        if item.get("surfaceId") not in surface_ids:
            errors.append(f"performance.measurementHandoff[{index}].surfaceId is unknown")
        if not text_ok(item.get("transition"), 12) or not text_ok(item.get("invariant"), 20):
            errors.append(f"performance.measurementHandoff[{index}] must be concrete")

    head = read_git(repo, "rev-parse", "HEAD")
    if summary.get("sourceRevision") != head or audit.get("sourceRevision") != head:
        errors.append("Preview summary and performance audit must reference current HEAD")
    changed = read_git(repo, "status", "--porcelain")
    allowed = tuple(str(p).rstrip("/") + "/" for p in prefixes or [])
    for line in changed.splitlines():
        path = line[3:].split(" -> ")[-1]
        if allowed and not path.startswith(allowed):
            errors.append(f"changed path is outside allowedChangePrefixes: {path}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(
        f"PASS: {len(ledger_ids)} ledger items, {len(seen_contracts)} behaviors, "
        f"{len(slice_ids)} converged slices, {len(surface_ids)} surfaces, "
        f"{len(field_paths)} state fields, "
        f"{len(scenario_names)} Preview scenarios"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
