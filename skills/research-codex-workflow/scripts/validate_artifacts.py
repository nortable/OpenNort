#!/usr/bin/env python3
"""Validate research-codex-workflow templates and synthetic fixture.

The bundled templates are JSON-compatible YAML, so this script uses the standard library only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Canonical schema registry (Pillar 4). Importing it is what turns "schema discipline" from prose
# into an enforced tool call shared by the validator and the generator.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from schemas import (  # noqa: E402
    SCHEMAS,
    TEMPLATE_SCHEMA_MAP,
    FORBIDDEN_WORKER_ACTIONS,
    FANOUT_RANGE,
    BUDGET_CEILING,
    validate_obj,
)


SKILL_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = SKILL_ROOT / "assets" / "templates"

# Map a run-tree glob to the schema each matching artifact instance must satisfy. The two
# "#decisions[]" wrappers validate their list elements via the registry's item_required mapping.
ARTIFACT_ROUTING: dict[str, str] = {
    "00-charter.yaml": "task-charter",
    "01-dispatch-plan.yaml": "dispatch-plan",
    "round-a-findings/*.yaml": "finding",
    "round-b-critiques/*.yaml": "critique",
    "round-c-evidence-decisions.yaml": "evidence-decision-bundle",
    "evidence-packets/*.yaml": "evidence-packet",
    "round-d-judge-scores/*.yaml": "judge-score",
    "round-e-decision-ledger.yaml": "decision-ledger",
    "round-f-user-checkpoint.yaml": "user-checkpoint",
    "progress-snapshots/*.yaml": "progress-snapshot",
    "round-g-final-report.yaml": "final-report",
    "experiment-cards/*.yaml": "experiment-card",
    "agents/*.json": "subagent-record",
}


def load_json_yaml(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path}: not JSON-compatible YAML: {exc}") from exc


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def validate_templates() -> list[str]:
    """Check every shipped template against the canonical registry (required keys + enum membership).

    Blank-template placeholders are tolerated, but a seeded enum value (e.g. judge-score
    final_class) that is not in the registry vocabulary fails here.
    """
    failures: list[str] = []
    for name, schema_name in TEMPLATE_SCHEMA_MAP.items():
        path = TEMPLATE_DIR / name
        require(path.exists(), f"missing template: {path}", failures)
        if not path.exists():
            continue
        data = load_json_yaml(path)
        require(isinstance(data, dict), f"{name}: top-level object must be a mapping", failures)
        if isinstance(data, dict):
            for err in validate_obj(schema_name, data, skip_empty=True, allow_extra=True):
                failures.append(f"{name}: {err}")
    return failures


def validate_fixture(path: Path) -> list[str]:
    failures: list[str] = []
    data = load_json_yaml(path)
    require(isinstance(data, dict), "fixture top-level must be a mapping", failures)
    if not isinstance(data, dict):
        return failures

    findings = data.get("round_a_findings", [])
    require(len(findings) >= 3, "fixture needs at least three Round A findings", failures)
    by_case = {item.get("seeded_case"): item for item in findings if isinstance(item, dict)}

    irrelevant = by_case.get("true_but_decision_irrelevant", {})
    require(irrelevant.get("expected_action") in {"PARK", "REJECT"}, "irrelevant finding must park or reject", failures)
    require(bool(irrelevant.get("evidence")), "irrelevant-but-true finding still needs inspectable evidence", failures)

    unsupported = by_case.get("plausible_blocker_without_inspectable_evidence", {})
    require(unsupported.get("evidence_present") is False, "unsupported blocker must have no evidence", failures)
    require(
        unsupported.get("expected_decision_class") == "rejected_or_unsupported",
        "unsupported blocker must not remain accepted",
        failures,
    )

    valid = by_case.get("valid_blocker_with_file_or_command_evidence", {})
    require(valid.get("evidence_present") is True, "valid blocker must have evidence", failures)
    require(valid.get("expected_support_status") == "accepted", "valid blocker must be accepted", failures)
    require(valid.get("expected_decision_class") == "accepted_blocker", "valid blocker must be accepted_blocker", failures)

    critiques = data.get("round_b_critiques", [])
    unsupported_critiques = [
        item for item in critiques
        if isinstance(item, dict) and item.get("seeded_case") == "rhetorically_strong_but_unsupported_critique"
    ]
    require(bool(unsupported_critiques), "fixture needs unsupported rhetorical critique", failures)
    if unsupported_critiques:
        critique = unsupported_critiques[0]
        require(critique.get("expected_support_status") == "unsupported", "unsupported critique must be downgraded", failures)

    loop = data.get("loop_guard_fixture", {})
    require(loop.get("expected_loop_guard_action") in {"HUMAN_REVIEW", "ABANDON", "REPLAN"}, "loop guard must trigger", failures)
    require(len(loop.get("repeated_task_signatures", [])) >= 2, "loop fixture needs repeated signatures", failures)

    checkpoint = data.get("round_f_checkpoint", {})
    require(checkpoint.get("expected_decision_class") == "needs_user_decision", "contested choice must need user decision", failures)
    require(checkpoint.get("expected_stop_round") == "F", "contested choice must stop at Round F", failures)

    ownership = data.get("worker_ownership_fixture", {})
    require(ownership.get("expected_parallel_write_allowed") is False, "overlapping writers must be prevented", failures)
    tasks = ownership.get("write_tasks", [])
    if len(tasks) >= 2:
        owns = [set(task.get("owns", [])) for task in tasks if isinstance(task, dict)]
        overlap = set.intersection(*owns) if owns else set()
        require(bool(overlap), "ownership fixture should contain a deliberate collision", failures)

    expected = data.get("expected_summary", {})
    for key in (
        "irrelevant_finding_parked",
        "unsupported_blocker_downgraded",
        "evidenced_blocker_accepted",
        "unsupported_critique_rejected",
        "loop_guard_triggered",
        "round_f_checkpoint_created",
        "overlapping_parallel_writes_prevented",
    ):
        require(expected.get(key) is True, f"expected_summary.{key} must be true", failures)
    require(expected.get("paid_api_required") is False, "synthetic fixture must not require paid APIs", failures)
    return failures


# Roles that must stay strictly read-only (R20). Matched EXACTLY against a dispatch role, never by
# substring (substring would wrongly gate legitimately-combined writer roles in lightweight/standard mode).
READ_ONLY_ROLES = frozenset({
    "Research Director", "Relevance Arbiter", "Literature Scout", "Data Auditor", "Baseline Auditor",
    "Claim Auditor", "Hypothesis Generator", "Falsifier", "Methodologist", "Code Red-Team",
    "Test Reviewer", "Evidence Auditor", "Judge", "Loop Guard", "Completeness Critic",
})

# Mandatory non-empty run directories (R22 per-round completeness). experiment-cards/ and writers/ may
# legitimately be empty, so they are not required here.
REQUIRED_NONEMPTY_DIRS = (
    "round-a-findings", "round-b-critiques", "round-d-judge-scores", "evidence-packets",
    "progress-snapshots",
)


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def validate_anonymization(run_root: Path, failures: list[str]) -> None:
    """R22: Round B critiques and evidence packets must not expose author identity. Identity terms are
    the finding `role` values plus the dispatch role names. Substring heuristic — reduces, does not
    eliminate, leaks (see full-adversarial-workflow.md anonymization rules)."""
    identity_terms: set[str] = set()
    for path in sorted(run_root.glob("round-a-findings/*.yaml")):
        data = load_json_yaml(path)
        if isinstance(data, dict):
            role = (data.get("role") or "").strip()
            if len(role) >= 3:
                identity_terms.add(role)
    plan_path = run_root / "01-dispatch-plan.yaml"
    if plan_path.exists():
        plan = load_json_yaml(plan_path)
        for d in plan.get("dispatches", []) if isinstance(plan, dict) else []:
            role = (d.get("role") or "").strip() if isinstance(d, dict) else ""
            if len(role) >= 3:
                identity_terms.add(role)
    if not identity_terms:
        return
    for pattern in ("round-b-critiques/*.yaml", "evidence-packets/*.yaml"):
        for path in sorted(run_root.glob(pattern)):
            text = path.read_text(encoding="utf-8")
            for term in identity_terms:
                if term in text:
                    failures.append(
                        f"{path.relative_to(run_root)}: anonymization leak — exposes author identity "
                        f"{term!r}"
                    )


def validate_round_completeness(run_root: Path, failures: list[str]) -> None:
    """R22: derive per-round completeness from the canonical manifest instead of only hardcoded paths."""
    for name in REQUIRED_NONEMPTY_DIRS:
        if not list((run_root / name).glob("*.yaml")):
            failures.append(f"round directory {name}/ is empty (expected at least one artifact)")


def validate_dispatch_plan(run_root: Path, failures: list[str]) -> None:
    """R18: value-check the concurrency / depth / budget / fan-out caps on a real plan. These are
    script-checked conventions (not engine-enforced) mirroring the canonical Concurrency Policy."""
    plan_path = run_root / "01-dispatch-plan.yaml"
    if not plan_path.exists():
        return
    plan = load_json_yaml(plan_path)
    if not isinstance(plan, dict):
        return

    if plan.get("max_subagent_depth") != 1:
        failures.append("01-dispatch-plan.yaml: max_subagent_depth must be 1")
    cap = plan.get("max_concurrent_subagents")
    if not _is_int(cap) or not (1 <= cap <= 12):
        failures.append("01-dispatch-plan.yaml: max_concurrent_subagents must be an int in [1,12]")
        cap = 12
    fallback = plan.get("fallback_if_subagents_unavailable")
    if not isinstance(fallback, str) or not fallback.strip():
        failures.append("01-dispatch-plan.yaml: fallback_if_subagents_unavailable must be a non-empty string")
    backstop = plan.get("agent_count_backstop")
    if not _is_int(backstop) or backstop < 1:
        failures.append("01-dispatch-plan.yaml: agent_count_backstop must be a positive int")
    tier = plan.get("budget_tier")
    ceiling = BUDGET_CEILING.get(tier)
    if ceiling is None:
        failures.append(f"01-dispatch-plan.yaml: budget_tier {tier!r} not in {sorted(BUDGET_CEILING)}")
        ceiling = 6
    stop_rule = plan.get("stop_rule")
    if stop_rule is not None:
        for err in validate_obj("stop-rule", stop_rule, skip_empty=False, allow_extra=True):
            failures.append(f"01-dispatch-plan.yaml stop_rule: {err}")

    for idx, group in enumerate(plan.get("dispatch_groups", [])):
        if not isinstance(group, dict):
            continue
        if "fanout_chosen" not in group and "fanout_min" not in group:
            continue  # fan-out block is optional; skip silently when absent
        rnd = group.get("round")
        fmin, fmax, fch = group.get("fanout_min"), group.get("fanout_max"), group.get("fanout_chosen")
        loc = f"01-dispatch-plan.yaml dispatch_groups[{idx}]"
        if not (_is_int(fmin) and _is_int(fmax) and _is_int(fch)):
            failures.append(f"{loc}: fanout_min/max/chosen must be ints")
            continue
        if not (fmin <= fch <= fmax):
            failures.append(f"{loc}: fanout_chosen {fch} not in [{fmin},{fmax}]")
        canonical = FANOUT_RANGE.get(rnd)
        if canonical is not None and (fmin, fmax) != canonical:
            failures.append(f"{loc}: round {rnd} fanout ({fmin},{fmax}) != canonical {canonical}")
        if fch > cap:
            failures.append(f"{loc}: fanout_chosen {fch} exceeds concurrency cap {cap}")
        if fch > ceiling:
            failures.append(f"{loc}: fanout_chosen {fch} exceeds budget_tier {tier!r} ceiling {ceiling}")

    # R20: read-only roles may not carry write permission or owned files (exact role match).
    for idx, dispatch in enumerate(plan.get("dispatches", [])):
        if not isinstance(dispatch, dict):
            continue
        role = (dispatch.get("role") or "").strip()
        if role in READ_ONLY_ROLES:
            if dispatch.get("permissions") != "read-only":
                failures.append(
                    f"01-dispatch-plan.yaml dispatches[{idx}]: read-only role {role!r} has "
                    f"permissions {dispatch.get('permissions')!r}"
                )
            if dispatch.get("files_owned"):
                failures.append(
                    f"01-dispatch-plan.yaml dispatches[{idx}]: read-only role {role!r} owns files "
                    f"{dispatch.get('files_owned')}"
                )


def validate_instances(run_root: Path, failures: list[str]) -> None:
    """R5: validate every real worker artifact instance against the canonical registry (not the blank
    template). Extra keys are tolerated here; the strict no-unknown-key check is reserved for the
    single-instance --artifact mode."""
    for pattern, schema_name in ARTIFACT_ROUTING.items():
        for path in sorted(run_root.glob(pattern)):
            data = load_json_yaml(path)
            for err in validate_obj(schema_name, data, skip_empty=False, allow_extra=True):
                failures.append(f"{path.relative_to(run_root)}: {err}")


def validate_packet_provenance(run_root: Path, failures: list[str]) -> None:
    """R2 enforcement: the Orchestrator may only assemble an evidence packet from an accepted or
    partially_supported Round C decision. Every packet's source_claim_ids must intersect that set."""
    decisions_path = run_root / "round-c-evidence-decisions.yaml"
    if not decisions_path.exists():
        return
    bundle = load_json_yaml(decisions_path)
    decisions = bundle.get("decisions", []) if isinstance(bundle, dict) else []
    accepted = {
        d.get("claim_or_critique_id")
        for d in decisions
        if isinstance(d, dict) and d.get("support_status") in {"accepted", "partially_supported"}
    }
    for path in sorted(run_root.glob("evidence-packets/*.yaml")):
        packet = load_json_yaml(path)
        sources = set(packet.get("source_claim_ids", []) if isinstance(packet, dict) else [])
        if not sources & accepted:
            failures.append(
                f"{path.relative_to(run_root)}: packet has no source_claim_id tracing to an accepted "
                f"Round C decision (Orchestrator may not assemble packets from unaccepted claims)"
            )


