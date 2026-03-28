"""Stub for MicroPython's `network` module (CYW43 / Pico W target).

The simulated WLAN always reports itself as connected with the loopback
address so wifi_connect() returns immediately and the web server binds
to 127.0.0.1.
"""

STA_IF = 0
AP_IF = 1

STAT_IDLE = 0
STAT_CONNECTING = 1
STAT_WRONG_PASSWORD = -3
STAT_NO_AP_FOUND = -2
STAT_CONNECT_FAIL = -1
STAT_GOT_IP = 3


class WLAN:
    def __init__(self, interface=STA_IF):
        self._interface = interface
        self._active = False

    def active(self, state=None):
        if state is not None:
            self._active = bool(state)
        return self._active

    def disconnect(self):
        pass

    def connect(self, ssid, password):
        pass

    def status(self):
        return STAT_GOT_IP

    def isconnected(self):
        return True

    def ifconfig(self):
        return ("127.0.0.1", "255.255.255.0", "127.0.0.1", "8.8.8.8")

    def config(self, *args, **kwargs):
        pass
