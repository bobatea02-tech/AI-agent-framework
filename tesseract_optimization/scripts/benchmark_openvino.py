import time
import argparse
import os
import sys
import psutil
import logging
import numpy as np
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

# Add src to path to import executor
sys.path.append(os.path.join(os.getcwd(), 'tesseract_optimization'))
from src.executors.ocr_executor import OcrExecutor

# Setup Directories
LOG_DIR = "tesseract_optimization/logs/benchmarks"
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("Benchmark")

def measure_memory():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # MB

def run_benchmark(executor, num_pages=10):
    latencies = []
    start_mem = measure_memory()
    
    start_global = time.perf_counter()
    
    for i in range(num_pages):
        # Simulate loading an image (random noise for demo)
        dummy_image = np.random.randint(0, 255, (1024, 768), dtype=np.uint8)
        
        result = executor.extract(dummy_image)
        latencies.append(result['latency_ms'])
        
    end_global = time.perf_counter()
    end_mem = measure_memory()
    
    total_time = end_global - start_global
    throughput = num_pages / total_time
    avg_latency = sum(latencies) / len(latencies)
    mem_delta = end_mem - start_mem
    
    return {
        "avg_latency": avg_latency,
        "throughput": throughput,
        "memory_delta": mem_delta,
        "latencies": latencies
    }

def generate_report(results_std, results_ov):
    report_path = os.path.join(LOG_DIR, "report.md")
    
    content = f"""# OCR Benchmark Report
Date: {time.strftime("%Y-%m-%d %H:%M:%S")}

## Summary
| Metric | Standard (Tesseract) | OpenVINO | Improvement |
|--------|----------------------|----------|-------------|
| Avg Latency (ms) | {results_std['avg_latency']:.2f} | {results_ov['avg_latency']:.2f} | {((results_std['avg_latency'] - results_ov['avg_latency']) / results_std['avg_latency'] * 100):.1f}% |
| Throughput (pages/s) | {results_std['throughput']:.2f} | {results_ov['throughput']:.2f} | {((results_ov['throughput'] - results_std['throughput']) / results_std['throughput'] * 100):.1f}% |
| Memory Delta (MB) | {results_std['memory_delta']:.2f} | {results_ov['memory_delta']:.2f} | - |

## Details
- **Test Set Size**: {len(results_std['latencies'])} pages
- **Hardware**: CPU (Simulated)
"""
    with open(report_path, "w") as f:
        f.write(content)
    
    print(f"Report saved to {report_path}")
    
    if plt:
        plt.figure(figsize=(10, 6))
        plt.plot(results_std['latencies'], label='Standard')
        plt.plot(results_ov['latencies'], label='OpenVINO')
        plt.xlabel('Page Number')
        plt.ylabel('Latency (ms)')
        plt.title('OCR Inference Latency Comparison')
        plt.legend()
        plt.grid(True)
        plot_path = os.path.join(LOG_DIR, "latency_comparison.png")
        plt.savefig(plot_path)
        print(f"Plot saved to {plot_path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", type=int, default=20, help="Number of pages to process")
    args = parser.parse_args()
    
    print(f"Starting Benchmark using {args.pages} pages...")
    
    # 1. Standard
    print("\n--- Benchmarking Standard Tesseract ---")
    exec_std = OcrExecutor(config={"USE_OPENVINO": False})
    results_std = run_benchmark(exec_std, args.pages)
    print(f"Standard Avg Latency: {results_std['avg_latency']:.2f} ms")
    
    # 2. OpenVINO
    print("\n--- Benchmarking OpenVINO ---")
    # Make sure we have a model to load, otherwise logic falls back
    # For this script to be meaningful, ensure 'dummy_ocr.xml' exists via optimize_models.py (which calls dummy gen)
    # or manual placement.
    exec_ov = OcrExecutor(config={"USE_OPENVINO": True, "OPENVINO_MODEL_PATH": "tesseract_optimization/models/openvino/FP32/dummy_ocr.xml"})
    results_ov = run_benchmark(exec_ov, args.pages)
    print(f"OpenVINO Avg Latency: {results_ov['avg_latency']:.2f} ms")
    
    # 3. Report
    generate_report(results_std, results_ov)

if __name__ == "__main__":
    main()
