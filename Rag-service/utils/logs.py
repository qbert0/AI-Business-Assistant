#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/6/1 12:41
@Author  : alexanderwu
@File    : logs.py
"""

from __future__ import annotations

import asyncio
import sys
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Optional

from loguru import logger as _logger
from pydantic import BaseModel, Field

from utils.constants import LLM_RESPONSE_LOG, ROOT_PATH, LLM_STREAM_LOG

LLM_STREAM_QUEUE: ContextVar[asyncio.Queue] = ContextVar("llm-stream")

VOICE_STREAM_QUEUE: ContextVar[asyncio.Queue] = ContextVar("voice-stream")

Logger = type(_logger)

class ToolLogItem(BaseModel):
    type_: str = Field(
        alias="type", default="str", description="Data type of `value` field."
    )
    name: str
    value: Any


TOOL_LOG_END_MARKER = ToolLogItem(
    type="str", name="end_marker", value="\x18\x19\x1b\x18"
)  # A special log item to suggest the end of a stream log

_print_level = "INFO"


def define_log_level(
    print_level="INFO", logfile_level="DEBUG", name: Optional[str] = None
):
    """Adjust the log level to above level"""
    global _print_level
    _print_level = print_level

    current_date = datetime.now()
    formatted_date = current_date.strftime("%Y%m%d")
    log_name = (
        f"{name}_{formatted_date}" if name else formatted_date
    )  # name a log with prefix name

    _logger.remove()
    _logger.add(
        sys.stderr,
        level=print_level,
        filter=lambda record: record["extra"].get("channel") != "llm_response",
    )
    _logger.add(
        ROOT_PATH / f"logs/{log_name}.txt",
        level=logfile_level,
        filter=lambda record: record["extra"].get("channel") != "llm_response",
    )
    if LLM_RESPONSE_LOG:
        _logger.add(
            ROOT_PATH / f"logs/llm_response_{formatted_date}.txt",
            level="DEBUG",
            filter=lambda record: record["extra"].get("channel") == "llm_response",
        )
    return _logger


define_log_level()
logger = _logger.bind(channel="app")
llm_response_logger = _logger.bind(channel="llm_response")
