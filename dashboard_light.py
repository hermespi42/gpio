#!/usr/bin/env python3
"""
dashboard_light.py — status LED for hermes-dashboard.service

LED patterns:
  Night session (02:00–04:30 local):
    Double-pulse (heartbeat): blink blink ... pause — Hermes is running
  Normal hours, dashboard healthy:
    Solid ON
  Normal hours, dashboard down:
    Slow single blink

LED connection:
  - Physical pin 12 (BCM 18) → 220Ω resistor → LED anode (+)
  - LED cathode (−) → GND (physical pin 9 or 14)

Run continuously: python3 dashboard_light.py
Or as a systemd service: hermes-gpio-status.service
"""

import os
import subprocess
import time
from datetime import datetime
from gpiozero import LED

LED_PIN = 18
CHECK_INTERVAL = 30  # seconds between health checks (normal mode)
SIGNAL_FILE = "/tmp/hermes-day-signal"  # touch this to trigger a "responding" flash

# Night session window (local time)
NIGHT_START = (2, 0)   # 02:00
NIGHT_END   = (4, 30)  # 04:30


def is_dashboard_healthy() -> bool:
    """Check if hermes-dashboard.service is active."""
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "hermes-dashboard.service"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip() == "active"
    except Exception:
        return False


def is_night_session() -> bool:
    """Return True if current local time is within the night session window."""
    now = datetime.now()
    h, m = now.hour, now.minute
    start_m = NIGHT_START[0] * 60 + NIGHT_START[1]
    end_m   = NIGHT_END[0]   * 60 + NIGHT_END[1]
    current = h * 60 + m
    return start_m <= current < end_m


def double_pulse(led):
    """Two quick blinks then a long pause — night session heartbeat."""
    led.on();  time.sleep(0.12)
    led.off(); time.sleep(0.12)
    led.on();  time.sleep(0.12)
    led.off(); time.sleep(1.5)


def triple_pulse(led):
    """Three quick blinks — daytime response signal."""
    for _ in range(3):
        led.on();  time.sleep(0.1)
        led.off(); time.sleep(0.1)
    time.sleep(0.4)


def check_signal(led):
    """Check for the day-signal file and flash if found."""
    if os.path.exists(SIGNAL_FILE):
        try:
            os.remove(SIGNAL_FILE)
        except OSError:
            pass
        triple_pulse(led)


def sleep_with_signal_check(led, seconds):
    """Sleep for `seconds` but wake every 1s to check for day-signal."""
    elapsed = 0
    while elapsed < seconds:
        time.sleep(1)
        elapsed += 1
        check_signal(led)


if __name__ == "__main__":
    led = LED(LED_PIN)
    print(f"[*] Dashboard status light on BCM {LED_PIN}")

    try:
        while True:
            check_signal(led)

            if is_night_session():
                # Heartbeat pattern during my working hours
                double_pulse(led)
                continue

            healthy = is_dashboard_healthy()
            if healthy:
                led.on()
                sleep_with_signal_check(led, CHECK_INTERVAL)
            else:
                # Slow blink — dashboard down
                led.on();  time.sleep(0.5)
                led.off(); time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n[*] Stopping — LED off")
        led.off()
