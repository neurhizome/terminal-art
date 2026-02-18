#!/usr/bin/env python3
"""
keyboard.py - Non-blocking keyboard input for interactive control

Allows reading keyboard input without blocking the main loop.
Perfect for real-time parameter tuning and capturing screenshots.
"""

import sys
import select
import tty
import termios
from typing import Optional


class KeyboardInput:
    """
    Non-blocking keyboard input reader.

    Usage:
        kb = KeyboardInput()
        kb.start()

        while running:
            key = kb.get_key()
            if key == 'c':
                capture_screenshot()
            elif key == 'q':
                break

        kb.stop()
    """

    def __init__(self):
        self.old_settings = None
        self.started = False

    def start(self):
        """Enable non-blocking keyboard input"""
        if self.started:
            return

        try:
            self.old_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
            self.started = True
        except:
            # Terminal doesn't support this (e.g., not a TTY)
            pass

    def stop(self):
        """Restore normal keyboard input"""
        if not self.started:
            return

        try:
            if self.old_settings:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
            self.started = False
        except:
            pass

    def get_key(self) -> Optional[str]:
        """
        Get pressed key without blocking.

        Returns:
            Key character if pressed, None otherwise
        """
        if not self.started:
            return None

        try:
            # Check if input is available
            if select.select([sys.stdin], [], [], 0)[0]:
                key = sys.stdin.read(1)
                return key
        except:
            pass

        return None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()
