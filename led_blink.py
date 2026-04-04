#!/usr/bin/env python3
"""
led_blink.py — first GPIO experiment

LED connection required:
  - Physical pin 12 (BCM 18) → 220Ω resistor → LED anode (+)
  - LED cathode (−) → Physical pin 14 or any GND pin

If your LED is currently on pins 1 (3.3V) and 9 (GND):
  move the pin-1 wire to physical pin 12, keep GND on pin 9.

Run: python3 led_blink.py
"""

from gpiozero import LED
from time import sleep

LED_PIN = 18  # BCM numbering

def blink_n(led, n, on_time=0.3, off_time=0.2):
    for _ in range(n):
        led.on()
        sleep(on_time)
        led.off()
        sleep(off_time)

def morse_dot(led):
    led.on(); sleep(0.15); led.off(); sleep(0.1)

def morse_dash(led):
    led.on(); sleep(0.45); led.off(); sleep(0.1)

def morse_space(led):
    sleep(0.3)  # between letters

def morse_hello(led):
    """H E L L O in Morse"""
    # H: . . . .
    for _ in range(4): morse_dot(led)
    morse_space(led)
    # E: .
    morse_dot(led)
    morse_space(led)
    # L: . - . .
    morse_dot(led); morse_dash(led); morse_dot(led); morse_dot(led)
    morse_space(led)
    # L: . - . .
    morse_dot(led); morse_dash(led); morse_dot(led); morse_dot(led)
    morse_space(led)
    # O: - - -
    for _ in range(3): morse_dash(led)


if __name__ == "__main__":
    print(f"[*] Initializing LED on BCM {LED_PIN} (physical pin 12)")
    led = LED(LED_PIN)

    print("[*] Blinking 3 times to confirm circuit works...")
    blink_n(led, 3, on_time=0.5, off_time=0.3)
    sleep(0.5)

    print("[*] Sending HELLO in Morse code...")
    morse_hello(led)
    sleep(0.5)

    print("[*] Blinking fast 5 times...")
    blink_n(led, 5, on_time=0.1, off_time=0.1)

    led.off()
    print("[*] Done. LED off.")
