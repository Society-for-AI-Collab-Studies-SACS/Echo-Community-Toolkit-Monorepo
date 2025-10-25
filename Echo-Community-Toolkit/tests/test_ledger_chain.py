import json
import sys
from pathlib import Path

# Ensure project root is on sys.path for direct 'agents.*' imports
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.state import JsonStateStore
from agents.bloom_chain import BloomChainAdapter


def read_chain(chain_path: Path):
    blocks = []
    if chain_path.exists():
        for line in chain_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                blocks.append(json.loads(line))
    return blocks


def test_create_appends_block_and_backrefs(tmp_path: Path):
    state_path = tmp_path / "state.json"
    chain_path = tmp_path / "chain.log"

    adapter = BloomChainAdapter(chain_path)
    store = JsonStateStore(state_path, on_create=adapter.record_event)

    # Create first record in 'glyphs'
    rec1_id = store.create_record("glyphs", {"token": "I-Glyph", "size": 32})
    rec1 = store.get_record("glyphs", rec1_id)
    chain = read_chain(chain_path)

    assert "block_hash" in rec1 and isinstance(rec1["block_hash"], str)
    assert len(chain) == 1
    assert chain[0]["payload"]["type"] == "glyphs"
    assert chain[0]["payload"]["record_id"] == rec1_id
    assert chain[0]["prev_hash"] == "GENESIS"
    assert chain[0]["hash"] == rec1["block_hash"]

    # Create second record in another section; chain should link by prev_hash
    rec2_id = store.create_record("mrp_embeds", {"cover": "cover.png", "message": "Hello"})
    rec2 = store.get_record("mrp_embeds", rec2_id)
    chain = read_chain(chain_path)

    assert len(chain) == 2
    assert chain[1]["payload"]["type"] == "mrp_embeds"
    assert chain[1]["payload"]["record_id"] == rec2_id
    assert chain[1]["prev_hash"] == chain[0]["hash"]
    assert chain[1]["hash"] == rec2["block_hash"]
