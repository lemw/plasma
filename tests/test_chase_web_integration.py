"""Integration tests for chase_web HTTP server."""
import sys
import os
import unittest
import asyncio
from unittest.mock import Mock

# Add project root to path  
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set up mocks
from tests.mocks.mock_micropython import (
    MockTime, Pin, PWM, WS2812, WLAN, MockAsyncio,
    MockStreamReader, MockStreamWriter
)

sys.modules['secrets'] = Mock(WIFI_SSID="TestSSID", WIFI_PASSWORD="TestPass")
sys.modules['time'] = MockTime
sys.modules['machine'] = Mock(Pin=Pin, PWM=PWM)
sys.modules['plasma'] = Mock(WS2812=WS2812, COLOR_ORDER_RGB=0, COLOR_ORDER_GRB=1, COLOR_ORDER_BGR=2)
sys.modules['network'] = Mock(WLAN=WLAN)
sys.modules['uasyncio'] = MockAsyncio

# Import module under test
import importlib.util
spec = importlib.util.spec_from_file_location(
    "chase_web",
    os.path.join(os.path.dirname(__file__), '../examples/plasma2350w/chase_web.py')
)
chase_web = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chase_web)


class TestWebServerIntegration(unittest.TestCase):
    """Integration tests for HTTP server endpoints."""
    
    def setUp(self):
        """Reset state before each test."""
        MockTime.reset()
        chase_web.state.speed = 25
        chase_web.state.color = (255, 0, 0)
        chase_web.state.paint = False
    
    async def _simulate_request(self, request_data):
        """Simulate an HTTP request to the server handler."""
        reader = MockStreamReader(request_data)
        writer = MockStreamWriter()
        
        # Get the handle function from web_server
        # We need to create a mock WLAN and start the server to capture the handler
        wlan = WLAN(WLAN.STA_IF)
        wlan._connected = True
        
        # Run web_server briefly to register handler
        server_task = asyncio.create_task(chase_web.web_server(wlan))
        await asyncio.sleep(0.01)  # Let it register
        
        # Get the registered handler
        handle = MockAsyncio._server_callback
        self.assertIsNotNone(handle, "Server handler not registered")
        
        # Call the handler
        await handle(reader, writer)
        server_task.cancel()
        
        try:
            await server_task
        except asyncio.CancelledError:
            pass
        
        return writer.get_response()
    
    def test_root_request_returns_html(self):
        """Test GET / returns HTML page."""
        async def test():
            request = b"GET / HTTP/1.1\r\nHost: test\r\n\r\n"
            response = await self._simulate_request(request)
            self.assertIn("200 OK", response)
            self.assertIn("text/html", response)
            self.assertIn("Plasma Chase", response)
        
        asyncio.run(test())
    
    def test_favicon_returns_204(self):
        """Test /favicon.ico returns 204 (issue #3)."""
        async def test():
            request = b"GET /favicon.ico HTTP/1.1\r\nHost: test\r\n\r\n"
            response = await self._simulate_request(request)
            self.assertIn("204 No Content", response)
            self.assertNotIn("<!DOCTYPE", response)  # No HTML body
        
        asyncio.run(test())
    
    def test_state_endpoint_returns_json(self):
        """Test /state returns JSON (issue #4)."""
        async def test():
            chase_web.state.color = (0, 255, 136)
            chase_web.state.speed = 60
            chase_web.state.paint = True
            
            request = b"GET /state HTTP/1.1\r\nHost: test\r\n\r\n"
            response = await self._simulate_request(request)
            
            self.assertIn("200 OK", response)
            self.assertIn("application/json", response)
            self.assertIn('"color":"#00ff88"', response)
            self.assertIn('"speed":60', response)
            self.assertIn('"paint":true', response)
        
        asyncio.run(test())
    
    def test_param_update_returns_204(self):
        """Test parameter updates return 204 (issue #2 optimization)."""
        async def test():
            request = b"GET /?speed=75 HTTP/1.1\r\nHost: test\r\n\r\n"
            response = await self._simulate_request(request)
            self.assertIn("204 No Content", response)
            self.assertEqual(chase_web.state.speed, 75)
        
        asyncio.run(test())
    
    def test_color_update(self):
        """Test color parameter updates work."""
        async def test():
            request = b"GET /?color=ff8800 HTTP/1.1\r\nHost: test\r\n\r\n"
            response = await self._simulate_request(request)
            self.assertIn("204", response)
            self.assertEqual(chase_web.state.color, (255, 136, 0))
        
        asyncio.run(test())
    
    def test_paint_mode_toggle(self):
        """Test paint mode can be toggled via remember param."""
        async def test():
            self.assertFalse(chase_web.state.paint)
            
            request = b"GET /?remember=1 HTTP/1.1\r\nHost: test\r\n\r\n"
            await self._simulate_request(request)
            self.assertTrue(chase_web.state.paint)
            
            request = b"GET /?remember=0 HTTP/1.1\r\nHost: test\r\n\r\n"
            await self._simulate_request(request)
            self.assertFalse(chase_web.state.paint)
        
        asyncio.run(test())
    
    def test_multiple_sequential_requests(self):
        """Test multiple requests in sequence."""
        async def test():
            # Set speed
            request1 = b"GET /?speed=10 HTTP/1.1\r\n\r\n"
            await self._simulate_request(request1)
            self.assertEqual(chase_web.state.speed, 10)
            
            # Set color
            request2 = b"GET /?color=0000ff HTTP/1.1\r\n\r\n"
            await self._simulate_request(request2)
            self.assertEqual(chase_web.state.color, (0, 0, 255))
            
            # Check state reflects both
            request3 = b"GET /state HTTP/1.1\r\n\r\n"
            response = await self._simulate_request(request3)
            self.assertIn('"speed":10', response)
            self.assertIn('"color":"#0000ff"', response)
        
        asyncio.run(test())
    
    def test_invalid_color_handled(self):
        """Test server handles invalid color gracefully (issue #5)."""
        async def test():
            original = chase_web.state.color
            request = b"GET /?color=gg HTTP/1.1\r\n\r\n"
            response = await self._simulate_request(request)
            # Should return 204 but not update color
            self.assertIn("204", response)
            self.assertEqual(chase_web.state.color, original)
        
        asyncio.run(test())
    
    def test_malformed_request_handled(self):
        """Test server handles malformed requests (issue #7 error handling)."""
        async def test():
            # Request with no proper HTTP structure
            request = b"GARBAGE\r\n\r\n"
            # Should not crash
            try:
                response = await self._simulate_request(request)
                # Any response is fine, just shouldn't crash
                self.assertIsInstance(response, str)
            except Exception as e:
                self.fail(f"Server crashed on malformed request: {e}")
        
        asyncio.run(test())


class TestWebServerResponses(unittest.TestCase):
    """Test HTTP response formatting."""
    
    def test_html_response_has_correct_headers(self):
        """Test HTML response has all required headers."""
        page = chase_web.build_page()
        lines = page.split('\r\n')
        
        # Check status line
        self.assertEqual(lines[0], "HTTP/1.0 200 OK")
        
        # Check required headers present
        headers = '\r\n'.join(lines[:10])  # First few lines
        self.assertIn("Content-Type: text/html", headers)
        self.assertIn("Content-Length:", headers)
        self.assertIn("Connection: close", headers)
    
    def test_json_response_has_correct_headers(self):
        """Test JSON response has correct headers."""
        response = chase_web._build_state_json()
        lines = response.split('\r\n')
        
        self.assertEqual(lines[0], "HTTP/1.0 200 OK")
        headers = '\r\n'.join(lines[:10])
        self.assertIn("Content-Type: application/json", headers)
        self.assertIn("Content-Length:", headers)
    
    def test_204_response_format(self):
        """Test 204 No Content response format."""
        response = chase_web._RESP_204
        self.assertIn("204 No Content", response)
        self.assertIn("Connection: close", response)


if __name__ == '__main__':
    unittest.main()
