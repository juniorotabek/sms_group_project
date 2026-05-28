import sys
import os

# Compatibility: pathlib for Python 2/3
try:
    from pathlib import Path
except ImportError:
    # Python 2 fallback
    from pathlib2 import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
