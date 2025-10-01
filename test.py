#!/usr/bin/env python3
"""
Test runner for Dynamic DCA Strategy
"""
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.test_strategy import main

if __name__ == "__main__":
    main()
