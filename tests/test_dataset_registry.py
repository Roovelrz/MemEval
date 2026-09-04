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

    def test_registers_frozen_memeval_until_system_adapter_is_ready(self) -> None:
        spec = load_dataset_registry()["MemEval-v0.1"]

        self.assertEqual(spec["case_count"], 298)
        self.assertEqual(spec["blocked_by"], "stage_24_system_adapter")
        with self.assertRaisesRegex(ValueError, "reserved"):
            resolve_dataset("MemEval-v0.1")

    def test_reserved_dataset_fails_before_runner_starts(self) -> None:
        with self.assertRaisesRegex(ValueError, "reserved"):
            resolve_dataset("LoCoMo-ZH-Localized")

    def test_local_english_datasets_are_available(self) -> None:
        _, locomo_spec = resolve_dataset("LoCoMo-EN-Full")
        _, personamem_spec = resolve_dataset("PersonaMem-EN-Full")
        self.assertEqual(locomo_spec["adapter"], "locomo")
        self.assertEqual(personamem_spec["adapter"], "personamem-v2")

    def test_run_metadata_distinguishes_selected_and_source_case_counts(self) -> None:
        spec = load_dataset_registry()["LongMemEval-EN-Full"]
        metadata = run_dataset_metadata(spec, selected_case_count=20, source_case_count=500)
        self.assertEqual(metadata["case_count"], 20)
        self.assertEqual(metadata["dataset_case_count"], 500)


if __name__ == "__main__":
    unittest.main()
