
import time
import sys
import numpy as np
from openvino.runtime import Core

def main():
    if len(sys.argv) < 2:
        print("Usage: python benchmark_models.py <model_xml>")
        sys.exit(1)
        
    model_path = sys.argv[1]
    core = Core()
    model = core.read_model(model_path)
    compiled_model = core.compile_model(model, "CPU")
    
    print(f"Benchmarking {model_path}...")
    # Blind dummy input
    data = np.random.rand(1, 1, 32, 128).astype(np.float32)
    
    start = time.time()
    for _ in range(100):
        compiled_model([data])
    print(f"Done. Avg Latency: { (time.time() - start)*10 :.2f} ms")

if __name__ == "__main__":
    main()
