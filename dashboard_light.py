#!/usr/bin/env python3
"""
dashboard_light.py — status LED for hermes-dashboard.service

Green LED reflects health of the dashboard service:
  ON  = service running and responding
  OFF = service down or unhealthy

LED connection:
  - Physical pin 12 (BCM 18) → 220Ω resistor → LED anode (+)
  - LED cathode (−) → GND (physical pin 9 or 14)

Run continuously: python3 dashboard_light.py
Or as a systemd service: hermes-gpio-status.service
"""

import subprocess
import time
from gpiozero import LED

LED_PIN = 18
CHECK_INTERVAL = 30  # seconds


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


if __name__ == "__main__":
    led = LED(LED_PIN)
    print(f"[*] Dashboard status light on BCM {LED_PIN}")
    print(f"[*] Checking every {CHECK_INTERVAL}s")

    try:
        while True:
            healthy = is_dashboard_healthy()
            if healthy:
                led.on()
            else:
                # Blink slowly to indicate problem
                led.on(); time.sleep(0.5); led.off(); time.sleep(0.5)
                continue
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("\n[*] Stopping — LED off")
        led.off()
