from __future__ import annotations

import unittest

from memory_eval.dataset_registry import (
    default_output_root,
    load_dataset_registry,
    resolve_dataset,
    run_dataset_metadata,
)


class DatasetRegistryTest(unittest.TestCase):
    def test_registers_both_longmemeval_benchmarks(self) -> None:
        registry = load_dataset_registry()
        self.assertEqual(set(registry) & {"LongMemEval-EN-Full", "LongMemEval-ZH-20-v0.1"}, {"LongMemEval-EN-Full", "LongMemEval-ZH-20-v0.1"})

        en_spec = registry["LongMemEval-EN-Full"]
        zh_spec = registry["LongMemEval-ZH-20-v0.1"]

        self.assertEqual(en_spec["language"], "en")
        self.assertEqual(zh_spec["language"], "zh-CN")
        self.assertEqual(default_output_root(en_spec, "ReMe").parts[-2:], ("en_full", "reme"))
        self.assertEqual(default_output_root(zh_spec, "ReMe").parts[-2:], ("zh_localized", "reme"))

    def test_reserved_dataset_fails_before_runner_starts(self) -> None:
        with self.assertRaisesRegex(ValueError, "reserved"):
            resolve_dataset("LoCoMo-EN-Full")

    def test_run_metadata_distinguishes_selected_and_source_case_counts(self) -> None:
        spec = load_dataset_registry()["LongMemEval-EN-Full"]
        metadata = run_dataset_metadata(spec, selected_case_count=20, source_case_count=500)
        self.assertEqual(metadata["case_count"], 20)
        self.assertEqual(metadata["dataset_case_count"], 500)


if __name__ == "__main__":
    unittest.main()
