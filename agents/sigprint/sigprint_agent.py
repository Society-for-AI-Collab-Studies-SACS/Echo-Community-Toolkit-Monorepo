#!/usr/bin/env python3
import argparse
import datetime
import math
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import grpc

from google.protobuf import empty_pb2
from protos import agents_pb2, agents_pb2_grpc

try:
    import serial  # optional EEG serial input
except ImportError:  # pragma: no cover - optional
    serial = None


class SigprintEncoder:
    def __init__(self, channel_names, sample_rate=250, lockin_freq=8.0):
        self.channel_names = channel_names
        self.sample_rate = sample_rate
        self.lockin_freq = lockin_freq
        t = np.arange(0, sample_rate) / float(sample_rate)
        self.ref_sin = np.sin(2 * np.pi * self.lockin_freq * t)
        self.ref_cos = np.cos(2 * np.pi * self.lockin_freq * t)
        self.prev_signature = None
        self.gate_flag = False
        self.last_coherence = 0.0
        self.last_distribution = {}
        self.last_features = {}

    def process_epoch(self, eeg_epoch):
        features = {}
        for ch, signal in eeg_epoch.items():
            N = len(self.ref_sin)
            if len(signal) != N:
                signal = signal[:N] if len(signal) > N else np.pad(signal, (0, N - len(signal)))
            I = float(np.dot(signal, self.ref_cos) / N)
            Q = float(np.dot(signal, self.ref_sin) / N)
            amp = math.sqrt(I * I + Q * Q)
            phase_deg = math.degrees(math.atan2(Q, I))
            features[ch] = {"amp": amp, "phase": phase_deg}

        phase_list = [features[ch]["phase"] for ch in self.channel_names if ch in features]
        coherence = self._compute_global_coherence(phase_list) if phase_list else 0
        distribution = self._compute_amplitude_distribution({ch: features[ch]["amp"] for ch in features})

        code_digits = []
        code_digits += self._encode_phase_pattern(features)
        code_digits += self._encode_amplitude_distribution(distribution)
        code_digits += self._encode_coherence(coherence)
        code_digits += self._encode_reserved()
        checksum = self._compute_checksum(code_digits)
        code_digits += checksum
        sig_code = "".join(str(int(d) % 10) for d in code_digits)

        self.gate_flag = False
        if self.prev_signature is not None:
            dist = self._signature_distance(self.prev_signature, sig_code)
            if dist > 5:
                self.gate_flag = True
                print("**Gate detected**: significant change in brain state signature")
        self.prev_signature = sig_code

        self.last_coherence = float(coherence)
        self.last_distribution = distribution
        self.last_features = features
        return sig_code

    def _compute_global_coherence(self, phases):
        radians = [math.radians(p) for p in phases]
        vec = complex(0.0, 0.0)
        if not radians:
            return 0
        for theta in radians:
            vec += complex(math.cos(theta), math.sin(theta))
        vec /= len(radians)
        return int(abs(vec) * 100)

    def _compute_amplitude_distribution(self, amplitudes):
        regions = {"frontal": 0.0, "occipital": 0.0}
        for ch, amp in amplitudes.items():
            if ch.upper().startswith("F"):
                regions["frontal"] += float(amp)
            elif ch.upper().startswith("O"):
                regions["occipital"] += float(amp)
        total = sum(float(v) for v in amplitudes.values()) or 1.0
        return {k: (v / total) * 100.0 for k, v in regions.items()}

    def _encode_phase_pattern(self, features):
        digits = [0, 0, 0, 0]
        if "F3" in features and "F4" in features:
            diff = (features["F3"]["phase"] - features["F4"]["phase"]) % 360
            diff_val = int(min(diff, 99))
            digits[0] = diff_val // 10
            digits[1] = diff_val % 10
        return digits

    def _encode_amplitude_distribution(self, dist):
        frontal = int(min(dist.get("frontal", 0.0), 99))
        occipital = int(min(dist.get("occipital", 0.0), 99))
        return [frontal // 10, frontal % 10, occipital // 10, occipital % 10]

    def _encode_coherence(self, coherence):
        v = int(max(0, min(int(coherence), 9999)))
        return [(v // 1000) % 10, (v // 100) % 10, (v // 10) % 10, v % 10]

    def _encode_reserved(self):
        return [0, 0, 0, 0, 0, 0]

    def _compute_checksum(self, code_digits):
        s = sum(int(d) for d in code_digits) % 97
        return [s // 10, s % 10]

    def _signature_distance(self, code1, code2):
        if len(code1) != len(code2):
            return max(len(code1), len(code2))
        return sum(1 for a, b in zip(code1, code2) if a != b)


class SigprintAgent:
    def __init__(self, channels, eeg_source=None):
        self.channels = channels
        self.eeg_source = eeg_source
        self.encoder = SigprintEncoder(channel_names=channels)
        self.last_update = None

        # gRPC stubs to Limnus and Garden (assumed running)
        self.ledger_channel = grpc.insecure_channel("localhost:50051")
        self.ledger_stub = agents_pb2_grpc.LedgerServiceStub(self.ledger_channel)
        self.garden_channel = grpc.insecure_channel("localhost:50052")
        self.garden_stub = agents_pb2_grpc.GardenServiceStub(self.garden_channel)

        self.ser = None
        if self.eeg_source:
            if serial is None:
                print("ERROR: pyserial not installed; cannot read EEG from serial.")
            else:
                try:
                    self.ser = serial.Serial(self.eeg_source, baudrate=115200, timeout=0)
                    print(f"Opened serial EEG source: {self.eeg_source}")
                except Exception as e:
                    print(f"Failed to open serial port {self.eeg_source}: {e}")
                    self.ser = None

    def _simulate_eeg_epoch(self, prev_phase_offsets, change_state=False):
        N = self.encoder.sample_rate
        t = np.arange(0, N) / float(self.encoder.sample_rate)
        epoch = {}
        new_phase_offsets = {}

        if change_state or prev_phase_offsets is None:
            for ch in self.channels:
                phase = np.random.uniform(0.0, 2.0 * math.pi)
                amp = np.random.uniform(5.0, 10.0)
                new_phase_offsets[ch] = (phase, amp)
        else:
            for ch, (phase, amp) in prev_phase_offsets.items():
                phase += math.radians(np.random.uniform(-5, 5))
                amp *= np.random.uniform(0.95, 1.05)
                new_phase_offsets[ch] = (phase, amp)

        for ch, (phase, amp) in new_phase_offsets.items():
            signal = amp * np.sin(2 * math.pi * self.encoder.lockin_freq * t + phase)
            noise = 0.1 * np.random.randn(N)
            epoch[ch] = signal + noise
        return epoch, new_phase_offsets

    def _read_serial_epoch(self):
        samples = {ch: [] for ch in self.channels}
        start_read = time.time()
        while time.time() - start_read < 1.0:
            line = self.ser.readline()
            if not line:
                continue
            try:
                parts = line.decode("utf-8", errors="ignore").strip().split()
                if len(parts) >= len(self.channels):
                    vals = [float(x) for x in parts[: len(self.channels)]]
                    for ch, val in zip(self.channels, vals):
                        samples[ch].append(val)
            except Exception:
                continue
        for ch in self.channels:
            samples[ch] = np.array(samples[ch], dtype=float)
        return samples

    def run(self):
        server = grpc.server(ThreadPoolExecutor(max_workers=2))

        class SigprintServicer(agents_pb2_grpc.SigprintServiceServicer):
            def __init__(self, agent):
                self.agent = agent

            def GetLatestSigprint(self, request, context):
                if self.agent.last_update:
                    return self.agent.last_update
                return agents_pb2.SigprintUpdate(time="", sigprint="", coherence=0.0, features={})

        agents_pb2_grpc.add_SigprintServiceServicer_to_server(SigprintServicer(self), server)
        server.add_insecure_port("[::]:50055")
        server.start()
        print("SIGPRINT agent gRPC service started on port 50055.")

        prev_phase_offsets = None
        try:
            while True:
                loop_start = time.time()

                if self.ser and getattr(self.ser, "is_open", False):
                    eeg_epoch = self._read_serial_epoch()
                else:
                    change_state = bool(np.random.rand() < 0.2)
                    eeg_epoch, prev_phase_offsets = self._simulate_eeg_epoch(prev_phase_offsets, change_state)

                code = self.encoder.process_epoch(eeg_epoch)
                timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

                feat_map = {
                    "frontal_pct": float(self.encoder.last_distribution.get("frontal", 0.0)),
                    "occipital_pct": float(self.encoder.last_distribution.get("occipital", 0.0)),
                }
                if "F3" in self.encoder.last_features and "F4" in self.encoder.last_features:
                    diff = (self.encoder.last_features["F3"]["phase"] - self.encoder.last_features["F4"]["phase"]) % 360
                    feat_map["phase_diff_F3_F4"] = float(diff)

                entry = agents_pb2.LedgerEntry(
                    time=timestamp,
                    type="SIGPRINT",
                    text="",
                    sigprint=code,
                    coherence=float(self.encoder.last_coherence),
                    features=feat_map,
                )
                try:
                    resp = self.ledger_stub.CommitEntry(entry)
                    if not resp or not resp.success:
                        print("Warning: Ledger commit failed or no response.")
                except Exception as e:
                    print(f"Ledger commit RPC error: {e}")

                self.last_update = agents_pb2.SigprintUpdate(
                    time=timestamp,
                    sigprint=code,
                    coherence=float(self.encoder.last_coherence),
                    features=feat_map,
                )

                if self.encoder.gate_flag:
                    try:
                        event = agents_pb2.GardenEvent(
                            event_type="STATE_CHANGE", description=f"Gate detected at {timestamp}"
                        )
                        self.garden_stub.NotifyEvent(event)
                    except Exception as e:
                        print(f"Garden notify RPC error: {e}")

                elapsed = time.time() - loop_start
                if elapsed < 1.0:
                    time.sleep(1.0 - elapsed)
        except KeyboardInterrupt:
            print("SIGPRINT agent shutting down.")
        finally:
            server.stop(0)
            if self.ser:
                try:
                    self.ser.close()
                except Exception:
                    pass


def main():
    parser = argparse.ArgumentParser(description="Run the SIGPRINT agent (EEG listener).")
    parser.add_argument("--port", "-p", help="Serial port for EEG input (else use simulated data).")
    args = parser.parse_args()
    channels = ["F3", "F4", "Pz", "Oz"]
    agent = SigprintAgent(channels, eeg_source=args.port)
    agent.run()


if __name__ == "__main__":
    main()

