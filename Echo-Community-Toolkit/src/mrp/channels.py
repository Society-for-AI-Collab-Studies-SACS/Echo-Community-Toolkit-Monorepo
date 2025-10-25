from typing import Literal

Channel = Literal["R", "G", "B"]
CHANNEL_INDEX = {"R": 0, "G": 1, "B": 2}

def ensure_channel(ch: str) -> Channel:
    if ch not in CHANNEL_INDEX:
        raise ValueError(f"Unsupported channel {ch}")
    return ch  # type: ignore[return-value]

