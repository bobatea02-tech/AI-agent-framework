import os
import sys
import time
import json
from prometheus_client import generate_latest

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from src.utils.logger import setup_logging, get_logger
from src.utils.metrics import (
    record_workflow_submission,
    record_workflow_completion,
    record_task_execution,
    track_task_duration
)

def verify_logger():
    print("--- Verifying Logger ---")
    setup_logging()
    logger = get_logger("verification_script")
    
    logger.info("Test info message", context="verification")
    logger.error("Test error message", error_code=500)
    
    # Check log file
    log_file = "logs/app.json"
    if os.path.exists(log_file):
        print(f"Log file {log_file} exists.")
        with open(log_file, 'r') as f:
            lines = f.readlines()
            last_line = lines[-1]
            try:
                log_json = json.loads(last_line)
                print("Last log entry is valid JSON:")
                print(json.dumps(log_json, indent=2))
                if log_json.get("message") == "Test error message":
                    print("SUCCESS: Logger verification passed.")
                else:
                    print("FAILURE: Log content mismatch.")
            except json.JSONDecodeError:
                print("FAILURE: Log file content is not valid JSON.")
    else:
        print(f"FAILURE: Log file {log_file} not found.")

def verify_metrics():
    print("\n--- Verifying Metrics ---")
    
    # 1. workflows_submitted_total
    record_workflow_submission("wf-1")
    record_workflow_submission("wf-1")
    
    # 2. workflows_completed_total
    record_workflow_completion("wf-1", "completed", 5.5)
    
    # 3. task_executions_total & duration
    record_task_execution("LLMExecutor", "success", 1.2)
    
    with track_task_duration("OCRExecutor"):
        time.sleep(0.1)
        
    # Check metrics output
    metrics_output = generate_latest().decode("utf-8")
    
    print("\nMetrics Output Snapshot:")
    relevant_metrics = [line for line in metrics_output.split('\n') if not line.startswith('#') and line]
    for line in relevant_metrics:
        if "workflows_submitted_total" in line or "task_executions_total" in line:
            print(line)
            
    if 'workflows_submitted_total{workflow_id="wf-1"} 2.0' in metrics_output:
        print("SUCCESS: Metrics verification passed.")
    else:
        print("FAILURE: Metrics values mismatch.")

if __name__ == "__main__":
    verify_logger()
    verify_metrics()
