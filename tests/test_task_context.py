from src.agent.task_context import TaskContextBuilder, TaskContextConfig, _extract_query_terms


def test_extract_query_terms_filters_common_words():
    terms = _extract_query_terms("Fix bug when json_normalize meta argument fails in pandas")
    assert "json_normalize" in terms
    assert "pandas" in terms
    assert "bug" not in terms


def test_build_task_without_method_returns_original():
    builder = TaskContextBuilder(TaskContextConfig(method="none"))
    task = builder.build_task(
        instance={"instance_id": "demo"},
        image_name="unused",
        base_task="Fix the failing test.",
    )
    assert task == "Fix the failing test."


def test_build_task_with_skill_scaffold_and_hints():
    builder = TaskContextBuilder(
        TaskContextConfig(
            method="skill_abstraction",
            include_skill_scaffold=True,
            include_pruning_hints=True,
        )
    )
    task = builder.build_task(
        instance={"instance_id": "demo"},
        image_name="unused",
        base_task="Fix the failing test.",
    )
    assert "Structured workflow" in task
    assert "Efficiency hints" in task
    assert "Fix the failing test." in task


def test_build_task_with_skill_memory(tmp_path, monkeypatch):
    skill_file = tmp_path / "skills.md"
    skill_file.write_text("## Heuristic\nUse rg first.")
    builder = TaskContextBuilder(
        TaskContextConfig(
            method="skill_memory_md",
            include_skill_memory=True,
            skill_file=str(skill_file),
        )
    )
    task = builder.build_task(
        instance={"instance_id": "demo"},
        image_name="unused",
        base_task="Fix the failing test.",
    )
    assert "Transferable skill memory" in task
    assert "Use rg first." in task
