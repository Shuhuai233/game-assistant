"""
Game Assistant — Main entry point.
Double-click to run. No terminal, no command line.
"""

# CRITICAL: Set env vars BEFORE any imports to prevent ONNX Runtime GPU errors
import os
os.environ["ORT_DISABLE_ALL_PROVIDERS"] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["CT2_FORCE_CPU"] = "1"

from app import main

if __name__ == "__main__":
    main()
