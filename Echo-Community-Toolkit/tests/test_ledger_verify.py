import sys
from pathlib import Path

# Ensure toolkit root on path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.state import JsonStateStore  # noqa: E402
from agents.bloom_chain import BloomChainAdapter  # noqa: E402
from scripts.verify_ledger_and_chain import verify  # noqa: E402


def test_verify_report_ok(tmp_path: Path):
    state_path = tmp_path / "state.json"
    chain_path = tmp_path / "chain.log"
    adapter = BloomChainAdapter(chain_path)
    store = JsonStateStore(state_path, on_create=adapter.record_event)

    # Add two entries
    gid = store.create_record("glyphs", {"token": "I-Glyph", "size": 32})
    eid = store.create_record("mrp_embeds", {"cover": "c.png", "message": "hi"})

    rep = verify(state_path, chain_path)
    assert rep["ok"] is True
    assert rep["link_ok"] is True
    assert rep["backref_ok"] is True
    assert rep["counts"]["blocks"] == 2

