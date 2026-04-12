#!/usr/bin/env python3
"""
button_buzzer_demo.py — button + buzzer integration demo

Press the button → buzzer plays a tone + LED flashes

This is a demonstration script (not a service). Run it manually to test
that the buzzer wiring works before integrating with the permanent services.

Hardware required:
  - LED already wired: BCM 18 (physical pin 12) + GND
  - Button already wired: BCM 23 (physical pin 16) + GND
  - Passive buzzer: BCM 24 (physical pin 18) → buzzer + leg; buzzer - leg → GND

Usage:
  python3 button_buzzer_demo.py
  Press Ctrl+C to stop.
"""

import time
from gpiozero import LED, Button, TonalBuzzer
from gpiozero.tones import Tone

LED_PIN    = 18
BUTTON_PIN = 23
BUZZER_PIN = 24

DEBOUNCE_TIME = 0.05  # seconds


def on_press(led, buzzer):
    """Called on each button press."""
    print(f"[button] pressed")

    # Quick flash + tone
    led.off()
    buzzer.play(Tone("E5"))
    time.sleep(0.08)
    buzzer.stop()
    led.on()
    time.sleep(0.05)

    buzzer.play(Tone("G5"))
    time.sleep(0.12)
    buzzer.stop()

    print("[button] done")


if __name__ == "__main__":
    led = LED(LED_PIN)
    buzzer = TonalBuzzer(BUZZER_PIN)
    button = Button(BUTTON_PIN, pull_up=True, bounce_time=DEBOUNCE_TIME)

    led.on()  # LED on while demo runs
    print(f"[*] Button+buzzer demo: BCM{BUTTON_PIN} + BCM{BUZZER_PIN}")
    print("[*] Press the button. Ctrl+C to exit.")

    button.when_pressed = lambda: on_press(led, buzzer)

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n[*] Exiting.")
    finally:
        buzzer.stop()
        led.off()
