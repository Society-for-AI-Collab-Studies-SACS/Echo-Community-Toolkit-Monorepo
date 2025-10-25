# Serial Logger (Host)

The serial logger captures JSON snapshots and CSV logs from the stylus firmware over a USB serial port.

## Usage
```
python host/logger_serial.py --port /dev/ttyACM0 --baud 115200
```

- Replace `/dev/ttyACM0` with the correct port (e.g., `/dev/ttyUSB0`, `COM5`).
- Ensure the board is running and enumerated; use `pio device list` to find ports.

## Output
- Console stream of JSON lines (e.g., boot/version, sensor snapshots).
- Optionally save to files; see script options (`-h`) for flags and paths.

## Tips
- Match the baud to `monitor_speed` in `platformio.ini` (115200).
- If you see no output, press the reset button on the board to re‑emit the boot line.

