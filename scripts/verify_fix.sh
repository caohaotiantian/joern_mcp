#!/bin/bash

# 验证脚本修复

echo "🔍 验证集成测试脚本修复"
echo "======================================"
echo ""

# 1. 语法检查
echo "1️⃣ 语法检查..."
if bash -n run_integration_tests.sh 2>/dev/null; then
    echo "   ✅ 脚本语法正确"
else
    echo "   ❌ 脚本语法错误"
    exit 1
fi
echo ""

# 2. 模拟参数展开
echo "2️⃣ 测试参数展开..."
TEST_MARKERS='-m "integration and not performance and not stress"'
COMMAND="pytest tests/integration/ ${TEST_MARKERS} --tb=short"
echo "   命令: $COMMAND"

# 检查是否包含 "and" 作为独立参数
if echo "$COMMAND" | grep -q ' and '; then
    echo "   ⚠️  警告：命令中 'and' 可能被错误解析"
else
    echo "   ✅ 参数展开正确"
fi
echo ""

# 3. 快速pytest测试（不实际运行，只收集）
echo "3️⃣ 测试pytest参数解析..."
cd "$(dirname "$0")/.."

if [ -d ".venv" ]; then
    # 使用--collect-only测试参数是否正确
    OUTPUT=$(.venv/bin/python -m pytest tests/integration/ -m "integration and not performance and not stress" --collect-only 2>&1)
    
    if echo "$OUTPUT" | grep -q "error: argument"; then
        echo "   ❌ pytest参数解析失败"
        echo "$OUTPUT" | grep "error:"
        exit 1
    elif echo "$OUTPUT" | grep -q "collected"; then
        COLLECTED=$(echo "$OUTPUT" | grep "collected" | sed 's/.*collected //' | sed 's/ items.*//')
        echo "   ✅ pytest参数正确，收集到 $COLLECTED 个测试"
    else
        echo "   ⚠️  无法确定结果"
    fi
else
    echo "   ⏭️  跳过（虚拟环境不存在）"
fi
echo ""

# 4. 检查所有选项
echo "4️⃣ 检查所有TEST_MARKERS定义..."
echo ""

grep -n "TEST_MARKERS=" run_integration_tests.sh | while read line; do
    LINE_NUM=$(echo "$line" | cut -d: -f1)
    CONTENT=$(echo "$line" | cut -d: -f2-)
    
    # 检查是否包含 'integration and' 
    if echo "$CONTENT" | grep -q "'integration and"; then
        echo "   ❌ 行 $LINE_NUM: 发现错误的单引号用法"
        echo "      $CONTENT"
    elif echo "$CONTENT" | grep -q '"integration and'; then
        echo "   ✅ 行 $LINE_NUM: 正确"
    else
        echo "   ✅ 行 $LINE_NUM: 简单参数（无需检查）"
    fi
done
echo ""

echo "======================================"
echo "✅ 验证完成！"
echo ""
echo "💡 现在可以运行："
echo "   ./run_integration_tests.sh -q"
echo "   或"
echo "   ./run_integration_tests.sh"

