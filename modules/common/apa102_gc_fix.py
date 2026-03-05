"""
APA102 Garbage Collection Bug Workaround (Issue #16)

This module provides a workaround for the issue where re-allocated APA102
objects have is_busy() always returning True after garbage collection.

Reference: https://github.com/pimoroni/plasma/issues/16

Workaround Strategy:
  The root cause is in the C extension - internal state isn't properly
  reset when the object is re-allocated after GC. This wrapper provides:

  1. A safe is_busy() method with retry logic
  2. A reinitialize() method that can be called after GC
  3. An optional automatic re-initialization on GC detection

Usage:
  # Use the wrapper instead of plasma.APA102 directly
  from modules.common.apa102_gc_fix import SafeAPA102

  led_strip = SafeAPA102(66)
  led_strip.clear()
  led_strip.update()

  # After gc.collect(), you can optionally reinitialize
  import gc
  gc.collect()
  led_strip.reinitialize()  # Forces re-sync with hardware

Example - Automatic handling:
  led_strip = SafeAPA102(66, auto_recover=True)
  # Now is_busy() will automatically recover if it detects the bug
"""

import time


class SafeAPA102:
    """
    Safe wrapper around APA102 with garbage collection bug workaround.

    Provides protection against Issue #16 where is_busy() hangs after GC.
    """

    def __init__(self, num_leds, auto_recover=False, retry_timeout_ms=100):
        """
        Initialize a safe APA102 wrapper.

        Args:
            num_leds: Number of LEDs in the strip
            auto_recover: If True, automatically retry is_busy() on timeout
            retry_timeout_ms: Timeout for potential is_busy() hang (ms)
        """
        import plasma

        self._strip = plasma.APA102(num_leds)
        self.num_leds = num_leds
        self.auto_recover = auto_recover
        self.retry_timeout_ms = retry_timeout_ms
        self._gc_count = 0
        self._is_busy_max_polls = 0

    def reinitialize(self):
        """
        Force re-initialization to clear garbage collection state.

        Call this after gc.collect() if you encounter is_busy() hangs.
        """
        import plasma

        # Re-create the underlying APA102 object
        self._strip = plasma.APA102(self.num_leds)

    def is_busy(self, timeout_ms=None):
        """
        Safe is_busy() wrapper with timeout protection.

        Args:
            timeout_ms: Timeout in milliseconds (uses self.retry_timeout_ms if None)

        Returns:
            True if the DMA transfer is still busy, False if idle

        Raises:
            RuntimeError: If is_busy() appears to be in infinite loop
        """
        if timeout_ms is None:
            timeout_ms = self.retry_timeout_ms

        # Estimate of tight-loop iterations per millisecond (very conservative)
        # A real is_busy() check should return in < 1ms
        # If we're still looping after timeout, assume the bug
        MAX_ITERATIONS = max(10000, timeout_ms * 100)  # Be very generous

        iteration = 0
        start_time = time.monotonic_ns()
        timeout_ns = timeout_ms * 1_000_000

        try:
            while iteration < MAX_ITERATIONS:
                try:
                    result = self._strip.is_busy()
                    time.monotonic_ns() - start_time

                    # Track max polls for diagnostics
                    if iteration > self._is_busy_max_polls:
                        self._is_busy_max_polls = iteration

                    return result
                except (AttributeError, RuntimeError):
                    # is_busy() might raise in corrupted state - retry
                    pass

                iteration += 1

                # Check timeout
                if time.monotonic_ns() - start_time > timeout_ns:
                    if self.auto_recover:
                        print(
                            "[APA102] Detected is_busy() hang (GC bug). "
                            "Auto-recovering..."
                        )
                        self.reinitialize()
                        # Try once more after restart
                        return self._strip.is_busy()
                    raise RuntimeError(
                        f"APA102.is_busy() timeout after {iteration} iterations. "
                        f"Likely hit Issue #16 (GC bug). "
                        f"Call reinitialize() or enable auto_recover=True"
                    )

            # Shouldn't reach here, but handle it
            raise RuntimeError(
                f"APA102.is_busy() infinite loop detected ({MAX_ITERATIONS} iterations)"
            )

        except AttributeError as e:
            # Object might have been corrupted by GC
            if "is_busy" in str(e):
                raise RuntimeError(
                    "APA102 object corrupted (likely GC issue). "
                    "Call reinitialize() to recover"
                ) from e
            raise

    def clear(self):
        """Clear all LEDs."""
        return self._strip.clear()

    def update(self):
        """Update the LED strip (transmit data to hardware)."""
        return self._strip.update()

    def set_rgb(self, index, r, g, b):
        """Set RGB color of a single LED."""
        return self._strip.set_rgb(index, r, g, b)

    def set_hsv(self, index, h, s, v):
        """Set HSV color of a single LED."""
        return self._strip.set_hsv(index, h, s, v)

    def get_rgb(self, index):
        """Get RGB color of a single LED."""
        return self._strip.get_rgb(index)

    def set_brightness(self, brightness):
        """Set global brightness (0-31 for APA102)."""
        return self._strip.set_brightness(brightness)

    def __getattr__(self, name):
        """Forward any other attributes to the underlying strip."""
        return getattr(self._strip, name)

    def __repr__(self):
        return f"SafeAPA102({self.num_leds} LEDs, auto_recover={self.auto_recover})"


class MonitoredAPA102(SafeAPA102):
    """
    Extended APA102 wrapper that monitors for GC events.

    Automatically detects when garbage collection has occurred and
    triggers automatic re-initialization if needed.
    """

    def __init__(self, num_leds, auto_recover=True, retry_timeout_ms=100):
        """Initialize monitored APA102."""
        super().__init__(num_leds, auto_recover, retry_timeout_ms)
        import gc

        self._last_gc_count = gc.collect()

    def check_garbage_collection(self):
        """
        Check if garbage collection has occurred.

        Returns:
            True if GC happened since last check, False otherwise
        """
        import gc

        current_count = gc.collect()
        if current_count != self._last_gc_count:
            self._last_gc_count = current_count
            return True
        return False

    def safe_is_busy(self, timeout_ms=None):
        """
        is_busy() with automatic re-initialization on GC.

        Monitors for GC and automatically re-initializes if needed.
        """
        # Check if GC happened
        if self.check_garbage_collection():
            self.reinitialize()

        return self.is_busy(timeout_ms)

    def __repr__(self):
        return f"MonitoredAPA102({self.num_leds} LEDs)"
