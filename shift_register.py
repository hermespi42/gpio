#!/usr/bin/env python3
"""
shift_register.py — 74HC595 8-bit shift register control

The 74HC595 expands GPIO output capacity: control 8 LED outputs
using only 3 GPIO pins (data, clock, latch).

Wiring (BCM pin numbers):
  Pi BCM 17 (physical 11) → 74HC595 DS  (pin 14) — serial data
  Pi BCM 27 (physical 13) → 74HC595 SH_CP (pin 11) — shift clock
  Pi BCM 22 (physical 15) → 74HC595 ST_CP (pin 12) — latch clock
  Pi 3.3V   (physical 1)  → 74HC595 VCC (pin 16)
  Pi GND    (physical 6)  → 74HC595 GND (pin 8)
  Pi 3.3V                 → 74HC595 OE\ (pin 13, active low, tie to GND or control)
  Pi 3.3V                 → 74HC595 MR\ (pin 10, active low reset, tie to VCC)

  74HC595 Q0–Q7 (pins 15, 1–7) → LEDs via 220Ω resistors → GND

Usage:
  python3 shift_register.py              # runs demo sequences
  python3 shift_register.py chase        # bouncing dot
  python3 shift_register.py binary       # count 0-255 in binary
  python3 shift_register.py all_on       # all LEDs on
  python3 shift_register.py all_off      # all LEDs off
"""

import sys
import time
import RPi.GPIO as GPIO

# GPIO pins (BCM)
DATA_PIN  = 17  # DS   — serial data in
CLOCK_PIN = 27  # SH_CP — shift clock
LATCH_PIN = 22  # ST_CP — storage/latch clock


def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(DATA_PIN,  GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(CLOCK_PIN, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(LATCH_PIN, GPIO.OUT, initial=GPIO.LOW)


def write_byte(value: int):
    """Shift out one byte (8 bits) to the 74HC595, then latch."""
    GPIO.output(LATCH_PIN, GPIO.LOW)
    for i in range(7, -1, -1):  # MSB first
        bit = (value >> i) & 1
        GPIO.output(DATA_PIN, bit)
        GPIO.output(CLOCK_PIN, GPIO.HIGH)
        GPIO.output(CLOCK_PIN, GPIO.LOW)
    GPIO.output(LATCH_PIN, GPIO.HIGH)
    GPIO.output(LATCH_PIN, GPIO.LOW)


def all_off():
    write_byte(0b00000000)

def all_on():
    write_byte(0b11111111)


def demo_chase(cycles: int = 3, delay: float = 0.08):
    """Single LED bouncing left and right."""
    for _ in range(cycles):
        for i in range(8):
            write_byte(1 << i)
            time.sleep(delay)
        for i in range(6, 0, -1):
            write_byte(1 << i)
            time.sleep(delay)


def demo_binary(delay: float = 0.05):
    """Count 0–255 in binary on 8 LEDs."""
    for n in range(256):
        write_byte(n)
        time.sleep(delay)


def demo_fill(delay: float = 0.1):
    """Fill LEDs one by one, then clear one by one."""
    val = 0
    for i in range(8):
        val = val | (1 << i)
        write_byte(val)
        time.sleep(delay)
    for i in range(8):
        val = val & ~(1 << i)
        write_byte(val)
        time.sleep(delay)


def demo_flash(times: int = 3, delay: float = 0.15):
    """Flash all LEDs."""
    for _ in range(times):
        all_on()
        time.sleep(delay)
        all_off()
        time.sleep(delay)


def run_demo():
    print("Chase...")
    demo_chase(2)
    time.sleep(0.3)

    print("Fill and clear...")
    demo_fill()
    time.sleep(0.3)

    print("Binary count (0-255)...")
    demo_binary(0.03)
    time.sleep(0.3)

    print("Flash...")
    demo_flash(3)

    all_off()
    print("Done.")


SEQUENCES = {
    "chase":   lambda: demo_chase(3),
    "binary":  demo_binary,
    "fill":    demo_fill,
    "flash":   demo_flash,
    "all_on":  all_on,
    "all_off": all_off,
    "demo":    run_demo,
}


if __name__ == "__main__":
    seq_name = sys.argv[1] if len(sys.argv) > 1 else "demo"

    if seq_name not in SEQUENCES:
        print(f"Unknown sequence '{seq_name}'. Options: {', '.join(SEQUENCES)}")
        sys.exit(1)

    try:
        setup()
        print(f"[*] 74HC595 on DATA={DATA_PIN}, CLK={CLOCK_PIN}, LATCH={LATCH_PIN}")
        print(f"[*] Running '{seq_name}'...")
        SEQUENCES[seq_name]()
    except KeyboardInterrupt:
        print("\n[*] Stopped.")
    finally:
        all_off()
        GPIO.cleanup()
