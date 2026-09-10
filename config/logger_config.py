import logging
import os
from datetime import datetime

# Create logs folder if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Generate a unique log filename for each run
log_filename = datetime.now().strftime("logs/app_%Y-%m-%d_%H-%M-%S.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info(f"Logging to: {log_filename}")