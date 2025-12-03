# 安全分析脚本

本目录包含用于检测各类漏洞的独立分析脚本。

## 脚本列表

| 脚本 | 描述 | 检测类型 |
|------|------|---------|
| `analyze_command_injection.py` | 命令注入检测 | CWE-78 |
| `analyze_buffer_overflow.py` | 缓冲区溢出检测 | CWE-120 |
| `analyze_all_vulnerabilities.py` | 综合安全扫描 | 多种漏洞类型 |

## 使用方法

### 前提条件

1. 确保已安装 Joern
2. 确保 Joern MCP 项目已安装：
   ```bash
   cd /path/to/joern_mcp
   pip install -e .
   ```

### 命令注入检测

```bash
python analyze_command_injection.py <源代码路径> [项目名称]

# 示例
python analyze_command_injection.py ../vulnerable_c cmd_test
```

### 缓冲区溢出检测

```bash
python analyze_buffer_overflow.py <源代码路径> [项目名称]

# 示例
python analyze_buffer_overflow.py ../vulnerable_c buffer_test
```

### 综合安全扫描

```bash
python analyze_all_vulnerabilities.py <源代码路径> [项目名称]

# 示例
python analyze_all_vulnerabilities.py ../vulnerable_c full_scan
```

综合扫描会生成一个 JSON 格式的详细报告文件。

## 输出说明

### 严重程度图标

- 🔴 CRITICAL - 严重漏洞，需立即修复
- 🟠 HIGH - 高危漏洞，应尽快修复
- 🟡 MEDIUM - 中等风险，建议修复
- 🟢 LOW - 低风险，可选修复

### 报告格式

综合扫描会在源代码目录生成 `security_report_<项目名>.json` 报告文件，包含：

```json
{
  "scan_time": "2025-12-03T10:00:00",
  "source_path": "/path/to/code",
  "project_name": "my_project",
  "duration_seconds": 45.2,
  "statistics": {
    "total_vulnerabilities": 5,
    "by_severity": {"CRITICAL": 1, "HIGH": 2, "MEDIUM": 2, "LOW": 0},
    "by_type": {"Command Injection": 1, "Buffer Overflow": 2}
  },
  "findings": [...]
}
```

## 自定义扫描

你可以基于这些脚本创建自己的扫描规则。参考 `TaintAnalysisService` 的 `check_specific_flow` 方法：

```python
from joern_mcp.services.taint import TaintAnalysisService

# 自定义源和汇模式
result = await taint_service.check_specific_flow(
    source_pattern="read.*|recv|fgets",
    sink_pattern="system|exec.*|popen",
    max_flows=20
)
```

## 注意事项

1. 首次扫描较大项目时，代码导入可能需要较长时间
2. 脚本会自动选择可用端口启动 Joern 服务器
3. 扫描完成后会自动停止服务器
4. 建议在性能较好的机器上运行大型项目扫描