def validate_judge_coverage(run_root: Path, failures: list[str]) -> None:
    """R27 enforcement: every assembled evidence packet must receive at least one Round D judge score.

    Closes the 'assembled N packets, judged 1, promoted N' coverage hole: a judge that picks only the
    "most decision-critical" packet leaves the rest unscored, yet Round E still promotes them. A packet
    that reaches the ledger as accepted must have been independently judged, never silently rubber-
    stamped. (Round D may legitimately be empty when Round C accepted nothing — no packets, no
    requirement.)"""
    packet_ids = [
        (load_json_yaml(p).get("packet_id", p.stem) if isinstance(load_json_yaml(p), dict) else p.stem)
        for p in sorted(run_root.glob("evidence-packets/*.yaml"))
    ]
    if not packet_ids:
        return
    judged: set[str] = set()
    for path in sorted(run_root.glob("round-d-judge-scores/*.yaml")):
        score = load_json_yaml(path)
        if isinstance(score, dict) and score.get("packet_id"):
            judged.add(score["packet_id"])
    for pid in packet_ids:
        if pid not in judged:
            failures.append(
                f"evidence-packets: packet {pid!r} has no Round D judge score — every assembled "
                f"packet must be independently judged (no silent promotion of unjudged evidence)"
            )


def validate_proportionate_verification(run_root: Path, warnings: list[str]) -> None:
    """R26 (advisory): verification effort should scale with a finding's contestability. A
    low-contestability binary fact (file exists / number A vs B) needs ONE confirmation pass, not a
    full multi-lens falsifier panel. Warn when a low-contestability finding drew >=2 critiques, and
    once when findings carry no contestability labels at all (so routing cannot be assessed)."""
    findings: dict[str, dict] = {}
    for path in sorted(run_root.glob("round-a-findings/*.yaml")):
        data = load_json_yaml(path)
        if isinstance(data, dict):
            findings[path.stem] = data
    if not findings:
        return
    if not any(f.get("contestability") for f in findings.values()):
        warnings.append(
            "Round A findings carry no contestability/depth labels; proportionate verification "
            "routing cannot be assessed (see references/full-adversarial-workflow.md "
            "'Proportionate Verification')"
        )
    crit_count: dict[str, int] = {}
    for path in sorted(run_root.glob("round-b-critiques/*.yaml")):
        crit = load_json_yaml(path)
        if isinstance(crit, dict):
            tgt = crit.get("target_finding_id")
            crit_count[tgt] = crit_count.get(tgt, 0) + 1
    for fid, data in findings.items():
        if data.get("contestability") == "low" and crit_count.get(fid, 0) >= 2:
            warnings.append(
                f"{fid}: low-contestability finding drew {crit_count[fid]} critiques; a single "
                f"confirmation pass is usually sufficient (over-verification of a binary fact)"
            )


