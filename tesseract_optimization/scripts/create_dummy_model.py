import torch
import torch.nn as nn
import torch.onnx
import os
import sys

# Force UTF-8 encoding for Windows console compatibility
sys.stdout.reconfigure(encoding='utf-8')

# Define a simple dummy model that simulates an OCR encoder (e.g., CNN + RNN)
# Input: [Batch, 1, Height, Width]
# Output: [Sequence_Length, Batch, Num_Classes]
class DummyOCR(nn.Module):
    def __init__(self):
        super(DummyOCR, self).__init__()
        self.conv = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.relu = nn.ReLU()
        self.pool = nn.MaxPool2d(2, 2)
        # Dummy linear to map to arbitrary classes
        # Input: 32 channels * 16 * 16
        self.fc = nn.Linear(32 * 16 * 16, 10)

    def forward(self, x):
        x = self.conv(x)
        x = self.relu(x)
        x = self.pool(x)
        # Flatten for dummy output
        b, c, h, w = x.size()
        x = x.view(b, -1)
        x = self.fc(x)
        return x

def create_dummy_model(save_path):
    model = DummyOCR()
    model.eval()
    
    # Dummy input: [1, 1, 32, 128] (Standard OCR height, variable width)
    dummy_input = torch.randn(1, 1, 32, 32)
    
    print(f"Exporting dummy model to {save_path}...")
    torch.onnx.export(model, 
                      dummy_input, 
                      save_path, 
                      input_names=['input'], 
                      output_names=['output'],
                      dynamic_axes={'input': {3: 'width'}, 'output': {0: 'batch'}})
    print("Export complete.")

if __name__ == "__main__":
    os.makedirs('tesseract_optimization/models/source', exist_ok=True)
    create_dummy_model('tesseract_optimization/models/source/dummy_ocr.onnx')
