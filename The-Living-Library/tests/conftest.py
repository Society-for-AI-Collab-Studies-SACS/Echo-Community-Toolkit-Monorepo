import pytest

# Skip the suite when the optional runtime is unavailable in bare CI images.
library_core = pytest.importorskip(
    "library_core",
    reason="Living Library runtime not present; skip in headless CI.",
)
