"""
Image Processor Name Tool

AI-powered image filename generator using Ollama LLaVA model.
"""

__version__ = "2.0.0"
__author__ = "Shane Holloman"
__email__ = "contact@shaneholloman.com"

from pathlib import Path

# Package paths
PACKAGE_ROOT = Path(__file__).parent
PROJECT_ROOT = PACKAGE_ROOT.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure logs directory exists
LOGS_DIR.mkdir(exist_ok=True)
