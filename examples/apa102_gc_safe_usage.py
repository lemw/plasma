"""
Example: Safe APA102 usage with garbage collection handling

Demonstrates how to use the SafeAPA102 wrapper to avoid Issue #16 hang.
This shows both basic and advanced usage patterns.

For full documentation, see ISSUE_16_FIX.md and modules/common/apa102_gc_fix.py
"""

import time
import gc

# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE 1: Basic Safe Usage
# ─────────────────────────────────────────────────────────────────────────────


def example_basic_safe_usage():
    """
    Simple replacement for plasma.APA102 with automatic safety.

    Change from:
        led_strip = plasma.APA102(66)

    To:
        led_strip = SafeAPA102(66)

    That's it! Automatic timeout protection on is_busy().
    """
    from modules.common.apa102_gc_fix import SafeAPA102

    print("=" * 60)
    print("Example 1: Basic Safe Usage")
    print("=" * 60)

    # Create safe LED strip
    led_strip = SafeAPA102(66)
    print(f"✓ Created: {led_strip}")

    # Use normally
    led_strip.clear()
    led_strip.update()
    print("✓ Set all LEDs to black")

    # Set some colors
    led_strip.set_rgb(0, 255, 0, 0)  # Red
    led_strip.set_rgb(1, 0, 255, 0)  # Green
    led_strip.set_rgb(2, 0, 0, 255)  # Blue
    print("✓ Set RGB colors")

    # Safe is_busy() - won't hang even if GC occurred
    is_busy = led_strip.is_busy()
    print(f"✓ is_busy() returned: {is_busy} (safe, with timeout protection)")

    # Update strip
    led_strip.update()
    print("✓ Updated strip")

    return led_strip


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE 2: Manual Re-initialization After GC
# ─────────────────────────────────────────────────────────────────────────────


def example_manual_reinit():
    """
    Explicitly call reinitialize() after garbage collection.

    Use this if you know GC just happened and want to sync hardware state.
    """
    from modules.common.apa102_gc_fix import SafeAPA102

    print("\n" + "=" * 60)
    print("Example 2: Manual Re-initialization After GC")
    print("=" * 60)

    led_strip = SafeAPA102(66)
    led_strip.clear()
    led_strip.update()
    print("✓ Created and initialized LED strip")

    # Do some work...
    for i in range(10):
        led_strip.set_rgb(i, 255, 0, 0)
    led_strip.update()
    print("✓ Set 10 red LEDs")

    # Memory pressure - can trigger GC
    print("\nCreating memory pressure...")
    temp_buffer = bytearray(200000)
    del temp_buffer
    gc.collect()
    print(f"✓ Garbage collection done (mem free: {gc.mem_free()})")

    # Explicitly re-initialize for safety
    print("\nRe-initializing LED strip...")
    led_strip.reinitialize()
    print("✓ LED strip re-initialized")

    # Now safe to use again
    is_busy = led_strip.is_busy()
    print(f"✓ is_busy() returned: {is_busy} (should be False)")

    led_strip.clear()
    led_strip.update()
    print("✓ Cleared and updated strip")


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE 3: Automatic Recovery Mode
# ─────────────────────────────────────────────────────────────────────────────


