#!/usr/bin/env python3
"""Generate a deterministic Round 0-F adversarial workflow run from the synthetic fixture."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

# Share the single canonical registry with the validator so the generator can never emit an artifact
# the validator would reject (the generate+validate-share-one-schema rule).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from schemas import SCHEMAS, ROUND_DIRS, assert_conforms  # noqa: E402


SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = SKILL_ROOT / "examples" / "synthetic-adversarial-case.yaml"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_artifact(path: Path, data: Any, schema_name: str) -> None:
    """Self-validate against the canonical schema before writing, so fixture drift fails loud."""
    if schema_name not in SCHEMAS:
        raise SystemExit(f"unknown schema '{schema_name}' for {path}")
    assert_conforms(schema_name, data)
    write_json(path, data)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def finding_artifact(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "finding_id": raw["finding_id"],
        "agent_id": "A-SCOUT-1",
        "role": "Synthetic Scout",
        "claim": raw["claim"],
        "claim_type": "observation",
        "provisional_severity": "blocker" if "BLOCKER" in raw["finding_id"] else "warning",
        "affected_decision": raw.get("decision_consequence", ""),
        "evidence": raw.get("evidence", []) if raw.get("evidence_present") else [],
        "counterevidence": [],
        "uncertainty": "synthetic fixture",
        "validity_verdict": "sufficient" if raw.get("evidence_present") else "insufficient",
        # R26: worker self-assessment that drives proportionate verification routing. The evidenced
        # blocker is a deep, more-contestable claim (gets the adversarial route); the rest are surface,
        # low-contestability facts that need only a light confirmation pass.
        "depth": "deep" if raw.get("evidence_present") else "surface",
        "contestability": "medium" if raw.get("evidence_present") else "low",
    }


def evidence_decision_for_finding(raw: dict[str, Any]) -> dict[str, Any]:
    if raw.get("seeded_case") == "true_but_decision_irrelevant":
        return {
            "claim_or_critique_id": raw["finding_id"],
            "agent_id": "C-AUDITOR-1",
            "support_status": "accepted",
            "evidence_quality": "medium",
            "accepted_evidence_ids": [f"E-{raw['finding_id']}"],
            "required_followup": "none",
            "downgraded_severity": "info",
            "reason": "True but no decision consequence; park instead of spending research budget.",
        }
    if not raw.get("evidence_present"):
        return {
            "claim_or_critique_id": raw["finding_id"],
            "agent_id": "C-AUDITOR-1",
            "support_status": raw.get("expected_support_status", "needs_evidence"),
            "evidence_quality": "none",
            "accepted_evidence_ids": [],
            "required_followup": "attach file path, command, statistic, source, or artifact",
            "downgraded_severity": "unsupported",
            "reason": "Plausible prose is not evidence.",
        }
    return {
        "claim_or_critique_id": raw["finding_id"],
        "agent_id": "C-AUDITOR-1",
        "support_status": raw.get("expected_support_status", "accepted"),
        "evidence_quality": "high",
        "accepted_evidence_ids": [f"E-{raw['finding_id']}"],
        "required_followup": "Round F user decision before contested edits",
        "downgraded_severity": "blocker",
        "reason": "Claim has inspectable file/command evidence and affects the protocol decision.",
    }


def evidence_decision_for_critique(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "claim_or_critique_id": raw["critique_id"],
        "agent_id": "C-AUDITOR-1",
        "support_status": raw.get("expected_support_status", "unsupported"),
        "evidence_quality": "none" if not raw.get("evidence_present") else "medium",
        "accepted_evidence_ids": [],
        "required_followup": "provide evidence or a resolvable test",
        "downgraded_severity": "unsupported",
        "reason": "Rhetorical attack has no inspectable evidence.",
    }


def decision_for(raw: dict[str, Any]) -> dict[str, Any]:
    evidence = raw.get("evidence", []) if raw.get("evidence_present") else []
    affected_files = sorted(
        {
            item["file_path"]
            for item in evidence
            if isinstance(item, dict) and item.get("file_path")
        }
    )
    return {
        "issue_id": f"I-{raw['finding_id']}",
        "title": raw["claim"],
        "decision_class": raw.get("expected_decision_class", "rejected_or_unsupported"),
        "action": raw.get("expected_action", "HUMAN_REVIEW"),
        "evidence_ids": [f"E-{raw['finding_id']}"] if evidence else [],
        "affected_files": affected_files,
        "recommended_change": "act only after evidence audit and user checkpoint",
        "alternatives": [],
        "user_decision_needed": raw.get("expected_decision_class") == "needs_user_decision",
        "edit_after_approval": raw.get("expected_decision_class") in {"accepted_blocker", "needs_user_decision"},
    }


def run_fixture(fixture_path: Path, out_root: Path, run_id: str | None = None) -> Path:
    fixture = load_json(fixture_path)
    rid = run_id or fixture["run_id"]
    root = out_root / rid
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    for rel in ROUND_DIRS:
        (root / rel).mkdir(parents=True, exist_ok=True)

    charter = {
        "run_id": rid,
        "objective": "Validate the full adversarial workflow on a deterministic synthetic case.",
        "decision_to_support": "Can the Codex skill separate evidence-backed blockers from unsupported claims and user-owned choices?",
        "decision_owner": "user",
        "scope": "offline fixture only",
        "non_goals": ["paid APIs", "project file edits", "standalone CLI product"],
        "success_criteria": list(fixture["expected_summary"].keys()),
        "known_high_risk_choices": ["contested protocol choice", "parallel writer collision"],
        "likely_affected_files": [],
        "required_evidence": ["file path", "command", "statistic", "artifact"],
        "budget_or_cost_constraints": "offline only",
        "user_checkpoint_required": "yes",
        "edit_permission_before_checkpoint": "no",
    }
    write_artifact(root / "00-charter.yaml", charter, "task-charter")

    dispatch = {
        "run_id": rid,
        "dispatches": [
            {"role": "Synthetic Scout", "objective": "emit seeded findings", "scope": "fixture", "non_goals": [], "inputs": [str(fixture_path)], "required_evidence": ["fixture evidence"], "required_output_schema": "Finding", "permissions": "read-only", "files_owned": [], "files_forbidden": ["*"], "validation": "validate_artifacts.py", "stop_conditions": ["Round F"]},
            {"role": "Falsifier", "objective": "attack anonymized findings", "scope": "fixture", "non_goals": [], "inputs": ["round-a-findings"], "required_evidence": ["evidence or minimal test"], "required_output_schema": "Critique", "permissions": "read-only", "files_owned": [], "files_forbidden": ["*"], "validation": "Evidence Tribunal", "stop_conditions": ["unsupported critique downgraded"]},
            {"role": "Evidence Auditor", "objective": "accept or downgrade findings and critiques", "scope": "fixture", "non_goals": [], "inputs": ["round-a-findings", "round-b-critiques"], "required_evidence": ["inspectable evidence"], "required_output_schema": "EvidenceDecision", "permissions": "read-only", "files_owned": [], "files_forbidden": ["*"], "validation": "hard gate", "stop_conditions": ["unsupported claims excluded from judge packets"]},
            {"role": "Judge", "objective": "score accepted evidence packets", "scope": "fixture", "non_goals": ["invent evidence"], "inputs": ["evidence-packets"], "required_evidence": ["accepted evidence only"], "required_output_schema": "JudgeScore", "permissions": "read-only", "files_owned": [], "files_forbidden": ["*"], "validation": "decision ledger", "stop_conditions": ["Round E"]},
        ],
        "dispatch_groups": [
            {"group_id": "A", "round": "A", "dispatch_kind": "barrier", "members": ["Synthetic Scout"], "next_group": "B", "barrier_reason": "collect all first-pass findings before anonymization and dedup"},
            {"group_id": "B", "round": "B", "dispatch_kind": "pipeline", "members": ["Falsifier"], "next_group": "C", "barrier_reason": ""},
            {"group_id": "C", "round": "C", "dispatch_kind": "pipeline", "members": ["Evidence Auditor"], "next_group": "D", "barrier_reason": ""},
            {"group_id": "D", "round": "D", "dispatch_kind": "barrier", "members": ["Judge"], "next_group": "E", "barrier_reason": "panel synthesis needs every judge score together"},
        ],
        "_doc": "dispatch_kind: barrier = wait_agent on ALL members before the next group; pipeline = stream each finding to the next stage as it lands (A->B->C). Orchestrator owns group sequencing.",
        "budget_tier": "standard",
        "agent_count_backstop": 18,
        "stop_rule": {"max_rounds": 8, "loop_until_dry_K": 2, "token_budget_target": None, "dedup_against": "all_seen"},
        "max_concurrent_subagents": 12,
        "max_subagent_depth": 1,
        "fallback_if_subagents_unavailable": "sequential artifact-producing passes",
    }
    write_artifact(root / "01-dispatch-plan.yaml", dispatch, "dispatch-plan")

    findings = [finding_artifact(item) for item in fixture["round_a_findings"]]
    for item in findings:
        write_artifact(root / "round-a-findings" / f"{item['finding_id']}.yaml", item, "finding")

    critiques = []
    for raw in fixture["round_b_critiques"]:
        critique = {
            "critique_id": raw["critique_id"],
            "agent_id": "B-FALSIFIER-1",
            "target_finding_id": raw["target_finding_id"],
            "attack_type": "irrelevant",
            "critique_claim": raw["critique_claim"],
            "evidence": [],
            "minimal_test_to_resolve": "provide reviewer decision evidence",
            "expected_decision_impact": "none without evidence",
            "verdict": raw.get("expected_verdict", "unsupported_attack"),
            "refute_disposition": "not_refuted",
            "lens": "decision-impact",
        }
        critiques.append(critique)
        write_artifact(root / "round-b-critiques" / f"{critique['critique_id']}.yaml", critique, "critique")

    evidence_decisions = [evidence_decision_for_finding(item) for item in fixture["round_a_findings"]]
    evidence_decisions.extend(evidence_decision_for_critique(item) for item in fixture["round_b_critiques"])
    write_artifact(root / "round-c-evidence-decisions.yaml", {"decisions": evidence_decisions}, "evidence-decision-bundle")

    accepted = [
        item for item in fixture["round_a_findings"]
        if item.get("evidence_present") and item.get("expected_support_status", "accepted") == "accepted"
        and item.get("expected_decision_class") in {"accepted_blocker", "accepted_non_blocking", "needs_user_decision"}
    ]
    packets = []
    packet_sources = []
    for raw in accepted:
        packet = {
            "packet_id": f"P-{raw['finding_id']}",
            "source_claim_ids": [raw["finding_id"]],
            "accepted_evidence_ids": [f"E-{raw['finding_id']}"],
            "claim": raw["claim"],
            "claim_type": "observation",
            "decision_relevance": raw.get("decision_consequence", ""),
            "counterevidence": [],
            "support_status": "accepted",
            "evidence_quality": "high",
            "hard_gate_failures": [],
            "excluded_unsupported_text": [c["critique_id"] for c in critiques if c["target_finding_id"] == raw["finding_id"]],
        }
        packets.append(packet)
        packet_sources.append((packet, raw))
        write_artifact(root / "evidence-packets" / f"{packet['packet_id']}.yaml", packet, "evidence-packet")

    for idx, (packet, raw) in enumerate(packet_sources, 1):
        score = {
            "packet_id": packet["packet_id"],
            "judge_id": f"J{idx}",
            "agent_id": f"D-JUDGE-{idx}",
            "blocker_score": 5,
            "warning_score": 1,
            "false_positive_risk": 1,
            "decision_relevance": 5,
            "evidence_quality": 5,
            "technical_validity": 5,
            "methodological_validity": 4,
            "reproducibility": 4,
            "final_class": raw.get("expected_decision_class", "accepted_non_blocking"),
            "hard_gate_failures": [],
            "rationale": "Accepted evidence supports a blocker and unsupported critique was excluded.",
        }
        write_artifact(root / "round-d-judge-scores" / f"{score['judge_id']}-{packet['packet_id']}.yaml", score, "judge-score")

    decisions = [decision_for(item) for item in fixture["round_a_findings"]]
    decisions.append({
        "issue_id": "I-ROUND-F-CHECKPOINT",
        "title": fixture["round_f_checkpoint"]["decision_required"],
        "decision_class": "needs_user_decision",
        "action": "HUMAN_REVIEW",
        "evidence_ids": ["E-F-VALID-BLOCKER-1"],
        "affected_files": [],
        "recommended_change": "Stop at Round F before contested edits.",
        "alternatives": ["choose protocol A", "choose protocol B"],
        "user_decision_needed": True,
        "edit_after_approval": True,
    })
    write_artifact(root / "round-e-decision-ledger.yaml", {"decisions": decisions}, "decision-ledger")

    checkpoint = {
        "checkpoints": [
            {
                "decision_id": "D1",
                "decision_required": fixture["round_f_checkpoint"]["decision_required"],
                "why_it_matters": "The workflow must not silently resolve project-owner protocol choices.",
                "recommended_option": "Require user approval before contested edits.",
                "alternatives": ["defer edits", "revise protocol", "archive unsupported claim"],
                "evidence_ids": ["E-F-VALID-BLOCKER-1"],
                "files_or_runs_affected": [],
                "consequence_of_no_decision": "Stop at Round F; no protected edits.",
            }
        ],
        "stop_round": "F",
        "edit_permission_before_approval": False,
    }
    write_artifact(root / "round-f-user-checkpoint.yaml", checkpoint, "user-checkpoint")
    write_text(
        root / "round-f-user-checkpoint.md",
        "# Round F User Checkpoint\n\n"
        f"- Decision: {checkpoint['checkpoints'][0]['decision_required']}\n"
        "- Recommendation: require user approval before contested edits.\n"
        "- Stop condition: do not edit protected research documents.\n",
    )

    snapshot = {
        "round": "E",
        "accepted_new_evidence_count": len(packets),
        "resolved_critical_contradictions": 1,
        "unresolved_high_impact_contradictions": 1,
        "decision_readiness_delta": 0.5,
        "new_primary_sources": 0,
        "new_reproducible_artifacts": 1,
        "repeated_task_signatures": fixture["loop_guard_fixture"]["repeated_task_signatures"],
        "repair_count_by_artifact": {},
        "cost_or_budget_delta": 0,
        "scope_drift": "low",
        "loop_guard_action": fixture["loop_guard_fixture"]["expected_loop_guard_action"],
        "specific_next_evidence_target": "user decision for contested protocol",
        "seen_claim_count": len(fixture["round_a_findings"]),
        "consecutive_dry_rounds": 1,
    }
    write_artifact(root / "progress-snapshots" / "round-e.yaml", snapshot, "progress-snapshot")

    accepted_blockers = sum(1 for d in decisions if d["decision_class"] == "accepted_blocker")
    rejected_or_unsupported = sum(1 for d in decisions if d["decision_class"] == "rejected_or_unsupported")
    needs_user_decision = sum(1 for d in decisions if d["decision_class"] == "needs_user_decision")

    final_report = {
        "run_id": rid,
        "mode": "full_adversarial",
        "summary_zh": "离线合成用例通过：无关结论被停车，缺证 blocker 被降级，有证据 blocker 被接受，争议选择停在 Round F。",
        "task_charter": charter,
        "decision_ledger": decisions,
        "accepted_evidence": packets,
        "downgraded_or_rejected_claims": [d for d in evidence_decisions if d["support_status"] in {"needs_evidence", "unsupported"}],
        "user_checkpoints": checkpoint["checkpoints"],
        "validation": ["offline synthetic fixture"],
        "protected_files_not_edited": True,
        "residual_risks": ["This is a synthetic fixture, not a live repository audit."],
        "next_highest_value_action": "Run a read-only forward test on a real research repository.",
    }
    write_artifact(root / "round-g-final-report.yaml", final_report, "final-report")
    write_text(
        root / "round-g-final-report.md",
        "# Round G Final Report\n\n"
        f"- Run: {rid}\n"
        "- Mode: full_adversarial\n"
        f"- Accepted blockers: {accepted_blockers}\n"
        f"- Rejected or unsupported: {rejected_or_unsupported}\n"
        f"- Needs user decision: {needs_user_decision}\n"
        "- Protected files edited: no\n"
        "- Next action: run a read-only forward test on a real research repository.\n",
    )

    # Per-subagent debug records (retained for debugging / later upgrades). One JSON file per agent_id.
    agent_records = [
        {"agent_id": "A-SCOUT-1", "role": "Synthetic Scout", "round": "A", "dispatch_kind": "barrier",
         "status": "completed", "output_artifact_path": "round-a-findings/",
         "schema_validated": True, "redispatch_count": 0},
        {"agent_id": "B-FALSIFIER-1", "role": "Falsifier", "round": "B", "dispatch_kind": "pipeline",
         "status": "completed", "output_artifact_path": "round-b-critiques/C-UNSUPPORTED-1.yaml",
         "schema_validated": True, "redispatch_count": 0},
        {"agent_id": "C-AUDITOR-1", "role": "Evidence Auditor", "round": "C", "dispatch_kind": "pipeline",
         "status": "completed", "output_artifact_path": "round-c-evidence-decisions.yaml",
         "schema_validated": True, "redispatch_count": 0},
        {"agent_id": "D-JUDGE-1", "role": "Judge", "round": "D", "dispatch_kind": "barrier",
         "status": "completed", "output_artifact_path": "round-d-judge-scores/",
         "schema_validated": True, "redispatch_count": 0},
    ]
    for record in agent_records:
        write_artifact(root / "agents" / f"{record['agent_id']}.json", record, "subagent-record")

    summary = {
        "run_id": rid,
        "run_root": str(root),
        "accepted_blockers": accepted_blockers,
        "rejected_or_unsupported": rejected_or_unsupported,
        "needs_user_decision": needs_user_decision,
        "loop_guard_action": snapshot["loop_guard_action"],
        "protected_files_not_edited": True,
    }
    write_json(root / "run-summary.yaml", summary)
    return root


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--out-root", type=Path, default=Path(".research-workflow") / "runs")
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args()

    root = run_fixture(args.fixture, args.out_root, args.run_id)
    print(json.dumps({"status": "ok", "run_root": str(root)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
