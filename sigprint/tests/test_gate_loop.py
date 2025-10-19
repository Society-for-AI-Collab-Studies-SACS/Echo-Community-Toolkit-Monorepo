from datetime import datetime, timedelta

from sigprint.gate_loop import GateLoopDetector, PatternAnalyzer


def test_gate_detection_with_large_change():
    det = GateLoopDetector(gate_threshold=0.2)
    det.add_code("12345678901234567890")
    res = det.add_code("12345678901234567890")
    assert not res["gate_detected"]
    res2 = det.add_code("98765432109876543210")
    assert res2["gate_detected"]
    assert res2["gate_info"]["distance"] > 0.2


def test_loop_detection_periodic_pattern():
    det = GateLoopDetector(loop_threshold=0.95, history_size=100, min_loop_period=2, max_loop_period=5)
    pattern = ["11111111111111111111", "22222222222222222222", "33333333333333333333"]
    # Warm up baseline
    for _ in range(3):
        det.add_code(pattern[0])
    found = False
    for _ in range(5):
        for c in pattern:
            out = det.add_code(c)
            if out["loop_detected"]:
                found = True
                assert 2 <= out["loop_info"]["period"] <= 5
                break
        if found:
            break
    assert found


def test_predict_next_code_in_strong_loop():
    det = GateLoopDetector(loop_threshold=0.99, min_loop_period=2, max_loop_period=3)
    cyc = ["AAAA", "BBBB", "CCCC"]
    for _ in range(3):
        for c in cyc:
            det.add_code(c)
    nxt = det.predict_next_code()
    assert nxt in cyc


def test_pattern_analyzer_summary_fields():
    pa = PatternAnalyzer()
    seq = ["1010"] * 5 + ["2020"] * 3 + ["1010"] * 5
    res = pa.analyze_sequence(seq)
    assert res["total_codes"] == len(seq)
    assert 0.0 <= res["entropy"] <= 1.0
    assert 0.0 <= res["complexity"] <= 1.0

