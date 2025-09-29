#!/usr/bin/env python3
"""
Launcher script for WhisperTube GUI
"""

import sys
import os
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from youtube_scraper_gui import main
    main()
except ImportError as e:
    print(f"Error: {e}")
    print("\nPlease install required dependencies:")
    print("pip install -r requirements.txt")
    input("\nPress Enter to exit...")
