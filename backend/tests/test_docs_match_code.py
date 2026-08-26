"""S7: README и architecture.md не выдают replica/cache за текущую схему."""
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
README = (REPO / "README.md").read_text(encoding="utf-8")
ARCH = (REPO / "docs" / "architecture.md").read_text(encoding="utf-8")

FACT_FORBIDDEN = (
    "replica",
    "реплик",
    "pub/sub",
    "pubsub",
)


def test_readme_does_not_claim_replica_or_dashboard_cache():
    low = README.lower()
    for needle in FACT_FORBIDDEN:
        assert needle not in low, needle
    assert "кеш" not in low and "cache" not in low
    assert "FastAPI" in README
    assert "vanilla JS" in README or "vanilla js" in low


def test_architecture_facts_then_not_implemented():
    assert "## Не реализовано" in ARCH
    facts, _, planned = ARCH.partition("## Не реализовано")
    facts_l = facts.lower()
    for needle in FACT_FORBIDDEN:
        assert needle not in facts_l, f"факт-секция не должна обещать {needle}"
    assert "кеширует" not in facts_l
    assert "FastAPI" in facts
    assert "PostgreSQL" in facts
    assert "vanilla JS" in facts or "Vanilla JS" in facts
    planned_l = planned.lower()
    assert "replica" in planned_l or "реплик" in planned_l
    assert "не внедрять" in planned_l or "нет" in planned_l
