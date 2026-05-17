# -*- coding: utf-8 -*-
"""
Mr.Pilot · NVIDIA NIM 统一接入层(v0.12.0)

用途:
  - 作为"AI 大脑"供其他模块调用(归类/重复检测/智能问答/凭证草稿)
  - 不做主 OCR(主 OCR 走 Gemini)· 但保留 VL 模型接口作为二次校验备用

关键设计:
  - 所有调用走 OpenAI 兼容 API · 切换模型只改 model 字符串
  - 全局 token bucket 控制并发(NVIDIA 免费层 ~40 RPM per model)
  - 失败静默 · 不影响主业务(OCR 已识别 · NVIDIA 增强可选)
  - 每次调用记录指标 · 方便调整策略

环境变量:
  - NVIDIA_API_KEY · 必需(nvapi-* 格式)· 去 build.nvidia.com 注册获得

模型用途映射:
  - MODEL_CLASSIFY  · 轻量 Llama · 给发票分类
  - MODEL_REASONING · 中型 Nemotron · 做凭证草稿 / 异常分析
  - MODEL_CHAT      · 大型 Llama 70B · 智能问答 / 月度总结
  - MODEL_EMBED     · Embedding 模型 · 向量化用于重复检测
  - MODEL_VL        · Nemotron Nano VL · 图像校验(备用)
"""
import os
import time
import json
import asyncio
import logging
import threading
from typing import Optional, List, Dict, Any
from collections import deque

logger = logging.getLogger(__name__)

# ============================================================
# 配置
# ============================================================
NVIDIA_BASE_URL = os.environ.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "")

# 模型选择 · 可以通过环境变量覆盖
MODEL_CLASSIFY = os.environ.get("NVIDIA_MODEL_CLASSIFY", "meta/llama-3.1-8b-instruct")
MODEL_REASONING = os.environ.get("NVIDIA_MODEL_REASONING", "nvidia/llama-3.1-nemotron-70b-instruct")
MODEL_CHAT = os.environ.get("NVIDIA_MODEL_CHAT", "meta/llama-3.1-70b-instruct")
MODEL_EMBED = os.environ.get("NVIDIA_MODEL_EMBED", "nvidia/nv-embedqa-e5-v5")
MODEL_VL = os.environ.get("NVIDIA_MODEL_VL", "nvidia/llama-3.1-nemotron-nano-vl-8b-v1")

# 速率限制策略
RATE_LIMIT_RPM = int(os.environ.get("NVIDIA_RATE_LIMIT_RPM", "30"))  # 留 10 RPM buffer
DEFAULT_TIMEOUT = int(os.environ.get("NVIDIA_TIMEOUT", "30"))  # 秒

# ============================================================
# 全局速率限制(简单 token bucket · 按分钟滑窗)
# ============================================================
_request_times: deque = deque()  # 保存最近 1 分钟的请求时间戳
_rate_lock = threading.Lock()


def _rate_limit_check() -> bool:
    """检查是否允许发起新请求 · 返回 True 表示可以 · False 表示超限"""
    now = time.time()
    with _rate_lock:
        # 清理 1 分钟前的记录
        while _request_times and now - _request_times[0] > 60:
            _request_times.popleft()
        # 判断容量
        if len(_request_times) >= RATE_LIMIT_RPM:
            return False
        _request_times.append(now)
        return True


def _get_rate_stats() -> Dict[str, Any]:
    """调试用 · 返回当前速率状态"""
    now = time.time()
    with _rate_lock:
        while _request_times and now - _request_times[0] > 60:
            _request_times.popleft()
        return {
            "current_rpm": len(_request_times),
            "limit_rpm": RATE_LIMIT_RPM,
            "remaining_rpm": max(0, RATE_LIMIT_RPM - len(_request_times)),
        }


# ============================================================
# OpenAI 客户端(懒加载)
# ============================================================
_client = None
_client_lock = threading.Lock()


def _get_client():
    """懒加载 OpenAI 客户端"""
    global _client
    if _client is not None:
        return _client
    with _client_lock:
        if _client is not None:
            return _client
        try:
            from openai import OpenAI
        except ImportError:
            logger.error("openai 库未安装 · pip install openai")
            return None
        if not NVIDIA_API_KEY:
            logger.warning("NVIDIA_API_KEY 未配置 · NVIDIA 所有功能将禁用")
            return None
        _client = OpenAI(base_url=NVIDIA_BASE_URL, api_key=NVIDIA_API_KEY, timeout=DEFAULT_TIMEOUT)
        logger.info(f"✅ NVIDIA 客户端初始化完成 · base_url={NVIDIA_BASE_URL}")
        return _client


