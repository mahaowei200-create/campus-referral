from pathlib import Path

import pytest

from app.services.skills import MindBridgeSkillRegistry, SkillLoadError


def write_skill(root: Path, name: str, text: str) -> None:
    path = root / name / "SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text(text, encoding="utf-8")


def test_skill_registry_loads_valid_skill(tmp_path: Path):
    write_skill(
        tmp_path,
        "demo_skill",
        (
            "---\n"
            "name: demo_skill\n"
            "description: Use for a clear and sufficiently described demo scenario.\n"
            "---\n\n"
            "# Demo\n\n"
            "## Workflow\n\n"
            "- Do one thing.\n"
        ),
    )

    skill = MindBridgeSkillRegistry(tmp_path).get_required("demo_skill")

    assert skill.name == "demo_skill"
    assert skill.validation_issues() == []


def test_skill_status_reports_warnings(tmp_path: Path):
    write_skill(
        tmp_path,
        "demo_skill",
        (
            "---\n"
            "name: demo_skill\n"
            "description: short\n"
            "---\n\n"
            "# Demo\n"
        ),
    )

    status = MindBridgeSkillRegistry(tmp_path).status_items()[0]

    assert status["status"] == "WARN"
    assert status["issues"]


def test_skill_requires_frontmatter(tmp_path: Path):
    write_skill(tmp_path, "bad", "# Missing metadata")

    with pytest.raises(SkillLoadError):
        MindBridgeSkillRegistry(tmp_path).get_required("bad")