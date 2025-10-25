from echo_soulcode.hilbert import normalize, HilbertState, phase_shift, dominant_frequency

def test_norm():
    a,b,g = normalize(0.58,0.39,0.63)
    assert abs((a*a+b*b+g*g) - 1.0) < 1e-9

def test_phase_frequency():
    a,b,g = normalize(1,1,1)
    assert 0.0 <= dominant_frequency(b, g, f0=13.0) <= 13.0
    assert isinstance(phase_shift(a,b,g), float)
