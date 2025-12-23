from loguru import logger
import sys

# Remove default handler
logger.remove()

# Add a beautiful colored handler for development
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
           "<level>{level: <8}</level> | "
           "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
           "<level>{message}</level>",
    level="DEBUG" if __debug__ else "INFO",
    colorize=True,
)

# Optional: Add file logging (uncomment if you want logs saved to file)
# logger.add(
#     "logs/app.log",
#     rotation="10 MB",        # New file when reaches 10 MB
#     retention="7 days",      # Keep logs for 7 days
#     level="INFO",
#     compression="zip"
# )

# Create logs folder if needed (optional)
# import os
# os.makedirs("logs", exist_ok=True)