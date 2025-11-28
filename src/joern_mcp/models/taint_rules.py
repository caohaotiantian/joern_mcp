"""污点分析规则定义"""
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class TaintRule:
    """污点规则"""
    name: str
    description: str
    severity: str  # HIGH, MEDIUM, LOW
    sources: List[str]  # 污点源（正则表达式列表）
    sinks: List[str]    # 污点汇（正则表达式列表）
    cwe_id: str = ""    # CWE编号


# 预定义的污点源
TAINT_SOURCES = {
    # 用户输入
    "user_input": [
        "gets", "scanf", "fscanf", "fgets",
        "getchar", "getc", "read", "recv",
        "recvfrom", "recvmsg",
        # Web输入
        "getParameter", "getHeader", "getCookie",
        "getQueryString", "getInputStream",
        # 命令行
        "argv", "getenv", "getopt",
    ],
    
    # 网络输入
    "network_input": [
        "recv", "recvfrom", "recvmsg",
        "accept", "read", "readv",
        "HttpServletRequest.*",
    ],
    
    # 文件输入
    "file_input": [
        "fread", "fgets", "fgetc", "fscanf",
        "read", "readFile", "readLine",
    ],
    
    # 数据库输入
    "database_input": [
        "executeQuery", "executeUpdate",
        "ResultSet.*", "getString", "getInt",
    ],
}

# 预定义的污点汇
TAINT_SINKS = {
    # 命令执行
    "command_execution": [
        "system", "exec", "execl", "execle",
        "execlp", "execv", "execve", "execvp",
        "popen", "ShellExecute", "CreateProcess",
        "Runtime.exec", "ProcessBuilder.start",
    ],
    
    # SQL查询
    "sql_query": [
        "execute", "executeQuery", "executeUpdate",
        "createStatement", "prepareStatement",
        "query", "rawQuery", "execSQL",
    ],
    
    # 文件操作
    "file_operation": [
        "fopen", "open", "openFile",
        "FileInputStream", "FileOutputStream",
        "createFile", "deleteFile",
    ],
    
    # 内存操作（危险函数）
    "memory_operation": [
        "strcpy", "strcat", "sprintf",
        "gets", "memcpy", "memmove",
    ],
    
    # 网络输出
    "network_output": [
        "send", "sendto", "sendmsg",
        "write", "writev",
    ],
    
    # 日志输出（信息泄露）
    "logging": [
        "printf", "fprintf", "syslog",
        "log", "logger", "println",
    ],
}

# 预定义的漏洞检测规则
VULNERABILITY_RULES = [
    TaintRule(
        name="Command Injection",
        description="用户输入未经验证直接传递到命令执行函数",
        severity="CRITICAL",
        sources=TAINT_SOURCES["user_input"],
        sinks=TAINT_SINKS["command_execution"],
        cwe_id="CWE-78"
    ),
    
    TaintRule(
        name="SQL Injection",
        description="用户输入未经验证直接用于SQL查询",
        severity="CRITICAL",
        sources=TAINT_SOURCES["user_input"],
        sinks=TAINT_SINKS["sql_query"],
        cwe_id="CWE-89"
    ),
    
    TaintRule(
        name="Path Traversal",
        description="用户输入未经验证用于文件路径",
        severity="HIGH",
        sources=TAINT_SOURCES["user_input"],
        sinks=TAINT_SINKS["file_operation"],
        cwe_id="CWE-22"
    ),
    
    TaintRule(
        name="Buffer Overflow",
        description="用户输入可能导致缓冲区溢出",
        severity="HIGH",
        sources=TAINT_SOURCES["user_input"],
        sinks=TAINT_SINKS["memory_operation"],
        cwe_id="CWE-120"
    ),
    
    TaintRule(
        name="Information Disclosure",
        description="敏感数据可能被记录或输出",
        severity="MEDIUM",
        sources=TAINT_SOURCES["database_input"] + ["password", "token", "secret"],
        sinks=TAINT_SINKS["logging"],
        cwe_id="CWE-200"
    ),
    
    TaintRule(
        name="Network Data Injection",
        description="网络输入未经验证直接用于命令执行",
        severity="CRITICAL",
        sources=TAINT_SOURCES["network_input"],
        sinks=TAINT_SINKS["command_execution"],
        cwe_id="CWE-94"
    ),
]


def get_rule_by_name(name: str) -> TaintRule:
    """根据名称获取规则"""
    for rule in VULNERABILITY_RULES:
        if rule.name == name:
            return rule
    raise ValueError(f"Rule not found: {name}")


def get_rules_by_severity(severity: str) -> List[TaintRule]:
    """根据严重程度获取规则"""
    return [rule for rule in VULNERABILITY_RULES if rule.severity == severity]


def list_all_rules() -> List[Dict]:
    """列出所有规则"""
    return [
        {
            "name": rule.name,
            "description": rule.description,
            "severity": rule.severity,
            "cwe_id": rule.cwe_id,
            "source_count": len(rule.sources),
            "sink_count": len(rule.sinks)
        }
        for rule in VULNERABILITY_RULES
    ]