def example_auto_recovery():
    """
    Use auto_recover=True for maximum safety.

    If is_busy() detects a hang, it automatically recovers.
    """
    from modules.common.apa102_gc_fix import SafeAPA102

    print("\n" + "=" * 60)
    print("Example 3: Automatic Recovery Mode")
    print("=" * 60)

    # Enable auto-recovery
    led_strip = SafeAPA102(66, auto_recover=True)
    print(f"✓ Created with auto_recover=True: {led_strip}")

    # Normal operations
    led_strip.clear()
    for i in range(66):
        h = (i * 360) // 66
        led_strip.set_hsv(i, h, 255, 255)
    led_strip.update()
    print("✓ Set rainbow colors")

    # Even if GC happens, is_busy() will handle it
    print("\nSimulating GC and re-allocation...")
    temp = bytearray(150000)
    del temp
    gc.collect()

    # This will auto-recover if needed
    try:
        is_busy = led_strip.is_busy()
        print(f"✓ is_busy() returned: {is_busy} (auto-recovered if needed)")
    except RuntimeError as e:
        print(f"✗ Even with auto-recovery: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE 4: GC-Aware Animation Loop
# ─────────────────────────────────────────────────────────────────────────────


def example_gc_aware_animation():
    """
    Animation loop with GC awareness.

    Demonstrates a real animation that handles GC correctly.
    """
    from modules.common.apa102_gc_fix import SafeAPA102

    print("\n" + "=" * 60)
    print("Example 4: GC-Aware Animation Loop")
    print("=" * 60)

    NUM_LEDS = 66
    led_strip = SafeAPA102(NUM_LEDS, auto_recover=True)
    print("✓ Created the LED strip")

    print("\nRunning color chase animation for 2 seconds...")
    print("(Will handle GC automatically if it occurs)\n")

    start_time = time.monotonic()
    frame = 0

    while time.monotonic() - start_time < 2:
        # Chase animation
        led_strip.clear()
        pos = frame % NUM_LEDS

        # Head
        led_strip.set_rgb(pos, 200, 200, 200)

        # Trail
        for i in range(1, 5):
            trail_pos = (pos - i) % NUM_LEDS
            brightness = (5 - i) * 50
            led_strip.set_rgb(trail_pos, brightness, brightness, brightness)

        led_strip.update()

        # Wait for transfer to complete (safe - won't hang)
        while led_strip.is_busy():
            pass

        # Small delay between frames
        time.sleep(0.03)
        frame += 1

    print(f"✓ Animation complete ({frame} frames)")
    led_strip.clear()
    led_strip.update()
    while led_strip.is_busy():
        pass
    print("✓ Strip cleared")


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE 5: Monitored APA102 (Advanced)
# ─────────────────────────────────────────────────────────────────────────────


def example_monitored():
    """
    Advanced: Use MonitoredAPA102 for automatic GC detection.

    This wrapper detects GC and automatically re-initializes.
    Use safe_is_busy() instead of is_busy().
    """
    from modules.common.apa102_gc_fix import MonitoredAPA102

    print("\n" + "=" * 60)
    print("Example 5: Monitored APA102 (Advanced)")
    print("=" * 60)

    # Create monitored strip
    led_strip = MonitoredAPA102(66)
    print(f"✓ Created: {led_strip}")
    print("  (Automatically monitors for GC)")

    # Use safe_is_busy() instead of is_busy()
    led_strip.clear()

    # Safe version handles GC automatically
    while led_strip.safe_is_busy():
        pass
    print("✓ Initial clear complete")

    # Simulate work with potential GC
    for i in range(10):
        led_strip.set_rgb(i, (i * 25) % 256, 100, 100)
    led_strip.update()

    # Monitor will detect GC and recover automatically
    while led_strip.safe_is_busy():
        pass

    print("✓ Monitor automatically recovered from GC if needed")


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE 6: Comparison - Before and After
# ─────────────────────────────────────────────────────────────────────────────


def example_comparison():
    """
    Side-by-side comparison of original vs safe approach.
    """
    print("\n" + "=" * 60)
    print("Example 6: Before and After Comparison")
    print("=" * 60)

    print("\n❌ BEFORE (prone to hanging):")
    print("""
    import plasma
    import gc

    led_strip = plasma.APA102(66)
    led_strip.clear()
    led_strip.update()

    # After garbage collection...
    gc.collect()
    led_strip = plasma.APA102(66)

    # This hangs forever! ❌
    while led_strip.is_busy():  # Always True!
        pass
    """)

    print("\n✅ AFTER (safe, with workaround):")
    print("""
    from modules.common.apa102_gc_fix import SafeAPA102
    import gc

    led_strip = SafeAPA102(66)  # Drop-in replacement
    led_strip.clear()
    led_strip.update()

    # After garbage collection...
    gc.collect()
    led_strip.reinitialize()  # Optional: force re-init

    # This works safely! ✅
    while led_strip.is_busy():  # Timeout protection + auto-recovery
        pass
    """)

    print("\n✨ Key improvements:")
    print("  • Drop-in replacement (just change import)")
    print("  • Timeout protection on is_busy()")
    print("  • Optional auto-recovery")
    print("  • Optional GC monitoring")
    print("  • No hanging!")


# ─────────────────────────────────────────────────────────────────────────────
# Main Entry Point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        print("\nAPA102 Safe Usage Examples")
        print("=" * 60)
        print("\nThese examples demonstrate safe APA102 usage with GC handling.")
        print("Run individually or together to learn the different approaches.\n")

        # Run examples (commented out to avoid hardware/mock issues)
        # Uncomment to run on actual hardware:

        # example_basic_safe_usage()
        # example_manual_reinit()
        # example_auto_recovery()
        # example_gc_aware_animation()
        # example_monitored()
        example_comparison()

        print("\n" + "=" * 60)
        print("Examples complete!")
        print("=" * 60)
        print("\nFor more information, see:")
        print("  • ISSUE_16_FIX.md - Complete analysis")
        print("  • modules/common/apa102_gc_fix.py - Implementation")
        print("  • tests/test_apa102_gc.py - Test case")

    except (RuntimeError, OSError, ImportError) as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
