"""Measure separate-chaining lookup costs across load factors."""

import csv
import random
from pathlib import Path

from src.hash_table import HashTable

CAPACITY = 4096
SAMPLE_COUNT = CAPACITY
SEED = 2026
LOAD_FACTORS = tuple(step / 4 for step in range(1, 17))
OUTPUT_DIR = Path(__file__).resolve().parent


def _make_keys(count: int, prefix: str, rng: random.Random) -> list[str]:
    alphabet = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return [
        f"{prefix}-{index:08x}-"
        + "".join(rng.choice(alphabet) for _ in range(12))
        for index in range(count)
    ]


def measure() -> list[tuple[float, int, float, float, float, float]]:
    rng = random.Random(SEED)
    keys = _make_keys(int(CAPACITY * LOAD_FACTORS[-1]), "hit", rng)
    misses = _make_keys(SAMPLE_COUNT, "miss", rng)
    results = []

    for load_factor in LOAD_FACTORS:
        item_count = round(CAPACITY * load_factor)
        table = HashTable(capacity=CAPACITY, max_load_factor=None)
        for index, key in enumerate(keys[:item_count]):
            table.set(key, index)

        successful_probes = sum(
            table.get_with_probes(key)[1] for key in keys[:item_count]
        )
        unsuccessful_probes = sum(
            table.get_with_probes(key)[1] for key in misses
        )
        measured_success = successful_probes / item_count
        measured_failure = unsuccessful_probes / len(misses)
        results.append(
            (
                load_factor,
                item_count,
                measured_success,
                1 + load_factor / 2,
                measured_failure,
                load_factor,
            )
        )
    return results


def _write_csv(rows: list[tuple[float, int, float, float, float, float]]) -> Path:
    path = OUTPUT_DIR / "probe_experiment.csv"
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output)
        writer.writerow(
            (
                "load_factor",
                "items",
                "measured_success",
                "theoretical_success",
                "measured_failure",
                "theoretical_failure",
            )
        )
        for row in rows:
            writer.writerow(
                (f"{row[0]:.2f}", row[1], *(f"{value:.4f}" for value in row[2:]))
            )
    return path


def _write_svg(rows: list[tuple[float, int, float, float, float, float]]) -> Path:
    width, height = 900, 520
    left, top, plot_width, plot_height = 85, 55, 745, 360
    y_max = 4.5

    def point(load_factor: float, probes: float) -> str:
        x = left + load_factor / 4 * plot_width
        y = top + plot_height - probes / y_max * plot_height
        return f"{x:.1f},{y:.1f}"

    series = (
        ("Measured success", 2, "#2563eb"),
        ("Theory success (1 + α/2)", 3, "#93c5fd"),
        ("Measured failure", 4, "#dc2626"),
        ("Theory failure (α)", 5, "#fca5a5"),
    )
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        "<title>Separate-chaining lookup probes by load factor</title>",
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="450" y="28" text-anchor="middle" font-family="sans-serif" '
        'font-size="18">Separate-chaining lookup cost vs. load factor</text>',
    ]

    for tick in range(5):
        x = left + tick / 4 * plot_width
        parts.append(
            f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" '
            f'y2="{top + plot_height}" stroke="#e5e7eb"/>'
        )
        parts.append(
            f'<text x="{x:.1f}" y="{top + plot_height + 22}" text-anchor="middle" '
            f'font-family="sans-serif" font-size="12">{tick}</text>'
        )
    for tick in range(5):
        y = top + plot_height - tick / y_max * plot_height
        parts.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_width}" '
            f'y2="{y:.1f}" stroke="#e5e7eb"/>'
        )
        parts.append(
            f'<text x="{left - 12}" y="{y + 4:.1f}" text-anchor="end" '
            f'font-family="sans-serif" font-size="12">{tick}</text>'
        )

    parts.extend(
        (
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" '
            'stroke="#111827"/>',
            f'<line x1="{left}" y1="{top + plot_height}" '
            f'x2="{left + plot_width}" y2="{top + plot_height}" stroke="#111827"/>',
            f'<text x="{left + plot_width / 2}" y="{height - 20}" text-anchor="middle" '
            'font-family="sans-serif" font-size="14">Load factor (α)</text>',
            f'<text x="20" y="{top + plot_height / 2}" text-anchor="middle" '
            'font-family="sans-serif" font-size="14" '
            f'transform="rotate(-90 20 {top + plot_height / 2})">Nodes visited</text>',
        )
    )
    for label, column, color in series:
        points = " ".join(point(row[0], row[column]) for row in rows)
        parts.append(
            f'<polyline points="{points}" fill="none" stroke="{color}" '
            'stroke-width="2"/>'
        )
        legend_y = 455 + (series.index((label, column, color)) % 2) * 24
        legend_x = left + (series.index((label, column, color)) // 2) * 365
        parts.append(
            f'<line x1="{legend_x}" y1="{legend_y}" x2="{legend_x + 28}" '
            f'y2="{legend_y}" stroke="{color}" stroke-width="3"/>'
        )
        parts.append(
            f'<text x="{legend_x + 36}" y="{legend_y + 4}" font-family="sans-serif" '
            f'font-size="12">{label}</text>'
        )
    parts.append("</svg>")

    path = OUTPUT_DIR / "probe_experiment.svg"
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")
    return path


def main() -> None:
    rows = measure()
    csv_path = _write_csv(rows)
    svg_path = _write_svg(rows)
    print("α     hit(measured/theory)     miss(measured/theory)")
    for row in rows:
        print(
            f"{row[0]:.2f}  {row[2]:.3f}/{row[3]:.3f}                 "
            f"{row[4]:.3f}/{row[5]:.3f}"
        )
    print(f"\nWrote {csv_path.relative_to(OUTPUT_DIR.parent)}")
    print(f"Wrote {svg_path.relative_to(OUTPUT_DIR.parent)}")


if __name__ == "__main__":
    main()
