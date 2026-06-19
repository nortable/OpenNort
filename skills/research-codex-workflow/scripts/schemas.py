#!/usr/bin/env python3
"""Canonical artifact-contract registry for research-codex-workflow.

This module is the SINGLE machine-readable source of truth for every adversarial-workflow
artifact. Both the validator (`validate_artifacts.py`) and the deterministic generator
(`run_synthetic_fixture.py`) import it, so a contract can never drift between "what the
prose says", "what the generator emits", and "what the validator enforces".

It is the Codex translation of the master-template rule (Pillar 4): every worker output is a
schema-conformant object the substrate actually checks (required keys + enum membership + int
bounds + resolvable list-element contracts), and the Orchestrator rejects + redispatches any
artifact that does not conform.

Standard library only (the templates are JSON-compatible YAML).
"""

from __future__ import annotations

from typing import Any


# JudgeScore.final_class historically drifted to the bare token "rejected"; the ledger uses
# "rejected_or_unsupported". These are DISTINCT fields (a judge's class vs the Orchestrator's
# decision class) that share a vocabulary; CLASS_MAP is the canonical normalization.
CLASS_MAP: dict[str, str] = {"rejected": "rejected_or_unsupported"}

DECISION_CLASSES = frozenset(
    {"accepted_blocker", "accepted_non_blocking", "rejected_or_unsupported", "needs_user_decision"}
)
ACTION_TOKENS = frozenset({"RUN", "DEFER", "PARK", "REJECT", "HUMAN_REVIEW"})
SCOPE_DRIFT = frozenset({"low", "medium", "high"})
SEVERITY = frozenset({"blocker", "warning", "info", "unsupported"})
CLAIM_TYPE = frozenset({"observation", "inference", "recommendation"})
SUPPORT_STATUS = frozenset(
    {"accepted", "partially_supported", "unsupported", "contradicted", "needs_evidence", "needs_user_decision"}
)
EVIDENCE_QUALITY = frozenset({"high", "medium", "low", "none"})
ATTACK_TYPE = frozenset(
    {
        "evidence_gap", "wrong_scope", "wrong_denominator", "confounder", "implementation_misread",
        "irrelevant", "circularity", "leakage", "other",
    }
)
VERDICT = frozenset({"valid_attack", "partial_attack", "weak_attack", "unsupported_attack"})
REFUTE_DISPOSITION = frozenset({"refuted", "not_refuted", "uncertain"})
# R26 proportionate verification. A finding's `depth` separates a surface doc-vs-tree/number mismatch
# from a deep design/statistical-validity insight; `contestability` is how settle-able the claim is (a
# binary file/command check vs a judgment a skeptic could reasonably dispute). The Orchestrator reads
# `contestability` to ROUTE verification effort: low -> one light confirmation pass; medium|high (or a
# high-stakes blocker) -> the full adversarial Falsifier -> Tribunal -> Judge chain.
DEPTH = frozenset({"surface", "deep"})
CONTESTABILITY = frozenset({"low", "medium", "high"})
VERIFICATION_ROUTE = frozenset({"light", "adversarial"})
LOOP_GUARD_ACTION = frozenset({"CONTINUE", "REPLAN", "BRANCH", "ABANDON", "HUMAN_REVIEW"})
BUDGET_TIER = frozenset({"economy", "standard", "deep"})
DISPATCH_KIND = frozenset({"barrier", "pipeline"})

# Canonical per-round fan-out ranges (ceilings on NEW spawns; never exceed the 12-open cap) and the
# budget-tier ceilings on Round-A fan-out. Single source for validate_dispatch_plan() and the docs.
FANOUT_RANGE: dict[str, tuple[int, int]] = {
    "A": (3, 6), "B": (2, 4), "C": (1, 2), "D": (2, 3), "E": (0, 0), "F": (0, 0),
}
BUDGET_CEILING: dict[str, int] = {"economy": 2, "standard": 4, "deep": 6}

# Single canonical run-tree directory manifest (R22). create_run_workspace.py AND
# run_synthetic_fixture.py both import this, so the three former copies can never drift. `writers/`
# holds per-writer isolated workspaces (R20). Union of every former list so nothing is dropped.
ROUND_DIRS: list[str] = [
    "round-a-findings",
    "round-b-critiques",
    "round-d-judge-scores",
    "evidence-packets",
    "experiment-cards",
    "progress-snapshots",
    "writers",
    "agents",
]

# Worker-emitted "decision verbs" forbidden in Round A/B/relevance/stagnation worker bodies.
# The Orchestrator (round-e ledger) is the only place an action token is legal.
FORBIDDEN_WORKER_ACTIONS = frozenset(
    {"RUN", "DEFER", "PARK", "REJECT", "CONTINUE", "REPLAN", "BRANCH", "ABANDON"}
)


