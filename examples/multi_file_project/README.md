# 多文件测试项目

这是一个专门设计用于测试 Joern MCP 工具的多文件 C 项目，包含复杂的跨文件函数调用关系。

## 项目结构

```
multi_file_project/
├── main.c          # 主入口，调用各模块
├── auth.c/h        # 认证模块
├── database.c/h    # 数据库模块
├── network.c/h     # 网络模块
├── utils.c/h       # 工具函数（底层）
└── Makefile        # 编译脚本
```

## 调用关系图

```
                        ┌─────────────────────────────────────┐
                        │              main()                  │
                        └─────────────────┬───────────────────┘
               ┌──────────────────────────┼──────────────────────────┐
               ▼                          ▼                          ▼
      ┌────────────────┐         ┌────────────────┐         ┌────────────────┐
      │  init_app()    │         │ authenticate() │         │handle_request()│
      └───────┬────────┘         └───────┬────────┘         └───────┬────────┘
              │                          │                          │
    ┌─────────┼─────────┐               │                 ┌────────┴────────┐
    ▼         ▼         ▼               ▼                 ▼                 ▼
init_db  init_network  log       check_password     query_user    check_permission
    │         │         ▲              │                  │                 │
    ▼         ▼         │              ▼                  ▼                 ▼
log_msg   log_msg       │    ┌────────┴────────┐    exec_query        log_msg
                        │    ▼                 ▼         │
                        │  hash_str      query_user      ▼
                        │    │                │       log_msg
                        │    ▼                ▼
                        └──log_msg       exec_query
                                              │
                                              ▼
                                          log_msg
```

## 核心调用链

### 1. 认证调用链 (向下 3 层)

```
main() 
  └─> authenticate()           [auth.c]
        └─> check_password()   [auth.c]
              ├─> query_user() [database.c]
              │     └─> exec_query() [database.c]
              │           └─> log_message() [utils.c]
              └─> hash_str()   [utils.c]
```

### 2. 网络调用链 (向下 4 层)

```
main()
  └─> init_network()           [network.c]
        └─> log_message()      [utils.c]

handle_connection()            [network.c]
  └─> process_request()        [network.c]
        ├─> authenticate()     [auth.c]
        │     └─> ... (见上)
        └─> query_user()       [database.c]
              └─> exec_query() [database.c]
                    └─> log_message() [utils.c]
```

### 3. 数据库调用链 (向上追溯)

```
log_message() <── exec_query() <── query_user() <── check_password() <── authenticate() <── main()
     [utils.c]     [database.c]    [database.c]      [auth.c]            [auth.c]         [main.c]
```

## 测试用例

### 测试 get_callers (查找调用者)

| 函数 | 预期调用者 |
|------|-----------|
| `log_message` | `init_app`, `authenticate`, `check_password`, `query_user`, `exec_query`, `init_db`, `init_network`, `send_request`, ... |
| `query_user` | `check_password`, `handle_request`, `process_request` |
| `exec_query` | `query_user`, `query_user_by_id`, `execute_action` |
| `hash_str` | `check_password`, `create_session`, `create_user` |

### 测试 get_callees (查找被调用者)

| 函数 | 预期被调用者 |
|------|-------------|
| `main` | `init_app`, `authenticate`, `handle_request`, `close_network`, `close_db` |
| `authenticate` | `log_message`, `get_failed_attempts`, `check_password`, `reset_failed_attempts`, `increment_failed_attempts` |
| `check_password` | `log_message`, `query_user`, `hash_str`, `verify_password_hash`, `safe_free`, `free_user_info` |
| `init_app` | `log_message`, `init_db`, `init_network` |

### 测试 get_call_chain (调用链)

#### 向上追溯 (direction="up")

从 `log_message` 开始，向上追溯：
- depth=1: `exec_query`, `init_db`, `authenticate`, ...
- depth=2: `query_user`, `init_app`, `check_password`, ...
- depth=3: `check_password`, `main`, `authenticate`, ...

#### 向下追溯 (direction="down")

从 `main` 开始，向下追溯：
- depth=1: `init_app`, `authenticate`, `handle_request`, ...
- depth=2: `init_db`, `check_password`, `query_user`, ...
- depth=3: `log_message`, `hash_str`, `exec_query`, ...

## 编译和运行

```bash
# 编译
make

# 运行
./app admin password read

# 清理
make clean
```

## 使用 MCP 工具测试

```python
# 1. 导入项目
await parse_project("/path/to/multi_file_project", "callgraph_test")

# 2. 测试 get_callers - 查找谁调用了 log_message
await get_callers("callgraph_test", "log_message", depth=1)

# 3. 测试 get_callees - 查找 main 调用了哪些函数  
await get_callees("callgraph_test", "main", depth=1)

# 4. 测试 get_call_chain - 追溯调用链
await get_call_chain("callgraph_test", "log_message", max_depth=3, direction="up")
await get_call_chain("callgraph_test", "main", max_depth=3, direction="down")

# 5. 测试 get_call_graph - 获取完整调用图
await get_call_graph("callgraph_test", "authenticate", depth=2)
```

