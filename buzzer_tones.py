#!/usr/bin/env python3
"""
buzzer_tones.py — passive buzzer tone sequences for Hermes

Passive buzzer on BCM 24 / physical pin 18:
  - Wire buzzer + leg to physical pin 18 (BCM 24)
  - Wire buzzer - leg to any GND (e.g. physical pin 20)

This uses gpiozero's TonalBuzzer which handles PWM frequency control.
Produces audible musical tones.

Usage:
  python3 buzzer_tones.py              # plays startup sequence
  python3 buzzer_tones.py alert        # plays short alert
  python3 buzzer_tones.py button       # plays button-press confirmation tone
  python3 buzzer_tones.py digest_done  # plays digest completion fanfare
"""

import sys
import time
from gpiozero import TonalBuzzer
from gpiozero.tones import Tone

BUZZER_PIN = 24  # BCM 24 / physical pin 18


def play_sequence(buzzer, notes: list[tuple]):
    """
    Play a sequence of (note, duration) pairs.
    note: MIDI note number (60=middle C), frequency in Hz, or None for rest
    duration: seconds
    """
    for note, duration in notes:
        if note is None:
            buzzer.stop()
        else:
            buzzer.play(note)
        time.sleep(duration)
    buzzer.stop()


# --- Musical sequences ---

def startup(buzzer):
    """Power-on / session start — three ascending notes."""
    play_sequence(buzzer, [
        (Tone("C4"), 0.1),
        (Tone("E4"), 0.1),
        (Tone("G4"), 0.2),
    ])

def alert(buzzer):
    """Short attention tone — single mid-high note."""
    play_sequence(buzzer, [
        (Tone("A4"), 0.15),
        (None,       0.05),
        (Tone("A4"), 0.15),
    ])

def button_press(buzzer):
    """Confirms button press — brief pleasant tone."""
    play_sequence(buzzer, [
        (Tone("E5"), 0.08),
        (None,       0.02),
        (Tone("G5"), 0.12),
    ])

def digest_done(buzzer):
    """Digest completed successfully — short fanfare."""
    play_sequence(buzzer, [
        (Tone("C5"), 0.12),
        (Tone("E5"), 0.12),
        (Tone("G5"), 0.12),
        (Tone("C6"), 0.25),
        (None,       0.08),
        (Tone("C6"), 0.15),
    ])


SEQUENCES = {
    "startup":     startup,
    "alert":       alert,
    "button":      button_press,
    "digest_done": digest_done,
}


if __name__ == "__main__":
    seq_name = sys.argv[1] if len(sys.argv) > 1 else "startup"

    if seq_name not in SEQUENCES:
        print(f"Unknown sequence '{seq_name}'. Options: {', '.join(SEQUENCES)}")
        sys.exit(1)

    try:
        buzzer = TonalBuzzer(BUZZER_PIN)
        print(f"[*] Playing '{seq_name}' on BCM {BUZZER_PIN}")
        SEQUENCES[seq_name](buzzer)
    except Exception as e:
        print(f"Error: {e}")
        print("Is the buzzer wired to BCM 24 / physical pin 18?")
        sys.exit(1)
