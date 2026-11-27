import csv
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree

from experiments.probe_experiment import (
    CAPACITY,
    LOAD_FACTORS,
    _write_csv,
    _write_svg,
    measure,
)


class ProbeExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = measure()

    def test_measurement_uses_requested_capacity_and_theoretical_load(self):
        self.assertEqual(CAPACITY, 4093)
        self.assertEqual(len(self.rows), 16)

        for index, row in enumerate(self.rows):
            load_factor, item_count, success, success_theory, failure, failure_theory = row
            expected_items = round(CAPACITY * LOAD_FACTORS[index])
            actual_load = expected_items / CAPACITY

            self.assertEqual(item_count, expected_items)
            self.assertAlmostEqual(load_factor, actual_load)
            self.assertAlmostEqual(success_theory, 1 + actual_load / 2)
            self.assertAlmostEqual(failure_theory, actual_load)
            self.assertLess(abs(success - success_theory), 0.15)
            self.assertLess(abs(failure - failure_theory), 0.15)

    def test_writers_create_requested_csv_table_and_svg_graph(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory)
            csv_path = _write_csv(self.rows, output_dir)
            svg_path = _write_svg(self.rows, output_dir)

            self.assertEqual(csv_path.name, "results.csv")
            self.assertEqual(svg_path.name, "results.svg")

            self.assertNotIn(b"\r", csv_path.read_bytes())
            with csv_path.open(newline="", encoding="utf-8") as source:
                csv_rows = list(csv.reader(source))
            self.assertEqual(
                csv_rows[0],
                [
                    "load_factor",
                    "items",
                    "measured_success",
                    "theoretical_success",
                    "measured_failure",
                    "theoretical_failure",
                ],
            )
            self.assertEqual(len(csv_rows), len(self.rows) + 1)

            root = ElementTree.parse(svg_path).getroot()
            self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")
            self.assertEqual(
                len(root.findall(".//{http://www.w3.org/2000/svg}polyline")),
                4,
            )


if __name__ == "__main__":
    unittest.main()
