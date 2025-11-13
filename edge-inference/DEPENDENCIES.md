# Dependency Management

## Runtime Dependencies (requirements.txt)

All dependencies in `requirements.txt` are **required at runtime** for the inference engine to function.

### Why pandas, tqdm, and seaborn are Runtime Dependencies

While these packages are primarily used by YOLOv5 internally, they are **not optional** for our use case:

1. **pandas** (≥2.0.0)
   - **Required by**: `src/inference.py:76`
   - **Usage**: `results.pandas().xyxy[0].to_dict('records')`
   - **Reason**: Our code directly uses YOLOv5's pandas interface for detection result parsing
   - **Cannot be optional**: Core inference functionality depends on this

2. **tqdm** (≥4.65.0)
   - **Required by**: YOLOv5 model loading and inference
   - **Usage**: Progress bars during model download and inference batches
   - **Reason**: YOLOv5 imports tqdm unconditionally
   - **Cannot be optional**: Module import fails without tqdm

3. **seaborn** (≥0.12.0)
   - **Required by**: YOLOv5 visualization utilities
   - **Usage**: Plotting and visualization dependencies in YOLOv5
   - **Reason**: YOLOv5 imports seaborn for color palettes
   - **Cannot be optional**: YOLOv5 initialization fails without seaborn

### Why Not Use extras_require?

Creating optional dependency groups (e.g., `pip install .[yolo]`) would:
- ❌ Complicate deployment (requires specifying extras)
- ❌ Risk runtime failures if extras not installed
- ❌ Not reduce size (inference engine IS the core functionality)

Since the **core purpose** of this module is object detection via YOLOv5, these dependencies are part of the minimum viable runtime, not optional features.

## Development Dependencies (requirements-dev.txt)

These are **only required for development and testing**:
- pytest
- pytest-asyncio
- pytest-cov
- httpx

Install with:
```bash
pip install -r requirements.txt -r requirements-dev.txt
```

## Dependency Size Analysis

Total install size breakdown:
- **torch + torchvision**: ~2.5GB (CUDA builds)
- **YOLOv5 model**: 3.87MB (runtime download)
- **pandas + tqdm + seaborn**: ~100MB
- **Other dependencies**: ~50MB

The YOLOv5 dependencies (pandas, tqdm, seaborn) represent only **~3.5%** of total install size.

## Alternative Approaches Considered

### 1. Use Direct NumPy Interface (Instead of Pandas)
```python
# Instead of: results.pandas().xyxy[0]
# Use: results.xyxyn[0].cpu().numpy()
```
- ✅ Would eliminate pandas dependency
- ❌ Requires manual result formatting (more code)
- ❌ Less maintainable (pandas interface is standard)
- **Decision**: Keep pandas for cleaner, more maintainable code

### 2. Switch to Ultralytics YOLO v8
```python
from ultralytics import YOLO
```
- ✅ More modern API
- ❌ Already using ultralytics package (dependency overlap)
- ❌ YOLOv5-nano meets size requirements (<10MB)
- **Decision**: YOLOv5-nano is sufficient for edge deployment

### 3. Custom Lightweight Model
- ✅ Could minimize dependencies
- ❌ Requires training infrastructure
- ❌ YOLOv5-nano already optimized (<10MB, <100ms target)
- **Decision**: Not worth the development effort

## Recommendations

### For Production Deployment
1. Use Docker containers with pre-installed dependencies
2. Consider multi-stage builds to reduce final image size
3. Cache PyTorch wheels for faster deployment

### For Size-Constrained Environments
If the ~2.6GB install size is prohibitive:
1. Use CPU-only PyTorch builds (~200MB smaller)
2. Consider ONNX export for inference-only deployments
3. Use TensorRT or OpenVINO for optimized inference

## Dependency Update Policy

- **torch/torchvision**: Pin to compatible versions (currently <2.2.0 for numpy compatibility)
- **numpy**: Must be <2.0.0 for PyTorch 2.1.x compatibility
- **pandas/tqdm/seaborn**: Use minimum viable versions (allows updates)
- **fastapi/pydantic**: Allow minor updates for security patches
