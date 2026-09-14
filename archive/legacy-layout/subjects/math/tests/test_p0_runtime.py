import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'src'))
import p0_runtime as p0

BASE = REPO
pacing = json.loads((BASE / 'knowledge/curriculum/ccs-2026-2027/pacing.json').read_text())
manifest = json.loads((BASE / 'config/template-manifest.json').read_text())
standards = json.loads((BASE / 'knowledge/curriculum/nc-math/standards-cache.json').read_text())



def test_enabled_grade_cache_coverage():
    expected = {'grade_1', 'grade_4', 'grade_5', 'grade_6', 'math_1', 'math_2'}
    assert expected.issubset(set(standards['grades']))
    assert '2026-08-24' in pacing['weeks']
    assert expected.issubset(set(pacing['weeks']['2026-08-24']))


def test_curriculum_cache():
    r = p0.resolve_curriculum(pacing, 'grade_6', '2026-08-24')
    assert r['cache_hit'] is True
    assert r['source'] == 'weekly_cache'
    assert 'NC.6.RP.1' in r['current']
    assert r['confidence'] == 'inferred'

    fallback = p0.resolve_curriculum(pacing, 'grade_6', '2026-08-31')
    assert fallback['cache_hit'] is True
    assert fallback['source'] == 'month_cache'
    assert fallback['requires_weekly_resolution'] is True

    miss = p0.resolve_curriculum(pacing, 'grade_6', '2026-09-07')
    assert miss['cache_hit'] is False
    assert miss['requires_web_resolution'] is True


def test_math_verifier():
    assert p0.compute('arithmetic_expression', {'expression': '4.8 + 2.35'}) == 7.15
    assert p0.compute('triangle_area', {'base': 12, 'height': 9}) == 54
    assert p0.compute('rect_prism_surface_area', {'length': 10, 'width': 4, 'height': 3}) == 164
    assert p0.compute('gcf', {'a': 18, 'b': 24}) == 6
    assert p0.compute('lcm', {'a': 6, 'b': 8}) == 24
    assert p0.compute('midpoint', {'x1': -2, 'y1': 6, 'x2': 4, 'y2': -2}) == (1, 2)
    assert p0.equivalent(p0.compute('distance', {'x1': 1, 'y1': 2, 'x2': 7, 'y2': 10}), 10)
    assert p0.compute('linear_eval', {'m': 2, 'x': 7, 'b': -3}) == 11
    assert p0.compute('quadratic_eval', {'a': 1, 'b': -4, 'c': 3, 'x': 5}) == 8


def sample_spec():
    return {
        'worksheet': {
            'grade': 'Grade 6',
            'title': 'MTS - CLASS WORKSHEET',
            'week_start': '2026-08-24',
            'question_count': 3,
            'duration_minutes': 15,
        },
        'curriculum': {'current': ['NC.6.RP.1'], 'confidence': 'inferred'},
        'sections': [{
            'id': 'A', 'title': 'RATIO BASICS', 'questions': [
                {'number': 1, 'prompt': 'Find 3 + 4.', 'answer': 7, 'skill': 'arithmetic', 'difficulty': 'easy',
                 'verification': {'method': 'arithmetic_expression', 'inputs': {'expression': '3+4'}}},
                {'number': 2, 'prompt': 'Area of triangle b=8, h=5.', 'answer': 20, 'skill': 'triangle_area', 'difficulty': 'easy',
                 'verification': {'method': 'triangle_area', 'inputs': {'base': 8, 'height': 5}}},
                {'number': 3, 'prompt': 'Explain a ratio.', 'answer': 'reasoning', 'skill': 'ratio_reasoning', 'difficulty': 'medium'},
            ]
        }],
        'verification': {'status': 'PENDING'},
    }


def test_spec_and_targeted_qa():
    spec = sample_spec()
    v = p0.verify_spec(spec)
    assert v['status'] == 'PASS'
    assert v['deterministic_checked'] == 2
    assert v['reasoning_required'] == 1

    bad = sample_spec()
    bad['sections'][0]['questions'][1]['answer'] = 21
    vb = p0.verify_spec(bad)
    assert vb['status'] == 'FAIL'
    assert vb['failures'][0]['number'] == 2

    text = 'MTS - CLASS WORKSHEET\nGrade 6\n1. Find 3 + 4.\n2. Area...\n3. Explain...'
    qa = p0.targeted_text_qa_v2(text, spec)
    assert qa['status'] == 'PASS', qa

    stale = text + '\n4. stale template question'
    qa2 = p0.targeted_text_qa_v2(stale, spec)
    assert qa2['status'] == 'FAIL'
    assert 'no_extra_numbered_slots' in qa2['failed_checks']


def test_targeted_qa_uses_grade_display_name_when_present():
    spec = sample_spec()
    spec['worksheet']['grade'] = 'grade_5'
    spec['worksheet']['grade_display_name'] = 'Grade 5'
    text = 'MTS - CLASS WORKSHEET\nGrade 5\n1. Find 3 + 4.\n2. Area...\n3. Explain...'
    assert p0.targeted_text_qa_v2(text, spec)['status'] == 'PASS'

    legacy = sample_spec()
    legacy['worksheet']['grade'] = 'grade_5'
    legacy_text = 'MTS - CLASS WORKSHEET\ngrade_5\n1. Find 3 + 4.\n2. Area...\n3. Explain...'
    assert p0.targeted_text_qa_v2(legacy_text, legacy)['status'] == 'PASS'


def test_template_cache_guard():
    hit = p0.template_cache_valid(manifest, '3', '2')
    assert hit['status'] == 'HIT'
    miss = p0.template_cache_valid(manifest, '4', '2')
    assert miss['status'] == 'MISS'
    assert miss['checks']['worksheet_revision_matches'] is False


def test_telemetry():
    t = p0.Telemetry()
    t.start_stage('verification')
    time.sleep(0.001)
    t.end_stage('verification')
    t.cache_hits = 2
    t.cache_misses = 1
    d = t.as_dict()
    assert d['stage_seconds']['verification'] >= 0
    assert d['cache_hits'] == 2
    assert d['cache_misses'] == 1
    assert 'token_usage' in d


def main():
    tests = [
        test_enabled_grade_cache_coverage,
        test_curriculum_cache,
        test_math_verifier,
        test_spec_and_targeted_qa,
        test_targeted_qa_uses_grade_display_name_when_present,
        test_template_cache_guard,
        test_telemetry,
    ]
    for test in tests:
        test()
        print('PASS', test.__name__)
    print(f'ALL_PASS {len(tests)}/{len(tests)}')


if __name__ == '__main__':
    main()