def validate_discovery_depth(run_root: Path, warnings: list[str]) -> None:
    """R26 (advisory): a deep audit should produce at least one design/statistical-validity insight,
    not only surface doc-vs-tree drift. When findings carry depth labels but none is `deep`, warn that
    the deep-insight lens may not have run (log it as a completeness gap)."""
    findings = [
        d for d in (load_json_yaml(p) for p in sorted(run_root.glob("round-a-findings/*.yaml")))
        if isinstance(d, dict)
    ]
    if not findings:
        return
    if any("depth" in f for f in findings) and not any(f.get("depth") == "deep" for f in findings):
        warnings.append(
            "Round A produced zero depth=deep findings (only surface doc-vs-tree drift); the "
            "design/statistical-validity lens may not have run — log this as a completeness gap "
            "(see references/agent-roster.md 'Deep-Insight Lens')"
        )


def validate_provenance(run_root: Path, failures: list[str]) -> None:
    """R7 enforcement: an artifact's author (agent_id) can never be its own skeptic/auditor/judge. A
    Finding author may not also author a Critique against it or a JudgeScore of a packet built from it.
    Empty agent_id is rejected (an unattributed artifact defeats the provenance check)."""
    finding_author: dict[str, str] = {}
    for path in sorted(run_root.glob("round-a-findings/*.yaml")):
        data = load_json_yaml(path)
        if isinstance(data, dict):
            aid = (data.get("agent_id") or "").strip()
            if not aid:
                failures.append(f"{path.relative_to(run_root)}: empty agent_id")
            finding_author[path.stem] = aid

    for path in sorted(run_root.glob("round-b-critiques/*.yaml")):
        crit = load_json_yaml(path)
        if not isinstance(crit, dict):
            continue
        aid = (crit.get("agent_id") or "").strip()
        if not aid:
            failures.append(f"{path.relative_to(run_root)}: empty agent_id")
        target = crit.get("target_finding_id")
        if aid and target in finding_author and finding_author[target] == aid:
            failures.append(
                f"{path.relative_to(run_root)}: critique author {aid!r} also authored the target "
                f"finding {target!r} (generate/verify boundary violated)"
            )

    # packet_id -> set of source-claim finding authors
    packet_authors: dict[str, set[str]] = {}
    for path in sorted(run_root.glob("evidence-packets/*.yaml")):
        packet = load_json_yaml(path)
        if isinstance(packet, dict):
            authors = {finding_author.get(src, "") for src in packet.get("source_claim_ids", []) or []}
            packet_authors[packet.get("packet_id", path.stem)] = authors

    for path in sorted(run_root.glob("round-d-judge-scores/*.yaml")):
        score = load_json_yaml(path)
        if not isinstance(score, dict):
            continue
        aid = (score.get("agent_id") or "").strip()
        if not aid:
            failures.append(f"{path.relative_to(run_root)}: empty agent_id")
        pid = score.get("packet_id")
        if aid and pid in packet_authors and aid in packet_authors[pid]:
            failures.append(
                f"{path.relative_to(run_root)}: judge author {aid!r} also authored a source finding "
                f"of packet {pid!r} (generate/verify boundary violated)"
            )