def _schema(
    required: set[str],
    optional: set[str] | None = None,
    enums: dict[str, frozenset[str]] | None = None,
    int_bounds: dict[str, tuple[int, int]] | None = None,
    item_required: dict[str, str] | None = None,
) -> dict[str, Any]:
    return {
        "required": set(required),
        "optional": set(optional or set()),
        "enums": dict(enums or {}),
        "int_bounds": dict(int_bounds or {}),
        # list_field -> schema name each element must conform to
        "item_required": dict(item_required or {}),
    }


SCHEMAS: dict[str, dict[str, Any]] = {
    # ---- Round 0 ----
    "task-charter": _schema(
        required={
            "run_id", "objective", "decision_to_support", "scope", "success_criteria",
            "user_checkpoint_required", "edit_permission_before_checkpoint",
        },
        optional={
            "decision_owner", "non_goals", "known_high_risk_choices", "likely_affected_files",
            "required_evidence", "budget_or_cost_constraints",
        },
        enums={
            "user_checkpoint_required": frozenset({"yes", "no", "unknown"}),
            "edit_permission_before_checkpoint": frozenset({"yes", "no"}),
        },
    ),
    "dispatch-plan": _schema(
        required={
            "run_id", "dispatches", "dispatch_groups", "budget_tier", "agent_count_backstop",
            "max_concurrent_subagents", "max_subagent_depth", "fallback_if_subagents_unavailable",
        },
        # stop_rule (R19) is added to the shipped template and validated when present on a real plan.
        optional={"stop_rule", "_doc"},
        enums={"budget_tier": BUDGET_TIER},
        int_bounds={
            "max_concurrent_subagents": (1, 12), "max_subagent_depth": (1, 1),
            "agent_count_backstop": (1, 64),
        },
    ),
    # Authoritative loop-termination object the Orchestrator evaluates (R19). dedup_against pins
    # loop-until-dry to deduping against everything SEEN, not only what was confirmed.
    "stop-rule": _schema(
        required={"max_rounds", "loop_until_dry_K", "dedup_against"},
        optional={"token_budget_target", "agent_count_backstop"},
        enums={"dedup_against": frozenset({"all_seen"})},
        int_bounds={"max_rounds": (1, 64), "loop_until_dry_K": (1, 10)},
    ),
    # One member of dispatch_groups[]. Validated per-element at run time (not template time) by
    # validate_dispatch_groups() so the dispatch_kind barrier/pipeline enum is enforced on real plans.
    # Per-round fan-out (R18) is optional and value-checked by validate_dispatch_plan() when present.
    "dispatch-group": _schema(
        required={"group_id", "round", "dispatch_kind", "members", "next_group", "barrier_reason"},
        optional={"fanout_min", "fanout_max", "fanout_chosen", "fanout_justification"},
        enums={"dispatch_kind": DISPATCH_KIND},
    ),
    # ---- Round A: worker findings (no action verbs; Pillar 1) ----
    "finding": _schema(
        required={
            "finding_id", "role", "claim", "claim_type", "provisional_severity",
            "affected_decision", "evidence", "uncertainty", "agent_id",
        },
        # depth/contestability (R26) are optional worker self-assessments; when present they let the
        # Orchestrator route verification proportionately and let the validator flag over-verification
        # of binary facts and discovery runs that produced zero deep findings.
        optional={"counterevidence", "validity_verdict", "depth", "contestability"},
        enums={
            "claim_type": CLAIM_TYPE,
            "provisional_severity": SEVERITY,
            "validity_verdict": frozenset({"sufficient", "insufficient", "fatal_flaw"}),
            "depth": DEPTH,
            "contestability": CONTESTABILITY,
        },
    ),
    # Relevance Arbiter output: scored data, never an action verb (R1).
    "relevance-score": _schema(
        required={
            "item_id", "decision_impact", "uncertainty_reduced", "action_unlocked",
            "cost_risk", "redundancy",
        },
        optional={"agent_id", "recommendation", "note"},
        enums={"decision_impact": frozenset({"positive", "negative", "null"})},
    ),
    # Loop Guard output: a stagnation SIGNAL as data, never CONTINUE/ABANDON/... (R1).
    "stagnation-signal": _schema(
        required={
            "round", "information_gain", "repeated_signatures", "scope_drift",
            "suggested_new_evidence_target",
        },
        optional={"agent_id", "consecutive_dry_rounds", "note"},
        enums={"scope_drift": SCOPE_DRIFT},
    ),
    # ---- Round B ----
    "critique": _schema(
        required={
            "critique_id", "target_finding_id", "attack_type", "critique_claim", "evidence",
            "minimal_test_to_resolve", "verdict", "agent_id", "refute_disposition", "lens",
        },
        optional={"expected_decision_impact"},
        enums={"attack_type": ATTACK_TYPE, "verdict": VERDICT, "refute_disposition": REFUTE_DISPOSITION},
    ),
    # ---- Round C ----
    "evidence-decision": _schema(
        required={
            "claim_or_critique_id", "support_status", "evidence_quality", "accepted_evidence_ids",
            "downgraded_severity", "reason", "agent_id",
        },
        optional={"required_followup"},
        enums={
            "support_status": SUPPORT_STATUS,
            "evidence_quality": EVIDENCE_QUALITY,
            "downgraded_severity": SEVERITY,
        },
    ),
    "evidence-decision-bundle": _schema(
        required={"decisions"},
        item_required={"decisions": "evidence-decision"},
    ),
    "evidence-packet": _schema(
        required={
            "packet_id", "source_claim_ids", "accepted_evidence_ids", "claim",
            "decision_relevance", "support_status", "evidence_quality", "excluded_unsupported_text",
        },
        optional={"claim_type", "counterevidence", "hard_gate_failures"},
        enums={
            "support_status": frozenset({"accepted", "partially_supported"}),
            "evidence_quality": frozenset({"high", "medium", "low"}),
            "claim_type": CLAIM_TYPE,
        },
    ),
    # ---- Round D ----
    "judge-score": _schema(
        required={
            "packet_id", "judge_id", "blocker_score", "warning_score", "false_positive_risk",
            "decision_relevance", "evidence_quality", "technical_validity",
            "methodological_validity", "reproducibility", "final_class", "hard_gate_failures",
            "rationale", "agent_id",
        },
        optional={"lens"},
        enums={"final_class": DECISION_CLASSES},
        int_bounds={
            "blocker_score": (0, 20), "warning_score": (0, 20), "false_positive_risk": (0, 20),
            "decision_relevance": (0, 20), "evidence_quality": (0, 20), "technical_validity": (0, 20),
            "methodological_validity": (0, 20), "reproducibility": (0, 20),
        },
    ),
    # ---- Round E ----
    "orchestrator-decision": _schema(
        required={
            "issue_id", "title", "decision_class", "action", "evidence_ids", "affected_files",
            "recommended_change", "alternatives", "user_decision_needed", "edit_after_approval",
        },
        enums={"decision_class": DECISION_CLASSES, "action": ACTION_TOKENS},
    ),
    "decision-ledger": _schema(
        required={"decisions"},
        item_required={"decisions": "orchestrator-decision"},
    ),
    # ---- Round F ----
    "user-checkpoint": _schema(
        required={"checkpoints", "stop_round", "edit_permission_before_approval"},
    ),
    # ---- Round E.5 (R16) ----
    "completeness-critique": _schema(
        required={
            "gap_id", "gap_type", "severity", "suggested_action", "produced_reviewed_findings",
            "unresolved_must_close",
        },
        optional={"agent_id"},
        enums={
            "gap_type": frozenset({"lens_not_run", "claim_unverified", "source_unread", "hypothesis_untested"}),
            "severity": frozenset({"must_close", "should_close", "acceptable"}),
        },
    ),
    # ---- Loop Guard / Orchestrator-owned snapshots ----
    "progress-snapshot": _schema(
        required={
            "round", "accepted_new_evidence_count", "decision_readiness_delta",
            "repeated_task_signatures", "scope_drift",
        },
        # loop_guard_action is Orchestrator-owned (re-homed from the worker, R1); optional here.
        optional={
            "resolved_critical_contradictions", "unresolved_high_impact_contradictions",
            "new_primary_sources", "new_reproducible_artifacts", "repair_count_by_artifact",
            "cost_or_budget_delta", "loop_guard_action", "specific_next_evidence_target",
            "seen_claim_count", "consecutive_dry_rounds",
        },
        enums={"scope_drift": SCOPE_DRIFT, "loop_guard_action": LOOP_GUARD_ACTION},
    ),
    "round-summary": _schema(
        required={
            "run_id", "round", "roles_used", "artifacts_created", "decision_classes", "coverage_log",
        },
        # loop_guard_action no longer a required worker key (R1); coverage_log required (R21).
        optional={
            "accepted_evidence_count", "downgraded_claim_count", "loop_guard_action", "next_round",
            "stop_reason",
        },
        enums={"loop_guard_action": LOOP_GUARD_ACTION},
    ),
    # ---- Round G / planning ----
    "experiment-card": _schema(
        required={
            "experiment_id", "version", "decision_link", "research_question", "primary_hypothesis",
            "null_hypothesis", "minimal_discriminating_test", "primary_metric",
            "interpretation_table", "spec_hash",
        },
    ),
    "final-report": _schema(
        required={
            "run_id", "mode", "summary_zh", "decision_ledger", "accepted_evidence",
            "user_checkpoints", "protected_files_not_edited", "next_highest_value_action",
        },
        optional={
            "task_charter", "downgraded_or_rejected_claims", "validation", "residual_risks",
        },
    ),
    # ---- Per-subagent debug record (retained for later debugging / upgrades) ----
    # Every dispatched subagent persists agents/<agent_id>.json so a run can be replayed, audited, or
    # used to tune the skill. The full raw output lives in raw_output (or output_artifact_path).
    "subagent-record": _schema(
        required={"agent_id", "role", "round", "status", "output_artifact_path"},
        optional={
            "dispatch_kind", "model", "started_at", "ended_at", "prompt_summary", "raw_output",
            "tokens", "error", "schema_validated", "redispatch_count",
        },
        enums={
            "status": frozenset({"completed", "blocked", "failed", "needs_review"}),
            "dispatch_kind": DISPATCH_KIND,
        },
    ),
    # ---- Common Envelope (mixin; prose-only contract, no standalone producer) ----
    "common-envelope": _schema(
        required={"run_id", "task_id", "artifact_id", "agent_role", "status", "summary"},
        optional={
            "evidence_ids", "artifact_paths", "uncertainties", "risks", "recommended_next_actions",
            "stop_signal",
        },
        enums={"status": frozenset({"completed", "blocked", "failed", "needs_review"})},
    ),
}


