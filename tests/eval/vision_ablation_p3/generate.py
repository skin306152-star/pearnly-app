# -*- coding: utf-8 -*-
"""P3 targeted OCR corpus generator.

This machine currently runs the generator through Node/Playwright because the
local Python installation is unavailable. Keep this wrapper so callers that
expect generate.py still have one stable entry point.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def main() -> None:
    node = shutil.which("node") or shutil.which("node.exe")
    if not node:
        raise SystemExit("node is required to generate vision_ablation_p3")
    script = Path(__file__).with_name("generate.cjs")
    subprocess.run([node, str(script)], check=True)


if __name__ == "__main__":
    main()
