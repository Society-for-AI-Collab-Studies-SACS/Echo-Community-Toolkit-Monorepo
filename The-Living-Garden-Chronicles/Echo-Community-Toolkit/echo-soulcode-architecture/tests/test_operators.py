from echo_soulcode.hilbert import normalize, to_complex
from echo_soulcode.operators import H_ECHO, bra_ket_expectation

def test_expectation_real_nonzero():
    a,b,g = normalize(0.58,0.39,0.63)
    v = to_complex(a,b,g, 0.0, 0.1, -0.2)
    val = bra_ket_expectation(H_ECHO, v)
    assert val.real != 0.0
