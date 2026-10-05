import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('benchmark_analyze', ROOT / 'analyze.py')
analyzer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(analyzer)


class AnalyzerTests(unittest.TestCase):
    def setUp(self):
        self.rows = analyzer.load(ROOT / 'synthetic.jsonl')

    def test_charges_failures_and_all_retries(self):
        report = analyzer.analyze(self.rows, True)
        baseline = report['variant_totals']['baseline']
        self.assertEqual(baseline['attempts'], 3)
        self.assertEqual(baseline['failed_attempts'], 1)
        self.assertEqual(baseline['cost_per_success_usd'], 1.75)
        self.assertEqual(report['variant_totals']['agent']['cost_per_success_usd'], 4.0)
        self.assertEqual(report['paired_deltas_agent_minus_baseline']['success_rate_delta'], -0.5)
        self.assertAlmostEqual(report['paired_deltas_agent_minus_baseline']['mean_episode_cost_delta_usd'], 0.25)
        self.assertEqual(report['independent_repository_count'], 1)

    def test_zero_success_cost_is_undefined(self):
        for row in self.rows:
            for attempt in row['attempts']:
                attempt['success'] = False
        self.assertIsNone(analyzer.analyze(self.rows, True)['variant_totals']['agent']['cost_per_success_usd'])

    def test_synthetic_requires_explicit_flag(self):
        with self.assertRaisesRegex(ValueError, 'Synthetic'):
            analyzer.analyze(self.rows)

    def test_missing_pair_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Missing paired'):
            analyzer.analyze(self.rows[:-1], True)

    def test_duplicates_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            analyzer.analyze(self.rows + [self.rows[0]], True)

    def test_invalid_costs_rejected(self):
        for value in (True, -1, float('nan'), float('inf'), '1'):
            with self.subTest(value=value):
                rows = copy.deepcopy(self.rows)
                rows[0]['attempts'][0]['cost_usd'] = value
                with self.assertRaises(ValueError):
                    analyzer.analyze(rows, True)

    def test_success_must_be_boolean(self):
        self.rows[0]['attempts'][0]['success'] = 'false'
        with self.assertRaisesRegex(ValueError, 'boolean'):
            analyzer.analyze(self.rows, True)

    def test_mixed_provenance_rejected(self):
        self.rows[0]['origin'] = 'observed'
        with self.assertRaisesRegex(ValueError, 'Cannot mix'):
            analyzer.analyze(self.rows, True)

    def test_missing_usage_not_invented(self):
        report = analyzer.analyze(self.rows, True)
        self.assertIsNone(report['variant_totals']['agent']['usage_totals']['input_tokens'])

    def test_repository_balancing_does_not_treat_repeat_as_repository(self):
        extra = copy.deepcopy(self.rows[:2])
        for row in extra:
            row['repository'] = 'second-fixture'
            row['attempts'] = [{'cost_usd': 1.0, 'success': row['variant'] == 'agent'}]
        report = analyzer.analyze(self.rows + extra, True)
        self.assertEqual(report['independent_repository_count'], 2)
        self.assertAlmostEqual(report['repository_balanced_success_delta'], 0.25)
        self.assertEqual(report['paired_deltas_agent_minus_baseline']['success_rate_delta'], 0.0)

    def test_empty_records_rejected(self):
        with self.assertRaisesRegex(ValueError, 'No observations'):
            analyzer.analyze([], True)


if __name__ == '__main__':
    unittest.main()
