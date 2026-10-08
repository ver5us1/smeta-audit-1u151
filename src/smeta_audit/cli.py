from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Расчёты и отчёт по аудиту сметной документации")
    parser.add_argument("command", choices=["run"], nargs="?", default="run")
    args = parser.parse_args()
    if args.command == "run":
        root = Path(__file__).resolve().parents[2]
        results = run_pipeline(root)
        print("Готово. Расчёты:")
        for name, value in results.items():
            print(f"- {name}: {value:.3f} тыс. руб.")


if __name__ == "__main__":
    main()
