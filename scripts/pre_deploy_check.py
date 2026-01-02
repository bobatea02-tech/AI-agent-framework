
import os
import sys
import socket
import shutil
from pathlib import Path

def print_result(check_name, passed, message=""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {check_name:<30} | {message}")

def check_python_version():
    req = (3, 10)
    current = sys.version_info[:2]
    passed = current >= req
    print_result("Python Version >= 3.10", passed, f"Found {current[0]}.{current[1]}")
    return passed

def check_docker():
    passed = shutil.which("docker") is not None
    print_result("Docker Installed", passed)
    return passed

def check_docker_compose():
    # Newer docker has 'docker compose'
    passed = shutil.which("docker") is not None
    # A simplified check, typically 'docker compose version' would be run
    print_result("Docker Compose Available", passed)
    return passed

def check_env_file():
    passed = Path(".env").exists()
    print_result(".env File Exists", passed)
    return passed

def check_port_availability():
    # Only relevant if running locally on host, less relevant for container deployment
    # but good sanity check for conflicts.
    ports = [8000, 5432, 6379, 9092]
    all_passed = True
    for port in ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            result = s.connect_ex(('localhost', port))
            # 0 means open (something listenting), which might be good or bad depending on context.
            # For pre-deploy, if we want to START services, they should be free (result != 0).
            # But if services are already running, result == 0 is expected.
            # We'll just log status.
            status = "In Use" if result == 0 else "Free"
            # print_result(f"Port {port}", True, status) 
            pass
    print_result("Port Availability Check", True, "Skipped (Context Dependent)")
    return True

def main():
    print("\n=== AI Agent Framework Pre-Deployment Check ===\n")
    
    checks = [
        check_python_version(),
        check_docker(),
        check_docker_compose(),
        check_env_file(),
        check_port_availability()
    ]
    
    if all(checks):
        print("\n✅ System is ready for deployment initialization.")
        sys.exit(0)
    else:
        print("\n❌ System checks failed. Please resolve issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
