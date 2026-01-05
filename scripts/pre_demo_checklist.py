"""
Pre-Demo Checklist Script
Runs all necessary checks to ensure the project is ready for demonstration
"""
import subprocess
import sys
import os
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

class PreDemoChecker:
    def __init__(self):
        self.checks_passed = []
        self.checks_failed = []
        self.project_root = Path(__file__).parent.parent
        
    def check_item(self, name, command=None, expected_output=None, check_func=None):
        """Check a single item"""
        print(f"\n{CYAN}Checking: {name}{RESET}")
        
        try:
            if check_func:
                # Custom check function
                result = check_func()
                success = result
            elif command:
                # Run command
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    shell=True
                )
                success = result.returncode == 0
                if expected_output:
                    success = success and expected_output in result.stdout
            else:
                print(f"{RED}No check method provided{RESET}")
                return False
            
            if success:
                print(f"{GREEN}✓ {name} - OK{RESET}")
                self.checks_passed.append(name)
                return True
            else:
                print(f"{RED}✗ {name} - FAILED{RESET}")
                self.checks_failed.append(name)
                return False
                
        except Exception as e:
            print(f"{RED}✗ {name} - ERROR: {e}{RESET}")
            self.checks_failed.append(name)
            return False
    
    def check_python_version(self):
        """Check Python version is 3.10+"""
        return sys.version_info >= (3, 10)
    
    def check_file_exists(self, filepath):
        """Check if a file exists"""
        return (self.project_root / filepath).exists()
    
    def check_directory_exists(self, dirpath):
        """Check if a directory exists"""
        return (self.project_root / dirpath).is_dir()
    
    def run_all_checks(self):
        """Run all pre-demo checks"""
        print(f"{BLUE}{'='*70}{RESET}")
        print(f"{BLUE}PRE-DEMO CHECKLIST - AI AGENT FRAMEWORK{RESET}")
        print(f"{BLUE}{'='*70}{RESET}")
        
        print(f"\n{YELLOW}1. PREREQUISITES{RESET}")
        self.check_item(
            "Python 3.10+",
            check_func=self.check_python_version
        )
        self.check_item(
            "Docker installed",
            command="docker --version"
        )
        self.check_item(
            "Docker Compose installed",
            command="docker compose version"
        )
        
        print(f"\n{YELLOW}2. PROJECT FILES{RESET}")
        self.check_item(
            "requirements.txt exists",
            check_func=lambda: self.check_file_exists("requirements.txt")
        )
        self.check_item(
            ".env file exists",
            check_func=lambda: self.check_file_exists(".env")
        )
        self.check_item(
            "docker-compose.yml exists",
            check_func=lambda: self.check_file_exists("docker-compose.yml")
        )
        
        print(f"\n{YELLOW}3. SOURCE CODE{RESET}")
        self.check_item(
            "src/ directory exists",
            check_func=lambda: self.check_directory_exists("src")
        )
        self.check_item(
            "tests/ directory exists",
            check_func=lambda: self.check_directory_exists("tests")
        )
        self.check_item(
            "scripts/ directory exists",
            check_func=lambda: self.check_directory_exists("scripts")
        )
        self.check_item(
            "workflows/ directory exists",
            check_func=lambda: self.check_directory_exists("workflows")
        )
        
        print(f"\n{YELLOW}4. DEPENDENCIES{RESET}")
        packages = [
            "fastapi",
            "sqlalchemy",
            "redis",
            "kafka-python",
            "pytest",
            "pydantic"
        ]
        for package in packages:
            self.check_item(
                f"{package} installed",
                command=f"{sys.executable} -c \"import {package.replace('-', '_')}\""
            )
        
        print(f"\n{YELLOW}5. DOCKER SERVICES (Optional - for full demo){RESET}")
        print(f"{CYAN}Note: These checks may fail if services aren't started yet{RESET}")
        self.check_item(
            "Docker daemon running",
            command="docker info"
        )
        # Don't fail if services aren't running - just informational
        try:
            result = subprocess.run(
                "docker compose ps".split(),
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and len(result.stdout) > 100:
                print(f"{GREEN}✓ Docker services status available{RESET}")
                print(f"  {CYAN}Services:{RESET}")
                for line in result.stdout.split('\n')[1:6]:  # Show first 5 services
                    if line.strip():
                        print(f"    {line}")
            else:
                print(f"{YELLOW}⚠ Docker services not started (run: docker compose up -d){RESET}")
        except:
            print(f"{YELLOW}⚠ Cannot check Docker services status{RESET}")
        
        print(f"\n{YELLOW}6. TEST FILES{RESET}")
        test_files = [
            "tests/unit/test_ocr_executor.py",
            "tests/verify_models.py",
            "tests/verify_ocr_executor.py",
            "scripts/health_check.py"
        ]
        for test_file in test_files:
            self.check_item(
                Path(test_file).name,
                check_func=lambda tf=test_file: self.check_file_exists(tf)
            )
        
        print(f"\n{YELLOW}7. DOCUMENTATION{RESET}")
        docs = [
            "README.md",
            "PROJECT_BRIEF.md",
            "docs/ARCHITECTURE.md",
            "docs/API_REFERENCE.md"
        ]
        for doc in docs:
            self.check_item(
                Path(doc).name,
                check_func=lambda d=doc: self.check_file_exists(d)
            )
        
        # Final summary
        self.print_summary()
        
    def print_summary(self):
        """Print final summary"""
        print(f"\n{BLUE}{'='*70}{RESET}")
        print(f"{BLUE}CHECKLIST SUMMARY{RESET}")
        print(f"{BLUE}{'='*70}{RESET}\n")
        
        total = len(self.checks_passed) + len(self.checks_failed)
        passed = len(self.checks_passed)
        failed = len(self.checks_failed)
        
        print(f"Total Checks: {total}")
        print(f"{GREEN}Passed: {passed}{RESET}")
        print(f"{RED}Failed: {failed}{RESET}")
        
        if failed > 0:
            print(f"\n{RED}Failed Checks:{RESET}")
            for check in self.checks_failed:
                print(f"  ✗ {check}")
        
        print(f"\n{BLUE}{'='*70}{RESET}")
        
        if failed == 0:
            print(f"{GREEN}✓ ALL CHECKS PASSED!{RESET}")
            print(f"{GREEN}Your project is ready for demonstration!{RESET}")
            print(f"\n{CYAN}Next steps:{RESET}")
            print(f"  1. Start Docker services: docker compose up -d")
            print(f"  2. Run health check: python scripts/health_check.py")
            print(f"  3. Run tests: python scripts/run_all_tests.py")
            print(f"  4. Review demo guide in the artifact")
        elif failed <= 3:
            print(f"{YELLOW}⚠ MINOR ISSUES DETECTED{RESET}")
            print(f"{YELLOW}Fix the items above before proceeding{RESET}")
        else:
            print(f"{RED}✗ MULTIPLE ISSUES DETECTED{RESET}")
            print(f"{RED}Please address the failed checks before demonstration{RESET}")
        
        print(f"{BLUE}{'='*70}{RESET}\n")
        
        return failed == 0

def main():
    checker = PreDemoChecker()
    success = checker.run_all_checks()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
