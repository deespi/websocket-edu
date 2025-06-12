"""
Logging Configuration
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Create logs directory if it doesn't exist
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

def setup_logger(
    name: str, 
    level: str = 'INFO',
    log_to_file: bool = True,
    log_to_console: bool = True
) -> logging.Logger:
    """
    Set up a logger with both file and console handlers
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        log_to_file: Whether to log to file
        log_to_console: Whether to log to console
        
    Returns:
        Configured logger instance
    """
    
    logger = logging.getLogger(name)
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_to_file:
        log_filename = LOGS_DIR / f"websocket_iot_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_filename,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # File gets all messages
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get an existing logger or create a new one
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

def set_log_level(logger_name: str, level: str):
    """
    Set log level for a specific logger
    
    Args:
        logger_name: Name of the logger
        level: New log level
    """
    logger = logging.getLogger(logger_name)
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    # Update handler levels too
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
            handler.setLevel(numeric_level)

def log_system_info():
    """Log system information for debugging"""
    logger = get_logger(__name__)
    
    import platform
    import websockets
    
    logger.info("🖥️  System Information:")
    logger.info(f"   Python version: {platform.python_version()}")
    logger.info(f"   Platform: {platform.platform()}")
    logger.info(f"   WebSockets version: {websockets.__version__}")
    logger.info(f"   Log directory: {LOGS_DIR}")

class WebSocketLogFilter(logging.Filter):
    """
    Custom log filter for WebSocket messages
    """
    
    def __init__(self, exclude_patterns: Optional[list] = None):
        super().__init__()
        self.exclude_patterns = exclude_patterns or [
            'connection open',
            'connection closed',
            '< text'
        ]
    
    def filter(self, record):
        """
        Filter log records based on patterns
        
        Args:
            record: LogRecord to filter
            
        Returns:
            True if record should be logged, False otherwise
        """
        message = record.getMessage().lower()
        
        # Exclude noisy WebSocket messages
        for pattern in self.exclude_patterns:
            if pattern in message:
                return False
        
        return True

def setup_websocket_logging():
    """Setup specific logging configuration for WebSocket components"""
    
    # Reduce verbosity of websockets library
    websockets_logger = logging.getLogger('websockets')
    websockets_logger.setLevel(logging.WARNING)
    
    # Add custom filter to reduce noise
    ws_filter = WebSocketLogFilter()
    websockets_logger.addFilter(ws_filter)

# Performance logging decorator
def log_performance(logger_name: str = __name__):
    """
    Decorator to log function execution time
    
    Args:
        logger_name: Name of logger to use
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name)
            start_time = datetime.now()
            
            try:
                result = func(*args, **kwargs)
                execution_time = (datetime.now() - start_time).total_seconds()
                logger.debug(f"⏱️  {func.__name__} executed in {execution_time:.3f}s")
                return result
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                logger.error(f"❌ {func.__name__} failed after {execution_time:.3f}s: {e}")
                raise
        
        return wrapper
    return decorator

# Example usage and testing
if __name__ == "__main__":
    # Test logger setup
    logger = setup_logger(__name__, level='DEBUG')
    
    logger.debug("🔍 This is a debug message")
    logger.info("ℹ️  This is an info message")
    logger.warning("⚠️  This is a warning message")
    logger.error("❌ This is an error message")
    logger.critical("🚨 This is a critical message")
    
    # Test performance logging
    @log_performance(__name__)
    def example_function():
        import time
        time.sleep(0.1)
        return "Done"
    
    result = example_function()
    logger.info(f"Function result: {result}")
    
    # Log system info
    log_system_info()
    
    print("✅ Logger testing complete! Check the logs/ directory for output files.")