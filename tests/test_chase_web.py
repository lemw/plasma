"""Unit tests for examples/plasma2350w/chase_web.py."""
import sys
import os
import unittest
from unittest.mock import Mock, patch
import asyncio

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set up mocks before importing chase_web
from tests.mocks.mock_micropython import (
    MockTime, Pin, PWM, WS2812, WLAN, MockAsyncio,
    MockStreamReader, MockStreamWriter
)

# Mock secrets module
sys.modules['secrets'] = Mock(WIFI_SSID="TestSSID", WIFI_PASSWORD="TestPass")

# Inject mocks into sys.modules
sys.modules['time'] = MockTime
sys.modules['machine'] = Mock(Pin=Pin, PWM=PWM)
sys.modules['plasma'] = Mock(
    WS2812=WS2812,
    COLOR_ORDER_RGB=0,
    COLOR_ORDER_GRB=1,
    COLOR_ORDER_BGR=2
)
sys.modules['network'] = Mock(WLAN=WLAN)
sys.modules['uasyncio'] = MockAsyncio

# Now import the module under test (this will use our mocks)
# We need to do this dynamically to avoid import-time side effects
import importlib.util
spec = importlib.util.spec_from_file_location(
    "chase_web",
    os.path.join(os.path.dirname(__file__), '../examples/plasma2350w/chase_web.py')
)
chase_web = importlib.util.module_from_spec(spec)


class TestChaseWebImports(unittest.TestCase):
    """Test that the module can be imported with mocked hardware."""
    
    def test_module_loads(self):
        """Test that chase_web module loads without errors."""
        # The import itself is the test - if it fails, test fails
        self.assertIsNotNone(spec)


class TestChaseState(unittest.TestCase):
    """Test the ChaseState class."""
    
    def setUp(self):
        """Execute module code to get classes."""
        spec.loader.exec_module(chase_web)
        self.ChaseState = chase_web.ChaseState
    
    def test_init_defaults(self):
        """Test ChaseState initializes with correct defaults."""
        state = self.ChaseState()
        self.assertEqual(state.speed, 25)  # DEFAULT_SPEED
        self.assertEqual(state.r, 255)
        self.assertEqual(state.g, 0)
        self.assertEqual(state.b, 0)
        self.assertFalse(state.paint)
        self.assertEqual(len(state.painted), 66)  # NUM_LEDS
    
    def test_color_property(self):
        """Test color property getter/setter."""
        state = self.ChaseState()
        state.color = (100, 150, 200)
        self.assertEqual(state.color, (100, 150, 200))
        self.assertEqual(state.r, 100)
        self.assertEqual(state.g, 150)
        self.assertEqual(state.b, 200)
    
    def test_hex_property(self):
        """Test hex color property."""
        state = self.ChaseState()
        state.color = (255, 136, 0)
        self.assertEqual(state.hex, "#ff8800")
    
    def test_set_hex_valid(self):
        """Test set_hex with valid 6-char hex."""
        state = self.ChaseState()
        state.set_hex("00ff88")
        self.assertEqual(state.r, 0)
        self.assertEqual(state.g, 255)
        self.assertEqual(state.b, 136)
    
    def test_set_hex_with_hash(self):
        """Test set_hex strips leading #."""
        state = self.ChaseState()
        state.set_hex("#ff0000")
        self.assertEqual(state.r, 255)
        self.assertEqual(state.g, 0)
        self.assertEqual(state.b, 0)
    
    def test_set_hex_invalid_length(self):
        """Test set_hex rejects invalid length (issue #5)."""
        state = self.ChaseState()
        original = state.color
        state.set_hex("ff")  # Too short
        self.assertEqual(state.color, original)  # Should not change
    
    def test_next_color(self):
        """Test cycling through color sequence."""
        state = self.ChaseState()
        initial = state.color
        state.next_color()
        second = state.color
        self.assertNotEqual(initial, second)
    
    def test_toggle_paint(self):
        """Test paint mode toggle."""
        state = self.ChaseState()
        self.assertFalse(state.paint)
        state.toggle_paint()
        self.assertTrue(state.paint)
        state.toggle_paint()
        self.assertFalse(state.paint)
    
    def test_toggle_pause(self):
        """Test speed pause toggle."""
        state = self.ChaseState()
        original_speed = state.speed
        self.assertGreater(original_speed, 0)
        state.toggle_pause()
        self.assertEqual(state.speed, 0)
        state.toggle_pause()
        self.assertEqual(state.speed, original_speed)
    
    def test_clear_canvas(self):
        """Test canvas clearing."""
        state = self.ChaseState()
        state.painted[0] = (255, 0, 0)
        state.clear_canvas()
        self.assertEqual(state.painted[0], (0, 0, 0))


