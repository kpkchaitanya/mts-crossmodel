import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))
from mts.subjects.math import p0_runtime as p0

BACKBONE = REPO / 'data/master/subjects/math/curriculum/progressive/progressive-math-backbone.json'
PACING = REPO / 'data/master/subjects/math/curriculum/ccs-2026-2027/pacing.json'


def test_backbone_structure():
    d = json.loads(BACKBONE.read_text(encoding='utf-8'))
    assert d['standards_included'] is False
    assert d['provenance']['not_official_ccs_pacing'] is True
    assert len(d['unit_families']) == 6
    assert set(d['grades']) == {f'grade_{i}' for i in range(1, 13)}
    for i in range(1, 13):
        g = d['grades'][f'grade_{i}']
        assert len(g['units']) == 6
        for u in g['units'].values():
            assert u['unit_name']
            assert len(u['key_concepts']) >= 3
            assert u['progression']
            assert 'builds_from' in u and 'leads_to' in u


def test_runtime_integration():
    d = json.loads(BACKBONE.read_text(encoding='utf-8'))
    pacing = json.loads(PACING.read_text(encoding='utf-8'))
    for grade, expected in [('grade_1', 1), ('grade_6', 6), ('math_1', 9), ('math_2', 10)]:
        r = p0.resolve_curriculum(pacing, grade, '2026-08-24', d)
        assert r['progressive_context']['grade'] == expected
        assert len(r['progressive_context']['units']) == 6
        assert r['progressive_context']['official_ccs_pacing'] is False


def main():
    tests = [test_backbone_structure, test_runtime_integration]
    for t in tests:
        t(); print('PASS', t.__name__)
    print(f'ALL_PASS {len(tests)}/{len(tests)}')

if __name__ == '__main__':
    main()