def validate_references(run_root: Path, failures: list[str]) -> None:
    """R6: every cross-artifact id must resolve. The Orchestrator operates on data, so a dangling
    reference (a critique pointing at a non-existent finding, a judge score at a non-existent packet)
    is a hard failure, not prose to skim past."""
    finding_ids: list[str] = [p.stem for p in sorted(run_root.glob("round-a-findings/*.yaml"))]
    packet_ids: list[str] = []
    evidence_universe: set[str] = set()

    for path in sorted(run_root.glob("evidence-packets/*.yaml")):
        packet = load_json_yaml(path)
        if isinstance(packet, dict):
            packet_ids.append(packet.get("packet_id", path.stem))
            evidence_universe.update(packet.get("accepted_evidence_ids", []) or [])
            for src in packet.get("source_claim_ids", []) or []:
                if src not in finding_ids:
                    failures.append(f"{path.relative_to(run_root)}: dangling source_claim_id {src!r}")

    decisions_path = run_root / "round-c-evidence-decisions.yaml"
    if decisions_path.exists():
        bundle = load_json_yaml(decisions_path)
        for d in bundle.get("decisions", []) if isinstance(bundle, dict) else []:
            if isinstance(d, dict):
                evidence_universe.update(d.get("accepted_evidence_ids", []) or [])

    for path in sorted(run_root.glob("round-b-critiques/*.yaml")):
        crit = load_json_yaml(path)
        target = crit.get("target_finding_id") if isinstance(crit, dict) else None
        if target is not None and target not in finding_ids:
            failures.append(f"{path.relative_to(run_root)}: dangling target_finding_id {target!r}")

    for path in sorted(run_root.glob("round-d-judge-scores/*.yaml")):
        score = load_json_yaml(path)
        pid = score.get("packet_id") if isinstance(score, dict) else None
        if pid is not None and pid not in packet_ids:
            failures.append(f"{path.relative_to(run_root)}: dangling packet_id {pid!r}")

    ledger_path = run_root / "round-e-decision-ledger.yaml"
    if ledger_path.exists():
        ledger = load_json_yaml(ledger_path)
        for d in ledger.get("decisions", []) if isinstance(ledger, dict) else []:
            if isinstance(d, dict):
                for eid in d.get("evidence_ids", []) or []:
                    if eid not in evidence_universe:
                        failures.append(
                            f"round-e-decision-ledger.yaml: dangling evidence_id {eid!r} in "
                            f"{d.get('issue_id', '?')}"
                        )

    # ID hygiene: finding and packet ids must be unique.
    for label, ids in (("finding", finding_ids), ("packet", packet_ids)):
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        if dupes:
            failures.append(f"duplicate {label} ids: {dupes}")


