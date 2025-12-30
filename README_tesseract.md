# Tesseract Optimization & OpenVINO Integration

This project contains scripts to convert, optimize, and benchmark OCR models using OpenVINO.

## structure

- `models/`: Stores source and optimized models.
- `scripts/`: Conversion and benchmarking scripts.
- `src/executors/`: OCR executor component.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### 1. Create a Dummy Model (For testing)
If you don't have a real OCR ONNX model, generate a dummy one:
```bash
python scripts/create_dummy_model.py
```

### 2. Optimize Model
Convert the model to OpenVINO IR format:
```bash
python scripts/optimize_models.py --input_model models/source/dummy_ocr.onnx
```

### 3. Benchmark
Compare performance between Standard Tesseract (simulation) and OpenVINO:
```bash
python scripts/benchmark_openvino.py --pages 50
```

## Integration
The `OcrExecutor` in `src/executors/ocr_executor.py` demonstrates how to integrate OpenVINO with a fallback to Tesseract.

```python
from src.executors.ocr_executor import OcrExecutor

# Use OpenVINO
executor = OcrExecutor(config={"USE_OPENVINO": True})
result = executor.extract(image_data)
```
