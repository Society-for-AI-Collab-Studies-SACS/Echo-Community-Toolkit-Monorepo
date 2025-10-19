import numpy as np

from sigprint.lockin import LockInAmplifier


def test_lockin_detects_8hz_amplitude_with_noise():
    fs = 250
    t = np.arange(fs) / fs
    # 8 Hz tone 30 uV + noise
    x = 30.0 * np.sin(2 * np.pi * 8.0 * t) + 5.0 * np.random.randn(fs)
    li = LockInAmplifier(sample_rate=fs, target_freq=8.0, lowpass_cutoff=2.0)
    I, Q, A, phase = li.process(x)
    assert A > 5.0  # detectable
    assert A < 100.0  # bounded