def _leaf_strings(obj: Any) -> list[str]:
    out: list[str] = []
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, dict):
        for value in obj.values():
            out.extend(_leaf_strings(value))
    elif isinstance(obj, list):
        for item in obj:
            out.extend(_leaf_strings(item))
    return out


def scan_forbidden_worker_actions(run_root: Path, failures: list[str]) -> None:
    """Pillar 1 enforcement: worker artifacts (Round A findings, Round B critiques, Relevance and
    Stagnation signals) must not carry an Orchestrator-owned decision verb. The Round E ledger is the
    only artifact where an action token is legal, so it is not scanned here. HUMAN_REVIEW is a
    checkpoint decision class, not a worker action, and is deliberately not forbidden.
    """
    worker_globs = [
        "round-a-findings/*.yaml",
        "round-b-critiques/*.yaml",
        "relevance-scores/*.yaml",
        "stagnation-signals/*.yaml",
    ]
    for pattern in worker_globs:
        for path in sorted(run_root.glob(pattern)):
            data = load_json_yaml(path)
            for leaf in _leaf_strings(data):
                token = leaf.strip()
                if token in FORBIDDEN_WORKER_ACTIONS:
                    failures.append(
                        f"{path.relative_to(run_root)}: worker artifact carries decision verb "
                        f"{token!r}; actions belong only to the Round E ledger"
                    )
                elif "RUN/DEFER" in token or "/PARK/" in token:
                    failures.append(
                        f"{path.relative_to(run_root)}: worker artifact leaks the action-verb menu "
                        f"({token!r}); the Orchestrator owns the action"
                    )


