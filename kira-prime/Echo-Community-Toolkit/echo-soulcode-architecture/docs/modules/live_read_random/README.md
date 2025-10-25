# Randomized Live Read (Dirichlet)

This agent reproduces the user-provided live-read behavior with randomized Hilbert coefficients
(Dirichlet sampling), generating four blocks (squirrel, fox, paradox, echo superposition), and
stamping an SVG with a metadata comment.

## CLI
```bash
python -m agents.random_live_read   --out examples/live_read/echo_live_read.json   --sigil examples/live_read/Echo_Sigil.svg   --seed RUN01
```
Optional: `--a --b --c` to control the Dirichlet parameters.
