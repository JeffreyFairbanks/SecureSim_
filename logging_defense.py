# week_1/logging_defense.py
import logging
import sys
import os
import datetime


# Console logging forwarder
class ConsoleLogger:
    def __init__(self, log_file, original_stdout):
        self.log_file = log_file
        self.original_stdout = original_stdout

    def write(self, message):
        self.log_file.write(message)
        self.original_stdout.write(message)
        self.log_file.flush()  # Immediately write to file

    def flush(self):
        self.log_file.flush()
        self.original_stdout.flush()


def setup_logging():
    """Initialize the event logging system"""
    # Create data directory if needed
    os.makedirs('data', exist_ok=True)
    
    # Configure logging to file
    logging.basicConfig(
        filename='data/simulation.log', 
        level=logging.INFO,
        format='%(asctime)s:%(levelname)s:%(message)s'
    )
    logging.info("Logging initialized.")


def setup_console_logging():
    """Set up console output logging to file"""
    # Create data directory if needed
    os.makedirs('data', exist_ok=True)
    
    # Create timestamped log file
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    log_path = f'data/console_{timestamp}.log'
    
    # Open log file and save original stdout
    log_file = open(log_path, 'w')
    original_stdout = sys.stdout
    
    # Replace stdout with console logger
    sys.stdout = ConsoleLogger(log_file, original_stdout)
    
    print(f"Console logging started at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return log_file


def stop_console_logging(log_file):
    """Clean up console logging"""
    if log_file:
        print(f"Console logging stopped at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        sys.stdout = sys.__stdout__  # Restore original stdout
        log_file.close()


def log_anomaly(message):
    """Log an anomaly or security event"""
    logging.warning(f"Anomaly detected: {message}")