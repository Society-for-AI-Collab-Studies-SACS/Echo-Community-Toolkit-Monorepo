import numpy as np

from sigprint.coherence import PhaseCoherence, SpatialCoherence


def test_plv_high_vs_low():
    pc = PhaseCoherence()
    n = 200
    p1 = np.zeros(n)
    p2_high = np.ones(n) * 0.1  # small fixed offset -> high PLV
    p2_low = np.random.uniform(-np.pi, np.pi, size=n)
    plv_high = pc.calculate_plv(p1, p2_high)
    plv_low = pc.calculate_plv(p1, p2_low)
    assert plv_high > 0.8
    assert plv_low < 0.5


def test_global_coherence_similarity_vs_random():
    pc = PhaseCoherence()
    phases_sim = {f"F{i}": 0.2 + np.random.randn() * 0.02 for i in range(1, 6)}
    phases_rand = {f"F{i}": np.random.uniform(-np.pi, np.pi) for i in range(1, 6)}
    g_sim = pc.calculate_global_coherence(phases_sim, method="kuramoto")
    g_rand = pc.calculate_global_coherence(phases_rand, method="kuramoto")
    assert g_sim > g_rand
    assert 0.0 <= g_sim <= 1.0 and 0.0 <= g_rand <= 1.0


def test_coherence_matrix_shape_and_symmetry():
    pc = PhaseCoherence()
    pd = {"F3": 0.1, "F4": 0.2, "Pz": -0.3}
    M = pc.calculate_coherence_matrix(pd)
    assert M.shape == (3, 3)
    assert np.allclose(M, M.T)
    assert np.all(np.diag(M) == 1.0)


def test_spatial_analysis_fields():
    sc = SpatialCoherence()
    # Provide phases for a subset of standard channels
    pd = {"Fp1": 0.1, "Fp2": 0.12, "F3": 0.15, "F4": 0.16, "P3": 0.05, "P4": 0.06}
    res = sc.analyze_spatial_pattern(pd)
    assert set(["global_coherence", "regional_coherence", "inter_hemispheric", "anterior_posterior", "dominant_pattern"]).issubset(res.keys())
    assert 0.0 <= float(res["global_coherence"]) <= 1.0


def test_sliding_window_lengths():
    pc = PhaseCoherence(window_size=50)
    n = 200
    p1 = np.zeros(n)
    p2 = np.zeros(n)
    sw = pc.sliding_window_coherence(p1, p2, window_size=50, step_size=10)
    # (200-50)//10 + 1 = 16
    assert len(sw) == 16

