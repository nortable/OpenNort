#!/usr/bin/env python3
"""Validate OpenNort's Codex extension-package compatibility surface.

This is intentionally small and stdlib-only. It checks the package-level contract that is outside the
normal run-artifact validator: plugin manifest, skill frontmatter, optional Codex metadata, integration
test documentation, and schema-fit fixture metadata. It does not prove semantic adapter behavior; that
belongs in per-integration schema-fit runners.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


SCRIPT = Path(__file__).resolve()
SKILL_DIR = SCRIPT.parents[1]
REPO_ROOT = SCRIPT.parents[3]


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)


def load_json(path: Path, failures: list[str]) -> Any:
    if not path.exists():
        fail(f"missing required file: {path.relative_to(REPO_ROOT)}", failures)
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{path.relative_to(REPO_ROOT)} is not valid JSON: {exc}", failures)
        return None


def parse_frontmatter(path: Path, failures: list[str]) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        fail(f"{path.relative_to(REPO_ROOT)} does not start with YAML frontmatter", failures)
        return {}
    try:
        _, block, _ = text.split("---\n", 2)
    except ValueError:
        fail(f"{path.relative_to(REPO_ROOT)} has unterminated frontmatter", failures)
        return {}
    out: dict[str, str] = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        out[key.strip()] = value.strip().strip('"')
    return out


def check_plugin(failures: list[str]) -> None:
    manifest_path = REPO_ROOT / ".codex-plugin" / "plugin.json"
    manifest = load_json(manifest_path, failures)
    if not isinstance(manifest, dict):
        return

    if manifest.get("name") != "opennort":
        fail(".codex-plugin/plugin.json name must be 'opennort'", failures)
    version = manifest.get("version")
    if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", version):
        fail(".codex-plugin/plugin.json version must be semver-like", failures)
    if manifest.get("skills") != "./skills/":
        fail(".codex-plugin/plugin.json must point skills to './skills/'", failures)
    if not (REPO_ROOT / "skills" / "research-codex-workflow" / "SKILL.md").exists():
        fail("plugin skills path does not contain research-codex-workflow/SKILL.md", failures)

    interface = manifest.get("interface")
    if not isinstance(interface, dict):
        fail(".codex-plugin/plugin.json missing interface object", failures)
        return
    for key in ("displayName", "shortDescription", "longDescription", "developerName", "category"):
        if not interface.get(key):
            fail(f".codex-plugin/plugin.json interface.{key} is required", failures)
    prompts = interface.get("defaultPrompt", [])
    if not isinstance(prompts, list) or not (1 <= len(prompts) <= 3):
        fail(".codex-plugin/plugin.json interface.defaultPrompt must contain 1-3 prompts", failures)
    for prompt in prompts:
        if not isinstance(prompt, str) or len(prompt) > 128:
            fail("each defaultPrompt entry must be a string no longer than 128 chars", failures)


def check_skill(failures: list[str]) -> None:
    skill_path = SKILL_DIR / "SKILL.md"
    fm = parse_frontmatter(skill_path, failures)
    if fm.get("name") != "research-codex-workflow":
        fail("SKILL.md frontmatter name must remain 'research-codex-workflow'", failures)
    description = fm.get("description", "")
    required_terms = ["research", "workflow", "Run 1", "Run 2"]
    for term in required_terms:
        if term not in description:
            fail(f"SKILL.md description should front-load trigger term {term!r}", failures)

    metadata = SKILL_DIR / "agents" / "openai.yaml"
    if not metadata.exists():
        fail("missing agents/openai.yaml for Codex extension metadata", failures)
    else:
        text = metadata.read_text(encoding="utf-8")
        for required in ("display_name:", "short_description:", "default_prompt:", "allow_implicit_invocation: true"):
            if required not in text:
                fail(f"agents/openai.yaml missing {required}", failures)
        if "$research-codex-workflow" not in text:
            fail("agents/openai.yaml default_prompt should explicitly mention $research-codex-workflow", failures)


def check_docs_and_fixtures(failures: list[str]) -> None:
    doc = REPO_ROOT / "docs" / "codex-extension-compatibility-and-integration-tests.md"
    if not doc.exists():
        fail("missing docs/codex-extension-compatibility-and-integration-tests.md", failures)
        return
    text = doc.read_text(encoding="utf-8")
    for heading in (
        "Codex Extension Compatibility",
        "Enablement Checks",
        "Integration Test Plan",
        "Spec Kit Mapping",
        "GitHub PR Bridge",
        "Skill Marketplace Audit",
        "Runtime Adapter Boundary",
        "Release Gates",
    ):
        if heading not in text:
            fail(f"integration test doc missing section: {heading}", failures)

    fixture_dir = REPO_ROOT / "examples" / "integration-fit"
    expected = [
        "spec-kit-feature.json",
        "github-pr-diff.json",
        "marketplace-skill-listing.json",
        "runtime-adapter-boundary.json",
    ]
    for name in expected:
        data = load_json(fixture_dir / name, failures)
        if not isinstance(data, dict):
            continue
        for key in (
            "fixture_id",
            "external_system",
            "input_kind",
            "source_version",
            "validation_command",
            "expected_artifacts",
            "expected_open_nort_mapping",
            "pass_criteria",
            "fail_criteria",
            "negative_controls",
        ):
            if key not in data:
                fail(f"examples/integration-fit/{name} missing {key}", failures)
        for list_key in ("expected_artifacts", "pass_criteria", "fail_criteria", "negative_controls"):
            value = data.get(list_key)
            if not isinstance(value, list) or not value:
                fail(f"examples/integration-fit/{name} {list_key} must be a non-empty list", failures)
        if not isinstance(data.get("expected_open_nort_mapping"), dict):
            fail(f"examples/integration-fit/{name} expected_open_nort_mapping must be an object", failures)


def main() -> int:
    failures: list[str] = []
    check_plugin(failures)
    check_skill(failures)
    check_docs_and_fixtures(failures)

    if failures:
        for item in failures:
            print(f"FAIL: {item}", file=sys.stderr)
        return 1

    print("OK: OpenNort Codex extension package surface and fixture metadata validate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
