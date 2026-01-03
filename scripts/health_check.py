#!/usr/bin/env python3
import sys
import os
import time
import json
import logging
import argparse
import concurrent.futures
import importlib
from datetime import datetime
from typing import Dict, Any, List

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    import psycopg2
    import redis
    from kafka import KafkaProducer, KafkaConsumer
    import requests
    from colorama import init, Fore, Style
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Please install: psycopg2-binary redis kafka-python requests colorama")
    sys.exit(1)

# Initialize colorama
init(autoreset=True)

# Configuration from src
try:
    from src.config import settings
except ImportError:
    # Fallback/Mock for standalone run if src not found or issues
    class Settings:
        database_url = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/dbname")
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", 6379))
        kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        airflow_url = os.getenv("AIRFLOW_URL", "http://localhost:8080")
        api_url = os.getenv("API_URL", "http://localhost:8000")
    settings = Settings()

# Setup Logging
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'health_check_report.txt')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("HealthCheck")

class HealthChecker:
    def __init__(self, verbose=False, fix=False):
        self.verbose = verbose
        self.fix = fix
        self.results: Dict[str, bool] = {}
        self.details: Dict[str, str] = {}

    def log_result(self, component: str, success: bool, message: str):
        self.results[component] = success
        self.details[component] = message
        status = f"{Fore.GREEN}PASS{Style.RESET_ALL}" if success else f"{Fore.RED}FAIL{Style.RESET_ALL}"
        print(f"[{status}] {component}: {message}")
        if self.verbose and not success:
            logger.error(f"{component} failed: {message}")
        elif self.verbose:
            logger.info(f"{component} passed: {message}")

    def check_database(self):
        """Test PostgreSQL connection and basic query."""
        try:
            if not settings.database_url:
                 self.log_result("Database", False, "No DATABASE_URL configured")
                 return
            
            # Using psycopg2 directly for raw check, independent of ORM
            conn = psycopg2.connect(settings.database_url)
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.fetchone()
            
            # Check for tables existence (basic check)
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = [row[0] for row in cur.fetchall()]
            
            cur.close()
            conn.close()
            
            self.log_result("Database", True, f"Connected. Found tables: {', '.join(tables) if tables else 'None'}")
        except Exception as e:
            self.log_result("Database", False, str(e))

    def check_redis(self):
        """Test Redis connection."""
        try:
            r = redis.Redis(host=settings.redis_host, port=settings.redis_port, socket_connect_timeout=2)
            if r.ping():
                self.log_result("Redis", True, "Connection successful")
            else:
                self.log_result("Redis", False, "Ping failed")
        except Exception as e:
            self.log_result("Redis", False, str(e))

    def check_kafka(self):
        """Test Kafka connection, producer, and consumer."""
        try:
            # Check Producer
            producer = KafkaProducer(bootstrap_servers=settings.kafka_bootstrap_servers)
            
            # Check Consumer
            consumer = KafkaConsumer(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                group_id='health_check_group',
                auto_offset_reset='earliest'
            )
            
            # Check Topics
            topics = consumer.topics()
            required_topics = {'workflows', 'workflow_results', 'workflow_events'}
            missing_topics = required_topics - topics
            
            if missing_topics:
                 self.log_result("Kafka", False, f"Missing topics: {missing_topics}")
                 return

            # Test Message Flow
            test_topic = 'health_check'
            producer.send(test_topic, b'ping')
            producer.flush()
            
            self.log_result("Kafka", True, f"Connected. Topics: {len(topics)} found.")
            
            # Clean up
            producer.close()
            consumer.close()
        except Exception as e:
            self.log_result("Kafka", False, str(e))

    def check_airflow(self):
        """Test Airflow Webserver and API."""
        base_url = getattr(settings, 'airflow_url', 'http://localhost:8080')
        try:
            # Check Health Endpoint
            resp = requests.get(f"{base_url}/health", timeout=5)
            if resp.status_code == 200:
                health_data = resp.json()
                scheduler_status = health_data.get('scheduler', {}).get('status')
                triggerer_status = health_data.get('triggerer', {}).get('status')
                
                msg = f"Webserver accessible. Scheduler: {scheduler_status}"
                self.log_result("Airflow", True, msg)
            else:
                self.log_result("Airflow", False, f"Health check returned {resp.status_code}")
                
            # Note: Checking for DAGs usually requires auth, skipping for basic health check 
            # unless we implement BasicAuth credentials here.
        except Exception as e:
            self.log_result("Airflow", False, f"Connection failed: {e}")

    def check_api(self):
        """Test Application API."""
        base_url = getattr(settings, 'api_url', 'http://localhost:8000')
        try:
            resp = requests.get(f"{base_url}/health", timeout=5)
            if resp.status_code == 200:
                self.log_result("API", True, "Health endpoint running")
            else:
                self.log_result("API", False, f"Returned {resp.status_code}")
        except Exception as e:
            self.log_result("API", False, f"Connection failed: {e}")

    def check_executors(self):
        """Test Executor Instantiation."""
        executor_modules = [
            ('src.executors.ocr_executor', 'OCRExecutor'),
            ('src.executors.llm_executor', 'LLMExecutor'),
            ('src.executors.validation_executor', 'ValidationExecutor')
        ]
        
        passed = []
        failed = []
        
        for module_name, class_name in executor_modules:
            try:
                module = importlib.import_module(module_name)
                executor_class = getattr(module, class_name)
                # Just checking if we can reference the class, instantiation might need args
                if executor_class:
                    passed.append(class_name)
            except Exception as e:
                failed.append(f"{class_name}: {e}")
        
        if failed:
            self.log_result("Executors", False, f"Failed: {', '.join(failed)}")
        else:
            self.log_result("Executors", True, f"Verified: {', '.join(passed)}")

    def check_filesystem(self):
        """Test File System Permissions."""
        paths = [
            ('uploads/', 'w'),
            ('logs/', 'w'),
            ('models/openvino/', 'r')
        ]
        
        failed = []
        root_dir = os.path.join(os.path.dirname(__file__), '..')
        
        for path_rel, mode in paths:
            path = os.path.join(root_dir, path_rel)
            if mode == 'w':
                try:
                    os.makedirs(path, exist_ok=True)
                    test_file = os.path.join(path, '.health_check_tmp')
                    with open(test_file, 'w') as f:
                        f.write('check')
                    os.remove(test_file)
                except Exception as e:
                    failed.append(f"{path} not writable: {e}")
            elif mode == 'r':
                if not os.path.exists(path):
                     # Try creating if fix is on (though 'r' usually implies expects existence)
                     if self.fix:
                         try:
                             os.makedirs(path, exist_ok=True)
                             if self.verbose: logger.info(f"Created missing directory {path}")
                         except:
                             failed.append(f"{path} missing")
                     else:
                        failed.append(f"{path} missing")
                        
        if failed:
            self.log_result("FileSystem", False, "; ".join(failed))
        else:
            self.log_result("FileSystem", True, "All paths verified")

    def run_all(self):
        """Run all checks in parallel."""
        print(f"{Fore.CYAN}Starting System Health Check...{Style.RESET_ALL}")
        print("-" * 50)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            futures = [
                executor.submit(self.check_database),
                executor.submit(self.check_redis),
                executor.submit(self.check_kafka),
                executor.submit(self.check_airflow),
                executor.submit(self.check_api),
                executor.submit(self.check_executors),
                executor.submit(self.check_filesystem)
            ]
            concurrent.futures.wait(futures)
            
        print("-" * 50)
        self.generate_report()
        
        # Determine exit code
        if all(self.results.values()):
            print(f"{Fore.GREEN}SYSTEM HEALTHY{Style.RESET_ALL}")
            return 0
        else:
            print(f"{Fore.RED}SYSTEM UNHEALTHY{Style.RESET_ALL}")
            return 1

    def generate_report(self):
        with open(LOG_FILE, 'w') as f:
            f.write("System Health Check Report\n")
            f.write(f"Generated at: {datetime.now()}\n")
            f.write("-" * 50 + "\n")
            for component, result in self.results.items():
                status = "PASS" if result else "FAIL"
                f.write(f"[{status}] {component}: {self.details.get(component, '')}\n")
        print(f"Report report generated at {LOG_FILE}")

def main():
    parser = argparse.ArgumentParser(description="System Health Check Script")
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--fix', action='store_true', help='Attempt to auto-fix common issues (e.g., create directories)')
    
    args = parser.parse_args()
    
    checker = HealthChecker(verbose=args.verbose, fix=args.fix)
    sys.exit(checker.run_all())

if __name__ == "__main__":
    main()
