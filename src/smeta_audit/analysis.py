"""Агрегация расчётных таблиц ВКР и подготовка результатов для отчёта."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

PUBLISHED_DETAIL_INCREASE = 26_521.25
PUBLISHED_DETAIL_DECREASE_CONSERVATIVE = 6_641.19
PUBLISHED_ESTIMATED_INCREASE = 8_150.43
PUBLISHED_ESTIMATED_DECREASE = 1_098.63


def load_processed_data(data_dir: Path) -> dict[str, pd.DataFrame]:
    return {
        "remarks": pd.read_csv(data_dir / "remark_groups.csv"),
        "detailed": pd.read_csv(data_dir / "detailed_cases.csv"),
        "estimated": pd.read_csv(data_dir / "estimated_impacts.csv"),
        "ssr": pd.read_csv(data_dir / "ssr_structure.csv"),
        "inventory": pd.read_csv(data_dir / "source_sheet_inventory.csv"),
        "reproduction": pd.read_csv(data_dir / "excel_reproduction.csv"),
    }


def aggregate_detailed_cases(cases: pd.DataFrame) -> dict[str, float]:
    included = cases[cases["include_conservative"] == 1]
    increase = included.loc[included["impact_type"] == "increase", "impact_thousand_rub"].sum()
    decrease = included.loc[included["impact_type"] == "decrease", "impact_thousand_rub"].sum()
    all_decrease = cases.loc[cases["impact_type"] == "decrease", "impact_thousand_rub"].sum()
    return {
        "row_sum_increase": round(float(increase), 2),
        "row_sum_decrease_conservative": round(float(decrease), 2),
        "row_sum_decrease_with_scenario": round(float(all_decrease), 2),
        "published_increase": PUBLISHED_DETAIL_INCREASE,
        "published_decrease_conservative": PUBLISHED_DETAIL_DECREASE_CONSERVATIVE,
        "published_net_conservative": round(
            PUBLISHED_DETAIL_INCREASE - PUBLISHED_DETAIL_DECREASE_CONSERVATIVE, 2
        ),
        "published_decrease_with_scenario": 115_734.46,
        "published_net_with_scenario": round(PUBLISHED_DETAIL_INCREASE - 115_734.46, 2),
    }


def aggregate_estimated_impacts(estimated: pd.DataFrame) -> dict[str, float]:
    increase = estimated["increase_thousand_rub"].sum()
    decrease = estimated["decrease_thousand_rub"].sum()
    net = estimated["net_thousand_rub"].sum()
    return {
        "increase": round(float(increase), 2),
        "decrease": round(float(decrease), 2),
        "net": round(float(net), 2),
        "published_increase": PUBLISHED_ESTIMATED_INCREASE,
        "published_decrease": PUBLISHED_ESTIMATED_DECREASE,
        "published_net": round(PUBLISHED_ESTIMATED_INCREASE - PUBLISHED_ESTIMATED_DECREASE, 2),
    }


def build_kpi_table(cases: pd.DataFrame, estimated: pd.DataFrame) -> pd.DataFrame:
    detail = aggregate_detailed_cases(cases)
    estimate = aggregate_estimated_impacts(estimated)
    return pd.DataFrame(
        [
            [
                "Детальный расчёт",
                16,
                detail["published_increase"],
                detail["published_decrease_conservative"],
                detail["published_net_conservative"],
            ],
            [
                "Оценочный расчёт",
                97,
                estimate["published_increase"],
                estimate["published_decrease"],
                estimate["published_net"],
            ],
            [
                "Итого с оценочным расчётом",
                113,
                detail["published_increase"] + estimate["published_increase"],
                detail["published_decrease_conservative"] + estimate["published_decrease"],
                detail["published_net_conservative"] + estimate["published_net"],
            ],
        ],
        columns=[
            "scenario",
            "remarks",
            "increase_thousand_rub",
            "decrease_thousand_rub",
            "net_thousand_rub",
        ],
    )
