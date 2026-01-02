
import os
import sys
import argparse
import logging
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MODELS_DIR = Path("models/openvino")
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Standard Intel Open Model Zoo models for OCR
# We use version 2022.3 or similar generally available ones
DETECTION_MODEL = "horizontal-text-detection-0001" 
RECOGNITION_MODEL = "text-recognition-resnet-fc" # Works well, widely used

def run_command(cmd):
    """Run a shell command and check for errors."""
    logger.info(f"Running: {cmd}")
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)

def check_dependencies():
    """Check if required OpenVINO dev tools are installed."""
    try:
        import openvino
        logger.info(f"OpenVINO Runtime found: {openvino.__version__}")
    except ImportError:
        logger.error("OpenVINO runtime is NOT installed. Please run: pip install openvino-dev")
        sys.exit(1)

def download_models(precision="FP16"):
    """
    Download pre-trained models using OMZ downloader.
    We assume 'omz_downloader' is in the path (installed via openvino-dev).
    """
    logger.info("Downloading models...")
    
    # We download directly to a structure like: models/openvino/intel/horizontal-text-detection-0001/FP16/...
    # Using omz_downloader
    cmd = f"omz_downloader --name {DETECTION_MODEL},{RECOGNITION_MODEL} --output_dir {MODELS_DIR} --precisions {precision}"
    
    # Fallback/Check: If omz_downloader is not in path, we might need to rely on direct HTTP (omitted for brevity, assuming dev env setup)
    run_command(cmd)

def convert_models():
    """ 
    Convert models to IR if downloaded in specific format, but OMZ usually gets them in IR or PyTorch/TF.
    For standard OMZ models, they often come as OpenVINO IR directly if using public/pretrained.
    The 'omz_converter' step is needed if they are public DL frameworks. 
    These specific Intel models are usually pre-converted in 'intel/' subdir.
    """
    # For 'intel' models (pre-trained by Intel), converter is not usually needed if we just grabbed the IR.
    # The downloader handles checking the cache.
    pass

def setup_directories():
    """Ensure directory structure matches what Executor expects."""
    # Our executor will look for models at configurable paths.
    # The downloader usually puts them in models/openvino/intel/<model_name>/<precision>/<model>.xml
    
    det_path = MODELS_DIR / "intel" / DETECTION_MODEL / "FP16" / f"{DETECTION_MODEL}.xml"
    rec_path = MODELS_DIR / "intel" / RECOGNITION_MODEL / "FP16" / f"{RECOGNITION_MODEL}.xml"
    
    if not det_path.exists():
        logger.warning(f"Detection model not found at {det_path} after download.")
    else:
        logger.info(f"Detection model ready: {det_path}")
        
    if not rec_path.exists():
        logger.warning(f"Recognition model not found at {rec_path} after download.")
    else:
        logger.info(f"Recognition model ready: {rec_path}")

def optimize_int8(model_path, output_path):
    """
    Optional: Apply INT8 quantization using NNCF (Neural Network Compression Framework).
    Requires a dataset for calibration. We will skip actual POT/NNCF execution 
    in this script and assume FP16 is sufficient for 'optimization' demo 
    unless specifically requested, as it requires complex dataset setup.
    """
    logger.info("INT8 Quantization requires a robust calibration dataset.")
    logger.info("Skipping generic INT8 quantization for this script to ensure easy runnability.")
    logger.info("For production, use Neural Network Compression Framework (NNCF) with representative data.")

def main():
    parser = argparse.ArgumentParser(description="Download and setup OpenVINO models for OCR.")
    parser.add_argument("--precision", default="FP16", choices=["FP16", "FP32", "INT8"], help="Model precision")
    args = parser.parse_args()
    
    check_dependencies()
    download_models(precision=args.precision)
    setup_directories()
    optimize_int8(None, None)
    
    logger.info("Model setup complete.")

if __name__ == "__main__":
    main()
