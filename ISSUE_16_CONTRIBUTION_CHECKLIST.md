# Issue #16 Fix - Contribution Checklist

Use this checklist when contributing the fix to upstream repositories.

## 📦 Package Contents Checklist

Before starting, verify you have all required files:

- [x] `tests/test_apa102_gc.py` - Test case
- [x] `modules/common/apa102_gc_fix.py` - Workaround implementation  
- [x] `ISSUE_16_FIX.md` - Complete analysis
- [x] `examples/apa102_gc_safe_usage.py` - Usage examples
- [x] `PR_TEMPLATE_ISSUE_16.md` - PR templates
- [x] This file

## 🎯 Fork 1: Contribute to pimoroni/plasma

### Before You Start
- [ ] Fork pimoroni/plasma
- [ ] Create branch: `issue-16-gc-fix`
- [ ] Read [ISSUE_16_FIX.md](ISSUE_16_FIX.md)

### Implementation Checklist
- [ ] Copy `tests/test_apa102_gc.py` to: `tests/test_apa102_gc.py`
- [ ] Copy `modules/common/apa102_gc_fix.py` to: `modules/common/apa102_gc_fix.py`
- [ ] Copy `examples/apa102_gc_safe_usage.py` to: `examples/apa102_gc_safe_usage.py`
- [ ] All files are in the right locations

### Testing Checklist
- [ ] `tests/test_apa102_gc.py` runs without errors
- [ ] Workaround can be imported: `from modules.common.apa102_gc_fix import SafeAPA102`
- [ ] No new dependencies added
- [ ] Existing tests still pass

### Documentation Checklist
- [ ] Update main `README.md` with link to workaround (add one line under Known Issues)
- [ ] Add section to `ISSUE_16_FIX.md` linking to this PR
- [ ] Include usage example in PR description

### PR Submission Checklist
- [ ] PR title: "Add: Issue #16 workaround and test case (APA102 GC hang)"
- [ ] PR description: Use template from [PR_TEMPLATE_ISSUE_16.md](PR_TEMPLATE_ISSUE_16.md)
- [ ] Reference issue: "Closes #16" in PR description
- [ ] Link to workaround: "See modules/common/apa102_gc_fix.py"
- [ ] Mention upstream fix: "Upstream fix needed in pimoroni-pico"

### Merge Readiness
- [ ] All checks pass
- [ ] Code review approved
- [ ] No breaking changes
- [ ] Backward compatible

---

## 🎯 Fork 2: Fix in pimoroni-pico (Upstream)

### Prerequisites
- [ ] Fork pimoroni/pimoroni-pico
- [ ] Create branch: `fix/apa102-gc-state-reset`
- [ ] Read [ISSUE_16_FIX.md](ISSUE_16_FIX.md) → "Upstream Fix (pimoroni-pico)"
- [ ] Identify APA102 C extension location (likely `modules/plasma/micropython/apa102.c`)

### Code Analysis Checklist
- [ ] Located APA102 `__init__` function
- [ ] Identified internal state variables (is_busy, dma_configured, etc.)
- [ ] Identified hardware state pointers (PIO, DMA)
- [ ] Found where state is initialized

### Fix Implementation Checklist
- [ ] Add state reset in `__init__`:
  ```c
  // Reset all internal state (Issue #16 fix)
  self->is_busy = false;
  self->dma_configured = false;
  self->pio_initialized = false;
  // ... other state resets
  ```
- [ ] Ensure all pointers are properly initialized
- [ ] Verify PIO/DMA configuration is fresh
- [ ] No code duplication (extract to function if needed)

### Testing Checklist - Hardware
- [ ] Build MicroPython with updated code
- [ ] Run [test_apa102_gc.py](tests/test_apa102_gc.py) on target hardware
- [ ] Verify no hangs occur after GC
- [ ] Run stress test (multiple GC cycles)
- [ ] Verify no regressions in normal operation

### Testing Checklist - Regression
- [ ] Run existing APA102 tests
- [ ] Test with both APA102 variants (if multiple)
- [ ] Test on all supported boards
- [ ] Verify is_busy() timeout behavior unchanged

### Documentation Checklist
- [ ] Code has clear comments explaining the fix
- [ ] Commit message references Issue #16
- [ ] Updated any relevant documentation
- [ ] Added note about the fix in changelog/release notes

### PR Submission Checklist
- [ ] PR title: "Fix: Reset APA102 internal state on re-allocation (Issue #16)"
- [ ] PR description: Use template from [PR_TEMPLATE_ISSUE_16.md](PR_TEMPLATE_ISSUE_16.md)
- [ ] Reference: "Closes pimoroni/plasma#16"
- [ ] Link to test: "Test case: pimoroni/plasma/tests/test_apa102_gc.py"
- [ ] Link to workaround: "Workaround available in pimoroni/plasma"

