"""
Simplified Demo Script for AI Agent Framework
Focuses on tests that work standalone without requiring all Docker services
"""
import subprocess
import sys
from pathlib import Path

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    GREEN = Fore.GREEN
    RED = Fore.RED
    YELLOW = Fore.YELLOW
    BLUE = Fore.BLUE
    CYAN = Fore.CYAN
    RESET = Style.RESET_ALL
except ImportError:
    GREEN = RED = YELLOW = BLUE = CYAN = RESET = ""

def print_header(text):
    """Print a formatted header"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{text.center(70)}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

def run_command(name, command):
    """Run a command and show results"""
    print(f"{CYAN}Running: {name}{RESET}")
    print(f"Command: {' '.join(command)}\n")
    
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print(f"{GREEN}✓ {name} - PASSED{RESET}\n")
            if result.stdout:
                # Show last 20 lines of output
                lines = result.stdout.split('\n')
                for line in lines[-20:]:
                    if line.strip():
                        print(f"  {line}")
            return True
        else:
            print(f"{RED}✗ {name} - FAILED{RESET}")
            print(f"{RED}Error:{RESET}\n{result.stderr[:500]}\n")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"{RED}✗ {name} - TIMEOUT{RESET}\n")
        return False
    except Exception as e:
        print(f"{RED}✗ {name} - ERROR: {e}{RESET}\n")
        return False

def main():
    """Run simplified demo"""
    print(f"{BLUE}╔══════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BLUE}║     AI AGENT FRAMEWORK - SIMPLIFIED DEMO                         ║{RESET}")
    print(f"{BLUE}║     (Standalone Tests - No Docker Required)                      ║{RESET}")
    print(f"{BLUE}╚══════════════════════════════════════════════════════════════════╝{RESET}")
    
    project_root = Path(__file__).parent.parent
    
    results = []
    
    # Test 1: Database Models
    print_header("TEST 1: DATABASE MODELS")
    print("Testing SQLAlchemy ORM models and relationships...")
    result = run_command(
        "Database Models Test",
        [sys.executable, "-m", "pytest", "tests/unit/test_database_models.py", "-v", "--tb=short"]
    )
    results.append(("Database Models", result))
    
    # Test 2: API Schemas
    print_header("TEST 2: API SCHEMAS")
    print("Testing Pydantic models for API validation...")
    result = run_command(
        "API Schemas Test",
        [sys.executable, "-m", "pytest", "tests/unit/test_api_schemas.py", "-v", "--tb=short"]
    )
    results.append(("API Schemas", result))
    
    # Test 3: Verify Models Script
    print_header("TEST 3: MODEL VERIFICATION")
    print("Running standalone model verification...")
    result = run_command(
        "Model Verification",
        [sys.executable, "tests/verify_models.py"]
    )
    results.append(("Model Verification", result))
    
    # Test 4: Show Code Structure
    print_header("PROJECT STRUCTURE")
    print("Key components of the AI Agent Framework:\n")
    
    components = {
        "Orchestration Engine": "src/core/orchestrator.py",
        "Task Executors": "src/executors/",
        "API Gateway": "src/api/routes.py",
        "Database Models": "src/database/models.py",
        "Kafka Integration": "src/kafka/",
        "Airflow DAGs": "src/airflow/dags/",
        "Workflow Definitions": "workflows/",
    }
    
    for component, path in components.items():
        full_path = project_root / path
        exists = "✓" if full_path.exists() else "✗"
        color = GREEN if full_path.exists() else RED
        print(f"  {color}{exists}{RESET} {component:25} → {path}")
    
    # Summary
    print_header("DEMO SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"Tests Run: {total}")
    print(f"{GREEN}Passed: {passed}{RESET}")
    print(f"{RED}Failed: {total - passed}{RESET}")
    print(f"Success Rate: {(passed/total*100):.1f}%\n")
    
    for name, result in results:
        status = f"{GREEN}✓ PASS{RESET}" if result else f"{RED}✗ FAIL{RESET}"
        print(f"  [{status}] {name}")
    
    print(f"\n{BLUE}{'='*70}{RESET}")
    
    if passed == total:
        print(f"{GREEN}ALL STANDALONE TESTS PASSED! ✓{RESET}")
        print(f"\n{CYAN}Next Steps for Full Demo:{RESET}")
        print(f"  1. Start Docker services: docker compose up -d")
        print(f"  2. Wait for services (60s)")
        print(f"  3. Run full test suite: python scripts/run_all_tests.py")
        print(f"  4. Access Airflow UI: http://localhost:8080")
        print(f"  5. Access API docs: http://localhost:8000/docs")
    else:
        print(f"{YELLOW}SOME TESTS FAILED{RESET}")
        print(f"Review errors above and ensure dependencies are installed.")
    
    print(f"{BLUE}{'='*70}{RESET}\n")
    
    print(f"\n{CYAN}What This Demonstrates:{RESET}")
    print(f"  • {GREEN}✓{RESET} SQLAlchemy ORM design with proper relationships")
    print(f"  • {GREEN}✓{RESET} Pydantic schemas for type-safe API validation")
    print(f"  • {GREEN}✓{RESET} Clean project structure and modularity")
    print(f"  • {GREEN}✓{RESET} Comprehensive database schema for workflow tracking")
    print(f"  • {GREEN}✓{RESET} Production-ready code organization\n")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