def validate_dispatch_groups(run_root: Path, failures: list[str], warnings: list[str]) -> None:
    """Validate the dispatch_groups[] block on a real plan: dispatch_kind enum + the A->B->C
    single-pipeline expectation (a warning, not a failure)."""
    plan_path = run_root / "01-dispatch-plan.yaml"
    if not plan_path.exists():
        return
    plan = load_json_yaml(plan_path)
    if not isinstance(plan, dict):
        return
    groups = plan.get("dispatch_groups", [])
    if not isinstance(groups, list) or not groups:
        warnings.append("dispatch plan has no dispatch_groups; barrier/pipeline shape is undeclared")
        return
    kinds_by_round: dict[str, str] = {}
    for idx, group in enumerate(groups):
        for err in validate_obj("dispatch-group", group, skip_empty=False, allow_extra=True):
            failures.append(f"01-dispatch-plan.yaml dispatch_groups[{idx}]: {err}")
        if isinstance(group, dict) and isinstance(group.get("round"), str):
            kinds_by_round[group["round"]] = group.get("dispatch_kind", "")
    if "B" in kinds_by_round and "C" in kinds_by_round:
        if not (kinds_by_round["B"] == "pipeline" and kinds_by_round["C"] == "pipeline"):
            warnings.append(
                "Rounds B and C should stream per-finding (dispatch_kind: pipeline) rather than run as "
                "separate barriers; see references/team-runbook.md Dispatch Script"
            )


