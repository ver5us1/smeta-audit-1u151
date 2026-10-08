"""Прозрачные функции, перенесённые из формул исходной книги Excel."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil


@dataclass(frozen=True)
class CommandTripInputs:
    duration_months: float
    workers_by_city: dict[str, int]
    rotation_months: float
    daily_allowance_rub: float
    days_per_month: float
    rail_cost_rub: dict[str, float]
    travel_days_one_way: dict[str, int]
    station_to_accommodation_km: float
    bus_speed_kmh: float
    bus_machine_hour_rub: float
    bus_capacity: int
    accommodation_rub_per_day: float


@dataclass(frozen=True)
class CommandTripResult:
    cycles: float
    rail_thousand_rub: float
    allowance_thousand_rub: float
    bus_hours: float
    bus_thousand_rub: float
    accommodation_thousand_rub: float
    total_thousand_rub: float


def calculate_command_trip(inputs: CommandTripInputs) -> CommandTripResult:
    """Считает командировочные расходы по листу «Командировка».

    Округление на промежуточных шагах повторяет формулы Excel: время одного
    автобусного цикла округляется до 2 знаков, стоимость — до 2 знаков.
    """

    workers = sum(inputs.workers_by_city.values())
    # В исходном листе число циклов округляется вверх: 10,5 / 2 = 5,25 → 6.
    cycles = ceil(inputs.duration_months / inputs.rotation_months)
    rail = (
        sum(
            inputs.workers_by_city[city] * inputs.rail_cost_rub[city]
            for city in inputs.workers_by_city
        )
        * cycles
        * 2
        / 1000
    )
    allowance = (
        inputs.daily_allowance_rub
        * sum(
            inputs.workers_by_city[city] * max(inputs.travel_days_one_way[city] - 1, 0)
            for city in inputs.workers_by_city
        )
        * cycles
        * 2
        / 1000
    )
    cycle_hours = round(2 * inputs.station_to_accommodation_km / inputs.bus_speed_kmh, 2)
    buses = ceil(workers / inputs.bus_capacity)
    bus_hours = round(cycle_hours * buses * cycles, 2)
    bus_cost = round(bus_hours * inputs.bus_machine_hour_rub / 1000, 2)
    accommodation = (
        inputs.accommodation_rub_per_day
        * workers
        * inputs.days_per_month
        * inputs.duration_months
        / 1000
    )
    total = round(rail + allowance + bus_cost + accommodation, 3)
    return CommandTripResult(
        cycles=cycles,
        rail_thousand_rub=round(rail, 3),
        allowance_thousand_rub=round(allowance, 3),
        bus_hours=bus_hours,
        bus_thousand_rub=bus_cost,
        accommodation_thousand_rub=round(accommodation, 2),
        total_thousand_rub=total,
    )


@dataclass(frozen=True)
class WorkerTransportInputs:
    workers: int
    duration_months: float
    work_days_per_month: int
    distance_km: float
    bus_speed_kmh: float
    bus_capacity: int
    bus_machine_hour_rub: float


@dataclass(frozen=True)
class WorkerTransportResult:
    daily_trips: int
    cycle_hours: float
    machine_hours: float
    total_thousand_rub: float


def calculate_worker_transport(inputs: WorkerTransportInputs) -> WorkerTransportResult:
    """Считает перевозку работников до места работ по листу «Перевозка»."""

    trips = ceil(inputs.workers / inputs.bus_capacity)
    cycle_hours = round(2 * inputs.distance_km / inputs.bus_speed_kmh, 2)
    machine_hours = round(
        cycle_hours * trips * inputs.duration_months * inputs.work_days_per_month, 2
    )
    total = round(machine_hours * inputs.bus_machine_hour_rub / 1000, 2)
    return WorkerTransportResult(trips, cycle_hours, machine_hours, total)


@dataclass(frozen=True)
class GnusInputs:
    workers: int
    hat_rub: float
    repellent_rub: float
    after_bite_balm_rub: float
    seasons: int


@dataclass(frozen=True)
class GnusResult:
    hats_thousand_rub: float
    repellents_thousand_rub: float
    total_thousand_rub: float


def calculate_gnus(inputs: GnusInputs) -> GnusResult:
    """Считает специальные мероприятия по защите работников от гнуса."""

    hats = round(inputs.hat_rub * inputs.seasons * inputs.workers / 1000, 2)
    repellents = round(
        (inputs.repellent_rub + inputs.after_bite_balm_rub)
        * inputs.seasons
        * inputs.workers
        / 1000,
        2,
    )
    return GnusResult(hats, repellents, round(hats + repellents, 2))


@dataclass(frozen=True)
class ElectricityInputs:
    consumption_total_kwh: float
    diesel_generation_kwh: float
    already_costed_kwh: float
    grid_price_rub_per_kwh: float
    diesel_machine_hour_rub: float
    diesel_power_kw: float


def calculate_legacy_electricity_difference(inputs: ElectricityInputs) -> float:
    """Воспроизводит лист «РАЗНИЦА ЭЛЕКТРО» из legacy-блока исходника.

    Лист сохранён для аудита, но в основной результат ВКР не включается:
    он относится к другому объекту и ценам 2017 года.
    """

    not_costed = (
        inputs.consumption_total_kwh - inputs.diesel_generation_kwh - inputs.already_costed_kwh
    )
    diesel_price = inputs.diesel_machine_hour_rub / inputs.diesel_power_kw
    first_part = diesel_price * not_costed
    second_part = (diesel_price - inputs.grid_price_rub_per_kwh) * inputs.already_costed_kwh
    return round((first_part + second_part) / 1000, 3)