def is_available() -> bool:
    """供外部判断 NVIDIA 是否可用"""
    return bool(NVIDIA_API_KEY) and _get_client() is not None


# ============================================================
# 核心:统一聊天接口
# ============================================================
def chat(
    messages: List[Dict[str, str]],
    model: str = MODEL_CHAT,
    temperature: float = 0.2,
    max_tokens: int = 512,
    json_mode: bool = False,
    timeout: Optional[int] = None,
) -> Optional[str]:
    """
    统一聊天调用 · 失败返回 None(静默 · 让调用方走 fallback)

    参数:
      messages    · OpenAI 格式的消息列表
      model       · 模型名 · 默认用 MODEL_CHAT
      temperature · 温度 · 0.0-1.0 · 默认 0.2(偏确定性 · 适合结构化任务)
      max_tokens  · 最多生成 token 数
      json_mode   · 如果 True · prompt 里会强调 JSON 输出格式
      timeout     · 单次请求超时秒数

    返回:
      str · 模型回复的内容 · 失败时 None
    """
    client = _get_client()
    if client is None:
        return None

    if not _rate_limit_check():
        logger.warning(f"[NVIDIA] 速率限制 · 跳过 ({_get_rate_stats()})")
        return None

    try:
        t0 = time.time()
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if timeout is not None:
            kwargs["timeout"] = timeout
        if json_mode:
            # 部分模型支持 response_format
            try:
                kwargs["response_format"] = {"type": "json_object"}
            except Exception:
                pass
        resp = client.chat.completions.create(**kwargs)
        elapsed = int((time.time() - t0) * 1000)
        content = resp.choices[0].message.content if resp.choices else ""
        logger.info(f"[NVIDIA] {model} · {elapsed}ms · {len(content)} chars")
        return content or ""
    except Exception as e:
        logger.warning(f"[NVIDIA] {model} 调用失败: {type(e).__name__}: {str(e)[:200]}")
        return None


# ============================================================
# Embedding 接口
# ============================================================
def embed(text: str, model: str = MODEL_EMBED) -> Optional[List[float]]:
    """
    生成文本向量 · 用于相似度搜索(重复发票检测)
    失败返回 None
    """
    client = _get_client()
    if client is None:
        return None
    if not _rate_limit_check():
        return None
    try:
        resp = client.embeddings.create(model=model, input=[text])
        if resp.data:
            return resp.data[0].embedding
    except Exception as e:
        logger.warning(f"[NVIDIA.embed] 失败: {type(e).__name__}: {str(e)[:200]}")
    return None


def embed_batch(texts: List[str], model: str = MODEL_EMBED) -> List[Optional[List[float]]]:
    """批量向量化 · 失败条目返回 None · 其他正常"""
    client = _get_client()
    if client is None:
        return [None] * len(texts)
    # 批量算 1 次 RPM
    if not _rate_limit_check():
        return [None] * len(texts)
    try:
        resp = client.embeddings.create(model=model, input=texts)
        out = [None] * len(texts)
        for d in resp.data:
            out[d.index] = d.embedding
        return out
    except Exception as e:
        logger.warning(f"[NVIDIA.embed_batch] 失败: {type(e).__name__}")
        return [None] * len(texts)


# ============================================================
# 便捷工具:安全解析 JSON 回复
# ============================================================
def parse_json_response(text: str) -> Optional[dict]:
    """从模型回复中提取 JSON · 兼容 ```json 围栏 / 纯 JSON / 回复前后带文字 等情况"""
    if not text:
        return None
    t = text.strip()
    # 去除 markdown 围栏
    if t.startswith("```"):
        # 找到第一个换行后到最后 ``` 之间
        lines = t.split("\n")
        if len(lines) >= 2:
            t = "\n".join(lines[1:])
            if t.rstrip().endswith("```"):
                t = t.rstrip()[:-3]
    t = t.strip()
    # 尝试直接 parse
    try:
        return json.loads(t)
    except Exception:
        pass
    # 尝试抽取 {...} 最外层
    start = t.find("{")
    end = t.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(t[start:end + 1])
        except Exception:
            return None
    return None


# ============================================================
# 健康检查(供前端 / 日志用)
# ============================================================
def health_check() -> Dict[str, Any]:
    """返回 NVIDIA 集成层当前状态"""
    return {
        "available": is_available(),
        "has_api_key": bool(NVIDIA_API_KEY),
        "base_url": NVIDIA_BASE_URL,
        "rate_stats": _get_rate_stats(),
        "models": {
            "classify": MODEL_CLASSIFY,
            "reasoning": MODEL_REASONING,
            "chat": MODEL_CHAT,
            "embed": MODEL_EMBED,
            "vl": MODEL_VL,
        },
    }
