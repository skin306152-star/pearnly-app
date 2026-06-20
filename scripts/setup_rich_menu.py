# -*- coding: utf-8 -*-
"""一次性上线 LINE Rich Menu(prod channel token)。

跑法(prod venv):  cd /opt/mrpilot && set -a && . ./.env && set +a && ./venv/bin/python scripts/setup_rich_menu.py
幂等:重复跑会先删旧同名菜单再重建,不堆叠。需 LINE_CHANNEL_TOKEN 在环境里。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.line_binding import line_rich_menu  # noqa: E402

if __name__ == "__main__":
    rid = line_rich_menu.setup_default_menu()
    print(f"rich menu id: {rid}")
    sys.exit(0 if rid else 1)
