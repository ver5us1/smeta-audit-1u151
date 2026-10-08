from pathlib import Path

from smeta_audit.analysis import (
    aggregate_detailed_cases,
    aggregate_estimated_impacts,
    build_kpi_table,
    load_processed_data,
)

ROOT = Path(__file__).parents[1]


def test_detailed_published_totals() -> None:
    data = load_processed_data(ROOT / "data/processed")
    result = aggregate_detailed_cases(data["detailed"])
    assert result["published_increase"] == 26521.25
    assert result["published_net_conservative"] == 19880.06
    assert result["row_sum_increase"] == 26521.24


def test_estimated_totals_and_kpi_table() -> None:
    data = load_processed_data(ROOT / "data/processed")
    result = aggregate_estimated_impacts(data["estimated"])
    assert result["increase"] == 8150.43
    assert result["decrease"] == 1098.63
    assert result["net"] == 7051.80
    kpi = build_kpi_table(data["detailed"], data["estimated"])
    assert kpi.iloc[-1]["net_thousand_rub"] == 26931.86
