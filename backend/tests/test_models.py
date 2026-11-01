import ast
import re
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from app.models.requests import CreatePlanRequest, ExpenseRequest


def test_shared_trimming(brief: dict[str, Any]) -> None:
    """Verify shared trimming."""
    brief.update(title=" Name ", city=" Pune ", preferences=" Music ")
    model = CreatePlanRequest.model_validate(brief)
    assert (model.title, model.city, model.preferences) == ("Name", "Pune", "Music")
    expense = ExpenseRequest(category=" venue ", amount=1, description=" Deposit ")
    assert expense.category == "venue" and expense.description == "Deposit"


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("title", "   "),
        ("title", "x" * 81),
        ("city", " "),
        ("city", "x" * 61),
        ("preferences", "x" * 301),
        ("currency", "JPY"),
        ("extra", "no"),
        ("guest_count", True),
    ],
)
def test_invalid_fields(brief: dict[str, Any], key: str, value: Any) -> None:
    """Verify invalid fields."""
    brief[key] = value
    with pytest.raises(ValidationError):
        CreatePlanRequest.model_validate(brief)


@pytest.mark.parametrize("amount", [float("inf"), float("nan"), 0, -1, 1.001])
def test_invalid_money(amount: float) -> None:
    """Verify invalid money."""
    with pytest.raises(ValidationError):
        ExpenseRequest(category="venue", amount=amount, description="Deposit")


def test_every_policy_constant_is_referenced() -> None:
    """Keep centralized policy free of unused aspirational constants."""
    config = Path("app/config.py")
    source = "\n".join(p.read_text() for p in Path("app").rglob("*.py") if p != config)
    names = []
    for node in ast.parse(config.read_text()).body:
        if isinstance(node, ast.Assign):
            names.extend(t.id for t in node.targets if isinstance(t, ast.Name))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.append(node.target.id)
    assert all(
        re.search(r"\b" + name + r"\b", source) for name in names if name.isupper()
    )


def test_source_structure_contract() -> None:
    """Guard module size, function size, documentation and type boundaries."""
    paths = list(Path("app").rglob("*.py")) + list(Path("tests").glob("*.py"))
    for path in paths:
        source = path.read_text()
        assert len(source.splitlines()) <= 250, path
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                assert node.end_lineno - node.lineno + 1 <= 35, (path, node.name)
                assert ast.get_docstring(node), (path, node.name)
                assert node.returns is not None, (path, node.name)
                assert all(
                    arg.annotation is not None or arg.arg in {"self", "cls"}
                    for arg in node.args.args
                ), (path, node.name)
            elif isinstance(node, ast.ClassDef):
                assert ast.get_docstring(node), (path, node.name)
    assert len(Path("app/main.py").read_text().splitlines()) < 100
