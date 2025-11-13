# NumPy 2.x Compatibility Issue - Resolution

**Date**: 2025-11-13
**Status**: ✅ RESOLVED

## Issue Summary

All inference tests (12/44 tests) were failing with:
```
ModelInferenceError: Inference failed: Numpy is not available
```

## Root Cause

**NumPy 2.0 ABI Breaking Change** - Binary incompatibility between NumPy 2.x and PyTorch 2.1.x

### Environment Details
- **numpy**: 2.2.6 (automatically installed as latest version)
- **torch**: 2.1.2+cu121 (compiled against NumPy 1.x)
- **pandas**: 2.3.3

### Technical Explanation

1. **NumPy 2.0 Release (Mid-2024)**: Introduced ABI-breaking changes including new `_ARRAY_API`
2. **PyTorch Compatibility**: PyTorch ≤2.1 was compiled against NumPy 1.x and cannot initialize with NumPy 2.x
3. **Failure Point**: YOLOv5's `results.pandas().xyxy[0]` internally uses `torch.from_numpy()`, which fails

### Error Messages
```
A module that was compiled using NumPy 1.x cannot be run in
NumPy 2.2.6 as it may crash. To support both 1.x and 2.x
versions of NumPy, modules must be compiled with NumPy 2.0.

UserWarning: Failed to initialize NumPy: _ARRAY_API not found
(Triggered internally at ../torch/csrc/utils/tensor_numpy.cpp:84.)
```

## Solution

### Implemented Fix
**Downgrade NumPy to 1.x** (numpy<2.0.0)

```bash
pip install "numpy<2.0"
# Installs: numpy 1.26.4 (latest stable 1.x version)
```

### Why This Works
- PyTorch ≤2.1 requires NumPy <2.0 for `.numpy()` and `.from_numpy()` operations
- NumPy 1.26.4 is the latest stable 1.x release
- Maintains compatibility with torch version constraint: `torch>=2.1.0,<2.2.0`
- No code changes required

### Test Results After Fix

**Before Fix** (numpy 2.2.6):
- 32/44 tests passing (73%)
- 72.29% coverage
- 12 inference tests failing

**After Fix** (numpy 1.26.4):
- **44/44 tests passing (100%)** ✅
- **75.50% coverage** ✅
- **0 tests failing** ✅

## Alternative Solutions (Not Implemented)

### Option 2: Upgrade PyTorch to ≥2.2
```bash
pip install torch>=2.2.0
```
**Rejected because**:
- Violates requirements.txt constraint `torch>=2.1.0,<2.2.0`
- Would require changing project requirements

### Option 3: Modify Code to Avoid Pandas
Replace in `src/inference.py`:
```python
# Instead of:
detections = results.pandas().xyxy[0].to_dict('records')

# Use:
detections = results.xyxyn[0].cpu().numpy()
# Then manually format to dict
```
**Rejected because**:
- Requires code refactoring
- NumPy downgrade is simpler and more maintainable

## References

- [PyTorch Issue #135013 - NumPy 2.1.0 Compatibility](https://github.com/pytorch/pytorch/issues/135013)
- [PyTorch Issue #107302 - NumPy 2.0 Support](https://github.com/pytorch/pytorch/issues/107302)
- [YOLOv5 Issue #6908 - Numpy is not available](https://github.com/ultralytics/yolov5/issues/6908)
- [Stack Overflow - PyTorch RuntimeError: Numpy is not available](https://stackoverflow.com/questions/71689095/)

## Key Takeaway

**PyTorch Version Compatibility Matrix**:
- PyTorch ≤2.1: Requires NumPy <2.0
- PyTorch ≥2.2: Compatible with NumPy 1.x and 2.x

When using PyTorch 2.1.x, always pin `numpy<2.0.0` in requirements.txt.
