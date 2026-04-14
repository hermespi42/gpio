#!/usr/bin/env python3
"""
sensor_collector.py — ADS1115 background collector daemon

Polls the ADS1115 every INTERVAL seconds and writes current readings
to ~/sensor_data.json. Runs as hermes-sensor-collector.service.

If the chip is not wired, writes a status JSON with connected=false
so the dashboard can show a "not connected" state gracefully.

--- Usage ---
  python3 sensor_collector.py             # default 30-second interval
  python3 sensor_collector.py --interval 10
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

OUTPUT_FILE = Path.home() / "sensor_data.json"
INTERVAL_DEFAULT = 30


def write_output(data: dict) -> None:
    tmp = OUTPUT_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(OUTPUT_FILE)


def run(interval: int) -> None:
    try:
        import board
        import busio
        import adafruit_ads1x15.ads1115 as ADS
    except ImportError:
        print("ERROR: adafruit-circuitpython-ads1x15 not installed.", flush=True)
        print("Run: pip3 install --break-system-packages adafruit-circuitpython-ads1x15", flush=True)
        sys.exit(1)

    # Import sensor helpers from sibling module
    sys.path.insert(0, str(Path(__file__).parent))
    from ads1115_sensors import read_all

    print(f"sensor_collector: starting, interval={interval}s, output={OUTPUT_FILE}", flush=True)

    while True:
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            ads = ADS.ADS1115(i2c)
            ads.gain = 1  # ±4.096V range

            print(f"[{datetime.now().strftime('%H:%M:%S')}] ADS1115 connected — collecting", flush=True)

            while True:
                try:
                    readings = read_all(ads)
                    write_output({
                        "connected": True,
                        "timestamp": datetime.now().isoformat(timespec="seconds"),
                        "interval_s": interval,
                        "readings": readings,
                    })
                except Exception as e:
                    write_output({
                        "connected": False,
                        "timestamp": datetime.now().isoformat(timespec="seconds"),
                        "error": str(e),
                    })
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Read error: {e}", flush=True)
                    break  # reconnect loop

                time.sleep(interval)

        except Exception as e:
            write_output({
                "connected": False,
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "error": f"Not connected: {e}",
            })
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Not connected: {e} — retrying in 60s", flush=True)
            time.sleep(60)  # slow retry when chip not found


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ADS1115 background collector")
    parser.add_argument("--interval", type=int, default=INTERVAL_DEFAULT,
                        help=f"Seconds between readings (default: {INTERVAL_DEFAULT})")
    args = parser.parse_args()
    run(args.interval)
