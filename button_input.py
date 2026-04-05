#!/usr/bin/env python3
"""
button_input.py — Read a button press from GPIO.

Circuit:
  Button one leg → physical pin 16 (BCM 23)
  Button other leg → physical pin 9 (GND)
  Internal pull-up enabled in software (no external resistor needed)

When button is pressed, it pulls pin 23 LOW.

Run:
  python3 ~/projects/gpio/button_input.py
"""

import time
import RPi.GPIO as GPIO

BUTTON_PIN = 23  # BCM numbering

def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    # Pull-up: pin reads HIGH normally, LOW when button pressed
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def wait_for_press(timeout=30.0):
    """Block until button pressed or timeout. Returns True if pressed."""
    start = time.time()
    while time.time() - start < timeout:
        if GPIO.input(BUTTON_PIN) == GPIO.LOW:
            return True
        time.sleep(0.02)
    return False


def debounced_press():
    """Wait for a clean button press (debounced)."""
    # Wait for press
    while GPIO.input(BUTTON_PIN) == GPIO.HIGH:
        time.sleep(0.01)
    # Debounce — confirm still pressed after 50ms
    time.sleep(0.05)
    if GPIO.input(BUTTON_PIN) == GPIO.HIGH:
        return False  # spurious
    # Wait for release
    while GPIO.input(BUTTON_PIN) == GPIO.LOW:
        time.sleep(0.01)
    time.sleep(0.05)  # debounce release
    return True


def main():
    setup()
    print("Button test — press the button (Ctrl+C to quit)")
    print(f"Listening on BCM pin {BUTTON_PIN} (physical pin 16)")
    print()

    press_count = 0
    try:
        while True:
            if debounced_press():
                press_count += 1
                print(f"Press #{press_count} detected at {time.strftime('%H:%M:%S')}")
                if press_count == 5:
                    print("Five presses — test complete.")
                    break
    except KeyboardInterrupt:
        print(f"\nStopped after {press_count} press(es).")
    finally:
        GPIO.cleanup()


if __name__ == "__main__":
    main()
