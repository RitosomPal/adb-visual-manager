"""Application logging configuration"""

import logging
import sys
from pathlib import Path

def setup_logging(log_file='adb-manager.log', level=logging.INFO):
    """
    Configure application-wide logging
    
    Args:
        log_file: Path to log file
        level: Logging level (INFO, DEBUG, ERROR, etc.)
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Setup handlers
    handlers = [
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
    
    # Configure logging
    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt=date_format,
        handlers=handlers
    )
    
    # Suppress verbose library logs
    logging.getLogger('ppadb').setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized")
    return logger
