#!/usr/bin/env python3
"""
button_led_toggle.py — toggle LED with button press (standalone demo)

This is a test script to confirm button hardware works. The LED and button pins
are normally managed by running services. Stop both before running this,
then restart them when done:

  sudo systemctl stop hermes-gpio-status hermes-button-listener
  python3 ~/projects/gpio/button_led_toggle.py
  sudo systemctl start hermes-gpio-status hermes-button-listener

Circuit:
  LED: physical pin 12 (BCM 18) → 220Ω resistor → LED anode → GND
  Button: physical pin 16 (BCM 23), other leg → GND (pull-up active)

Each press toggles the LED. Ctrl+C to stop.
"""

import time
from gpiozero import LED, Button

LED_PIN = 18
BUTTON_PIN = 23


def main():
    led = LED(LED_PIN)
    button = Button(BUTTON_PIN, pull_up=True, bounce_time=0.05)

    print("Button-LED toggle test")
    print(f"  LED on BCM {LED_PIN} (physical pin 12)")
    print(f"  Button on BCM {BUTTON_PIN} (physical pin 16)")
    print("  Press the button to toggle the LED. Ctrl+C to stop.")
    print()

    led.off()
    led_state = False
    press_count = 0

    def on_press():
        nonlocal led_state, press_count
        press_count += 1
        led_state = not led_state
        if led_state:
            led.on()
        else:
            led.off()
        print(f"Press #{press_count}: LED {'ON' if led_state else 'OFF'}")

    button.when_pressed = on_press

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print(f"\nDone. {press_count} press(es) counted.")
    finally:
        led.off()
        led.close()
        button.close()


if __name__ == "__main__":
    main()
