# PSD Quicklook (Host)

The PSD quicklook script analyzes captured CSV logs and surfaces frequency lines of interest.

## Usage
```
python host/psd_quicklook.py sample.csv
```

- Input: CSV with columns like `t_ms,stage,emit,tx_f,ads_raw,cap_raw,lux,mag_x,mag_y,mag_z`.
- Output: Console summary of PSD peaks; use CI’s synthetic dataset to validate (expects a strong ~444 Hz in S3).

## Tips
- Provide a longer capture for better frequency resolution (e.g., 2048+ samples at 1 kHz).
- Use the `emit` window and `stage` markers to compare background vs transmit intervals.
- Pin Python deps: `pip install numpy pandas scipy` (CI does this automatically).

