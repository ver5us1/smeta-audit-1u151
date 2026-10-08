"""Единый pipeline: расчёты, графики и markdown-отчёт."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from .analysis import (
    aggregate_detailed_cases,
    aggregate_estimated_impacts,
    build_kpi_table,
    load_processed_data,
)
from .calculations import (
    CommandTripInputs,
    ElectricityInputs,
    GnusInputs,
    WorkerTransportInputs,
    calculate_command_trip,
    calculate_gnus,
    calculate_legacy_electricity_difference,
    calculate_worker_transport,
)


def _read_inputs(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def reproduce_excel_calculations(input_path: Path) -> dict[str, float]:
    data = _read_inputs(input_path)
    command = data["command_trip"]
    command_result = calculate_command_trip(
        CommandTripInputs(
            duration_months=command["duration_months"],
            workers_by_city=command["workers_by_city"],
            rotation_months=command["rotation_months"],
            daily_allowance_rub=command["daily_allowance_rub"],
            days_per_month=command["days_per_month"],
            rail_cost_rub=command["rail_cost_rub"],
            travel_days_one_way=command["travel_days_one_way"],
            station_to_accommodation_km=command["station_to_accommodation_km"],
            bus_speed_kmh=command["bus_speed_kmh"],
            bus_machine_hour_rub=command["bus_machine_hour_rub"],
            bus_capacity=command["bus_capacity"],
            accommodation_rub_per_day=command["accommodation_rub_per_day"],
        )
    )
    transport = data["worker_transport"]
    transport_result = calculate_worker_transport(WorkerTransportInputs(**transport))
    gnus = data["gnus"]
    gnus_result = calculate_gnus(
        GnusInputs(
            workers=gnus["workers"],
            hat_rub=gnus["hat_rub"],
            repellent_rub=gnus["repellent_rub"],
            after_bite_balm_rub=gnus["after_bite_balm_rub"],
            seasons=gnus["seasons"],
        )
    )
    electricity = calculate_legacy_electricity_difference(
        ElectricityInputs(**data["electricity_legacy_sheet"])
    )
    return {
        "Командировка": command_result.total_thousand_rub,
        "Перевозка работников": transport_result.total_thousand_rub,
        "Специальные мероприятия «гнус»": gnus_result.total_thousand_rub,
        "Разница электроэнергии (legacy)": electricity,
    }


def _style(ax: plt.Axes) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.22)
    ax.set_axisbelow(True)


def build_figures(data: dict[str, pd.DataFrame], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "figure.dpi": 150})
    navy, blue, orange = "#17324D", "#3E78B2", "#E58F3A"

    remarks = data["remarks"].sort_values("share_pct")
    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.barh(remarks["group"], remarks["share_pct"], color=blue)
    ax.set_xlabel("Доля замечаний, %")
    ax.set_title("Структура замечаний к сметной документации", loc="left", weight="bold")
    for y, value in enumerate(remarks["share_pct"]):
        ax.text(value + 0.3, y, f"{value:.1f}%", va="center", fontsize=9)
    _style(ax)
    fig.tight_layout()
    fig.savefig(output_dir / "01_remark_structure.png", bbox_inches="tight")
    plt.close(fig)

    detail = aggregate_detailed_cases(data["detailed"])
    fig, ax = plt.subplots(figsize=(8, 4.7))
    labels = ["Увеличение\nстоимости", "Снижение\n(консервативно)", "Чистое\nвлияние"]
    values = [
        detail["published_increase"],
        -detail["published_decrease_conservative"],
        detail["published_net_conservative"],
    ]
    colors = [blue, "#9A9A9A", navy]
    bars = ax.bar(labels, values, color=colors, width=0.62)
    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.set_ylabel("тыс. руб.")
    ax.set_title("Детальный расчёт: подтверждённое влияние", loc="left", weight="bold")
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + (500 if value >= 0 else -1000),
            f"{value:,.2f}".replace(",", " "),
            ha="center",
            va="bottom" if value >= 0 else "top",
            fontsize=9,
        )
    _style(ax)
    fig.tight_layout()
    fig.savefig(output_dir / "02_detailed_impact.png", bbox_inches="tight")
    plt.close(fig)

    estimate = aggregate_estimated_impacts(data["estimated"])
    fig, ax = plt.subplots(figsize=(8, 4.7))
    labels = ["Возможное\nувеличение", "Возможное\nснижение", "Чистое\nвлияние"]
    values = [
        estimate["published_increase"],
        -estimate["published_decrease"],
        estimate["published_net"],
    ]
    bars = ax.bar(labels, values, color=[blue, "#9A9A9A", navy], width=0.62)
    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.set_ylabel("тыс. руб.")
    ax.set_title("Оценочный расчёт: сценарное влияние", loc="left", weight="bold")
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + (180 if value >= 0 else -160),
            f"{value:,.2f}".replace(",", " "),
            ha="center",
            va="bottom" if value >= 0 else "top",
            fontsize=9,
        )
    _style(ax)
    fig.tight_layout()
    fig.savefig(output_dir / "03_estimated_impact.png", bbox_inches="tight")
    plt.close(fig)

    kpi = build_kpi_table(data["detailed"], data["estimated"])
    fig, ax = plt.subplots(figsize=(9, 4.8))
    x = range(len(kpi))
    ax.bar(
        [i - 0.18 for i in x], kpi["increase_thousand_rub"], 0.36, label="Увеличение", color=blue
    )
    ax.bar(
        [i + 0.18 for i in x], kpi["decrease_thousand_rub"], 0.36, label="Снижение", color=orange
    )
    ax.set_xticks(list(x), ["Детальный", "Оценочный", "Всего"])
    ax.set_ylabel("тыс. руб.")
    ax.set_title("Масштаб стоимостного влияния по сценариям", loc="left", weight="bold")
    ax.legend(frameon=False, ncol=2)
    _style(ax)
    fig.tight_layout()
    fig.savefig(output_dir / "04_scenario_comparison.png", bbox_inches="tight")
    plt.close(fig)


def build_report(
    data: dict[str, pd.DataFrame], calculations: dict[str, float], report_path: Path
) -> None:
    detail = aggregate_detailed_cases(data["detailed"])
    estimated = aggregate_estimated_impacts(data["estimated"])
    kpi = build_kpi_table(data["detailed"], data["estimated"])
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Итоговый аналитический отчёт",
        "",
        "## Что проверено",
        "",
        "Python-пайплайн переводит в воспроизводимый вид три релевантных листа Excel — «Командировка», «Перевозка» и «Гнус» — и агрегирует результаты ВКР по замечаниям к проектно-сметной документации установки 1У-151.",
        "",
        "## Ключевые результаты ВКР",
        "",
        "| Сценарий | Замечаний | Увеличение, тыс. руб. | Снижение, тыс. руб. | Чистое влияние, тыс. руб. |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in kpi.itertuples(index=False):
        lines.append(
            f"| {row.scenario} | {row.remarks} | {row.increase_thousand_rub:,.2f} | {row.decrease_thousand_rub:,.2f} | {row.net_thousand_rub:,.2f} |".replace(
                ",", " "
            )
        )
    lines += [
        "",
        f"Подтверждённый консервативный итог: **+{detail['published_net_conservative']:,.2f} тыс. руб.**".replace(
            ",", " "
        ),
        f"Расширенный итог с оценочными замечаниями: **+{detail['published_net_conservative'] + estimated['published_net']:,.2f} тыс. руб.**".replace(
            ",", " "
        ),
        "",
        "## Перенос формул Excel → Python",
        "",
        "| Лист | Python, тыс. руб. | Excel, тыс. руб. | Комментарий |",
        "|---|---:|---:|---|",
    ]
    comments = {
        "Командировка": "формула воспроизведена; в таблице ВКР указан другой итог",
        "Перевозка работников": "формула воспроизведена; в таблице ВКР указан другой итог",
        "Специальные мероприятия «гнус»": "формула воспроизведена; в таблице ВКР указан другой итог",
        "Разница электроэнергии (legacy)": "исключено из ВКР: другой объект и цены 2017 года",
    }
    for name, value in calculations.items():
        excel = data["reproduction"].set_index("calculation").loc[name, "excel_result_thousand_rub"]
        lines.append(
            f"| {name} | {value:,.3f} | {float(excel):,.3f} | {comments[name]} |".replace(",", " ")
        )
    lines += [
        "",
        "## Ограничения интерпретации",
        "",
        "- Итоговые строки ВКР округлены отдельно от строк исходной таблицы. Поэтому сумма опубликованных строк может отличаться на 0,01 тыс. руб.; расхождение сохранено в проекте явно.",
        "- В исходной книге смешаны расчёты по 1У-151 (цены 2024 года) и legacy-блок по КС Дивенская (цены 2017 года). Legacy-листы с `#REF!` не включены в основной результат.",
        "- 97 замечаний рассчитаны оценочно и требуют дополнительных первичных данных; их результат не следует трактовать как подтверждённую экономию.",
        "",
        "## Воспроизводимость",
        "",
        "```bash",
        "pip install -e .[dev]",
        "smeta-audit run",
        "pytest -q",
        "```",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_pipeline(project_root: Path) -> dict[str, float]:
    data_dir = project_root / "data" / "processed"
    data = load_processed_data(data_dir)
    calculations = reproduce_excel_calculations(
        project_root / "data" / "source" / "excel_inputs.json"
    )
    build_figures(data, project_root / "reports" / "figures")
    build_report(data, calculations, project_root / "reports" / "analysis_report.md")
    pd.DataFrame([calculations]).to_csv(
        project_root / "reports" / "excel_reproduction_python.csv", index=False
    )
    detail = aggregate_detailed_cases(data["detailed"])
    estimated = aggregate_estimated_impacts(data["estimated"])
    summary = {
        "detail_net_conservative_thousand_rub": detail["published_net_conservative"],
        "estimated_net_thousand_rub": estimated["published_net"],
        "extended_net_thousand_rub": detail["published_net_conservative"]
        + estimated["published_net"],
    }
    (project_root / "reports" / "verification_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return calculations
