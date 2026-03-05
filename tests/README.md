# Plasma 2350W Test Suite

Comprehensive testing infrastructure for the Plasma 2350W examples, focused on the `chase_web.py` web-controlled LED animation.

## Overview

This test suite provides:
- **Unit tests** with mocked MicroPython hardware
- **Integration tests** for HTTP endpoints
- **Simulated RP2350W environment** (no physical hardware required)
- **CI/CD pipeline** via GitHub Actions

## Running Tests Locally

### Prerequisites

```bash
pip install -r requirements-test.txt
```

### Run All Tests

```bash
# All tests
python -m pytest tests/ -v

# Unit tests only
python -m pytest tests/test_chase_web.py -v

# Integration tests only
python -m pytest tests/test_chase_web_integration.py -v

# With coverage
python -m pytest tests/ --cov=examples/plasma2350w --cov-report=html
```

### Lint Code

```bash
ruff check examples/plasma2350w/
ruff format --check examples/plasma2350w/
```

## Test Structure

```
tests/
├── __init__.py
├── README.md                          # This file
├── mocks/
│   ├── __init__.py
│   └── mock_micropython.py           # Mock hardware modules
├── test_chase_web.py                 # Unit tests
└── test_chase_web_integration.py     # HTTP integration tests
```

## Mock Hardware

The test suite mocks all MicroPython-specific modules:

- **`plasma.WS2812`**: LED strip driver (stores colors in memory)
- **`machine.Pin`**: GPIO pins
- **`machine.PWM`**: PWM for onboard RGB LED
- **`network.WLAN`**: WiFi interface (simulated connection)
- **`uasyncio`**: Async I/O (maps to standard `asyncio`)
- **`time`**: Time functions with controllable tick counter

## What's Tested

### Unit Tests (`test_chase_web.py`)

- ✅ **ChaseState** class (color, speed, paint mode)
- ✅ **OnboardLED** PWM control and cleanup
- ✅ **HTTP request parsing** (query parameters)
- ✅ **Input validation** (hex colors, speed bounds)
- ✅ **State endpoint** JSON formatting
- ✅ **Page building** with Content-Length headers

### Integration Tests (`test_chase_web_integration.py`)

- ✅ **GET /** returns HTML page
- ✅ **GET /favicon.ico** returns 204 (optimization)
- ✅ **GET /state** returns JSON (live sync feature)
- ✅ **Parameter updates** (speed, color, paint mode)
- ✅ **Error handling** (malformed requests, invalid data)
- ✅ **HTTP response formatting** (headers, content-length)

## CI/CD Pipeline

See `.github/workflows/plasma2350w-testing.yml` for the automated pipeline:

1. **Lint**: Code quality checks with `ruff`
2. **Unit Tests**: Mock hardware tests
3. **Integration Tests**: HTTP server tests
4. **Syntax Check**: MicroPython syntax validation
5. **Functional Verification**: Complete test suite
6. **Code Quality**: Complexity and maintainability analysis

The pipeline runs on:
- Every push to `main`, `claude-opus`, or `gpt-suggestions`
- Every pull request to `main`
- When `examples/plasma2350w/` or `tests/` files change

## Adding New Tests

### Unit Test Example

```python
def test_new_feature(self):
    """Test description."""
    spec.loader.exec_module(chase_web)
    state = chase_web.ChaseState()
    # Test your feature
    self.assertEqual(state.some_value, expected)
```

### Integration Test Example

```python
def test_new_endpoint(self):
    """Test description."""
    async def test():
        request = b"GET /new-endpoint HTTP/1.1\r\n\r\n"
        response = await self._simulate_request(request)
        self.assertIn("expected content", response)
    
    asyncio.run(test())
```

## Limitations

- **No actual hardware**: Tests use mocks, not real RP2350W
- **No WiFi radio simulation**: Network layer is mocked
- **No PIO simulation**: LED strip operations are memory-only
- **Timing is simulated**: `time.sleep()` doesn't actually wait

For hardware-in-the-loop testing, use `mpremote` with a physical board.

## Related GitHub Issues

Tests verify fixes for:
- **#2**: JS throttling (client-side, verified via response format)
- **#3**: `/favicon.ico` short-circuit
- **#4**: `/state` JSON endpoint
- **#5**: Hex color validation in `set_hex()`
- **#6**: `Content-Length` header on responses
- **#7**: Graceful error handling (malformed requests)
- **#8**: Pre-computed paint dimming (performance)
- **#9**: Named constants for speed-delay formula

## Contributing

When adding features to `chase_web.py`:
1. Add corresponding unit tests to `test_chase_web.py`
2. Add integration tests to `test_chase_web_integration.py` if HTTP-related
3. Update mocks in `mock_micropython.py` if new hardware APIs are used
4. Run tests locally before pushing
5. CI will validate on push

## Questions?

See the main repo [README.md](../README.md) or open an issue.
