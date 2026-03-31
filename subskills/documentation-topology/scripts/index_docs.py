#!/usr/bin/env python3
from __future__ import annotations

import runpy
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "index_docs.py"
sys.path.insert(0, str(SCRIPT.parent))
runpy.run_path(str(SCRIPT), run_name="__main__")
