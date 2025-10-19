#!/usr/bin/env python3
import argparse
import datetime
import sys

import grpc
from google.protobuf import empty_pb2
from protos import agents_pb2, agents_pb2_grpc

try:
    import speech_recognition as sr  # optional voice mode
except ImportError:  # pragma: no cover
    sr = None


class JournalLogger:
    def __init__(self, voice_mode=False):
        self.voice_mode = voice_mode
        self.sig_channel = grpc.insecure_channel("localhost:50055")
        self.sig_stub = agents_pb2_grpc.SigprintServiceStub(self.sig_channel)
        self.ledger_channel = grpc.insecure_channel("localhost:50051")
        self.ledger_stub = agents_pb2_grpc.LedgerServiceStub(self.ledger_channel)
        self.garden_channel = grpc.insecure_channel("localhost:50052")
        self.garden_stub = agents_pb2_grpc.GardenServiceStub(self.garden_channel)

        self.recognizer = None
        if self.voice_mode and sr:
            try:
                self.recognizer = sr.Recognizer()
                with sr.Microphone() as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
                    print("Microphone calibrated for ambient noise.")
            except Exception as e:
                print(f"Microphone setup error: {e}")
                self.recognizer = None

    def _transcribe_voice(self):
        if not self.recognizer or not sr:
            return ""
        text = ""
        try:
            with sr.Microphone() as source:
                print("Listening for speech... (Ctrl+C to stop)")
                audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=10)
            try:
                text = self.recognizer.recognize_google(audio)
            except sr.UnknownValueError:
                print("Sorry, I could not understand the audio.")
            except sr.RequestError as e:
                print(f"Voice recognition error: {e}")
        except KeyboardInterrupt:
            raise
        return text

    def run(self):
        print("Journal Logger started. Mode:", "VOICE" if self.voice_mode else "TEXT")
        print(
            "Speak and pause to record, Ctrl+C to quit." if self.voice_mode else "Type and press Enter; 'exit' to quit."
        )
        try:
            while True:
                if self.voice_mode:
                    entry_text = self._transcribe_voice()
                    if entry_text == "":
                        continue
                    print(f"Transcribed entry: \"{entry_text}\"")
                else:
                    entry_text = input("> ").strip()
                    if entry_text.lower() == "exit":
                        break
                    if entry_text == "":
                        continue

                timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                sig_code = ""
                coherence = 0.0
                features = {}
                try:
                    sig_update = self.sig_stub.GetLatestSigprint(empty_pb2.Empty())
                    if sig_update:
                        sig_code = sig_update.sigprint
                        coherence = sig_update.coherence
                        features = dict(sig_update.features)
                except Exception as e:
                    print(f"Error fetching SIGPRINT: {e}")

                entry = agents_pb2.LedgerEntry(
                    time=timestamp,
                    type="JOURNAL",
                    text=entry_text,
                    sigprint=sig_code,
                    coherence=coherence,
                    features=features,
                )
                try:
                    resp = self.ledger_stub.CommitEntry(entry)
                    if resp and resp.success:
                        print(f"Journal entry logged with SIGPRINT {sig_code}.")
                    else:
                        print("Warning: Failed to log entry to ledger.")
                except Exception as e:
                    print(f"Ledger commit error: {e}")

                try:
                    event = agents_pb2.GardenEvent(
                        event_type="SELF_REFLECTION", description="User journaled an entry"
                    )
                    self.garden_stub.NotifyEvent(event)
                except Exception as e:
                    print(f"Garden notify error (continuing): {e}")

        except KeyboardInterrupt:
            print("\nVoice journaling stopped by user." if self.voice_mode else "\nExiting journal logger.")
        finally:
            self.sig_channel.close()
            self.ledger_channel.close()
            self.garden_channel.close()


def main():
    parser = argparse.ArgumentParser(description="Run the Journal Logger (voice or text mode).")
    parser.add_argument("--voice", "-v", action="store_true", help="Enable voice transcription mode.")
    args = parser.parse_args()
    logger = JournalLogger(voice_mode=args.voice)
    logger.run()


if __name__ == "__main__":
    main()

