import logging
import time
import os
import sys

# Mocking tesseract import for environment where it might not be installed
try:
    import pytesseract
except ImportError:
    pytesseract = None

try:
    from openvino.runtime import Core
except ImportError:
    Core = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OCRExecutor")

class OcrExecutor:
    def __init__(self, config=None):
        self.config = config or {}
        self.use_openvino = self.config.get("USE_OPENVINO", False)
        self.model_path = self.config.get("OPENVINO_MODEL_PATH", "tesseract_optimization/models/openvino/FP32/dummy_ocr.xml")
        
        # Initialize OpenVINO if enabled
        self.ov_core = None
        self.compiled_model = None
        
        if self.use_openvino:
            if Core is None:
                logger.warning("OpenVINO not installed. Falling back to standard Tesseract.")
                self.use_openvino = False
            else:
                self._load_openvino_model()

    def execute(self, config: dict, inputs: dict) -> dict:
        """
        Execute the OCR task.
        
        Args:
            config: Task configuration
            inputs: Input data containing 'document' which is the image to process
            
        Returns:
            Dictionary containing extraction results
        """
        if "document" not in inputs:
            raise ValueError("Input 'document' is required for OcrExecutor")
            
        return self.extract(inputs["document"])

    def _load_openvino_model(self):
        try:
            logger.info(f"Loading OpenVINO model from {self.model_path}")
            if not os.path.exists(self.model_path):
                 raise FileNotFoundError(f"Model file not found: {self.model_path}")
            
            self.ov_core = Core()
            model = self.ov_core.read_model(self.model_path)
            self.compiled_model = self.ov_core.compile_model(model, "CPU")
            logger.info("OpenVINO model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load OpenVINO model: {e}")
            logger.info("Disabling OpenVINO usage for this instance.")
            self.use_openvino = False

    def extract(self, image):
        """
        Extract text from an image. 
        'image' is expected to be a numpy array or similar for this demo.
        """
        start_time = time.perf_counter()
        result = ""
        method = "Tesseract"

        if self.use_openvino:
            try:
                result = self._extract_with_openvino(image)
                method = "OpenVINO"
            except Exception as e:
                logger.error(f"OpenVINO extraction failed: {e}")
                logger.info("Falling back to Tesseract.")
                result = self._extract_with_tesseract(image)
        else:
            result = self._extract_with_tesseract(image)

        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000
        logger.info(f"Extraction Method: {method} | Latency: {latency_ms:.2f} ms")
        
        return {
            "text": result,
            "method": method,
            "latency_ms": latency_ms
        }

    def _extract_with_openvino(self, image):
        # Placeholder for preprocessing
        # For the dummy model, we expect specific input shape. 
        # Here we just assume 'image' is pre-processed or we do a dummy inference.
        
        if self.compiled_model is None:
            raise RuntimeError("OpenVINO model not compiled.")

        # Create dummy input if image is not in correct format (Just for demo)
        import numpy as np
        if isinstance(image, np.ndarray):
            # Check if it matches expected input
            input_layer = self.compiled_model.input(0)
            try:
                expected_shape = list(input_layer.shape)
            except:
                p_shape = input_layer.partial_shape
                expected_shape = []
                for dim in p_shape:
                    if dim.is_dynamic:
                        expected_shape.append(32) # Default to 32 (safer for pooling)
                    else:
                        expected_shape.append(dim.get_length())

            # handle dynamic batch/dims (legacy check)
            expected_shape = [s if s != -1 else 1 for s in expected_shape]
            
            # Simple resize/reshape would go here. 
            # For this demo, we force a dummy input shape match
            input_tensor = np.zeros(expected_shape, dtype=np.float32)
        else:
            # If image is just a path or bytes, we would load it here.
            input_tensor = np.random.randn(1, 1, 32, 32).astype(np.float32)

        # Inference
        output = self.compiled_model([input_tensor])
        
        # Post-processing (CTC decoding etc)
        # Placeholder return
        return "DUMMY_OCR_TEXT"

    def _extract_with_tesseract(self, image):
        # Placeholder for real tesseract call
        if pytesseract:
            # pytesseract.image_to_string(image)
            pass
        
        # Simulate some processing time
        time.sleep(0.1) 
        return "TESSERACT_TEXT_FALLBACK"

if __name__ == "__main__":
    # Simple test
    print("Initializing Standard Executor...")
    exec_std = OCRExecutor(config={"USE_OPENVINO": False})
    print(exec_std.extract("dummy_img"))

    print("\nInitializing OpenVINO Executor...")
    # Ensure raw model exists from previous steps or use dummy path
    exec_ov = OCRExecutor(config={"USE_OPENVINO": True})
    print(exec_ov.extract("dummy_img"))