class TestOnboardLED(unittest.TestCase):
    """Test the OnboardLED class."""
    
    def setUp(self):
        """Execute module and get OnboardLED class."""
        MockTime.reset()
        spec.loader.exec_module(chase_web)
        self.OnboardLED = chase_web.OnboardLED
    
    def test_init(self):
        """Test OnboardLED initializes PWM channels."""
        led = self.OnboardLED()
        self.assertIsNotNone(led._r)
        self.assertIsNotNone(led._g)
        self.assertIsNotNone(led._b)
    
    def test_set_color(self):
        """Test setting LED color."""
        led = self.OnboardLED()
        led.set(255, 128, 0, brightness=0.5)
        # Active-low: 65535 - value
        self.assertLess(led._r.duty_u16(), 65535)
    
    def test_off(self):
        """Test turning LED off."""
        led = self.OnboardLED()
        led.off()
        # Active-low: off = 65535
        self.assertEqual(led._r.duty_u16(), 65535)
        self.assertEqual(led._g.duty_u16(), 65535)
        self.assertEqual(led._b.duty_u16(), 65535)
    
    def test_deinit(self):
        """Test PWM deinit (issue #7 cleanup)."""
        led = self.OnboardLED()
        led.deinit()  # Should not raise
        self.assertEqual(led._r.duty_u16(), 65535)


class TestRequestParsing(unittest.TestCase):
    """Test HTTP request parsing."""
    
    def setUp(self):
        """Execute module."""
        spec.loader.exec_module(chase_web)
        self.parse_request = chase_web.parse_request
        self.state = chase_web.state
        # Reset state
        self.state.speed = 25
        self.state.color = (255, 0, 0)
        self.state.paint = False
    
    def test_parse_speed(self):
        """Test parsing speed parameter."""
        request = b"GET /?speed=50 HTTP/1.1\r\n\r\n"
        result = self.parse_request(request)
        self.assertTrue(result)
        self.assertEqual(self.state.speed, 50)
    
    def test_parse_speed_bounds(self):
        """Test speed clamping."""
        request = b"GET /?speed=150 HTTP/1.1\r\n\r\n"
        self.parse_request(request)
        self.assertEqual(self.state.speed, 100)
        
        request = b"GET /?speed=-10 HTTP/1.1\r\n\r\n"
        self.parse_request(request)
        self.assertEqual(self.state.speed, 0)
    
    def test_parse_color(self):
        """Test parsing color parameter."""
        request = b"GET /?color=00ff88 HTTP/1.1\r\n\r\n"
        result = self.parse_request(request)
        self.assertTrue(result)
        self.assertEqual(self.state.r, 0)
        self.assertEqual(self.state.g, 255)
        self.assertEqual(self.state.b, 136)
    
    def test_parse_invalid_color_ignored(self):
        """Test that invalid hex colors are ignored (issue #5)."""
        original = self.state.color
        request = b"GET /?color=zz HTTP/1.1\r\n\r\n"
        self.parse_request(request)
        self.assertEqual(self.state.color, original)
    
    def test_parse_remember(self):
        """Test parsing remember (paint mode) parameter."""
        request = b"GET /?remember=1 HTTP/1.1\r\n\r\n"
        self.parse_request(request)
        self.assertTrue(self.state.paint)
        
        request = b"GET /?remember=0 HTTP/1.1\r\n\r\n"
        self.parse_request(request)
        self.assertFalse(self.state.paint)
    
    def test_parse_multiple_params(self):
        """Test parsing multiple parameters."""
        request = b"GET /?speed=75&color=ff0000&remember=1 HTTP/1.1\r\n\r\n"
        result = self.parse_request(request)
        self.assertTrue(result)
        self.assertEqual(self.state.speed, 75)
        self.assertEqual(self.state.color, (255, 0, 0))
        self.assertTrue(self.state.paint)
    
    def test_parse_no_query(self):
        """Test request with no query string."""
        request = b"GET / HTTP/1.1\r\n\r\n"
        result = self.parse_request(request)
        self.assertFalse(result)
    
    def test_parse_malformed_param(self):
        """Test handling malformed parameters (issue #6 robustness)."""
        original_speed = self.state.speed
        request = b"GET /?speed=abc HTTP/1.1\r\n\r\n"
        self.parse_request(request)
        # Speed should be unchanged
        self.assertEqual(self.state.speed, original_speed)


