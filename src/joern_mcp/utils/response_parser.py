"""
Joern Server 响应解析工具

统一处理 Joern Server 返回的 Scala REPL 风格输出：
- 提取 JSON 数据
- 处理双重 JSON 编码
- 清理 ANSI 颜色码（现已在 HTTP 客户端层完成）
"""

import json
import re
from typing import Any

from loguru import logger


def parse_joern_response(stdout: str) -> Any:
    """
    解析 Joern Server 响应中的数据

    Joern Server 返回的 stdout 格式示例：
    1. 直接 JSON: `[{"name": "main", ...}]`
    2. Scala REPL: `val res1: String = "[{\"name\": \"main\", ...}]"`
    3. 双重编码: JSON 字符串作为 JSON 字符串返回

    Args:
        stdout: Joern Server 返回的 stdout 内容（已去除 ANSI 码）

    Returns:
        解析后的数据（通常是 list 或 dict）

    Raises:
        ValueError: 无法解析响应
    """
    if not stdout:
        return []

    clean_output = stdout.strip()

    # 尝试方法 1: 直接解析 JSON
    try:
        data = json.loads(clean_output)
        # 处理双重编码（JSON 字符串内嵌 JSON）
        if isinstance(data, str):
            data = json.loads(data)
        return data
    except json.JSONDecodeError:
        pass

    # 尝试方法 2: 从 Scala REPL 输出提取 JSON
    # 格式: `val res1: Type = "..."` 或 `val res1: Type = [...]`
    match = re.search(r'=\s*(.+)$', clean_output, re.MULTILINE)
    if match:
        try:
            json_str = match.group(1).strip()
            data = json.loads(json_str)
            # 处理双重编码
            if isinstance(data, str):
                data = json.loads(data)
            return data
        except json.JSONDecodeError:
            pass

    # 尝试方法 3: 查找第一个 JSON 数组或对象
    json_match = re.search(r'(\[.*\]|\{.*\})', clean_output, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            if isinstance(data, str):
                data = json.loads(data)
            return data
        except json.JSONDecodeError:
            pass

    logger.warning(f"Cannot parse Joern response: {clean_output[:200]}...")
    raise ValueError(f"Cannot parse Joern response: {clean_output[:100]}...")


def safe_parse_joern_response(stdout: str, default: Any = None) -> Any:
    """
    安全解析 Joern Server 响应（不抛出异常）

    Args:
        stdout: Joern Server 返回的 stdout 内容
        default: 解析失败时返回的默认值

    Returns:
        解析后的数据或默认值
    """
    try:
        return parse_joern_response(stdout)
    except (ValueError, json.JSONDecodeError) as e:
        logger.debug(f"Failed to parse response: {e}")
        return default if default is not None else []


def extract_json_from_repl(stdout: str) -> str | None:
    """
    从 Scala REPL 输出中提取原始 JSON 字符串

    Args:
        stdout: Joern Server 返回的 stdout 内容

    Returns:
        提取的 JSON 字符串，或 None
    """
    if not stdout:
        return None

    clean_output = stdout.strip()

    # 如果本身就是 JSON，直接返回
    if clean_output.startswith('[') or clean_output.startswith('{'):
        return clean_output

    # 从 Scala REPL 格式提取
    match = re.search(r'=\s*(.+)$', clean_output, re.MULTILINE)
    if match:
        return match.group(1).strip()

    return None

