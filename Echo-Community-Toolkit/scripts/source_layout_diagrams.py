"""Echo-Community-Toolkit Source Layout Diagrams

Provides small helper functions that return ASCII tree diagrams of the
Echo-Community-Toolkit internal `src/` layout for the three core module
groups: LSB1, MRP (Phase‑A), and G2V (glyph‑to‑volume).

These functions are dependency‑free and return plain strings suitable for
printing, logging, or prompt chaining.
"""

def lsb1_structure_diagram() -> str:
    """Generates an ASCII tree diagram of the LSB1 steganography core modules.

    Focuses on the `lsb_extractor.py` and `lsb_encoder_decoder.py` files in the
    Echo-Community-Toolkit `src/` directory. These implement the core PNG
    decoder and encoder/CLI for the LSB1 protocol.
    """
    diagram = """Echo-Community-Toolkit/src/
├── lsb_extractor.py        # LSB1 PNG decoder
└── lsb_encoder_decoder.py  # LSB1 encoder & CLI
"""
    return diagram


def mrp_structure_diagram() -> str:
    """Generates an ASCII tree diagram of the Multi‑Channel Resonance Protocol (MRP) modules.

    Focuses on the `src/mrp/` package structure within Echo‑Community‑Toolkit.
    Key components include:
    - `headers.py` for the MRP1 header format (magic, flags, length).
    - `channels.py` for channel data structures/utilities (R/G/B handling).
    - `ecc.py` error‑correction helpers (parity/ECC for Phase‑A).
    - `meta.py` metadata helpers (e.g., sidecar JSON assembly).
    - `codec.py` Phase‑A encode/decode orchestration.
    - `adapters/png_lsb.py` PNG LSB adapter bridging to LSB stego.
    - `adapters/wav_lsb.py` WAV LSB adapter (stub).
    """
    diagram = """Echo-Community-Toolkit/src/
└── mrp/
    ├── headers.py       # MRP1 header format
    ├── channels.py      # R/G/B channel utilities
    ├── ecc.py           # Error correction (Phase‑A)
    ├── meta.py          # Metadata helpers / sidecar
    ├── codec.py         # MRP encoder/decoder (Phase‑A)
    └── adapters/
        ├── png_lsb.py   # PNG LSB adapter
        └── wav_lsb.py   # WAV LSB adapter (stub)
"""
    return diagram


def g2v_structure_diagram() -> str:
    """Generates an ASCII tree diagram of the glyph‑to‑volume (G2V) toolkit modules.

    Reflects the current `src/g2v/` contents in Echo‑Community‑Toolkit:
    - `volume.py` for stacking glyphs into volumes, slicing, projections, and glyph synthesis.
    - `fft_codec.py` for frequency‑domain encode/decode (FFT/IFT).
    - `cli.py` command‑line interface for G2V operations.
    """
    diagram = """Echo-Community-Toolkit/src/
└── g2v/
    ├── volume.py       # Volume stack/slice/projection + glyphs
    ├── fft_codec.py    # FFT encode/decode helpers
    └── cli.py          # CLI entry point for G2V commands
"""
    return diagram


if __name__ == "__main__":  # manual preview
    print(lsb1_structure_diagram())
    print(mrp_structure_diagram())
    print(g2v_structure_diagram())
