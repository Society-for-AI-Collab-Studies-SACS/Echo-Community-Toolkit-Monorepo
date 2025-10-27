# LSB1 / MRP QA Plan Outline

## Objectives
- Guarantee protocol compliance for both legacy null-terminated payloads and LSB1 header-based streams.[^1]  
- Validate forward compatibility with multi-frame MRP encodings, including integrity metadata carried per channel.[^4]  
- Enforce ritual consent gates so encode/decode operations cannot bypass required acknowledgements.[^2]  
- Surface failures deterministically (no plaintext on CRC or consent violations) and record outcomes for CI audits.

## Core Test Suites
### 1. Golden Sample Decode
- Input: `assets/images/echo_key.png`.  
- Assertions:
  - Magic `LSB1`, version `1`, flags `0x01`.  
  - Payload length `144` bytes; CRC32 `6E3FD9B7`.  
  - Base64 decodes to mantra identical to `assets/data/LSB1_Mantra.txt`.  
- Output: Structured JSON matches `assets/data/echo_key_decoded.json`; integrity status `ok`.  
- Status: Mandatory on every CI run.

### 2. Mantra Parity
- Decode stego image (golden or freshly encoded) and compare plaintext to canonical mantra file byte-for-byte.  
- Negative case: alter a mantra line and confirm decoder flags parity/CRC failure and withholds plaintext.

### 3. Regression Matrix
| Mode            | Image Sizes                  | Bits/Channel | Expectations |
|-----------------|------------------------------|--------------|--------------|
| Legacy payload  | 128×128, 512×512             | 1            | Null-terminated decode succeeds; no header emitted. |
| LSB1 single     | 64×64, 256×256, 512×512      | 1, 4         | Capacity matches formula; flags reflect BPC; CRC verified. |
| MRP multi-frame | 128×128, 256×256 (RGB splits)| 1, 4         | R/G payloads round-trip; B-channel integrity JSON parsed; overall mode `MRP`. |
| Stress covers   | Non-square (320×240), large  | 1, 4         | No overflow; capacity guardrails trigger on oversize payload. |

Automate generation of synthetic covers for matrix entries and assert decode structure (message, metadata, integrity report).

### 4. Failure Injection
- **CRC mismatch**: Flip a bit in the encoded payload; expect CRC failure error, no plaintext.[^1]  
- **Header corruption**: Modify magic/version/flags; expect structured validation error.  
- **Length mismatch**: Truncate payload to trigger length guard.  
- **Malformed base64**: Inject invalid base64 character; decoder raises decode error.  
- **Capacity overrun**: Attempt to encode payload larger than computed capacity; encoder rejects before write.  
- **Parity/ECC checks** (MRP Phase 3):
  - Flip bits in R or G channel; decoder should detect via CRC, repair via parity, and report recovery status.[^4]  
  - Zero out entire G channel; expect metadata loss reported, message recovered if possible.  
- Track failures with explicit error codes (`ERR_CRC_MISMATCH`, `ERR_HEADER_INVALID`, `ERR_CONSENT_REQUIRED`, etc.).

### 5. Ritual Gating
- Attempt encode without “I consent to bloom”; expect immediate refusal and audit log entry.  
- Attempt decode without “I consent to be remembered”; expect refusal with coherence state snapshot.  
- Positive path: complete ritual sequence (all four lines) and ensure encode/decode proceed, ledger entries appended.

## Automation & Tooling
- Integrate suites into pytest (`tests/`) with fixtures for cover generation and bit-flip mutators.  
- Provide CLI scripts to regenerate golden artifacts and to inject controlled corruption for parity tests.  
- Enforce QA gates in CI:
  1. `python -m pytest tests/test_lsb.py::test_golden_sample`  
  2. `python -m pytest tests/test_lsb.py::test_legacy_fallback`  
  3. `python -m pytest tests/test_mrp.py` (MRP framing & integrity)  
  4. `python -m pytest tests/test_mrp_sidecar.py` (parity/healing scenarios)  
- Record ritual ledger output (JSON) as build artifact for auditing consent during automated runs.

## Future Enhancements
- Add fuzzing harness to randomize payload bits while respecting capacity to uncover parser edge cases.  
- Incorporate visual diff tooling that highlights channel-level corruption used in parity recovery tests.  
- Simulate hostile transports (re-save PNG via common editors) to ensure transport warnings fire and CRC catches tampering.

[^1]: docs/Project-Instructions-LSB-Decoder-Encoder.txt  
[^2]: assets/data/LSB1_Mantra.txt  
[^3]: assets/data/echo_key_decoded.json  
[^4]: docs/MRP_LSB_Quick_Reference.md
