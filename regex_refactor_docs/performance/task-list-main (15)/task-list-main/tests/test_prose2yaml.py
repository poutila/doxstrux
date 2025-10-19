from tasklist.prose2yaml import build_task_list


def test_prose_conversion_generates_tasks_with_acceptance():
    markdown = """\
# Primary Refactor

```bash
make test
```
Verify that the suite passes.

## Stepwise Plan
1. Capture baseline
2. Apply migration
3. Verify results

### Additional Context
The service must remain online during changes.
"""

    data = build_task_list(markdown, title="Refactor", output_name="plan.yaml")

    phase = data["phases"]["phase_0"]
    tasks = phase["tasks"]

    assert len(tasks) >= 3
    for task in tasks:
        assert task["acceptance_criteria"], "Each task should have acceptance criteria"
        for criterion in task["acceptance_criteria"]:
            assert "{{" not in criterion

    first_task = tasks[0]
    assert any(step.startswith("Run: make test") for step in first_task["steps"])

    second_task = tasks[1]
    assert any("Capture baseline" in step for step in second_task["steps"])

    third_task = tasks[2]
    assert any("Review section" in step for step in third_task["steps"])
