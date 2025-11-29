# Joern MCP 性能优化指南

## 📊 概述

Joern MCP Server 集成了多项性能优化功能，包括：

- **混合缓存系统** (LRU + TTL)
- **自适应并发控制**
- **查询复杂度分析**
- **慢查询监控**
- **实时性能指标**

## 🚀 性能特性

### 1. 混合缓存系统

#### 特性
- **热缓存**：LRU策略，存储频繁访问的查询
- **冷缓存**：TTL策略，自动过期
- **智能提升**：访问频繁的冷数据自动升级到热缓存
- **自动压缩**：大结果自动压缩节省内存

#### 配置
```python
# .env 或环境变量
QUERY_CACHE_SIZE=1000        # 冷缓存大小
HOT_CACHE_SIZE=100           # 热缓存大小
QUERY_CACHE_TTL=3600         # TTL (秒)
CACHE_COMPRESSION_THRESHOLD=10240  # 压缩阈值 (字节)
```

#### 使用
```python
# 启用缓存（默认）
result = await executor.execute(query, use_cache=True)

# 禁用缓存
result = await executor.execute(query, use_cache=False)

# 清空缓存
executor.clear_cache()

# 获取缓存统计
stats = executor.get_cache_stats()
print(f"Cache hit rate: {stats['hit_rate']}%")
```

### 2. 自适应并发控制

#### 特性
- **动态调整**：根据响应时间自动调整并发数
- **负载均衡**：避免系统过载
- **性能优化**：在响应时间和吞吐量之间平衡

#### 配置
```python
# .env 或环境变量
ENABLE_ADAPTIVE_CONCURRENCY=true
MIN_CONCURRENT_QUERIES=3
MAX_CONCURRENT_LIMIT=20
TARGET_RESPONSE_TIME=1.0     # 目标响应时间 (秒)
```

#### 工作原理
- 响应时间 > 1.5x目标 → 减少并发数
- 响应时间 < 0.5x目标 → 增加并发数
- 每10个查询评估一次

#### 监控
```python
# 获取当前并发限制
limit = executor.get_current_concurrent_limit()
print(f"Current concurrent limit: {limit}")
```

### 3. 查询复杂度分析

#### 特性
- **自动评估**：分析查询复杂度（1-10级）
- **智能路由**：简单查询→热缓存，复杂查询→冷缓存
- **超时调整**：复杂查询自动延长超时

#### 评估因素
- 查询长度
- 嵌套深度
- 特殊操作 (repeat, flows, reachableBy等)

#### 示例
```python
from joern_mcp.utils.performance import QueryComplexityAnalyzer

analyzer = QueryComplexityAnalyzer()
info = analyzer.analyze("cpg.method.name(\"main\").repeat(_.caller)(10).dedup")

print(f"Complexity: {info['complexity']}/10")
print(f"Estimated time: {info['estimated_time']}s")
print(f"Priority: {info['priority']}/5")
```

### 4. 慢查询监控

#### 特性
- **自动检测**：超过阈值的查询自动记录
- **详细信息**：包含查询、时间、复杂度等
- **趋势分析**：识别性能问题

#### 配置
```python
# .env 或环境变量
ENABLE_SLOW_QUERY_LOG=true
SLOW_QUERY_THRESHOLD=5.0     # 慢查询阈值 (秒)
```

#### 使用
```python
# 获取慢查询列表
slow_queries = executor.get_slow_queries(limit=10)

for query in slow_queries:
    print(f"Query: {query['query']}")
    print(f"Duration: {query['duration']}s")
    print(f"Complexity: {query['complexity']}/10")
```

### 5. 性能指标收集

#### 指标
- **查询统计**：总数、成功、失败
- **响应时间**：平均、最小、最大、P50/P95/P99
- **缓存性能**：命中率、命中次数
- **并发情况**：当前、峰值

#### 使用
```python
# 获取性能统计
stats = executor.get_performance_stats()

print(f"Total queries: {stats['total_queries']}")
print(f"Average time: {stats['avg_time']}s")
print(f"P95: {stats['p95']}s")
print(f"Cache hit rate: {stats['cache_hit_rate']}%")
print(f"Success rate: {stats['success_rate']}%")
```

## 🔧 MCP 工具

### 性能监控工具

```json
// 获取性能统计
{
  "tool": "get_performance_stats"
}

// 获取缓存统计
{
  "tool": "get_cache_stats"
}

// 清空缓存
{
  "tool": "clear_query_cache"
}

// 获取慢查询
{
  "tool": "get_slow_queries",
  "parameters": {
    "limit": 10
  }
}

// 获取系统健康状态
{
  "tool": "get_system_health"
}

// 获取优化建议
{
  "tool": "optimize_performance"
}
```

