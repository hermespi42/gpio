#!/usr/bin/env python3
"""
rgb_status.py — RGB LED dashboard status light

A colour-coded version of dashboard_light.py using the kit's RGB LED.
Replaces the single green LED (BCM 18) with a three-colour indicator.

--- Colour scheme ---
  Blue double-pulse  : night session (02:00–04:30) — Hermes is running
  Green triple-pulse : day-response signal (day-response.sh triggered)
  Solid green        : dashboard healthy
  Amber slow blink   : dashboard slow (response > 1s)
  Red slow blink     : dashboard down

--- Wiring (common-cathode RGB LED) ---
  Common cathode (longest leg, −) → physical pin 30 (GND)
  Red leg   → 220Ω → BCM 5  (physical pin 29)
  Green leg → 220Ω → BCM 6  (physical pin 31)
  Blue leg  → 220Ω → BCM 13 (physical pin 33)

Common-anode variant: wire common to 3.3V (pin 17) and invert logic
  in the COMMON_ANODE flag below.

Note: this script replaces dashboard_light.py / hermes-gpio-status.service.
Disconnect the old single LED from BCM 18 (pin 12) before running.

--- Run ---
  python3 rgb_status.py
  sudo systemctl restart hermes-gpio-status.service  (after updating service file)
"""

import os
import subprocess
import time
from datetime import datetime

from gpiozero import RGBLED

# GPIO pins (BCM numbering)
PIN_RED   = 5    # physical pin 29
PIN_GREEN = 6    # physical pin 31
PIN_BLUE  = 13   # physical pin 33

# Set True if your RGB LED has a common anode instead of common cathode
COMMON_ANODE = False

CHECK_INTERVAL = 30       # seconds between dashboard health checks
SLOW_THRESHOLD = 1.0      # seconds — response time above this = amber
SIGNAL_FILE = "/tmp/hermes-day-signal"

NIGHT_START = (2, 0)
NIGHT_END   = (4, 30)


def is_night_session() -> bool:
    now = datetime.now()
    current = now.hour * 60 + now.minute
    start   = NIGHT_START[0] * 60 + NIGHT_START[1]
    end     = NIGHT_END[0]   * 60 + NIGHT_END[1]
    return start <= current < end


def check_dashboard() -> tuple[bool, float]:
    """Return (healthy, response_time_seconds). healthy=False if service not active."""
    try:
        t0 = time.monotonic()
        result = subprocess.run(
            ["systemctl", "is-active", "hermes-dashboard.service"],
            capture_output=True, text=True, timeout=5
        )
        elapsed = time.monotonic() - t0
        return result.stdout.strip() == "active", elapsed
    except Exception:
        return False, 0.0


def set_color(led: RGBLED, r: float, g: float, b: float) -> None:
    """Set LED colour. Values 0.0–1.0. Inverted for common-anode."""
    if COMMON_ANODE:
        led.color = (1 - r, 1 - g, 1 - b)
    else:
        led.color = (r, g, b)


def off(led: RGBLED) -> None:
    if COMMON_ANODE:
        led.color = (1, 1, 1)
    else:
        led.off()


def double_pulse_blue(led: RGBLED) -> None:
    """Two quick blue blinks then a long pause — night session heartbeat."""
    set_color(led, 0, 0, 1)
    time.sleep(0.12)
    off(led)
    time.sleep(0.12)
    set_color(led, 0, 0, 1)
    time.sleep(0.12)
    off(led)
    time.sleep(1.5)


def triple_pulse_green(led: RGBLED) -> None:
    """Three quick green blinks — day-response signal."""
    for _ in range(3):
        set_color(led, 0, 1, 0)
        time.sleep(0.1)
        off(led)
        time.sleep(0.1)
    time.sleep(0.4)


def check_signal(led: RGBLED) -> None:
    """Flash green triple-pulse if day-signal file exists."""
    if os.path.exists(SIGNAL_FILE):
        try:
            os.remove(SIGNAL_FILE)
        except OSError:
            pass
        triple_pulse_green(led)


def sleep_with_signal_check(led: RGBLED, seconds: float) -> None:
    """Sleep for `seconds` but wake every 1s to check for day-signal."""
    elapsed = 0.0
    while elapsed < seconds:
        time.sleep(1)
        elapsed += 1
        check_signal(led)


if __name__ == "__main__":
    led = RGBLED(PIN_RED, PIN_GREEN, PIN_BLUE, active_high=not COMMON_ANODE)
    print(f"[*] RGB status light — R=BCM{PIN_RED}, G=BCM{PIN_GREEN}, B=BCM{PIN_BLUE}")
    print(f"[*] Common {'anode' if COMMON_ANODE else 'cathode'} mode")

    try:
        while True:
            check_signal(led)

            if is_night_session():
                double_pulse_blue(led)
                continue

            healthy, response_time = check_dashboard()

            if not healthy:
                # Red slow blink — dashboard down
                set_color(led, 1, 0, 0)
                time.sleep(0.5)
                off(led)
                time.sleep(0.5)

            elif response_time > SLOW_THRESHOLD:
                # Amber slow blink — dashboard slow
                set_color(led, 1, 0.5, 0)
                time.sleep(0.5)
                off(led)
                time.sleep(0.5)

            else:
                # Solid green — healthy
                set_color(led, 0, 1, 0)
                sleep_with_signal_check(led, CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("\n[*] Stopping — LED off")
        off(led)
