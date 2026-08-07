from pathlib import Path

import pytest
from research.experiment_registry import ExperimentRegistry, RegistryError


def test_experiment_registry_is_write_once_and_runs_are_append_only(tmp_path: Path):
    registry = ExperimentRegistry(tmp_path / "experiments.db")
    record = registry.register(
        experiment_id="exp-001",
        family_id="family-001",
        hypothesis="entry_ok has measurable path outcome",
        rationale="Validate the existing candidate without adding parameters",
        planned_tests=["label_permutation", "signal_permutation"],
        planned_runs=1000,
    )

    assert registry.get("exp-001")["record_hash"] == record["record_hash"]
    with pytest.raises(RegistryError, match="already registered"):
        registry.register(
            experiment_id="exp-001",
            family_id="family-001",
            hypothesis="changed",
            rationale="changed",
            planned_tests=["changed"],
            planned_runs=1,
        )

    run = registry.record_run(
        experiment_id="exp-001",
        run_id="exp-001-0000",
        run_index=0,
        seed=17,
        input_hash="sha256:input",
        status="completed",
        result={"mean_net_return_pct": 0.1},
    )
    assert run["record_hash"]
    with pytest.raises(RegistryError, match="already recorded"):
        registry.record_run(
            experiment_id="exp-001",
            run_id="exp-001-0000",
            run_index=0,
            seed=18,
            input_hash="sha256:other",
            status="completed",
            result={},
        )
