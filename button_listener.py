#!/usr/bin/env python3
"""
button_listener.py — persistent button event service.

Runs continuously as hermes-button-listener.service.
When the button is pressed:
  1. Records timestamp to ~/.button_presses.json
  2. Posts an acknowledgment message on the board

Circuit:
  Button: physical pin 16 (BCM 23), other leg → GND (pull-up active)

The LED (BCM 18) is left alone — managed by hermes-gpio-status.service.
"""

import json
import uuid
import time
from datetime import datetime
from pathlib import Path
import RPi.GPIO as GPIO

BUTTON_PIN = 23
PRESSES_FILE = Path("/home/hermes/.button_presses.json")
MESSAGES_FILE = Path("/home/hermes/messages.json")

# Minimum seconds between registered presses (prevents accidental double-press)
DEBOUNCE_WINDOW = 2.0

last_press_time = 0.0


def load_presses() -> list:
    if not PRESSES_FILE.exists():
        return []
    try:
        return json.loads(PRESSES_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def record_press(ts: str) -> None:
    presses = load_presses()
    presses.append({"timestamp": ts, "responded": False})
    PRESSES_FILE.write_text(
        json.dumps(presses, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def post_board_message(text: str) -> None:
    """Append a message from hermes to messages.json without affecting read state."""
    try:
        if MESSAGES_FILE.exists():
            data = json.loads(MESSAGES_FILE.read_text(encoding="utf-8"))
        else:
            data = {"messages": []}
        data["messages"].append({
            "id": str(uuid.uuid4()),
            "from": "hermes",
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M"),
            "text": text,
            "read_by_hermes": True,
        })
        MESSAGES_FILE.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
    except Exception as e:
        print(f"[button_listener] Failed to post board message: {e}", flush=True)


def on_press(channel):
    global last_press_time
    now = time.time()
    if now - last_press_time < DEBOUNCE_WINDOW:
        return
    last_press_time = now

    ts = datetime.now().strftime("%Y-%m-%dT%H:%M")
    time_str = datetime.now().strftime("%H:%M")
    print(f"[{ts}] Button pressed.", flush=True)

    record_press(ts)
    post_board_message(
        f"Button pressed at {time_str}. I saw it — I'll respond properly in my next session at 02:00 CET."
    )


def main():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=on_press, bouncetime=200)

    print(f"[button_listener] Watching BCM {BUTTON_PIN} (physical pin 16)", flush=True)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[button_listener] Stopped.", flush=True)
    finally:
        GPIO.cleanup(BUTTON_PIN)


if __name__ == "__main__":
    main()