def validate_run_output(run_root: Path, warnings: list[str] | None = None) -> list[str]:
    failures: list[str] = []
    if warnings is None:
        warnings = []
    required_paths = [
        "00-charter.yaml",
        "01-dispatch-plan.yaml",
        "round-a-findings/F-IRRELEVANT-1.yaml",
        "round-a-findings/F-UNSUPPORTED-BLOCKER-1.yaml",
        "round-a-findings/F-VALID-BLOCKER-1.yaml",
        "round-b-critiques/C-UNSUPPORTED-1.yaml",
        "round-c-evidence-decisions.yaml",
        "evidence-packets/P-F-VALID-BLOCKER-1.yaml",
        "round-d-judge-scores/J1-P-F-VALID-BLOCKER-1.yaml",
        "round-e-decision-ledger.yaml",
        "round-f-user-checkpoint.yaml",
        "round-f-user-checkpoint.md",
        "progress-snapshots/round-e.yaml",
        "round-g-final-report.yaml",
        "round-g-final-report.md",
        "run-summary.yaml",
    ]
    for rel in required_paths:
        require((run_root / rel).exists(), f"generated run missing {rel}", failures)
    if failures:
        return failures
    require(
        not (run_root / "evidence-packets/P-F-IRRELEVANT-1.yaml").exists(),
        "irrelevant finding must be parked before Judge evidence packets",
        failures,
    )

    ledger = load_json_yaml(run_root / "round-e-decision-ledger.yaml")
    decisions = ledger.get("decisions", []) if isinstance(ledger, dict) else []
    classes = {item.get("decision_class") for item in decisions if isinstance(item, dict)}
    require("accepted_blocker" in classes, "generated run must contain accepted_blocker", failures)
    require("rejected_or_unsupported" in classes, "generated run must contain rejected_or_unsupported", failures)
    require("needs_user_decision" in classes, "generated run must contain needs_user_decision", failures)

    checkpoint = load_json_yaml(run_root / "round-f-user-checkpoint.yaml")
    require(checkpoint.get("stop_round") == "F", "generated run must stop at Round F", failures)
    require(checkpoint.get("edit_permission_before_approval") is False, "generated run must block edits before approval", failures)

    summary = load_json_yaml(run_root / "run-summary.yaml")
    require(summary.get("protected_files_not_edited") is True, "generated run must preserve protected files", failures)
    require(summary.get("loop_guard_action") in {"HUMAN_REVIEW", "ABANDON", "REPLAN"}, "generated run must trigger Loop Guard", failures)

    failures.extend(validate_real_run(run_root, warnings))
    return failures


