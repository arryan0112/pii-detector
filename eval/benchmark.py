import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.layers import layer1_regex as l1
from app.layers import layer2_ner as l2
from app.layers import layer3_llm as l3
from app.fusion import analyze


def spans_match(expected_span: str, findings: list) -> bool:
    """Check if expected span appears in any finding — fuzzy match."""
    expected = expected_span.lower().strip()
    for f in findings:
        found = f.text_span.lower().strip() if hasattr(f, 'text_span') else f.get('text_span', '').lower().strip()
        if expected in found or found in expected:
            return True
    return False


def evaluate_layer(cases: list, layer_fn, layer_name: str) -> dict:
    """Evaluate a single layer against test cases."""
    tp = fp = fn = 0
    errors = []

    relevant_cases = [c for c in cases if layer_name in c['detectable_by']]

    for case in relevant_cases:
        try:
            findings = layer_fn(case['text'])
            for expected in case['expected']:
                if spans_match(expected['text_span'], findings):
                    tp += 1
                else:
                    fn += 1
                    errors.append({
                        'id': case['id'],
                        'missed': expected['text_span'],
                        'text': case['text']
                    })
            # Count false positives — findings not in expected
            for f in findings:
                span = f.text_span if hasattr(f, 'text_span') else f.get('text_span', '')
                if not any(
                    span.lower() in e['text_span'].lower() or
                    e['text_span'].lower() in span.lower()
                    for e in case['expected']
                ):
                    fp += 1
        except Exception as e:
            errors.append({'id': case['id'], 'error': str(e)})

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1        = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return {
        'layer': layer_name,
        'test_cases': len(relevant_cases),
        'tp': tp, 'fp': fp, 'fn': fn,
        'precision': round(precision * 100, 1),
        'recall':    round(recall * 100, 1),
        'f1':        round(f1 * 100, 1),
        'missed': errors
    }


def evaluate_full_pipeline(cases: list) -> dict:
    """Evaluate the full 3-layer pipeline."""
    tp = fp = fn = 0

    for case in cases:
        try:
            result = analyze(case['text'], run_llm=True)
            for expected in case['expected']:
                if spans_match(expected['text_span'], result.findings):
                    tp += 1
                else:
                    fn += 1
        except Exception:
            fn += len(case['expected'])

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1        = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return {
        'layer': 'full pipeline',
        'test_cases': len(cases),
        'tp': tp, 'fp': fp, 'fn': fn,
        'precision': round(precision * 100, 1),
        'recall':    round(recall * 100, 1),
        'f1':        round(f1 * 100, 1),
    }


def print_results(results: list):
    print("\n" + "=" * 60)
    print("BENCHMARK RESULTS")
    print("=" * 60)
    print(f"{'Layer':<20} {'Cases':<8} {'Precision':<12} {'Recall':<10} {'F1':<8}")
    print("-" * 60)
    for r in results:
        print(f"{r['layer']:<20} {r['test_cases']:<8} {r['precision']:<12} {r['recall']:<10} {r['f1']:<8}")
    print("=" * 60)

    print("\nMISSED FINDINGS:")
    for r in results:
        if r.get('missed'):
            print(f"\n  [{r['layer']}]")
            for m in r['missed'][:3]:
                if 'missed' in m:
                    print(f"    - {m['id']}: missed '{m['missed']}'")


if __name__ == "__main__":
    cases = json.load(open("eval/test_cases.json"))
    print(f"Loaded {len(cases)} test cases")
    print("Running benchmark — LLM layer will take ~60 seconds due to rate limiting...")

    results = []

    print("\n[1/4] Evaluating Layer 1 (regex)...")
    results.append(evaluate_layer(cases, l1.detect, "regex"))

    print("[2/4] Evaluating Layer 2 (NER)...")
    results.append(evaluate_layer(cases, l2.detect, "ner"))

    print("[3/4] Evaluating Layer 3 (LLM)...")
    results.append(evaluate_layer(cases, l3.detect, "llm"))

    print("[4/4] Evaluating full pipeline...")
    results.append(evaluate_full_pipeline(cases))

    print_results(results)

    # Save results
    with open("eval/results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nResults saved to eval/results.json")