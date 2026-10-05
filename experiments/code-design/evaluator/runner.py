#!/usr/bin/env python3
"""Run frozen prompt-derived acceptance tests against one candidate directory."""
import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import time
import traceback
import types
import unittest


EVALUATOR_DIR = Path(__file__).resolve().parent


def load_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f'Cannot load {path}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_ids(suite):
    for entry in suite:
        if isinstance(entry, unittest.TestSuite):
            yield from test_ids(entry)
        else:
            yield entry.id()


def source_hashes():
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(EVALUATOR_DIR.glob('*.py'))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--domain', required=True, choices=['inventory', 'pricing'])
    parser.add_argument('--stage', required=True, type=int, choices=[1, 2])
    parser.add_argument('--arm', type=Path, help='Directory containing inventory.py or pricing.py')
    parser.add_argument('--list', action='store_true', help='List tests without importing candidate code')
    args = parser.parse_args()
    if not args.list and args.arm is None:
        parser.error('--arm is required unless --list is used')

    started = time.perf_counter()
    candidate = types.ModuleType('candidate')
    candidate.module = None
    sys.modules['candidate'] = candidate
    captured_stdout, captured_stderr = io.StringIO(), io.StringIO()
    report = dict(domain=args.domain, stage=args.stage,
                  arm=str(args.arm.resolve()) if args.arm else None,
                  evaluator_sha256=source_hashes(), tests_run=0, failures=[], errors=[])
    try:
        with contextlib.redirect_stdout(captured_stdout), contextlib.redirect_stderr(captured_stderr):
            if not args.list:
                arm = args.arm.resolve()
                sys.path.insert(0, str(arm))
                # Each CLI invocation is a fresh interpreter. Explicit path loading
                # also prevents accidental import from evaluator's working directory.
                candidate.module = load_file(args.domain, arm / f'{args.domain}.py')
            tests = load_file(f'acceptance_{args.domain}', EVALUATOR_DIR / f'test_{args.domain}.py')
            loader = unittest.TestLoader()
            suite = unittest.TestSuite()
            prefix = args.domain.capitalize()
            suite.addTests(loader.loadTestsFromTestCase(getattr(tests, f'{prefix}Stage1Tests')))
            if args.stage == 2:
                suite.addTests(loader.loadTestsFromTestCase(getattr(tests, f'{prefix}Stage2Tests')))
            if args.list:
                report['test_ids'] = list(test_ids(suite))
                report['tests_expected'] = suite.countTestCases()
                report['mode'] = 'list_only_no_candidate_import'
                success = True
            else:
                result = unittest.TestResult()
                suite.run(result)
                report['tests_run'] = result.testsRun
                report['failures'] = [{'test_id': test.id(), 'detail': detail}
                                      for test, detail in result.failures]
                report['errors'] = [{'test_id': test.id(), 'detail': detail}
                                    for test, detail in result.errors]
                report['skipped'] = [{'test_id': test.id(), 'reason': reason}
                                     for test, reason in result.skipped]
                report['expected_failures'] = [{'test_id': test.id(), 'detail': detail}
                                               for test, detail in result.expectedFailures]
                report['unexpected_successes'] = [test.id() for test in result.unexpectedSuccesses]
                success = result.wasSuccessful() and not result.skipped and not result.expectedFailures
    except BaseException:
        report['errors'].append({'test_id': f'{args.domain}.import_or_runner',
                                 'detail': traceback.format_exc()})
        success = False
    report['successful'] = success
    report['duration_seconds'] = round(time.perf_counter() - started, 6)
    report['captured_stdout'] = captured_stdout.getvalue()
    report['captured_stderr'] = captured_stderr.getvalue()
    print(json.dumps(report, sort_keys=True))
    return 0 if success else 1


if __name__ == '__main__':
    raise SystemExit(main())
