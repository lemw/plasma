"""Mock MicroPython hardware modules for testing chase_web.py."""
import asyncio
from typing import Optional


# ─── Mock time module ────────────────────────────────────────────────────────

class MockTime:
    """Mock for MicroPython time module."""
    _ticks = 0
    
    @classmethod
    def sleep(cls, seconds):
        """Mock blocking sleep."""
        pass
    
    @classmethod
    def ticks_ms(cls):
        """Return mock millisecond ticks."""
        cls._ticks += 50
        return cls._ticks
    
    @classmethod
    def ticks_add(cls, base, delta):
        """Add delta to base tick value."""
        return base + delta
    
    @classmethod
    def ticks_diff(cls, end, start):
        """Calculate difference between tick values."""
        return end - start
    
    @classmethod
    def reset(cls):
        """Reset mock time counter."""
        cls._ticks = 0


# ─── Mock machine module ─────────────────────────────────────────────────────

class Pin:
    """Mock GPIO Pin."""
    IN = 0
    OUT = 1
    PULL_UP = 1
    
    def __init__(self, pin, mode=None, pull=None):
        self.pin = pin
        self.mode = mode
        self.pull = pull
        self._value = 1 if pull == self.PULL_UP else 0
    
    def value(self, val=None):
        """Get or set pin value."""
        if val is not None:
            self._value = val
        return self._value


class PWM:
    """Mock PWM output."""
    def __init__(self, pin, freq=1000, duty_u16=0):
        self.pin = pin
        self.freq = freq
        self._duty = duty_u16
    
    def duty_u16(self, value=None):
        """Get or set PWM duty cycle (0-65535)."""
        if value is not None:
            self._duty = value
        return self._duty
    
    def deinit(self):
        """Deinitialize PWM."""
        pass


# ─── Mock plasma module ──────────────────────────────────────────────────────

class WS2812:
    """Mock WS2812 LED strip driver."""
    COLOR_ORDER_RGB = 0
    COLOR_ORDER_GRB = 1
    COLOR_ORDER_BGR = 2
    
    def __init__(self, num_leds, pio=0, sm=0, dat=15, color_order=COLOR_ORDER_RGB):
        self.num_leds = num_leds
        self.leds = [(0, 0, 0)] * num_leds
    
    def start(self):
        """Start the LED driver."""
        pass
    
    def set_rgb(self, index, r, g, b):
        """Set RGB color for a specific LED."""
        if 0 <= index < self.num_leds:
            self.leds[index] = (r, g, b)
    
    def get_rgb(self, index):
        """Get RGB color of a specific LED."""
        if 0 <= index < self.num_leds:
            return self.leds[index]
        return (0, 0, 0)


# ─── Mock network module ─────────────────────────────────────────────────────

class WLAN:
    """Mock WiFi network interface."""
    STA_IF = 0
    AP_IF = 1
    
    # Status constants
    STAT_IDLE = 0
    STAT_CONNECTING = 1
    STAT_WRONG_PASSWORD = -3
    STAT_NO_AP_FOUND = -2
    STAT_CONNECT_FAIL = -1
    STAT_GOT_IP = 3
    
    def __init__(self, interface):
        self.interface = interface
        self._active = False
        self._connected = False
        self._status = self.STAT_IDLE
        self._ip = "192.168.1.100"
    
    def active(self, state=None):
        """Get or set interface active state."""
        if state is not None:
            self._active = state
        return self._active
    
    def connect(self, ssid, password):
        """Connect to WiFi network."""
        self._status = self.STAT_CONNECTING
        # Simulate successful connection
        self._connected = True
        self._status = self.STAT_GOT_IP
    
    def disconnect(self):
        """Disconnect from WiFi."""
        self._connected = False
        self._status = self.STAT_IDLE
    
    def isconnected(self):
        """Check if connected to WiFi."""
        return self._connected
    
    def status(self):
        """Return connection status."""
        return self._status
    
    def ifconfig(self):
        """Return network configuration."""
        return (self._ip, "255.255.255.0", "192.168.1.1", "8.8.8.8")
    
    def config(self, **kwargs):
        """Configure interface parameters."""
        pass


# ─── Mock uasyncio module ────────────────────────────────────────────────────

class MockAsyncio:
    """Mock uasyncio using standard asyncio."""
    
    @staticmethod
    async def sleep(seconds):
        """Async sleep."""
        await asyncio.sleep(seconds)
    
    @staticmethod
    async def sleep_ms(milliseconds):
        """Async sleep in milliseconds."""
        await asyncio.sleep(milliseconds / 1000)
    
    @staticmethod
    async def gather(*tasks):
        """Run multiple coroutines concurrently."""
        return await asyncio.gather(*tasks)
    
    @staticmethod
    def run(coro):
        """Run a coroutine."""
        return asyncio.run(coro)
    
    @staticmethod
    async def start_server(callback, host, port):
        """Mock HTTP server - stores callback for testing."""
        # For testing, we'll just store the callback
        MockAsyncio._server_callback = callback
        return MockServerHandle()
    
    _server_callback = None


class MockServerHandle:
    """Mock server handle."""
    pass


class MockStreamReader:
    """Mock async stream reader."""
    def __init__(self, data: bytes):
        self.data = data
    
    async def read(self, n):
        """Read n bytes from stream."""
        result = self.data[:n]
        self.data = self.data[n:]
        return result


class MockStreamWriter:
    """Mock async stream writer."""
    def __init__(self):
        self.data = b""
        self._closed = False
    
    def write(self, data):
        """Write data to stream."""
        if isinstance(data, str):
            data = data.encode()
        self.data += data
    
    async def drain(self):
        """Wait for data to be written."""
        await asyncio.sleep(0)
    
    def close(self):
        """Close the writer."""
        self._closed = True
    
    async def wait_closed(self):
        """Wait for writer to close."""
        await asyncio.sleep(0)
    
    def get_response(self):
        """Get accumulated response data."""
        return self.data.decode()
