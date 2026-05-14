"""Tests for plan entity type (files + tools)."""

import os
import pytest

from docket_md.config import init_project, register_project
from docket_md.files import (
    list_plans,
    next_plan_id,
    plan_path,
    find_plan_file,
    read_markdown,
    write_markdown,
)
from docket_md._logic.plan import (
    plan_create,
    plan_list,
    plan_view,
    plan_update,
    plan_verify,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup_project(tmp_path) -> tuple[str, str]:
    """Init + register a temp project, return (project_root, project_id)."""
    project_root = str(tmp_path)
    config = init_project(project_root)
    register_project(project_root)
    return project_root, config.id


# ---------------------------------------------------------------------------
# TestPlanFiles
# ---------------------------------------------------------------------------

class TestPlanFiles:
    def test_next_plan_id_empty(self, tmp_path):
        project_root, _ = _setup_project(tmp_path)
        assert next_plan_id(project_root) == "PLAN-0001"

    def test_next_plan_id_sequential(self, tmp_path):
        project_root, _ = _setup_project(tmp_path)
        # Write two plans manually
        fp1 = plan_path(project_root, "PLAN-0001", "First plan")
        write_markdown(fp1, {"id": "PLAN-0001", "title": "First plan", "status": "draft", "created": "2026-03-25"}, "")
        fp2 = plan_path(project_root, "PLAN-0002", "Second plan")
        write_markdown(fp2, {"id": "PLAN-0002", "title": "Second plan", "status": "draft", "created": "2026-03-25"}, "")
        assert next_plan_id(project_root) == "PLAN-0003"

    def test_plan_roundtrip(self, tmp_path):
        project_root, _ = _setup_project(tmp_path)
        fm = {"id": "PLAN-0001", "title": "Test Plan", "status": "draft", "created": "2026-03-25"}
        content = "This is the plan body."
        fp = plan_path(project_root, "PLAN-0001", "Test Plan")
        write_markdown(fp, fm, content)
        parsed = read_markdown(fp)
        assert parsed.frontmatter["id"] == "PLAN-0001"
        assert parsed.frontmatter["title"] == "Test Plan"
        assert parsed.content == content

    def test_find_plan_file(self, tmp_path):
        project_root, _ = _setup_project(tmp_path)
        fp = plan_path(project_root, "PLAN-0001", "My Plan")
        write_markdown(fp, {"id": "PLAN-0001", "title": "My Plan", "status": "draft", "created": "2026-03-25"}, "")
        found = find_plan_file(project_root, "PLAN-0001")
        assert found is not None
        assert "PLAN-0001" in found

    def test_find_plan_file_missing(self, tmp_path):
        project_root, _ = _setup_project(tmp_path)
        assert find_plan_file(project_root, "PLAN-9999") is None

    def test_list_plans(self, tmp_path):
        project_root, _ = _setup_project(tmp_path)
        # Empty at start
        assert list_plans(project_root) == []
        # Add two plans
        fp1 = plan_path(project_root, "PLAN-0001", "Alpha")
        write_markdown(fp1, {"id": "PLAN-0001", "title": "Alpha", "status": "draft", "created": "2026-03-25"}, "")
        fp2 = plan_path(project_root, "PLAN-0002", "Beta")
        write_markdown(fp2, {"id": "PLAN-0002", "title": "Beta", "status": "approved", "created": "2026-03-25"}, "")
        plans = list_plans(project_root)
        assert len(plans) == 2
        assert plans[0].frontmatter["id"] == "PLAN-0001"
        assert plans[1].frontmatter["id"] == "PLAN-0002"


# ---------------------------------------------------------------------------
# TestPlanTools
# ---------------------------------------------------------------------------

class TestPlanTools:
    def test_plan_create(self, tmp_path):
        _, pid = _setup_project(tmp_path)
        result = plan_create(pid, "Launch Strategy", content="We will launch in Q2.", tags=["strategy"])
        assert "PLAN-0001" in result
        assert "Launch Strategy" in result
        # Verify file exists
        plans = list_plans(str(tmp_path))
        assert len(plans) == 1
        assert plans[0].frontmatter["status"] == "draft"
        assert plans[0].frontmatter["tags"] == ["strategy"]

    def test_plan_list(self, tmp_path):
        _, pid = _setup_project(tmp_path)
        plan_create(pid, "Plan A")
        plan_create(pid, "Plan B")
        result = plan_list(pid)
        assert "PLAN-0001" in result
        assert "PLAN-0002" in result
        # Filter by status
        result_draft = plan_list(pid, status="draft")
        assert "PLAN-0001" in result_draft
        result_approved = plan_list(pid, status="approved")
        assert "No plans found" in result_approved

    def test_plan_view(self, tmp_path):
        _, pid = _setup_project(tmp_path)
        plan_create(pid, "Detailed Plan", content="Full details here.", verification=["Check A", "Check B"])
        result = plan_view(pid, "PLAN-0001")
        assert "Detailed Plan" in result
        assert "Full details here." in result
        assert "Check A" in result
        assert "Check B" in result

    def test_plan_update_status(self, tmp_path):
        _, pid = _setup_project(tmp_path)
        plan_create(pid, "Approval Test")
        # Update to approved — should auto-set approved date
        plan_update(pid, "PLAN-0001", status="approved")
        plans = list_plans(str(tmp_path))
        fm = plans[0].frontmatter
        assert fm["status"] == "approved"
        assert fm.get("approved") is not None
        assert fm.get("updated") is not None

    def test_plan_verify(self, tmp_path):
        _, pid = _setup_project(tmp_path)
        plan_create(pid, "Verify Test", verification=["Step 1", "Step 2", "Step 3"])
        result = plan_verify(pid, "PLAN-0001")
        assert "Step 1" in result
        assert "Step 2" in result
        assert "Step 3" in result
        # No verification
        plan_create(pid, "No Verification")
        result_empty = plan_verify(pid, "PLAN-0002")
        assert "no verification criteria" in result_empty
