"""Compare separate chaining and linear probing on identical workloads."""

import csv
import random
from pathlib import Path

from src.hash_table import HashTable
from src.linear_probing import LinearProbingHashTable

CAPACITY = 4096
SAMPLE_COUNT = CAPACITY
SEED = 2026
LOAD_FACTORS = tuple(step / 10 for step in range(1, 10))
OUTPUT_DIR = Path(__file__).resolve().parent


def _make_keys(count: int, prefix: str, rng: random.Random) -> list[str]:
    alphabet = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return [
        f"{prefix}-{index:08x}-"
        + "".join(rng.choice(alphabet) for _ in range(12))
        for index in range(count)
    ]


def measure() -> list[tuple[float, int, float, float, float, float, float, float, float, float]]:
    rng = random.Random(SEED)
    keys = _make_keys(round(CAPACITY * LOAD_FACTORS[-1]), "hit", rng)
    misses = _make_keys(SAMPLE_COUNT, "miss", rng)
    results = []

    for load_factor in LOAD_FACTORS:
        item_count = round(CAPACITY * load_factor)
        chained = HashTable(capacity=CAPACITY, max_load_factor=None)
        linear = LinearProbingHashTable(capacity=CAPACITY, max_load_factor=None)
        for index, key in enumerate(keys[:item_count]):
            chained.set(key, index)
            linear.set(key, index)

        chained_success = sum(
            chained.get_with_probes(key)[1] for key in keys[:item_count]
        ) / item_count
        chained_failure = sum(
            chained.get_with_probes(key)[1] for key in misses
        ) / len(misses)
        linear_success = sum(
            linear.get_with_probes(key)[1] for key in keys[:item_count]
        ) / item_count
        linear_failure = sum(
            linear.get_with_probes(key)[1] for key in misses
        ) / len(misses)
        results.append(
            (
                load_factor,
                item_count,
                chained_success,
                1 + load_factor / 2,
                chained_failure,
                load_factor,
                linear_success,
                0.5 * (1 + 1 / (1 - load_factor)),
                linear_failure,
                0.5 * (1 + 1 / (1 - load_factor) ** 2),
            )
        )
    return results


def _write_csv(rows: list[tuple[float, int, float, float, float, float, float, float, float, float]]) -> Path:
    path = OUTPUT_DIR / "comparison_experiment.csv"
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output)
        writer.writerow(
            (
                "load_factor",
                "items",
                "chained_success_measured",
                "chained_success_theory",
                "chained_failure_measured",
                "chained_failure_theory",
                "linear_success_measured",
                "linear_success_theory",
                "linear_failure_measured",
                "linear_failure_theory",
            )
        )
        for row in rows:
            writer.writerow(
                (f"{row[0]:.1f}", row[1], *(f"{value:.4f}" for value in row[2:]))
            )
    return path


def _write_svg(rows: list[tuple[float, int, float, float, float, float, float, float, float, float]]) -> Path:
    width, height = 1000, 760
    left, plot_width, plot_height = 100, 830, 230
    panels = (
        (
            "Successful lookup: measured and theoretical probes",
            70,
            6.0,
            ((2, 3, "#2563eb", "Chaining"), (6, 7, "#ea580c", "Linear probing")),
        ),
        (
            "Unsuccessful lookup: measured and theoretical probes",
            390,
            55.0,
            ((4, 5, "#dc2626", "Chaining"), (8, 9, "#16a34a", "Linear probing")),
        ),
    )
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        "<title>Chaining versus linear probing</title>",
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="500" y="32" text-anchor="middle" font-family="sans-serif" '
        'font-size="20">Hash-table lookup cost by load factor</text>',
    ]

    for title, top, y_max, series in panels:
        def point(load_factor: float, probes: float) -> str:
            x = left + (load_factor - 0.1) / 0.8 * plot_width
            y = top + plot_height - probes / y_max * plot_height
            return f"{x:.1f},{y:.1f}"

        parts.append(
            f'<text x="{left}" y="{top - 14}" font-family="sans-serif" '
            f'font-size="15">{title}</text>'
        )
        tick_step = 1 if y_max == 6 else 10
        for tick in range(0, int(y_max) + 1, tick_step):
            y = top + plot_height - tick / y_max * plot_height
            parts.append(
                f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_width}" '
                f'y2="{y:.1f}" stroke="#e5e7eb"/>'
            )
            parts.append(
                f'<text x="{left - 12}" y="{y + 4:.1f}" text-anchor="end" '
                f'font-family="sans-serif" font-size="11">{tick}</text>'
            )
        for tick in range(1, 10):
            load_factor = tick / 10
            x = left + (load_factor - 0.1) / 0.8 * plot_width
            parts.append(
                f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" '
                f'y2="{top + plot_height}" stroke="#f3f4f6"/>'
            )
            parts.append(
                f'<text x="{x:.1f}" y="{top + plot_height + 18}" '
                f'text-anchor="middle" font-family="sans-serif" '
                f'font-size="10">{load_factor:.1f}</text>'
            )
        parts.extend(
            (
                f'<line x1="{left}" y1="{top + plot_height}" '
                f'x2="{left + plot_width}" y2="{top + plot_height}" stroke="#111827"/>',
                f'<text x="{left + plot_width / 2}" y="{top + plot_height + 36}" '
                'text-anchor="middle" font-family="sans-serif" font-size="12">'
                'Load factor (α)</text>',
            )
        )

        for series_index, (measured_column, theory_column, color, label) in enumerate(series):
            measured_points = " ".join(
                point(row[0], row[measured_column]) for row in rows
            )
            theory_points = " ".join(point(row[0], row[theory_column]) for row in rows)
            parts.append(
                f'<polyline points="{measured_points}" fill="none" stroke="{color}" '
                'stroke-width="2.5"/>'
            )
            parts.append(
                f'<polyline points="{theory_points}" fill="none" stroke="{color}" '
                'stroke-width="2" stroke-dasharray="6 4"/>'
            )
            legend_x = left + series_index * 390
            legend_y = top + plot_height + 62
            parts.append(
                f'<line x1="{legend_x}" y1="{legend_y}" x2="{legend_x + 30}" '
                f'y2="{legend_y}" stroke="{color}" stroke-width="2.5"/>'
            )
            parts.append(
                f'<text x="{legend_x + 38}" y="{legend_y + 4}" '
                'font-family="sans-serif" font-size="11">'
                f'{label} measured / dashed: theory</text>'
            )

    parts.append("</svg>")
    path = OUTPUT_DIR / "comparison_experiment.svg"
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")
    return path


def main() -> None:
    rows = measure()
    csv_path = _write_csv(rows)
    svg_path = _write_svg(rows)
    print("α     chaining success/failure     linear success/failure")
    for row in rows:
        print(
            f"{row[0]:.1f}  {row[2]:.3f}/{row[4]:.3f}                  "
            f"{row[6]:.3f}/{row[8]:.3f}"
        )
    print(f"\nWrote {csv_path.relative_to(OUTPUT_DIR.parent)}")
    print(f"Wrote {svg_path.relative_to(OUTPUT_DIR.parent)}")


if __name__ == "__main__":
    main()