## 📈 性能基准测试

### 运行基准测试

```bash
python scripts/benchmark_performance.py
```

### 测试项目
1. **单查询性能**：测试各类查询响应时间
2. **缓存性能**：测试缓存加速效果
3. **并发性能**：测试不同并发级别的QPS
4. **自适应并发**：测试并发限制自动调整
5. **慢查询检测**：验证慢查询日志

### 结果输出
- 实时日志输出
- JSON格式结果保存到 `benchmark_results/`
- 包含详细的性能指标

## 📊 性能优化建议

### 高缓存命中率 (70%+)
- 增加缓存大小
- 延长 TTL
- 使用预编译查询模板

### 低响应时间 (<1s 平均)
- 启用自适应并发
- 增加并发限制
- 优化查询复杂度

### 高并发处理
- 增加 `max_concurrent_limit`
- 优化 Joern 服务器配置
- 使用连接池

### 内存优化
- 降低缓存大小
- 启用缓存压缩
- 定期清理缓存

## 🎯 性能目标

### 优秀水平
- 平均响应时间 < 1s
- P95 响应时间 < 3s
- 缓存命中率 > 70%
- 成功率 > 95%
- 并发能力 > 20 QPS

### 良好水平
- 平均响应时间 < 2s
- P95 响应时间 < 5s
- 缓存命中率 > 50%
- 成功率 > 90%
- 并发能力 > 10 QPS

## 🔍 故障排查

### 问题：缓存命中率低

**症状**：`cache_hit_rate < 30%`

**原因**：
- 查询多样性太高
- 缓存大小不足
- TTL 太短

**解决**：
```bash
# 增加缓存大小
QUERY_CACHE_SIZE=2000
HOT_CACHE_SIZE=200

# 延长 TTL
QUERY_CACHE_TTL=7200
```

### 问题：响应时间长

**症状**：`avg_time > 3s`

**原因**：
- 查询复杂度高
- 并发限制低
- Joern 性能问题

**解决**：
```bash
# 增加并发限制
MAX_CONCURRENT_LIMIT=30

# 启用自适应
ENABLE_ADAPTIVE_CONCURRENCY=true

# 查看慢查询
get_slow_queries(limit=10)

# 优化复杂查询
```

### 问题：成功率低

**症状**：`success_rate < 90%`

**原因**：
- 超时设置太短
- 查询语法错误
- Joern 服务器不稳定

**解决**：
```bash
# 增加超时
QUERY_TIMEOUT=600

# 检查 Joern 状态
get_system_health()

# 查看失败查询日志
```

## 🎓 最佳实践

### 1. 使用查询模板
```python
from joern_mcp.joern.templates import QueryTemplates

# 使用预编译模板（更快）
query = QueryTemplates.build("GET_CALLERS", name="main")
```

### 2. 批量查询优化
```python
# 合并多个查询
queries = [
    "cpg.method.name.l",
    "cpg.call.methodFullName.l"
]

# 使用批量查询工具
results = await batch_query(queries)
```

### 3. 合理设置缓存
```python
# 频繁查询：启用缓存
await executor.execute(query, use_cache=True)

# 一次性查询：禁用缓存
await executor.execute(query, use_cache=False)

# 定期清理缓存（如需要）
executor.clear_cache()
```

### 4. 监控性能
```python
# 定期检查性能
stats = executor.get_performance_stats()
if stats['avg_time'] > 3.0:
    logger.warning("Performance degradation detected!")
    
# 检查系统健康
health = get_system_health()
if health['performance_grade'] in ['D', 'F']:
    logger.error("Poor performance!")
```

### 5. 优化查询
```python
# 分析查询复杂度
info = analyzer.analyze(query)
if info['complexity'] > 7:
    logger.warning("Complex query detected, consider optimization")

# 查看慢查询
slow_queries = executor.get_slow_queries()
for sq in slow_queries:
    # 分析并优化
    pass
```

## 📚 相关文档

- [配置指南](./CONFIG.md)
- [API参考](./API_REFERENCE.md)
- [故障排查](./TROUBLESHOOTING.md)
- [开发计划](../PERFORMANCE_OPTIMIZATION_PLAN.md)

---

**版本**: 1.0  
**更新时间**: 2024年  
**维护**: Joern MCP Team

