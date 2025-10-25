# Running the Glyph‑to‑Volume Toolkit (LLM Guide)

This guide explains how to run the Glyph‑to‑Volume (g2v) toolkit in this
repository.  It is intended for language‑model‑based agents that need
deterministic instructions for building, testing and executing the code
without access to external internet resources.

## 1. Repository structure

The key directories and files are:

| Path              | Purpose                                                    |
|-------------------|------------------------------------------------------------|
| `src/g2v/`        | Python package with volume, FFT, phase, metrics and CLI    |
| `examples/`       | Runnable example scripts demonstrating usage               |
| `tests/`          | Pytest suite for volume operations and FFT round‑trip       |
| `docs/`           | Design notes and Tink binding guidelines                  |
| `Makefile`        | Convenience targets for setup, tests and examples         |
| `pyproject.toml`  | Project metadata and dependency specification             |
| `README.md`       | Overview of the toolkit and expanded features             |

## 2. Setting up a virtual environment

1. Create a virtual environment (this isolates dependencies):

       python -m venv .venv

2. Activate the virtual environment (on Unix shells):

       . .venv/bin/activate

3. Install dependencies in editable mode:

       pip install -U pip
       pip install -e .

   This reads `pyproject.toml` and installs the `numpy` dependency along
   with the `g2v` package itself.

## 3. Running the test suite

After activating the virtual environment and installing dependencies, run:

    pytest -q

The suite includes tests for volume stacking, slicing, projection and
FFT encode/decode.  All tests should pass without warnings.

## 4. Using the command‑line interface

The package installs a `g2v` command when installed via `pip`.  You can
invoke it as follows:

1. Stack glyphs into a volume:

       g2v stack --out volume.npy glyph1.npy glyph2.npy

2. Extract a layer from a volume:

       g2v slice volume.npy --z 0 --out layer0.npy

3. Project a volume through an angle:

       g2v project volume.npy --theta 45 --axis x --out proj.npy

4. Perform an FFT round‑trip:

       g2v fft glyph.npy --out-recon recon.npy --out-spec spec.npy

The CLI prints a JSON summary upon completion of each command.

## 5. Running the example script

The `examples/demo_stack_and_project.py` script demonstrates how to use
the high‑level API to construct a volume from Tink concepts, slice it and
project it.  Run it with:

    python examples/demo_stack_and_project.py

It creates several `.npy` files in `examples/data/` and prints the path
where they are saved.

## 6. Repository export

The entire repository can be bundled into a ZIP archive for transfer.  To
create a ZIP file named `g2v_repo.zip` including all files and folders in
the repository root, run:

    zip -r g2v_repo.zip .

This will produce a single archive containing the full directory tree.
Ensure you execute this command from the root of the repository so that
no files are excluded.

## 7. Notes on Tink integration

If your workflow involves Tink 1.txt, consult `docs/TINK_NOTES.md` for
examples on mapping named concepts (e.g. I‑Glyph, Octave Cycle Drive)
into glyph patterns via `g2v.volume.glyph_from_tink_token`.  These
mappings can be customised to reflect specific semantics.

