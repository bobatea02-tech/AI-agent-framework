
import logging
import time
import os
import cv2
import numpy as np
from typing import List, Tuple, Dict, Any

# Mocking tesseract import
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

class OCRExecutor:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.use_openvino = self.config.get("USE_OPENVINO", os.getenv("USE_OPENVINO", "false").lower() == "true")
        
        # Paths to models (defaulting to where optimize script puts them)
        base_path = "models/openvino/intel"
        self.det_model_path = self.config.get(
            "DET_MODEL_PATH", 
            f"{base_path}/horizontal-text-detection-0001/FP16/horizontal-text-detection-0001.xml"
        )
        self.rec_model_path = self.config.get(
            "REC_MODEL_PATH", 
            f"{base_path}/text-recognition-resnet-fc/FP16/text-recognition-resnet-fc.xml"
        )
        
        # Initialize OpenVINO if enabled
        self.ov_core = None
        self.det_compiled = None
        self.rec_compiled = None
        self.det_input_layer = None
        self.rec_input_layer = None
        
        if self.use_openvino:
            if Core is None:
                logger.warning("OpenVINO not installed. Falling back to standard Tesseract.")
                self.use_openvino = False
            else:
                self._load_openvino_models()

    def _load_openvino_models(self):
        try:
            logger.info("Loading OpenVINO Runtime...")
            self.ov_core = Core()
            
            # 1. Detection Model
            if os.path.exists(self.det_model_path):
                logger.info(f"Loading Detection Model: {self.det_model_path}")
                det_model = self.ov_core.read_model(self.det_model_path)
                self.det_compiled = self.ov_core.compile_model(det_model, "CPU")
                self.det_input_layer = self.det_compiled.input(0)
            else:
                logger.warning(f"Detection model missing at {self.det_model_path}")
                raise FileNotFoundError("Detection model missing")

            # 2. Recognition Model
            if os.path.exists(self.rec_model_path):
                logger.info(f"Loading Recognition Model: {self.rec_model_path}")
                rec_model = self.ov_core.read_model(self.rec_model_path)
                self.rec_compiled = self.ov_core.compile_model(rec_model, "CPU")
                self.rec_input_layer = self.rec_compiled.input(0)
            else:
                logger.warning(f"Recognition model missing at {self.rec_model_path}")
                raise FileNotFoundError("Recognition model missing")
                
            logger.info("OpenVINO models loaded successfully.")
            
        except Exception as e:
            logger.error(f"Failed to load OpenVINO models: {e}")
            logger.info("Disabling OpenVINO usage for this instance.")
            self.use_openvino = False

    def execute(self, config: dict, inputs: dict) -> dict:
        """
        Execute OCR task.
        inputs['document'] can be a path or a numpy array (image).
        """
        image_input = inputs.get("document")
        if not image_input:
            raise ValueError("Input 'document' is required")
        
        # Prepare image (Load if path)
        if isinstance(image_input, str):
            if os.path.exists(image_input):
                image = cv2.imread(image_input)
            else:
                # Assuming it might be raw text for some reason? No, strict check.
                raise FileNotFoundError(f"Document not found: {image_input}")
        elif isinstance(image_input, np.ndarray):
            image = image_input
        else:
            raise ValueError("Unsupported document format")

        return self.extract(image)

    def extract(self, image: np.ndarray) -> dict:
        start_time = time.perf_counter()
        result = ""
        method = "Tesseract"
        
        if self.use_openvino and self.det_compiled and self.rec_compiled:
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

    def _extract_with_openvino(self, image: np.ndarray) -> str:
        """
        Full pipeline: Detection -> Crop -> Recognition -> CTC Decode
        """
        # 1. Detection
        boxes = self._detect_text(image)
        
        # 2. Recognition Loop
        full_text = []
        for box in boxes:
            cropped = self._crop_box(image, box)
            if cropped.size == 0:
                continue
            text = self._recognize_text(cropped)
            full_text.append(text)
            
        return "\n".join(full_text)

    def _detect_text(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Run text detection model.
        Model: horizontal-text-detection-0001
        Input: [1x3x704x704]
        Output: [N, 5] (x_min, y_min, x_max, y_max, score) or similar
        """
        # Resize to expected shape (704x704 is common for this model)
        input_h, input_w = 704, 704
        resized_image = cv2.resize(image, (input_w, input_h))
        # CHW format
        input_tensor = resized_image.transpose((2, 0, 1))
        input_tensor = np.expand_dims(input_tensor, 0).astype(np.float32)
        
        # Inference
        results = self.det_compiled([input_tensor])[self.det_compiled.output(0)]
        
        # Parse results
        # Output shape is typically [N, 5] or [100, 5]
        # x_min, y_min, x_max, y_max, conf
        boxes = []
        h_scale = image.shape[0] / input_h
        w_scale = image.shape[1] / input_w
        
        for item in results:
            xmin, ymin, xmax, ymax, conf = item
            if conf > 0.5:
                # Scale back
                boxes.append((
                    int(xmin * w_scale),
                    int(ymin * h_scale),
                    int(xmax * w_scale),
                    int(ymax * h_scale)
                ))
        
        # Sort boxes top-to-bottom
        boxes.sort(key=lambda b: b[1])
        return boxes

    def _crop_box(self, image: np.ndarray, box: Tuple[int, int, int, int]) -> np.ndarray:
        x1, y1, x2, y2 = box
        # Clamp
        h, w = image.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        return image[y1:y2, x1:x2]

    def _recognize_text(self, image: np.ndarray) -> str:
        """
        Run text recognition model.
        Model: text-recognition-resnet-fc (grayscale input usually)
        Input: [1x1x32x100] (Checking shape is easier)
        Output: [100, 1, 29] (for ResNet-FC) - needs decoding
        """
        # Get input shape from model
        # We'll assume dynamic or fixed. Usually 32 height is key.
        n, c, h, w = self.rec_input_layer.shape
        
        # Preprocess
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (w, h))
        input_tensor = resized.reshape(1, 1, h, w).astype(np.float32)
        
        # Inference
        output = self.rec_compiled([input_tensor])[self.rec_compiled.output(0)]
        
        # CTC Decoding
        # Output shape is typically [SequencLength, Batch, NumClasses] -> [30, 1, 29]
        # We need to take argmax per step and de-duplicate
        
        # Flatten batch
        output = np.squeeze(output) # [SeqLen, NumClasses]
        if output.ndim == 3: # Handle if batch dim persists
             output = np.squeeze(output, axis=1)

        argmax = np.argmax(output, axis=1)
        
        # Decode
        # Alphabet for this model (0-9, a-z, etc). Usually alphanumeric.
        # This mapping depends strictly on the specific model version.
        # We will use a standard alphanumeric mapping for 'text-recognition-resnet-fc'
        # 0-9, a-z, blank implicit?
        # A simple fallback mapping:
        chars = "0123456789abcdefghijklmnopqrstuvwxyz#" # #=blank?
        # Note: Proper decoding needs the exact charlist.txt
        
        decoded_res = ""
        prev_idx = -1
        for idx in argmax:
            if idx != prev_idx and idx < len(chars) and chars[idx] != '#':
                decoded_res += chars[idx]
            prev_idx = idx
            
        return decoded_res

    def _extract_with_tesseract(self, image: np.ndarray) -> str:
        if pytesseract:
            # Need to configure Tesseract path if on Windows/Linux custom
            return pytesseract.image_to_string(image)
        return "Tesseract Not Available (Install tesseract-ocr)"

if __name__ == "__main__":
    # Demo/Test
    pass
