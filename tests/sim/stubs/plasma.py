"""Stub for the MicroPython `plasma` C-extension module.

Supports WS2812 (NeoPixel) and APA102 strips.  All hardware operations
are no-ops so the application code can be exercised in a host-side
Python environment without physical LEDs attached.
"""

COLOR_ORDER_RGB = 0
COLOR_ORDER_RBG = 1
COLOR_ORDER_GRB = 2
COLOR_ORDER_GBR = 3
COLOR_ORDER_BRG = 4
COLOR_ORDER_BGR = 5


class WS2812:
    """Simulated WS2812 / NeoPixel LED strip."""

    def __init__(self, num_leds, pio=0, sm=0, dat=None, color_order=COLOR_ORDER_BGR):
        self.num_leds = num_leds
        self._leds = [(0, 0, 0)] * num_leds

    def start(self):
        pass

    def set_rgb(self, idx, r, g, b):
        if 0 <= idx < self.num_leds:
            self._leds[idx] = (r, g, b)

    def get(self, idx):
        return self._leds[idx] if 0 <= idx < self.num_leds else (0, 0, 0)


class APA102:
    """Simulated APA102 LED strip."""

    def __init__(self, num_leds, pio=0, sm=0, dat=None, clk=None, color_order=COLOR_ORDER_BGR):
        self.num_leds = num_leds
        self._leds = [(0, 0, 0)] * num_leds

    def start(self):
        pass

    def set_rgb(self, idx, r, g, b):
        if 0 <= idx < self.num_leds:
            self._leds[idx] = (r, g, b)

    def get(self, idx):
        return self._leds[idx] if 0 <= idx < self.num_leds else (0, 0, 0)
