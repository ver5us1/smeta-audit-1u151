import json
from pathlib import Path

from smeta_audit.calculations import (
    CommandTripInputs,
    ElectricityInputs,
    GnusInputs,
    WorkerTransportInputs,
    calculate_command_trip,
    calculate_gnus,
    calculate_legacy_electricity_difference,
    calculate_worker_transport,
)

ROOT = Path(__file__).parents[1]


def _inputs() -> dict:
    return json.loads((ROOT / "data/source/excel_inputs.json").read_text(encoding="utf-8"))


def test_command_trip_reproduces_excel_total() -> None:
    data = _inputs()["command_trip"]
    result = calculate_command_trip(
        CommandTripInputs(
            duration_months=data["duration_months"],
            workers_by_city=data["workers_by_city"],
            rotation_months=data["rotation_months"],
            daily_allowance_rub=data["daily_allowance_rub"],
            days_per_month=data["days_per_month"],
            rail_cost_rub=data["rail_cost_rub"],
            travel_days_one_way=data["travel_days_one_way"],
            station_to_accommodation_km=data["station_to_accommodation_km"],
            bus_speed_kmh=data["bus_speed_kmh"],
            bus_machine_hour_rub=data["bus_machine_hour_rub"],
            bus_capacity=data["bus_capacity"],
            accommodation_rub_per_day=data["accommodation_rub_per_day"],
        )
    )
    assert result.total_thousand_rub == 9482.755
    assert result.rail_thousand_rub == 1780.935
    assert result.bus_hours == 28.08


def test_worker_transport_reproduces_excel_total() -> None:
    result = calculate_worker_transport(WorkerTransportInputs(**_inputs()["worker_transport"]))
    assert result.machine_hours == 309.54
    assert result.total_thousand_rub == 708.76


def test_gnus_reproduces_excel_total() -> None:
    data = _inputs()["gnus"]
    result = calculate_gnus(
        GnusInputs(
            workers=data["workers"],
            hat_rub=data["hat_rub"],
            repellent_rub=data["repellent_rub"],
            after_bite_balm_rub=data["after_bite_balm_rub"],
            seasons=data["seasons"],
        )
    )
    assert result.hats_thousand_rub == 4.34
    assert result.repellents_thousand_rub == 90.38
    assert result.total_thousand_rub == 94.72


def test_legacy_electricity_is_reproduced_but_separate() -> None:
    result = calculate_legacy_electricity_difference(
        ElectricityInputs(**_inputs()["electricity_legacy_sheet"])
    )
    assert result == 41701.279
