"""Stub for MicroPython's `machine` module.

Covers Pin and PWM — the only machine peripherals used by the
plasma_2350_w examples.  All hardware operations are no-ops.
"""


class Pin:
    IN = 0
    OUT = 1
    PULL_UP = 2
    PULL_DOWN = 3
    OPEN_DRAIN = 4

    def __init__(self, pin, mode=None, pull=None, value=None):
        self._pin = pin
        self._value = 1  # default HIGH (button not pressed)
        if value is not None:
            self._value = int(bool(value))

    def value(self, v=None):
        if v is not None:
            self._value = int(bool(v))
            return None
        return self._value

    def on(self):
        self._value = 1

    def off(self):
        self._value = 0

    def __call__(self, v=None):
        return self.value(v)


class PWM:
    def __init__(self, pin, freq=1000, duty_u16=0):
        self._pin = pin
        self._freq = freq
        self._duty = duty_u16

    def duty_u16(self, value=None):
        if value is not None:
            self._duty = value
            return None
        return self._duty

    def freq(self, value=None):
        if value is not None:
            self._freq = value
            return None
        return self._freq

    def deinit(self):
        pass
