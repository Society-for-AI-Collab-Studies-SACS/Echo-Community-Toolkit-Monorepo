"""
MemoryBlocks – placeholder for multi-image reassembly.
Future phases will stream large payloads across multiple images and stitch them here.
"""


class MemoryBlocks:
    def __init__(self):
        self.sessions = {}

    def start_session(self, session_id: str, total_parts: int):
        self.sessions[session_id] = {
            "total_parts": total_parts,
            "received_parts": 0,
            "data_parts": {},
        }

    def add_part(self, session_id: str, part_index: int, data: bytes):
        if session_id not in self.sessions:
            raise KeyError(f"Session {session_id} not initialized")
        session = self.sessions[session_id]
        session["data_parts"][part_index] = data
        session["received_parts"] += 1

    def is_complete(self, session_id: str) -> bool:
        return (
            session_id in self.sessions
            and self.sessions[session_id]["received_parts"]
            >= self.sessions[session_id]["total_parts"]
        )

    def assemble(self, session_id: str) -> bytes:
        if not self.is_complete(session_id):
            raise ValueError(f"Session {session_id} is incomplete")
        session = self.sessions[session_id]
        total = session["total_parts"]
        return b"".join(session["data_parts"].get(i) or b"" for i in range(1, total + 1))

    def clear_session(self, session_id: str):
        self.sessions.pop(session_id, None)

