SIGPRINT Encoder (8 Hz Alpha)

Overview
- Computes a 20-digit signature per ~1s EEG epoch using a simple software lock-in at 8 Hz per channel, plus global phase coherence and amplitude distribution features.
- Intended to run alongside a voice journaling CLI; call `SigprintEncoder.process_epoch(...)` to produce a signature for the current moment and store it with the transcript.

Quick Start
- Create an encoder and feed a 1-second epoch (dict[str, np.ndarray]):

  ```python
  import numpy as np
  from sigprint.encoder import SIGPRINTEncoder

  sr = 250
  t = np.arange(sr) / sr
  f = 8.0
  epoch = {
      "F3": np.sin(2*np.pi*f*t + 0.0),
      "F4": np.sin(2*np.pi*f*t + np.deg2rad(10.0)),
      "Oz": 2.0*np.sin(2*np.pi*f*t + np.deg2rad(5.0)),
      "Pz": 0.2*np.sin(2*np.pi*f*t + np.deg2rad(20.0)),
  }
  enc = SIGPRINTEncoder(["F3", "F4", "Pz", "Oz"], sample_rate=sr, lockin_freq=f)
  res = enc.process_epoch(epoch)  # returns SigprintResult
  print(res.code)  # 20-digit signature
  ```

Bazel
- Test the module: `bazel test //sigprint:encoder_tests`
- Advanced lock-in: `bazel test //sigprint:lockin_tests`
 - Coherence and gate/loop: `bazel test //sigprint:coherence_tests //sigprint:gate_loop_tests`

Advanced Lock-in (optional SciPy)
- The lock-in module (`sigprint/lockin.py`) uses SciPy if available for Butterworth filtering.
- Without SciPy, it falls back to an exponential low-pass and still works for prototyping.

Notes
- The checksum is `sum(first 18 digits) % 97` rendered as two digits.
- Regional distribution uses a simple mapping: channels starting with `F` -> frontal, `O` -> occipital.
- Loop/Gate detection compares successive codes with a Hamming distance, threshold = 5.
 - Additional modules: `sigprint/coherence.py` (global/regional coherence), `sigprint/gate_loop.py` (gate/loop detector).