### Merge Readiness
- [ ] Hardware tests pass on all boards
- [ ] CI/CD tests pass (if available)
- [ ] Code review approved
- [ ] No performance regression
- [ ] Backward compatible

---

## 🔍 Verification Checklist

After implementing fixes, verify with this checklist:

### Does the fix work?
```bash
# Run test on target hardware with fixed code
micropython tests/test_apa102_gc.py
# Expected output: ✓ Test passed
```

### Is it backward compatible?
```python
# Old code should still work
import plasma
led_strip = plasma.APA102(66)
# Should work exactly as before
```

### Does workaround still work?
```python
# Even though bug is fixed, workaround should still work
from modules.common.apa102_gc_fix import SafeAPA102
led_strip = SafeAPA102(66)
# Should work fine
```

### No regressions?
- [ ] Normal LED operations work
- [ ] is_busy() returns correct values
- [ ] update() transfers complete properly
- [ ] No performance degradation

---

## 📝 Commit Message Templates

### For pimoroni/plasma (workaround)
```
Add: Issue #16 workaround and test case (APA102 GC hang)

- Add test_apa102_gc.py with Issue #16 reproduction
- Add SafeAPA102 and MonitoredAPA102 wrapper classes
- Add comprehensive documentation and examples
- Workaround available until upstream fix (pimoroni-pico)

Issue: #16
Ref: pimoroni/pimoroni-pico/issues/XXX (when known)
```

### For pimoroni-pico (upstream fix)
```
Fix: Reset APA102 internal state on re-allocation

After garbage collection, re-allocated APA102 objects would have
is_busy() returning True constantly, hanging the application.

Root cause: C extension didn't reset internal state variables 
when the Python object was re-allocated.

Solution: Reset all internal state in apa102_init() to ensure
clean hardware state.

Test case: pimoroni/plasma/tests/test_apa102_gc.py
Related: pimoroni/plasma#16
```

---

## 🚀 Fast Track (Copy-Paste)

### For pimoroni/plasma workaround PR:

```markdown
## Add: Issue #16 workaround and test case (APA102 GC hang)

Closes #16

### Problem
After garbage collection, re-allocated APA102 objects have `is_busy()` 
always returning True, hanging the application.

### Solution
Provide workaround wrapper classes until upstream fix is merged:
- **SafeAPA102**: Drop-in replacement with timeout protection
- **MonitoredAPA102**: Auto-detects GC and recovers automatically

### Changes
- ✅ `tests/test_apa102_gc.py` - Comprehensive test case
- ✅ `modules/common/apa102_gc_fix.py` - Wrapper implementation
- ✅ `examples/apa102_gc_safe_usage.py` - Usage examples

### Usage
```python
from modules.common.apa102_gc_fix import SafeAPA102
strip = SafeAPA102(66)  # Drop-in replacement
```

### Status
- ✓ Test case ready
- ✓ Workaround production-ready
- ⏳ Upstream fix pending (in pimoroni-pico)

See [ISSUE_16_FIX.md](../../ISSUE_16_FIX.md) for complete analysis.
```

---

## 💬 Communication

### When To Mention This Package
- [ ] In GitHub Issue #16 comments
- [ ] In PR descriptions pointing to this repo
- [ ] In commit messages linking to analysis
- [ ] In documentation/user guides
- [ ] In release notes

### Key Links To Share
- Development issue: https://github.com/pimoroni/plasma/issues/16
- This package: `ISSUE_16_PACKAGE_README.md`
- Analysis: `ISSUE_16_FIX.md`
- Workaround: `modules/common/apa102_gc_fix.py`
- Test case: `tests/test_apa102_gc.py`

---

## 🎓 References

- **Plasma Repository**: https://github.com/pimoroni/plasma
- **pimoroni-pico Repository**: https://github.com/pimoroni/pimoroni-pico
- **Issue #16**: https://github.com/pimoroni/plasma/issues/16
- **MicroPython C Extensions**: https://docs.micropython.org/en/latest/develop/extmod.html

---

## ✅ Final Sign-Off

- [ ] All files present and documented
- [ ] Test case runs successfully
- [ ] Workaround is production-ready
- [ ] PR templates are accurate
- [ ] Ready to contribute upstream
- [ ] No blockers identified

**Status**: ✅ Ready for submission

---

Questions? See detailed analysis in [ISSUE_16_FIX.md](ISSUE_16_FIX.md)
