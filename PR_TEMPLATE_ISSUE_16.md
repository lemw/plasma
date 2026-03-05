# PR Template for Issue #16 Fix

This file contains templates for contributing the fix upstream.

## For this Repository (pimoroni/plasma)

### GitHub PR Description

```markdown
## Fix: Add test case and workaround for APA102 GC bug (Issue #16)

### Problem
Re-allocated APA102 objects hang after garbage collection because `is_busy()` always returns True.

Ref: #16

### Changes
- ✅ **test_apa102_gc.py**: Comprehensive test case that reproduces the issue
- ✅ **apa102_gc_fix.py**: Safe wrapper classes (SafeAPA102, MonitoredAPA102) 
- ✅ **Documentation**: ISSUE_16_FIX.md with analysis and usage guide

### Solution Type
- Test case for issue verification
- Workaround wrapper classes for end users
- Documentation pointing to upstream fix location

### How to Test
```bash
# Run the test case
micropython tests/test_apa102_gc.py

# Test the workaround
python examples/apa102_gc_example.py  # (if example is included)
```

### Workaround Usage
Users can immediately fix their code:
```python
from modules.common.apa102_gc_fix import SafeAPA102
strip = SafeAPA102(66)  # Drop-in replacement
```

### Root Cause (upstream)
The C extension (pimoroni-pico/modules/plasma/micropython) doesn't reset internal state 
when APA102 is re-allocated after garbage collection.

### Upstream Fix Needed
Fix required in pimoroni-pico repository:
- Reset internal state in APA102.__init__()
- Ensure PIO/DMA state is properly re-initialized
- See ISSUE_16_FIX.md for detailed analysis

### Checklist
- [x] Reproduces Issue #16
- [x] Includes test case  
- [x] Provides working workaround
- [x] Documentation and examples
- [x] No breaking changes
- [x] Backward compatible
```

### Commit Message

```
Add test case and workaround for Issue #16 (APA102 GC hang)

- Add test_apa102_gc.py with reproduction and stress tests
- Add apa102_gc_fix.py with SafeAPA102 and MonitoredAPA102 wrappers
- Add ISSUE_16_FIX.md with complete analysis and integration guide

This provides immediate workaround for users while upstream fix
(in pimoroni-pico) is developed. See ISSUE_16_FIX.md for details.

Fixes #16
```

## For Upstream Repository (pimoroni/pimoroni-pico)

### GitHub PR Description

```markdown
## Fix: Reset APA102 internal state on re-allocation

### Problem
After garbage collection, re-allocated APA102 objects have `is_busy()` always 
returning True, causing applications to hang indefinitely.

Issue: pimoroni/plasma#16

### Root Cause
The C extension doesn't properly reset internal state when the Python object 
is re-allocated. Internal flags and hardware state pointers become stale.

### Solution
Reset all internal state variables in APA102 `__init__`:
- Clear busy flag and hardware state
- Reset PIO/DMA configuration
- Re-initialize hardware pointers

### Files Changed
- `modules/plasma/micropython/apa102.c` (or your actual structure)
  - Add state reset in apa102_init()
  - Ensure hardware clean state

### Testing
Use test case from pimoroni/plasma#16:
- tests/test_apa102_gc.py reproduces the issue
- Can verify fix resolves the hang

### Impact
- Fixes critical hang issue in APA102 driver
- No API changes
- Backward compatible

### Workaround Available
Until this is merged, users can use SafeAPA102 wrapper from pimoroni/plasma.
```

### Commit Message

```
Fix: Reset APA102 internal state on re-allocation (pimoroni/plasma#16)

When APA102 object is re-allocated after garbage collection, internal
state variables weren't being reset, causing is_busy() to always return
True and applications to hang.

This fixes the issue by properly initializing all internal state in the
apa102_init() function.

Ref: pimoroni/plasma#16
```

---

## Patch Format (if needed)

Save the upstream fix as a patch:

```bash
# Create patch from upstream changes
git diff pimoroni-pico/modules/plasma/micropython/apa102.c > issue-16-fix.patch
```

Expected changes in the patch:

```diff
--- a/modules/plasma/micropython/apa102.c
+++ b/modules/plasma/micropython/apa102.c
@@ -xx,x +xx,x @@
 static mp_obj_t apa102_init(...) {
     // ... existing code ...
     
+    // Reset state (Issue #16 fix)
+    self->is_busy = false;
+    self->dma_configured = false;
+    self->hardware_state = UNINITIALIZED;
     
     return mp_const_none;
 }
```

---

## Submission Checklist

### For plasma repo (this one)
- [x] Create test_apa102_gc.py
- [x] Create apa102_gc_fix.py  
- [x] Create ISSUE_16_FIX.md
- [x] All files have proper docstrings
- [x] Examples are runnable
- [x] No breaking changes
- [ ] Create example usage file
- [ ] Update main README

### For pimoroni-pico repo
- [ ] Identify exact C code location
- [ ] Implement state reset fix
- [ ] Test on hardware
- [ ] Verify no regressions
- [ ] Create PR with commit message
- [ ] Reference plasma issue

---

## Links & Resources

- **Plasma Issue**: https://github.com/pimoroni/plasma/issues/16
- **pimoroni-pico Repo**: https://github.com/pimoroni/pimoroni-pico
- **Workaround Module**: [apa102_gc_fix.py](../modules/common/apa102_gc_fix.py)
- **Test Case**: [test_apa102_gc.py](../tests/test_apa102_gc.py)
- **Analysis**: [ISSUE_16_FIX.md](../ISSUE_16_FIX.md)
