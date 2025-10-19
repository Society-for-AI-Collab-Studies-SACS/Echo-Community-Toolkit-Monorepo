#!/usr/bin/env python3
import argparse
import asyncio
import binascii
import struct
import threading
import time
from dataclasses import dataclass
from typing import Optional, Tuple, Dict

import grpc
import websockets
from google.protobuf import empty_pb2

from protos import agents_pb2, agents_pb2_grpc

try:
    import serial  # optional
except ImportError:  # pragma: no cover
    serial = None


HEADER_FMT = "<HBBIHH"  # magic, version, ptype, ts_ms, packet_size, checksum
HEADER_SIZE = struct.calcsize(HEADER_FMT)
MAGIC = 0x5347

# Layout sizes from firmware (#pragma pack(1))
NUM_CHANNELS = 8
NUM_BANDS = 5
EEG_SIZE = 1 + (NUM_CHANNELS * 4) + (NUM_CHANNELS * NUM_BANDS * 4) + (NUM_CHANNELS * NUM_BANDS * 4)  # 353
SIG_SIZE = 10 + 4 + 1 + 1 + 4  # code[10], coherence f32, gate u8, loop u8, entropy f32 = 20
TAIL_SIZE = 1 + 2  # stage u8, zipper_freq u16 = 3
DATA_SIZE = EEG_SIZE + SIG_SIZE + TAIL_SIZE  # 376


def bcd_to_str(bcd10: bytes) -> str:
    out = []
    for b in bcd10:
        out.append(str((b >> 4) & 0x0F))
        out.append(str(b & 0x0F))
    return "".join(out)


@dataclass
class ParsedSigprint:
    timestamp_ms: int
    code: str
    coherence_0_1: float
    gate_flags: int
    loop_flags: int
    entropy: float
    band_power_avg: Dict[str, float]
    stage: int
    zipper_freq: int


def parse_packet(buf: bytes) -> Optional[ParsedSigprint]:
    if len(buf) < HEADER_SIZE:
        return None
    magic, version, ptype, ts_ms, psize, checksum = struct.unpack_from(HEADER_FMT, buf, 0)
    if magic != MAGIC or psize != DATA_SIZE:
        return None
    # We could validate checksum here (CCITT), but skipping for now.
    off = HEADER_SIZE
    # EEG block
    ch_count = buf[off]
    off += 1
    # raw samples (8 x int32)
    off += NUM_CHANNELS * 4
    # band power 8x5 float32
    band_power = struct.unpack_from(
        "<" + "f" * (NUM_CHANNELS * NUM_BANDS), buf, off
    )
    off += NUM_CHANNELS * NUM_BANDS * 4
    # band phase 8x5 float32
    off += NUM_CHANNELS * NUM_BANDS * 4

    # SIGPRINT block
    code_b = struct.unpack_from("<10B", buf, off)
    off += 10
    coherence = struct.unpack_from("<f", buf, off)[0]
    off += 4
    gate_flags = buf[off]
    off += 1
    loop_flags = buf[off]
    off += 1
    entropy = struct.unpack_from("<f", buf, off)[0]
    off += 4
    # Tail
    stage = buf[off]
    off += 1
    zipper_freq = struct.unpack_from("<H", buf, off)[0]
    off += 2

    # Aggregate band power across channels for features
    names = ["delta", "theta", "alpha", "beta", "gamma"]
    band_power_avg = {}
    # band_power layout: per-channel contiguous across bands (ch major)
    # We'll sum per band
    for b in range(NUM_BANDS):
        s = 0.0
        for ch in range(NUM_CHANNELS):
            idx = ch * NUM_BANDS + b
            s += float(band_power[idx])
        band_power_avg[names[b]] = s / max(1, NUM_CHANNELS)

    code = bcd_to_str(bytes(code_b))
    return ParsedSigprint(
        timestamp_ms=ts_ms,
        code=code,
        coherence_0_1=float(coherence),
        gate_flags=int(gate_flags),
        loop_flags=int(loop_flags),
        entropy=float(entropy),
        band_power_avg=band_power_avg,
        stage=int(stage),
        zipper_freq=int(zipper_freq),
    )


