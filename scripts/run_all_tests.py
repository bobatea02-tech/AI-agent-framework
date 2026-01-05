"""
Quick Test Runner for AI Agent Framework
Runs all tests and generates a comprehensive report for demonstration
"""
import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path

# ANSI color codes for Windows
try:
    import colorama
    colorama.init(autoreset=True)
    GREEN = colorama.Fore.GREEN
    RED = colorama.Fore.RED
    YELLOW = colorama.Fore.YELLOW
    BLUE = colorama.Fore.BLUE
    RESET = colorama.Style.RESET_ALL
except ImportError:
    GREEN = RED = YELLOW = BLUE = RESET = ""

class TestRunner:
    def __init__(self):
        self.results = {}
        self.start_time = datetime.now()
        self.project_root = Path(__file__).parent.parent
        
    def print_header(self, text):
        """Print a formatted header"""
        print(f"\n{BLUE}{'='*70}{RESET}")
        print(f"{BLUE}{text.center(70)}{RESET}")
        print(f"{BLUE}{'='*70}{RESET}\n")
        
    def run_command(self, name, command, cwd=None):
        """Run a command and capture results"""
        print(f"{YELLOW}Running: {name}{RESET}")
        print(f"Command: {' '.join(command)}\n")
        
        try:
            result = subprocess.run(
                command,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            success = result.returncode == 0
            self.results[name] = {
                'success': success,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
            if success:
                print(f"{GREEN}✓ {name} PASSED{RESET}\n")
            else:
                print(f"{RED}✗ {name} FAILED{RESET}")
                print(f"Error Output:\n{result.stderr}\n")
                
            return success
            
        except subprocess.TimeoutExpired:
            print(f"{RED}✗ {name} TIMEOUT{RESET}\n")
            self.results[name] = {
                'success': False,
                'error': 'Timeout after 5 minutes'
            }
            return False
        except Exception as e:
            print(f"{RED}✗ {name} ERROR: {e}{RESET}\n")
            self.results[name] = {
                'success': False,
                'error': str(e)
            }
            return False
    
    def run_health_check(self):
        """Run system health check"""
        self.print_header("SYSTEM HEALTH CHECK")
        return self.run_command(
            "Health Check",
            [sys.executable, "scripts/health_check.py", "--verbose"]
        )
    
    def run_unit_tests(self):
        """Run unit tests with coverage"""
        self.print_header("UNIT TESTS")
        return self.run_command(
            "Unit Tests",
            [
                sys.executable, "-m", "pytest",
                "tests/unit",
                "-v",
                "--tb=short",
                "-m", "unit or not integration and not e2e and not performance"
            ]
        )
    
    def run_verification_scripts(self):
        """Run verification scripts"""
        self.print_header("VERIFICATION SCRIPTS")
        
        scripts = [
            ("Database Models", "tests/verify_models.py"),
            ("OCR Executor", "tests/verify_ocr_executor.py"),
            ("LLM Executor", "tests/verify_llm_executor.py"),
            ("Validation Executor", "tests/verify_validation_executor.py"),
        ]
        
        all_passed = True
        for name, script in scripts:
            passed = self.run_command(
                name,
                [sys.executable, script]
            )
            all_passed = all_passed and passed
            
        return all_passed
    
    def run_integration_tests(self):
        """Run integration tests"""
        self.print_header("INTEGRATION TESTS")
        return self.run_command(
            "Integration Tests",
            [
                sys.executable, "-m", "pytest",
                "tests/integration",
                "-v",
                "--tb=short",
                "-m", "integration"
            ]
        )
    
    def run_e2e_tests(self):
        """Run end-to-end tests"""
        self.print_header("END-TO-END TESTS")
        return self.run_command(
            "E2E Tests",
            [
                sys.executable, "-m", "pytest",
                "tests/e2e",
                "-v",
                "--tb=short",
                "-m", "e2e"
            ]
        )
    
    def generate_report(self):
        """Generate final test report"""
        self.print_header("TEST SUMMARY REPORT")
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results.values() if r.get('success', False))
        failed_tests = total_tests - passed_tests
        
        print(f"Total Test Suites: {total_tests}")
        print(f"{GREEN}Passed: {passed_tests}{RESET}")
        print(f"{RED}Failed: {failed_tests}{RESET}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        print(f"Duration: {datetime.now() - self.start_time}")
        
        print(f"\n{BLUE}Detailed Results:{RESET}\n")
        for name, result in self.results.items():
            status = f"{GREEN}✓ PASS{RESET}" if result.get('success') else f"{RED}✗ FAIL{RESET}"
            print(f"  [{status}] {name}")
            
        # Save report to file
        report_file = self.project_root / "logs" / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w') as f:
            f.write("="*70 + "\n")
            f.write("AI AGENT FRAMEWORK - TEST REPORT\n")
            f.write("="*70 + "\n\n")
            f.write(f"Generated: {datetime.now()}\n")
            f.write(f"Total Suites: {total_tests}\n")
            f.write(f"Passed: {passed_tests}\n")
            f.write(f"Failed: {failed_tests}\n")
            f.write(f"Success Rate: {(passed_tests/total_tests*100):.1f}%\n\n")
            
            for name, result in self.results.items():
                f.write(f"\n{'='*70}\n")
                f.write(f"Test: {name}\n")
                f.write(f"Status: {'PASS' if result.get('success') else 'FAIL'}\n")
                f.write(f"{'='*70}\n\n")
                
                if 'stdout' in result:
                    f.write("Standard Output:\n")
                    f.write(result['stdout'])
                    f.write("\n\n")
                    
                if 'stderr' in result and result['stderr']:
                    f.write("Error Output:\n")
                    f.write(result['stderr'])
                    f.write("\n\n")
        
        print(f"\n{GREEN}Full report saved to: {report_file}{RESET}\n")
        
        return passed_tests == total_tests

def main():
    """Main test runner"""
    print(f"{BLUE}╔══════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BLUE}║     AI AGENT FRAMEWORK - COMPREHENSIVE TEST SUITE                ║{RESET}")
    print(f"{BLUE}╚══════════════════════════════════════════════════════════════════╝{RESET}")
    
    runner = TestRunner()
    
    # Run test suites in order
    test_suites = [
        ("Health Check", runner.run_health_check),
        ("Unit Tests", runner.run_unit_tests),
        ("Verification Scripts", runner.run_verification_scripts),
        # Commented out by default - uncomment if services are running
        # ("Integration Tests", runner.run_integration_tests),
        # ("E2E Tests", runner.run_e2e_tests),
    ]
    
    print(f"\n{YELLOW}Running {len(test_suites)} test suite(s)...{RESET}\n")
    print(f"{YELLOW}Note: Integration and E2E tests are skipped by default.{RESET}")
    print(f"{YELLOW}      To run them, ensure Docker services are running and uncomment in script.{RESET}\n")
    
    for name, test_func in test_suites:
        try:
            test_func()
        except KeyboardInterrupt:
            print(f"\n{RED}Test run interrupted by user{RESET}")
            sys.exit(1)
        except Exception as e:
            print(f"{RED}Error running {name}: {e}{RESET}")
    
    # Generate final report
    all_passed = runner.generate_report()
    
    if all_passed:
        print(f"\n{GREEN}{'='*70}{RESET}")
        print(f"{GREEN}ALL TESTS PASSED! ✓{RESET}")
        print(f"{GREEN}Your project is ready for demonstration!{RESET}")
        print(f"{GREEN}{'='*70}{RESET}\n")
        return 0
    else:
        print(f"\n{RED}{'='*70}{RESET}")
        print(f"{RED}SOME TESTS FAILED ✗{RESET}")
        print(f"{RED}Please review the report above and fix issues before demo.{RESET}")
        print(f"{RED}{'='*70}{RESET}\n")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{RED}Test run cancelled{RESET}")
        sys.exit(1)
