import os
import sys
import time
import subprocess
import logging
import asyncio
import psutil
from datetime import datetime
from typing import Optional
import requests
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - GUARDIAN - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('guardian.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

MAIN_PROCESS_NAME = "main.py"
GATEWAY_PORT = 8000
HEALTH_CHECK_INTERVAL = 10
MAX_RESTART_ATTEMPTS = 10
RESTART_COOLDOWN = 5

class Guardian:
    def __init__(self):
        self.restart_count = 0
        self.last_restart_time = 0
        self.main_process: Optional[subprocess.Popen] = None
        self.running = True
        
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are installed"""
        required_packages = [
            'fastapi', 'uvicorn', 'httpx', 'pydantic', 'psutil'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            logger.warning(f"Missing dependencies: {missing_packages}")
            self.install_dependencies(missing_packages)
            return False
        
        return True
    
    def install_dependencies(self, packages: list):
        """Install missing dependencies"""
        logger.info(f"Installing missing packages: {packages}")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install"] + packages,
                check=True,
                capture_output=True,
                text=True
            )
            logger.info("Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e.stderr}")
            self.update_requirements_txt(packages)
    
    def update_requirements_txt(self, packages: list):
        """Update requirements.txt with missing packages"""
        requirements_path = "requirements.txt"
        existing_packages = set()
        
        if os.path.exists(requirements_path):
            with open(requirements_path, 'r') as f:
                existing_packages = set(line.strip().split('==')[0] for line in f if line.strip())
        
        with open(requirements_path, 'a') as f:
            for package in packages:
                if package not in existing_packages:
                    f.write(f"{package}\n")
                    logger.info(f"Added {package} to requirements.txt")
    
    def check_port_conflict(self) -> bool:
        """Check if the gateway port is already in use"""
        for conn in psutil.net_connections():
            if conn.laddr.port == GATEWAY_PORT and conn.status == 'LISTEN':
                logger.warning(f"Port {GATEWAY_PORT} is already in use by PID {conn.pid}")
                try:
                    process = psutil.Process(conn.pid)
                    logger.info(f"Killing process {process.name()} (PID: {conn.pid})")
                    process.kill()
                    time.sleep(1)
                    return True
                except psutil.NoSuchProcess:
                    return True
        return False
    
    def check_health(self) -> bool:
        """Check if the gateway is healthy"""
        try:
            response = requests.get(
                f"http://localhost:{GATEWAY_PORT}/health",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Health check failed: {str(e)}")
            return False
    
    def analyze_error_logs(self) -> Optional[str]:
        """Analyze error logs to determine the issue"""
        log_file = "gateway.log"
        if not os.path.exists(log_file):
            return None
        
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()[-100:]  # Last 100 lines
            
            error_lines = [line for line in lines if 'ERROR' in line or 'Exception' in line]
            
            if error_lines:
                last_error = error_lines[-1]
                logger.info(f"Last error detected: {last_error.strip()}")
                
                # Analyze common errors
                if 'ImportError' in last_error or 'ModuleNotFoundError' in last_error:
                    return "dependency_missing"
                elif 'Port' in last_error or 'Address already in use' in last_error:
                    return "port_conflict"
                elif '429' in last_error or 'rate limit' in last_error.lower():
                    return "rate_limit"
                elif 'timeout' in last_error.lower():
                    return "timeout"
                elif 'authentication' in last_error.lower() or '401' in last_error:
                    return "auth_error"
                else:
                    return "unknown_error"
        except Exception as e:
            logger.error(f"Failed to analyze logs: {str(e)}")
        
        return None
    
    def auto_fix_code(self, error_type: str):
        """Automatically fix code based on error type"""
        logger.info(f"Attempting auto-fix for: {error_type}")
        
        if error_type == "dependency_missing":
            self.check_dependencies()
        elif error_type == "port_conflict":
            self.check_port_conflict()
        elif error_type == "auth_error":
            logger.warning("Authentication error detected. Please check .env file.")
            self.verify_env_variables()
        elif error_type == "rate_limit":
            logger.info("Rate limit detected. This is expected behavior, will auto-retry.")
        else:
            logger.info("Attempting generic restart")
    
    def verify_env_variables(self):
        """Verify that all required environment variables are set"""
        required_vars = [
            "AGNES_MERCHANT_KEY", "AGNES_PERSONAL_KEY", 
            "NVIDIA_API_KEY", "AWS_ACCESS_KEY_ID", 
            "AWS_SECRET_ACCESS_KEY", "LOCAL_AUTH_TOKEN"
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.error(f"Missing environment variables: {missing_vars}")
            logger.info("Please ensure .env file exists and is properly configured")
        else:
            logger.info("All environment variables are set")
    
    def start_main_process(self):
        """Start the main gateway process"""
        logger.info("Starting main gateway process...")
        
        # Check for port conflicts first
        self.check_port_conflict()
        
        # Check dependencies
        self.check_dependencies()
        
        try:
            self.main_process = subprocess.Popen(
                [sys.executable, MAIN_PROCESS_NAME],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            logger.info(f"Main process started with PID: {self.main_process.pid}")
            self.restart_count = 0
            return True
        except Exception as e:
            logger.error(f"Failed to start main process: {str(e)}")
            return False
    
    def stop_main_process(self):
        """Stop the main gateway process"""
        if self.main_process:
            logger.info("Stopping main process...")
            try:
                self.main_process.terminate()
                self.main_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning("Main process did not terminate gracefully, killing...")
                self.main_process.kill()
            except Exception as e:
                logger.error(f"Error stopping main process: {str(e)}")
            
            self.main_process = None
    
    def restart_main_process(self):
        """Restart the main gateway process with cooldown"""
        current_time = time.time()
        
        if current_time - self.last_restart_time < RESTART_COOLDOWN:
            wait_time = RESTART_COOLDOWN - (current_time - self.last_restart_time)
            logger.info(f"Cooldown period, waiting {wait_time:.1f} seconds...")
            time.sleep(wait_time)
        
        self.stop_main_process()
        
        if self.restart_count >= MAX_RESTART_ATTEMPTS:
            logger.error(f"Max restart attempts ({MAX_RESTART_ATTEMPTS}) reached. Giving up.")
            self.running = False
            return False
        
        self.restart_count += 1
        self.last_restart_time = current_time
        
        logger.info(f"Restart attempt {self.restart_count}/{MAX_RESTART_ATTEMPTS}")
        
        # Analyze errors before restart
        error_type = self.analyze_error_logs()
        if error_type:
            self.auto_fix_code(error_type)
        
        return self.start_main_process()
    
    def monitor_process(self):
        """Monitor the main process and restart if needed"""
        while self.running:
            if not self.main_process or self.main_process.poll() is not None:
                logger.warning("Main process is not running!")
                if not self.restart_main_process():
                    break
            elif not self.check_health():
                logger.warning("Health check failed!")
                if not self.restart_main_process():
                    break
            else:
                logger.info("Gateway is healthy")
            
            time.sleep(HEALTH_CHECK_INTERVAL)
    
    def run(self):
        """Main guardian loop"""
        logger.info("Guardian starting...")
        
        # Verify environment
        self.verify_env_variables()
        
        # Start main process
        if not self.start_main_process():
            logger.error("Failed to start main process initially")
            return
        
        # Monitor
        try:
            self.monitor_process()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Guardian error: {str(e)}")
        finally:
            logger.info("Guardian shutting down...")
            self.stop_main_process()

if __name__ == "__main__":
    guardian = Guardian()
    guardian.run()
