
import time
import argparse
import numpy as np
import cv2
import pandas as pd
from pathlib import Path
from src.executors.ocr_executor import OCRExecutor

# Setup basic test image equivalent to a document (1024x768 with text-like noise)
def create_dummy_document():
    img = np.ones((768, 1024, 3), dtype=np.uint8) * 255
    # Draw some "text" bars
    for i in range(10):
        cv2.rectangle(img, (50, 50 + i*60), (800, 90 + i*60), (0, 0, 0), -1)
    return img

def benchmark(iterations=50):
    print(f"Running Benchmark: {iterations} iterations")
    doc = create_dummy_document()
    
    # 1. Tesseract (Simulated if not installed, but Executor handles it)
    exec_tess = OCRExecutor(config={"USE_OPENVINO": False})
    
    tess_times = []
    print("Benchmarking Tesseract...")
    for _ in range(iterations):
        res = exec_tess.extract(doc)
        tess_times.append(res['latency_ms'])
        
    # 2. OpenVINO
    exec_ov = OCRExecutor(config={"USE_OPENVINO": True})
    
    ov_times = []
    print("Benchmarking OpenVINO...")
    # Warmup
    try:
        exec_ov.extract(doc)
    except Exception as e:
        print(f"OpenVINO Failed: {e}")
        return

    for _ in range(iterations):
        res = exec_ov.extract(doc)
        ov_times.append(res['latency_ms'])
    
    # Report
    t_avg = np.mean(tess_times)
    t_p95 = np.percentile(tess_times, 95)
    
    o_avg = np.mean(ov_times)
    o_p95 = np.percentile(ov_times, 95)
    
    print("\n" + "="*40)
    print("      INTEL OPENVINO BENCHMARK REPORT      ")
    print("="*40)
    print(f"Tesseract Avg Latency: {t_avg:.2f} ms")
    print(f"OpenVINO  Avg Latency: {o_avg:.2f} ms")
    print(f"Speedup: {t_avg / o_avg:.2f}x")
    print("-" * 40)
    print(f"Tesseract P95: {t_p95:.2f} ms")
    print(f"OpenVINO  P95: {o_p95:.2f} ms")
    print("="*40)
    
    # Save Report
    with open("benchmark_report.md", "w") as f:
        f.write("# Intel OpenVINO Optimization Report\n\n")
        f.write(f"**Speedup**: {t_avg / o_avg:.2f}x\n\n")
        f.write("| Backend | Avg Latency (ms) | P95 Latency (ms) |\n")
        f.write("|---|---|---|\n")
        f.write(f"| Tesseract | {t_avg:.2f} | {t_p95:.2f} |\n")
        f.write(f"| OpenVINO | {o_avg:.2f} | {o_p95:.2f} |\n")

if __name__ == "__main__":
    benchmark()
