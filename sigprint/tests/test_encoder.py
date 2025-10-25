import re
import numpy as np

from sigprint.encoder import SigprintEncoder, compute_checksum


def test_sigprint_code_format_and_checksum():
    sr = 250
    t = np.arange(sr) / sr
    f = 8.0

    # Build a simple 1s epoch: four channels with 8 Hz tones
    # F3 and F4 slightly out of phase, Oz stronger amp, Pz weaker
    epoch = {
        "F3": np.sin(2 * np.pi * f * t + 0.0),
        "F4": np.sin(2 * np.pi * f * t + np.deg2rad(10.0)),
        "Oz": 2.0 * np.sin(2 * np.pi * f * t + np.deg2rad(5.0)),
        "Pz": 0.2 * np.sin(2 * np.pi * f * t + np.deg2rad(20.0)),
    }

    enc = SigprintEncoder(["F3", "F4", "Pz", "Oz"], sample_rate=sr, lockin_freq=f)
    code = enc.process_epoch(epoch)

    assert isinstance(code, str)
    assert len(code) == 20
    assert re.fullmatch(r"\d{20}", code)

    # Validate checksum: last two digits should equal sum(first 18) % 97
    digits = [int(c) for c in code]
    s = sum(digits[:18]) % 97
    assert digits[18] * 10 + digits[19] == s


def test_gate_detection_distance_changes():
    sr = 250
    t = np.arange(sr) / sr
    f = 8.0
    enc = SigprintEncoder(["F3", "F4"], sample_rate=sr, lockin_freq=f)

    epoch1 = {
        "F3": np.sin(2 * np.pi * f * t + 0.0),
        "F4": np.sin(2 * np.pi * f * t + 0.0),
    }
    epoch2 = {
        "F3": np.sin(2 * np.pi * f * t + np.deg2rad(90.0)),
        "F4": np.sin(2 * np.pi * f * t + np.deg2rad(180.0)),
    }

    c1 = enc.process_epoch(epoch1)
    c2 = enc.process_epoch(epoch2)

def test_reserved_digits_injection():
    sr = 250
    t = np.arange(sr) / sr
    f = 8.0
    epoch = {
        "F3": np.sin(2 * np.pi * f * t + 0.0),
        "F4": np.sin(2 * np.pi * f * t + 0.0),
    }
    enc = SigprintEncoder(["F3", "F4"], sample_rate=sr, lockin_freq=f)
    code_default = enc.process_epoch(epoch)
    code_stage5 = enc.process_epoch(epoch, reserved_digits=[0, 5])
    assert len(code_default) == 20 and len(code_stage5) == 20
    # Digits 13-14 reside at indices 12 and 13
    assert code_stage5[12:14] != code_default[12:14]
    # Ensure codes differ by at least one digit
    assert code_default != code_stage5
