"""
Pytest configuration for skeleton tests.

Adds skeleton/doxstrux to Python path so tests can import from 'doxstrux' namespace.
This allows tests to import from skeleton code instead of production src/doxstrux/.
"""
import sys
from pathlib import Path

# Add skeleton directory to Python path
skeleton_root = Path(__file__).parent.parent
sys.path.insert(0, str(skeleton_root))
