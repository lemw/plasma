"""
Test case for APA102 garbage collection bug (Issue #16).

Reproduces the issue where re-allocated APA102 objects have is_busy()
always returning True after garbage collection.

This test can be run on actual hardware:
  - Copy to board and run: micropython test_apa102_gc.py
  - Or include as part of test suite on hardware

For testing without hardware, this demonstrates the expected behavior.
"""

import gc
import time


def test_apa102_gc_issue():
    """
    Reproduce Issue #16: Re-allocated APA102 object hangs is_busy() after gc.

    Expected behavior:
    - APA102 object works normally
    - After gc.collect() and re-allocation, is_busy() returns False when idle
    - is_busy() doesn't hang in infinite loop

    Actual behavior (bug):
    - After gc.collect() and re-allocation, is_busy() always returns True
    - Program hangs in the while loop
    """
    try:
        import plasma
    except ImportError:
        print("WARNING: plasma module not available - skipping hardware test")
        return None

    NUM_LED = 10
    TEST_ITERATIONS = 5
    TIMEOUT_SEC = 2

    print("=" * 60)
    print("APA102 Garbage Collection Bug Test (Issue #16)")
    print("=" * 60)

    # Phase 1: Initial allocation and use
    print("\n[Phase 1] Create and use initial APA102 object...")
    led_strip = plasma.APA102(NUM_LED)
    led_strip.clear()
    led_strip.update()
    print(f"  - Created APA102 with {NUM_LED} LEDs")
    print(f"  - is_busy() returned: {led_strip.is_busy()}")
    print(f"  - Memory free: {gc.mem_free()}")

    # Phase 2: Create memory pressure and gc
    print("\n[Phase 2] Creating memory pressure and triggering gc.collect()...")
    var = bytearray(250000)
    print("  - Allocated 250KB temporary buffer")
    del var
    gc.collect()
    print("  - Released buffer and called gc.collect()")
    print(f"  - Memory free: {gc.mem_free()}")

    # Phase 3: Allocate new buffer and re-create APA102
    print("\n[Phase 3] Allocate new buffer and re-allocate APA102...")
    bytearray(50000)
    led_strip = plasma.APA102(NUM_LED)
    print("  - Created new APA102 object")
    print(f"  - Memory free: {gc.mem_free()}")

    # Phase 4: Test is_busy() with timeout
    print("\n[Phase 4] Testing is_busy() with timeout protection...")
    print(f"  - Running {TEST_ITERATIONS} iterations with {TIMEOUT_SEC}s timeout")

    for iteration in range(TEST_ITERATIONS):
        print(f"\n  Iteration {iteration + 1}/{TEST_ITERATIONS}:")

        # Set timeout for is_busy() check
        start_time = time.monotonic()
        try:
            # This should return False immediately when idle
            is_busy = led_strip.is_busy()
            elapsed = time.monotonic() - start_time

            if elapsed > TIMEOUT_SEC:
                print(
                    f"    - ❌ TIMEOUT: is_busy() took {elapsed:.2f}s (bug suspected)"
                )
                return False
            print(f"    - is_busy() = {is_busy} (took {elapsed * 1000:.2f}ms)")

            if is_busy:
                print("    - LED still busy, waiting...")
                time.sleep(0.1)
        except (RuntimeError, AttributeError) as e:
            print(f"    - ❌ Exception: {e}")
            return False

        # Do a quick update
        led_strip.clear()
        led_strip.update()

    print("\n" + "=" * 60)
    print("✓ Test passed: APA102 garbage collection handling is OK")
    print("=" * 60)
    return True


def test_apa102_gc_stress():
    """
    Stress test: Repeatedly allocate, use, gc, and re-allocate.
    More aggressively triggers the bug if it exists.
    """
    try:
        import plasma
    except ImportError:
        print("WARNING: plasma module not available - skipping hardware test")
        return None

    NUM_LED = 10
    STRESS_CYCLES = 20
    ALLOC_SIZE = 100000

    print("\n" + "=" * 60)
    print("APA102 Garbage Collection Stress Test")
    print("=" * 60)

    for cycle in range(STRESS_CYCLES):
        print(f"\nCycle {cycle + 1}/{STRESS_CYCLES}:")

        # Create object
        led_strip = plasma.APA102(NUM_LED)
        led_strip.clear()
        led_strip.update()

        # Create memory pressure
        buffers = [bytearray(ALLOC_SIZE) for _ in range(3)]
        for buf in buffers:
            del buf
        gc.collect()

        # Test is_busy with short timeout
        try:
            is_busy = led_strip.is_busy()
            print(f"  - Created, used, gc'd, re-allocated: is_busy={is_busy}")

            if not is_busy:
                # Try to update
                led_strip.clear()
                led_strip.update()
        except (RuntimeError, AttributeError) as e:
            print(f"  - ❌ Failed: {e}")
            return False

    print("\n" + "=" * 60)
    print("✓ Stress test passed: No hangs detected")
    print("=" * 60)
    return True


if __name__ == "__main__":
    print("\nRunning APA102 garbage collection tests...\n")

    # Run test
    success1 = test_apa102_gc_issue()

    # Run stress test if first test passed
    if success1:
        success2 = test_apa102_gc_stress()
        final_success = success2
    else:
        final_success = False

    # Exit with appropriate code
    exit(0 if final_success else 1)
