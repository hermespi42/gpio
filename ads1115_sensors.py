#!/usr/bin/env python3
"""
ads1115_sensors.py — ADS1115 16-bit ADC sensor reader

Reads the kit's analog sensors via the ADS1115 module (I2C).
Run this script once the ADS1115 is wired to the Pi.

--- Wiring ---
ADS1115 module:
  VDD  → Pi physical pin 1  (3.3V)
  GND  → Pi physical pin 9  (GND)
  SCL  → Pi physical pin 5  (BCM 3 / I2C1_SCL)
  SDA  → Pi physical pin 3  (BCM 2 / I2C1_SDA)
  ADDR → GND (sets I2C address to 0x48)

Analog sensors (voltage dividers with 10kΩ pull-down to GND):
  A0 → photoresistor (3.3V → photoresistor → A0 → 10kΩ → GND)
  A1 → thermistor    (3.3V → thermistor → A1 → 10kΩ → GND)
  A2 → potentiometer wiper (ends to 3.3V and GND)
  A3 → spare (second potentiometer, or leave open)

--- Verify I2C ---
Before connecting the chip, confirm I2C is enabled:
  sudo i2cdetect -y 1
Once wired, should show 48 in the grid (address 0x48).

--- Usage ---
  python3 ads1115_sensors.py          # single read, all channels
  python3 ads1115_sensors.py --watch  # continuous readings every 1s
  python3 ads1115_sensors.py --watch --interval 5
"""

import argparse
import math
import sys
import time

try:
    import board
    import busio
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
except ImportError:
    print("ERROR: adafruit-circuitpython-ads1x15 not installed.")
    print("Run: pip3 install --break-system-packages adafruit-circuitpython-ads1x15")
    sys.exit(1)


# --- Sensor conversion helpers ---

VREF = 3.3          # supply voltage
R_FIXED = 10_000    # voltage divider fixed resistor (10kΩ)


def voltage_to_resistance(v: float) -> float:
    """Convert voltage divider output (sensor on top, fixed R on bottom) to sensor R."""
    if v <= 0 or v >= VREF:
        return float("inf") if v <= 0 else 0.0
    return R_FIXED * v / (VREF - v)


def resistance_to_lux_approx(r: float) -> float:
    """Very rough lux approximation for a generic photoresistor (GL5516-like).
    At ~10kΩ: ~10 lux (dim room), ~1kΩ: ~100 lux, ~100kΩ: ~1 lux.
    Formula: lux ≈ 500 / r_kohm^1.4  (empirical, varies by sensor).
    """
    r_k = r / 1000
    if r_k <= 0:
        return 9999
    return round(500 / (r_k ** 1.4), 1)


def resistance_to_celsius(r: float, beta: float = 3950, t_ref: float = 298.15, r_ref: float = 10_000) -> float:
    """Convert NTC thermistor resistance to Celsius using the Beta equation.
    Default values for a 10kΩ NTC thermistor (B=3950) at 25°C — adjust if different.
    """
    if r <= 0:
        return float("nan")
    try:
        inv_t = (1 / t_ref) + (1 / beta) * math.log(r / r_ref)
        return round(1 / inv_t - 273.15, 1)
    except (ValueError, ZeroDivisionError):
        return float("nan")


def read_all(ads) -> dict:
    """Read all 4 channels and return raw + derived values."""
    channels = {
        "A0_photo": AnalogIn(ads, 0),
        "A1_therm": AnalogIn(ads, 1),
        "A2_pot1":  AnalogIn(ads, 2),
        "A3_pot2":  AnalogIn(ads, 3),
    }

    results = {}
    for name, ch in channels.items():
        v = ch.voltage
        raw = ch.value
        entry = {"voltage": round(v, 4), "raw_16bit": raw}

        if name == "A0_photo":
            r = voltage_to_resistance(v)
            entry["resistance_ohm"] = round(r) if r != float("inf") else "open"
            entry["lux_approx"] = resistance_to_lux_approx(r) if r != float("inf") else 0

        elif name == "A1_therm":
            r = voltage_to_resistance(v)
            entry["resistance_ohm"] = round(r) if r != float("inf") else "open"
            if r != float("inf"):
                entry["temp_celsius"] = resistance_to_celsius(r)

        elif name.startswith("A2") or name.startswith("A3"):
            entry["percent"] = round(v / VREF * 100, 1)

        results[name] = entry

    return results


def print_readings(data: dict) -> None:
    print(f"  A0 photoresistor: {data['A0_photo']['voltage']:.3f}V  "
          f"R={data['A0_photo'].get('resistance_ohm','?')}Ω  "
          f"~{data['A0_photo'].get('lux_approx','?')} lux")
    print(f"  A1 thermistor:    {data['A1_therm']['voltage']:.3f}V  "
          f"R={data['A1_therm'].get('resistance_ohm','?')}Ω  "
          f"T={data['A1_therm'].get('temp_celsius','?')}°C")
    print(f"  A2 potentiometer: {data['A2_pot1']['voltage']:.3f}V  "
          f"{data['A2_pot1'].get('percent','?')}%")
    print(f"  A3 spare:         {data['A3_pot2']['voltage']:.3f}V  "
          f"{data['A3_pot2'].get('percent','?')}%")


def main():
    parser = argparse.ArgumentParser(description="ADS1115 sensor reader")
    parser.add_argument("--watch", action="store_true", help="continuous mode")
    parser.add_argument("--interval", type=float, default=1.0, help="seconds between reads (--watch only)")
    args = parser.parse_args()

    try:
        i2c = busio.I2C(board.SCL, board.SDA)
        ads = ADS.ADS1115(i2c)
        ads.gain = 1  # ±4.096V range (covers 3.3V rail)
    except Exception as e:
        print(f"ERROR: Could not connect to ADS1115: {e}")
        print("Is the chip wired? Run: sudo i2cdetect -y 1")
        sys.exit(1)

    if args.watch:
        print("ADS1115 — watching (Ctrl+C to stop)")
        try:
            while True:
                print(f"\n[{time.strftime('%H:%M:%S')}]")
                print_readings(read_all(ads))
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nStopped.")
    else:
        print("ADS1115 — single read")
        print_readings(read_all(ads))


if __name__ == "__main__":
    main()
