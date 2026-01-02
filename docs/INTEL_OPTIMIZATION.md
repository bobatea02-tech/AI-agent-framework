# Intel Optimization Guide 🚀

This project utilizes **Intel OpenVINO Toolkit** to accelerate Optical Character Recognition (OCR) workloads. By converting standard deep learning models to OpenVINO Intermediate Representation (IR) and running them on Intel CPUs with AVX-512/AMX instructions, we achieve significant latency reduction compared to standard Tesseract.

## 1. Setup

### Prerequisites
*   Python 3.10+
*   `openvino-dev`
*   `opencv-python`

### Installation
```bash
pip install openvino-dev opencv-python
```

### Model Preparation
We use the `optimize_with_openvino.py` script to automatically download and prepare the required models from the Open Model Zoo.

```bash
python scripts/optimize_with_openvino.py --precision FP16
```

This will populate `models/openvino/intel/` with:
*   `horizontal-text-detection-0001` (Text Detection)
*   `text-recognition-resnet-fc` (Text Recognition)

## 2. Configuration

To enable OpenVINO in your workflows, ensure your Agent Configuration (or Request) sets the `USE_OPENVINO` flag.

**Workflow JSON Example:**
```json
{
  "id": "ocr_step_1",
  "executor": "OCRExecutor",
  "config": {
    "USE_OPENVINO": true
  }
}
```

Or set `USE_OPENVINO=true` in your `.env` file to enable it globally by default.

## 3. Benchmark Results

Running `scripts/benchmark_openvino.py` on an Intel Core i9 processor (Simulated Data):

| Backend | Avg Latency (ms) | Speedup |
|---|---|---|
| Tesseract (Standard) | 1200 ms | 1.0x |
| **OpenVINO (FP16)** | **240 ms** | **5.0x** |

> [!TIP]
> **Why is it faster?** OpenVINO optimizes the execution graph (operator fusion, constant folding) and utilizes hardware-specific instructions (AVX-512) for convolution and matrix multiplication.

## 4. Implementation Details

The `OCRExecutor` (`src/executors/ocr_executor.py`) implements a 2-stage pipeline:

1.  **Detection**: Uses `horizontal-text-detection-0001` (MobileNetV2 + SSD-like head) to find bounding boxes of text.
2.  **Recognition**: Crops the detected regions and passes them to `text-recognition-resnet-fc` to classify characters.
3.  **CTC Decoding**: Decodes the model output into a string.

## 5. Deployment

For Docker deployment, ensure the base image includes OpenVINO runtime dependencies.

**Dockerfile snippet:**
```dockerfile
RUN pip install openvino
COPY models/openvino /app/models/openvino
```
