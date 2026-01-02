
import cv2
import time
import numpy as np
import argparse
from src.executors.ocr_executor import OCRExecutor

def create_demo_image():
    """Create a visually interesting test image with text."""
    # White background
    img = np.ones((600, 800, 3), dtype=np.uint8) * 255
    
    # Add Title
    cv2.putText(img, "Intel OpenVINO Demo", (50, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 113, 197), 3) # Intel Blue
    
    # Add Body Text
    texts = [
        "Accelerating AI Workloads",
        "Optimized for Intel Architecture",
        "High Performance Inference",
        "Low Latency OCR Pipeline"
    ]
    
    for i, text in enumerate(texts):
        y = 150 + (i * 70)
        # varying fonts/sizes
        cv2.putText(img, text, (50, y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
        
    return img

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--save", action="store_true", help="Save comparison image")
    args = parser.parse_args()
    
    print("Generating demo image...")
    img = create_demo_image()
    
    # 1. Run Standard
    print("Running Standard OCR...")
    exec_std = OCRExecutor(config={"USE_OPENVINO": False})
    # Warmup?
    start = time.perf_counter()
    res_std = exec_std.extract(img.copy())
    dur_std = (time.perf_counter() - start) * 1000
    
    # 2. Run OpenVINO
    print("Running OpenVINO OCR...")
    exec_ov = OCRExecutor(config={"USE_OPENVINO": True})
    # Warmup not typically needed for OV compiled model in this script as compile happens in init
    # but run once to be fair if JIT happens
    start = time.perf_counter()
    res_ov = exec_ov.extract(img.copy())
    dur_ov = (time.perf_counter() - start) * 1000
    
    # 3. Visual Comparison
    print(f"\nResults:")
    print(f"Standard: {dur_std:.2f} ms")
    print(f"OpenVINO: {dur_ov:.2f} ms")
    print(f"Speedup:  {dur_std / dur_ov:.2f}x")
    
    # Draw results on image
    result_img = img.copy()
    
    # Overlay Box
    cv2.rectangle(result_img, (450, 400), (780, 580), (240, 240, 240), -1)
    cv2.rectangle(result_img, (450, 400), (780, 580), (0, 0, 0), 1)
    
    cv2.putText(result_img, "Benchmark", (470, 430), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(result_img, f"Std: {dur_std:.1f}ms", (470, 470), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)
    cv2.putText(result_img, f"OV:  {dur_ov:.1f}ms", (470, 510), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 128, 0), 2)
    cv2.putText(result_img, f"Speedup: {dur_std/dur_ov:.1f}x", (470, 550), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 113, 197), 2)

    if args.save:
        cv2.imwrite("demo_result.jpg", result_img)
        print("Saved result to demo_result.jpg")
    else:
        # In a headless env, keeping it safe.
        print("Skipping cv2.imshow (headless mode implied). Use --save to write file.")

if __name__ == "__main__":
    main()
