#!/usr/bin/env python3
import sys
import json
import time
import csv
import serial

"""
Reads JSON snapshots from ESP32-S3 firmware over USB serial,
writes rolling CSV, and prints Zipper stage transitions.
"""

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyACM0"
BAUD = 115200
CSV_OUT = sys.argv[2] if len(sys.argv) > 2 else f"rhz_host_{int(time.time())}.csv"

FIELDS = ["t_ms", "stage", "emit", "tx_f", "ads_raw", "cap_raw", "lux", "mag_x", "mag_y", "mag_z"]

with serial.Serial(PORT, BAUD, timeout=1) as ser, open(CSV_OUT, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDS)
    writer.writeheader()
    last_stage = None
    print(f"Logging to {CSV_OUT} (Ctrl-C to stop)")
    while True:
        line = ser.readline().decode(errors="ignore").strip()
        if not line:
            continue
        if line.startswith("{") and ("boot" in line or "log_file" in line):
            print(line)
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        row = {
            "t_ms": obj.get("t_ms"),
            "stage": obj.get("stage"),
            "emit": 1 if obj.get("emit") else 0,
            "tx_f": obj.get("tx", {}).get("f"),
            "ads_raw": obj.get("rx", {}).get("ads_raw"),
            "cap_raw": obj.get("cap_raw"),
            "lux": obj.get("lux"),
            "mag_x": (obj.get("mag_uT") or [None, None, None])[0],
            "mag_y": (obj.get("mag_uT") or [None, None, None])[1],
            "mag_z": (obj.get("mag_uT") or [None, None, None])[2],
        }
        writer.writerow(row)
        f.flush()

        if obj.get("stage") != last_stage:
            last_stage = obj.get("stage")
            print(f"[MARK] stage={last_stage}, emit={obj.get('emit')}, t_ms={obj.get('t_ms')}")
