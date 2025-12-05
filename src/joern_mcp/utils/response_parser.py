"""
Joern Server 响应解析工具

统一处理 Joern Server 返回的 Scala REPL 风格输出：
- 提取 JSON 数据
- 处理双重 JSON 编码
- 清理 ANSI 颜色码（现已在 HTTP 客户端层完成）
- 解析 Scala 原生格式（如 List, String 等）
"""

import contextlib
import json
import re
from typing import Any

from loguru import logger


def _parse_scala_string(value: str) -> str:
    """解析 Scala 字符串值

    处理带引号的字符串，去除首尾引号。

    Args:
        value: Scala 字符串值（可能带引号）

    Returns:
        解析后的字符串
    """
    value = value.strip()
    # 移除首尾引号
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def _parse_scala_list(value: str) -> list:
    """解析 Scala List 格式

    处理 Scala 的 List("item1", "item2") 格式。

    Args:
        value: Scala List 字符串

    Returns:
        解析后的 Python 列表
    """
    # 匹配 List(...) 格式
    list_match = re.match(r'List\s*\((.*)\)', value, re.DOTALL)
    if not list_match:
        return []

    content = list_match.group(1).strip()
    if not content:
        return []

    # 解析列表元素（支持带引号的字符串）
    items = []
    # 使用正则匹配每个带引号的字符串
    string_pattern = r'"([^"\\]*(?:\\.[^"\\]*)*)"'
    for match in re.finditer(string_pattern, content):
        # 处理转义字符
        item = match.group(1).replace('\\"', '"').replace('\\n', '\n')
        items.append(item)

    return items


def _recursively_parse_json(data: Any, max_depth: int = 5) -> Any:
    """递归解析可能多重编码的 JSON 数据

    Args:
        data: 要解析的数据
        max_depth: 最大递归深度

    Returns:
        完全解析后的数据
    """
    if max_depth <= 0:
        return data

    # 如果是字符串，尝试解析为 JSON
    if isinstance(data, str):
        data_stripped = data.strip()
        # 移除多余的首尾双引号（如 '""[...]""'）
        while (data_stripped.startswith('""') and data_stripped.endswith('""')
               and len(data_stripped) > 4):
            data_stripped = data_stripped[2:-2]
        # 单层引号包裹
        while (data_stripped.startswith('"') and data_stripped.endswith('"')
               and len(data_stripped) > 2):
            inner = data_stripped[1:-1]
            # 检查内部是否像 JSON
            if inner.startswith('[') or inner.startswith('{'):
                data_stripped = inner
                break
            else:
                break

        with contextlib.suppress(json.JSONDecodeError):
            parsed = json.loads(data_stripped)
            return _recursively_parse_json(parsed, max_depth - 1)
        return data_stripped

    # 如果是列表，递归解析每个元素
    if isinstance(data, list):
        return [_recursively_parse_json(item, max_depth - 1) for item in data]

    # 如果是字典，递归解析每个值
    if isinstance(data, dict):
        return {k: _recursively_parse_json(v, max_depth - 1) for k, v in data.items()}

    return data


def parse_joern_response(stdout: str) -> Any:
    """
    解析 Joern Server 响应中的数据

    Joern Server 返回的 stdout 格式示例：
    1. 直接 JSON: `[{"name": "main", ...}]`
    2. Scala REPL JSON: `val res1: String = "[{\"name\": \"main\", ...}]"`
    3. Scala REPL String: `val res1: String = "/path/to/project"`
    4. Scala REPL List: `val res1: List[String] = List("item1", "item2")`
    5. 双重/多重编码: JSON 字符串作为 JSON 字符串返回

    Args:
        stdout: Joern Server 返回的 stdout 内容（已去除 ANSI 码）

    Returns:
        解析后的数据（通常是 list, dict 或 str）

    Raises:
        ValueError: 无法解析响应
    """
    if not stdout:
        return []

    clean_output = stdout.strip()

    # 预处理：移除多余的首尾双引号
    while (clean_output.startswith('""') and clean_output.endswith('""')
           and len(clean_output) > 4):
        clean_output = clean_output[2:-2]

    # 尝试方法 1: 直接解析 JSON
    try:
        data = json.loads(clean_output)
        # 递归处理多重编码
        return _recursively_parse_json(data)
    except json.JSONDecodeError:
        pass

    # 尝试方法 2: 从 Scala REPL 输出提取值
    # 格式: `val res1: Type = ...`
    repl_match = re.search(r'val\s+\w+:\s*[\w\[\]]+\s*=\s*(.+)', clean_output, re.DOTALL)
    if repl_match:
        value_part = repl_match.group(1).strip()

        # 2a: 尝试解析为 JSON
        try:
            data = json.loads(value_part)
            return _recursively_parse_json(data)
        except json.JSONDecodeError:
            pass

        # 2b: 尝试解析 Scala List 格式
        if value_part.startswith('List('):
            return _parse_scala_list(value_part)

        # 2c: 尝试解析为 Scala 字符串
        if value_part.startswith('"'):
            return _parse_scala_string(value_part)

    # 尝试方法 3: 查找第一个 JSON 数组或对象
    json_match = re.search(r'(\[.*\]|\{.*\})', clean_output, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            return _recursively_parse_json(data)
        except json.JSONDecodeError:
            pass

    # 尝试方法 4: 检查是否是简单的等号赋值格式
    simple_match = re.search(r'=\s*(.+)$', clean_output, re.MULTILINE)
    if simple_match:
        value = simple_match.group(1).strip()
        # 尝试解析为字符串
        if value.startswith('"') and value.endswith('"'):
            return _parse_scala_string(value)

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