class SigprintBridge:
    def __init__(self, ledger_addr: str, garden_addr: str):
        self.ledger_stub = agents_pb2_grpc.LedgerServiceStub(grpc.insecure_channel(ledger_addr))
        self.garden_stub = agents_pb2_grpc.GardenServiceStub(grpc.insecure_channel(garden_addr))
        self.last_update: Optional[agents_pb2.SigprintUpdate] = None
        self.prev_code: Optional[str] = None

    def _post_update(self, parsed: ParsedSigprint):
        # Scale coherence to 0–100 for consistency with existing pipeline
        coh_pct = max(0.0, min(100.0, parsed.coherence_0_1 * 100.0))
        ts_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        feat = {
            "entropy": parsed.entropy,
            "gate_flags": float(parsed.gate_flags),
            "loop_flags": float(parsed.loop_flags),
        }
        # Optional firmware metadata
        feat["stage"] = float(parsed.stage)
        feat["zipper_freq"] = float(parsed.zipper_freq)
        for k, v in parsed.band_power_avg.items():
            feat[f"{k}_power"] = float(v)

        # Commit to ledger
        entry = agents_pb2.LedgerEntry(
            time=ts_iso,
            type="SIGPRINT",
            text="",
            sigprint=parsed.code,
            coherence=coh_pct,
            features=feat,
        )
        try:
            self.ledger_stub.CommitEntry(entry)
        except Exception:
            pass

        # Update local last_update
        self.last_update = agents_pb2.SigprintUpdate(
            time=ts_iso, sigprint=parsed.code, coherence=coh_pct, features=feat
        )

        # Gate or anomaly notifications
        is_gate = parsed.gate_flags != 0
        if self.prev_code is not None:
            changes = sum(1 for a, b in zip(parsed.code, self.prev_code) if a != b)
            if changes > 5:
                is_gate = True
        self.prev_code = parsed.code

        if is_gate:
            try:
                self.garden_stub.NotifyEvent(
                    agents_pb2.GardenEvent(
                        event_type="STATE_CHANGE",
                        description=f"Gate detected. coherence={coh_pct:.1f} flags=0x{parsed.gate_flags:02x}",
                    )
                )
            except Exception:
                pass


class BridgeServer(agents_pb2_grpc.SigprintServiceServicer):
    def __init__(self, bridge: SigprintBridge):
        self.bridge = bridge

    def GetLatestSigprint(self, request, context):
        if self.bridge.last_update:
            return self.bridge.last_update
        return agents_pb2.SigprintUpdate(time="", sigprint="", coherence=0.0, features={})


async def run_ws_loop(url: str, bridge: SigprintBridge):
    backoff = 1.0
    while True:
        try:
            async with websockets.connect(url, max_size=None) as ws:
                backoff = 1.0
                async for msg in ws:
                    if isinstance(msg, (bytes, bytearray)):
                        parsed = parse_packet(msg)
                        if parsed:
                            bridge._post_update(parsed)
        except Exception:
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 10.0)


def run_serial_loop(port: str, bridge: SigprintBridge):
    if serial is None:
        print("pyserial not installed; cannot read serial.")
        return
    with serial.Serial(port, baudrate=921600, timeout=1) as ser:
        buf = bytearray()
        while True:
            chunk = ser.read(8192)
            if not chunk:
                continue
            buf.extend(chunk)
            # Find header
            while len(buf) >= HEADER_SIZE:
                magic = struct.unpack_from("<H", buf, 0)[0]
                if magic != MAGIC:
                    # resync: drop first byte
                    buf.pop(0)
                    continue
                if len(buf) < HEADER_SIZE:
                    break
                _, _, _, ts_ms, psize, _ = struct.unpack_from(HEADER_FMT, buf, 0)
                total = HEADER_SIZE + psize
                if len(buf) < total:
                    break
                packet = bytes(buf[:total])
                del buf[:total]
                parsed = parse_packet(packet)
                if parsed:
                    bridge._post_update(parsed)


def main():
    parser = argparse.ArgumentParser(description="Bridge firmware binary stream to Limnus/Garden + SigprintService.")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--ws-url", help="WebSocket URL of firmware, e.g., ws://192.168.4.1/sigprint")
    src.add_argument("--serial-port", help="Serial port for firmware binary output, e.g., /dev/ttyUSB0")
    parser.add_argument("--ledger", default="localhost:50051", help="LedgerService host:port")
    parser.add_argument("--garden", default="localhost:50052", help="GardenService host:port")
    parser.add_argument("--serve-port", type=int, default=50055, help="Local SigprintService port")
    args = parser.parse_args()

    bridge = SigprintBridge(ledger_addr=args.ledger, garden_addr=args.garden)

    # Start local SigprintService server
    # The grpc.server() expects a futures.Executor; use ThreadPoolExecutor
    from concurrent.futures import ThreadPoolExecutor

    server = grpc.server(ThreadPoolExecutor(max_workers=4))
    agents_pb2_grpc.add_SigprintServiceServicer_to_server(BridgeServer(bridge), server)
    server.add_insecure_port(f"[::]:{args.serve_port}")
    server.start()
    print(f"Sigprint Bridge service started on :{args.serve_port}")

    try:
        if args.ws_url:
            asyncio.run(run_ws_loop(args.ws_url, bridge))
        else:
            run_serial_loop(args.serial_port, bridge)
    except KeyboardInterrupt:
        pass
    finally:
        server.stop(0)


if __name__ == "__main__":
    main()