def validate_real_run(run_root: Path, warnings: list[str]) -> list[str]:
    """The substrate checks that apply to ANY run tree (not only the synthetic fixture): schema
    conformance, cross-artifact references, generate/verify provenance, dispatch caps, anonymization,
    packet provenance, judge coverage, and the proportionate-verification / discovery-depth advisories.

    Unlike validate_run_output (which also asserts the fixture's exact filenames and seeded decision
    classes), this is fixture-agnostic, so `--audit-run <path>` can gate a real Codex/agent run."""
    failures: list[str] = []
    validate_instances(run_root, failures)
    validate_references(run_root, failures)
    validate_provenance(run_root, failures)
    validate_dispatch_plan(run_root, failures)
    validate_dispatch_groups(run_root, failures, warnings)
    scan_forbidden_worker_actions(run_root, failures)
    validate_packet_provenance(run_root, failures)
    validate_judge_coverage(run_root, failures)
    validate_anonymization(run_root, failures)
    validate_round_completeness(run_root, failures)
    validate_proportionate_verification(run_root, warnings)
    validate_discovery_depth(run_root, warnings)
    return failures


def validate_single_artifact(path: Path, schema_name: str | None) -> list[str]:
    """Strict single-instance validation (used by `--artifact PATH --type NAME`).

    Unknown top-level keys are rejected in this mode so a worker that pads its artifact with
    out-of-contract fields fails, mirroring tool-layer schema validation.
    """
    if schema_name is None:
        return ["--artifact requires --type <schema_name> (see scripts/schemas.py SCHEMAS)"]
    if schema_name not in SCHEMAS:
        return [f"unknown schema '{schema_name}' (see scripts/schemas.py SCHEMAS)"]
    if not path.exists():
        return [f"missing artifact: {path}"]
    data = load_json_yaml(path)
    return validate_obj(schema_name, data, skip_empty=False, allow_extra=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, default=SKILL_ROOT / "examples" / "synthetic-adversarial-case.yaml")
    parser.add_argument("--run-root", type=Path, default=None,
                        help="validate the synthetic fixture run tree (fixture-specific paths + general checks)")
    parser.add_argument("--audit-run", type=Path, default=None,
                        help="gate any real run tree with the fixture-agnostic substrate checks")
    parser.add_argument("--artifact", type=Path, default=None, help="validate a single artifact instance")
    parser.add_argument("--type", dest="schema_name", default=None, help="schema name for --artifact")
    args = parser.parse_args()

    warnings: list[str] = []

    if args.artifact is not None:
        failures = validate_single_artifact(args.artifact, args.schema_name)
    elif args.audit_run is not None:
        failures = validate_real_run(args.audit_run, warnings)
    else:
        failures = validate_templates()
        failures.extend(validate_fixture(args.fixture))
        if args.run_root is not None:
            failures.extend(validate_run_output(args.run_root, warnings))

    for warning in warnings:
        print(f"WARN: {warning}", file=sys.stderr)
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1

    if args.artifact is not None:
        print(f"OK: {args.artifact} conforms to schema '{args.schema_name}'")
    elif args.audit_run is not None:
        print(f"OK: {args.audit_run} passes the fixture-agnostic substrate checks")
    else:
        print("OK: templates parse and synthetic fixture satisfies seeded adversarial checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
