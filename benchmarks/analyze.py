#!/usr/bin/env python3
"""Validate paired run records and produce descriptive, non-inferential summaries."""
import argparse
import json
import math
from pathlib import Path

VARIANTS = ('baseline', 'agent')
TOKENS = ('input_tokens', 'cached_input_tokens', 'output_tokens', 'tool_calls')


def number(value, label, integer=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{label} must be a number, not a boolean')
    if not math.isfinite(value) or value < 0:
        raise ValueError(f'{label} must be finite and nonnegative')
    if integer and not isinstance(value, int):
        raise ValueError(f'{label} must be an integer')


def validate(records, allow_synthetic=False):
    if not records:
        raise ValueError('No observations')
    seen = set()
    origins = set()
    pairs = {}
    for index, row in enumerate(records, 1):
        if not isinstance(row, dict):
            raise ValueError(f'Row {index} must be an object')
        for field in ('repository', 'task', 'model'):
            if not isinstance(row.get(field), str) or not row[field].strip():
                raise ValueError(f'Row {index}: {field} must be a nonempty string')
        number(row.get('repeat'), f'Row {index}: repeat', integer=True)
        variant = row.get('variant')
        if variant not in VARIANTS:
            raise ValueError(f'Row {index}: variant must be baseline or agent')
        origin = row.get('origin')
        if origin not in ('observed', 'synthetic'):
            raise ValueError(f'Row {index}: origin must be observed or synthetic')
        if origin == 'synthetic' and not allow_synthetic:
            raise ValueError('Synthetic fixture requires --allow-synthetic')
        origins.add(origin)
        key = tuple(row[k] for k in ('repository', 'task', 'model', 'repeat'))
        full_key = key + (variant,)
        if full_key in seen:
            raise ValueError(f'Duplicate observation: {full_key}')
        seen.add(full_key)
        pairs.setdefault(key, {})[variant] = row
        attempts = row.get('attempts')
        if not isinstance(attempts, list) or not attempts:
            raise ValueError(f'Row {index}: attempts must be a nonempty list')
        for attempt in attempts:
            if not isinstance(attempt, dict):
                raise ValueError(f'Row {index}: attempt must be an object')
            if not isinstance(attempt.get('success'), bool):
                raise ValueError(f'Row {index}: success must be a boolean')
            number(attempt.get('cost_usd'), f'Row {index}: cost_usd')
            for field in TOKENS:
                if field in attempt:
                    number(attempt[field], f'Row {index}: {field}', integer=True)
    if len(origins) != 1:
        raise ValueError('Cannot mix synthetic and observed runs')
    for key, pair in pairs.items():
        if set(pair) != set(VARIANTS):
            raise ValueError(f'Missing paired variant: {key}')
    return pairs


def cost(row):
    return math.fsum(attempt['cost_usd'] for attempt in row['attempts'])


def success(row):
    return any(attempt['success'] for attempt in row['attempts'])


def summarize(rows):
    successes = sum(success(row) for row in rows)
    total_cost = math.fsum(cost(row) for row in rows)
    attempts = [attempt for row in rows for attempt in row['attempts']]
    return {
        'episodes': len(rows),
        'attempts': len(attempts),
        'failed_attempts': sum(not attempt['success'] for attempt in attempts),
        'verified_successes': successes,
        'success_rate': successes / len(rows),
        'total_cost_usd': total_cost,
        'cost_per_success_usd': total_cost / successes if successes else None,
        'usage_totals': {
            field: sum(a[field] for a in attempts) if all(field in a for a in attempts) else None
            for field in TOKENS
        },
    }


def paired_summary(pairs):
    values = list(pairs)
    return {
        'pairs': len(values),
        'success_rate_delta': sum(int(success(p['agent'])) - int(success(p['baseline'])) for p in values) / len(values),
        'mean_episode_cost_delta_usd': math.fsum(cost(p['agent']) - cost(p['baseline']) for p in values) / len(values),
        'agent_only_successes': sum(success(p['agent']) and not success(p['baseline']) for p in values),
        'baseline_only_successes': sum(success(p['baseline']) and not success(p['agent']) for p in values),
    }


def analyze(records, allow_synthetic=False):
    pairs = validate(records, allow_synthetic)
    by_repository = {}
    for repository in sorted({key[0] for key in pairs}):
        subset = [pair for key, pair in pairs.items() if key[0] == repository]
        by_repository[repository] = paired_summary(subset)
    return {
        'origin': records[0]['origin'],
        'interpretation': 'Descriptive only. Repeats and tasks are not independent repositories. No confidence intervals or causal efficacy claim.',
        'variant_totals': {variant: summarize([r for r in records if r['variant'] == variant]) for variant in VARIANTS},
        'paired_deltas_agent_minus_baseline': paired_summary(pairs.values()),
        'by_repository': by_repository,
        'by_model': {model: paired_summary([p for key, p in pairs.items() if key[2] == model]) for model in sorted({key[2] for key in pairs})},
        'repository_balanced_success_delta': sum(r['success_rate_delta'] for r in by_repository.values()) / len(by_repository),
        'repository_balanced_cost_delta_usd': math.fsum(r['mean_episode_cost_delta_usd'] for r in by_repository.values()) / len(by_repository),
        'independent_repository_count': len(by_repository),
    }


def load(path):
    records = []
    with Path(path).open(encoding='utf-8') as stream:
        for line_number, line in enumerate(stream, 1):
            if line.strip():
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as error:
                    raise ValueError(f'Invalid JSON at line {line_number}: {error.msg}') from error
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('results')
    parser.add_argument('--allow-synthetic', action='store_true')
    args = parser.parse_args()
    try:
        report = analyze(load(args.results), args.allow_synthetic)
    except (OSError, ValueError) as error:
        parser.exit(2, f'error: {error}\n')
    print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