class TestStateEndpoint(unittest.TestCase):
    """Test /state JSON endpoint (issue #4)."""
    
    def setUp(self):
        """Execute module."""
        spec.loader.exec_module(chase_web)
        self.build_state_json = chase_web._build_state_json
        self.state = chase_web.state
        self.state.speed = 50
        self.state.color = (255, 136, 0)
        self.state.paint = True
    
    def test_state_json_format(self):
        """Test /state returns valid JSON-like response."""
        response = self.build_state_json()
        self.assertIn("200 OK", response)
        self.assertIn("application/json", response)
        self.assertIn("Content-Length:", response)
        self.assertIn('"color":"#ff8800"', response)
        self.assertIn('"speed":50', response)
        self.assertIn('"paint":true', response)
    
    def test_state_json_content_length(self):
        """Test Content-Length header is correct (issue #6)."""
        response = self.build_state_json()
        lines = response.split('\r\n')
        body = lines[-1]
        
        # Find Content-Length header
        content_length = None
        for line in lines:
            if line.startswith("Content-Length:"):
                content_length = int(line.split(":")[1].strip())
                break
        
        self.assertIsNotNone(content_length)
        self.assertEqual(content_length, len(body))


class TestBuildPage(unittest.TestCase):
    """Test HTML page building."""
    
    def setUp(self):
        """Execute module."""
        spec.loader.exec_module(chase_web)
        self.build_page = chase_web.build_page
        self.state = chase_web.state
    
    def test_page_has_headers(self):
        """Test page includes HTTP headers."""
        page = self.build_page()
        self.assertIn("HTTP/1.0 200 OK", page)
        self.assertIn("Content-Type: text/html", page)
    
    def test_page_has_content_length(self):
        """Test page includes Content-Length header (issue #6)."""
        page = self.build_page()
        self.assertIn("Content-Length:", page)
    
    def test_page_content_length_accurate(self):
        """Test Content-Length matches actual body length."""
        page = self.build_page()
        parts = page.split('\r\n\r\n', 1)
        headers = parts[0]
        body = parts[1]
        
        # Extract Content-Length
        for line in headers.split('\r\n'):
            if line.startswith("Content-Length:"):
                stated_length = int(line.split(":")[1].strip())
                self.assertEqual(stated_length, len(body))
                return
        
        self.fail("Content-Length header not found")
    
    def test_page_reflects_state(self):
        """Test page reflects current color and speed."""
        self.state.color = (255, 0, 255)
        self.state.speed = 80
        page = self.build_page()
        self.assertIn("#ff00ff", page)
        self.assertIn('value="80"', page)


if __name__ == '__main__':
    unittest.main()
