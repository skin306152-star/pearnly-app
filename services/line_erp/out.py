from __future__ import annotations

import asyncio
import logging


def make_spawn(tag: str):
    logger = logging.getLogger(tag)

    def spawn(coro) -> None:
        async def run() -> None:
            try:
                await coro
            except Exception:
                logger.exception("background task failed")

        try:
            asyncio.get_running_loop().create_task(run())
        except RuntimeError:
            logger.warning("no running event loop; background task dropped")

    return spawn
