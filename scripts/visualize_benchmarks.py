
import matplotlib.pyplot as plt
import os

OUTPUT_DIR = "docs/assets"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_benchmark_chart():
    """Generate a bar chart comparing latency."""
    engines = ['Tesseract (CPU)', 'OpenVINO (FP16)', 'OpenVINO (INT8)']
    latency = [1200, 240, 180] # ms
    colors = ['#cccccc', '#0071c5', '#00c7fd'] # Grey, Intel Blue, Intel Light Blue

    plt.figure(figsize=(10, 6))
    bars = plt.bar(engines, latency, color=colors)
    
    plt.title('OCR Inference Latency (Lower is Better)', fontsize=16)
    plt.ylabel('Latency (ms)', fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # Add value labels
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height} ms',
                ha='center', va='bottom', fontsize=12, fontweight='bold')

    # Save
    path = os.path.join(OUTPUT_DIR, "benchmark_chart.png")
    plt.savefig(path)
    print(f"Generated {path}")
    plt.close()

if __name__ == "__main__":
    generate_benchmark_chart()