# Template file name -> schema name. validate_templates() iterates this so the templates and the
# registry can never disagree.
TEMPLATE_SCHEMA_MAP: dict[str, str] = {
    "task-charter.yaml": "task-charter",
    "dispatch-plan.yaml": "dispatch-plan",
    "finding.yaml": "finding",
    "critique.yaml": "critique",
    "evidence-decision.yaml": "evidence-decision",
    "evidence-packet.yaml": "evidence-packet",
    "judge-score.yaml": "judge-score",
    "decision-ledger.yaml": "decision-ledger",
    "experiment-card.yaml": "experiment-card",
    "final-report.yaml": "final-report",
    "progress-snapshot.yaml": "progress-snapshot",
    "user-checkpoint.yaml": "user-checkpoint",
    "round-summary.yaml": "round-summary",
}


def _is_placeholder(value: Any) -> bool:
    """Empty-string/zero/empty-list placeholders in blank templates are not enum violations."""
    return value in ("", 0, 0.0, None, [], {})


def validate_obj(
    name: str,
    data: Any,
    *,
    skip_empty: bool = False,
    allow_extra: bool = True,
    path: str = "",
) -> list[str]:
    """Validate one object against a registered schema. Returns a list of error strings.

    skip_empty=True tolerates blank-template placeholders (used for template checks).
    allow_extra=False rejects unknown top-level keys (used for strict --artifact mode).
    """
    errors: list[str] = []
    prefix = f"{path}: " if path else ""
    if name not in SCHEMAS:
        return [f"{prefix}unknown schema '{name}'"]
    schema = SCHEMAS[name]
    if not isinstance(data, dict):
        return [f"{prefix}{name} must be a mapping"]

    missing = sorted(schema["required"] - set(data))
    if missing:
        errors.append(f"{prefix}{name}: missing required keys {missing}")

    if not allow_extra:
        known = schema["required"] | schema["optional"]
        extra = sorted(set(data) - known)
        if extra:
            errors.append(f"{prefix}{name}: unexpected keys {extra}")

    for field, allowed in schema["enums"].items():
        if field in data:
            value = data[field]
            if skip_empty and _is_placeholder(value):
                continue
            normalized = CLASS_MAP.get(value, value) if isinstance(value, str) else value
            if normalized not in allowed:
                errors.append(f"{prefix}{name}.{field}={value!r} not in {sorted(allowed)}")

    for field, (lo, hi) in schema["int_bounds"].items():
        if field in data:
            value = data[field]
            if skip_empty and _is_placeholder(value) and value != 0:
                continue
            if isinstance(value, bool) or not isinstance(value, int):
                errors.append(f"{prefix}{name}.{field}={value!r} must be an int")
            elif not (lo <= value <= hi):
                errors.append(f"{prefix}{name}.{field}={value} out of bounds [{lo},{hi}]")

    for field, item_schema in schema["item_required"].items():
        items = data.get(field, [])
        if not isinstance(items, list):
            errors.append(f"{prefix}{name}.{field} must be a list")
            continue
        for idx, item in enumerate(items):
            errors.extend(
                validate_obj(
                    item_schema, item, skip_empty=skip_empty, allow_extra=allow_extra,
                    path=f"{prefix}{name}.{field}[{idx}]".rstrip(),
                )
            )
    return errors


def assert_conforms(name: str, obj: Any) -> None:
    """Raise SystemExit if obj does not conform. Used by the generator so fixture drift fails loud."""
    errors = validate_obj(name, obj, skip_empty=False, allow_extra=True)
    if errors:
        raise SystemExit("schema violation:\n  " + "\n  ".join(errors))
