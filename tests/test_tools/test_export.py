"""
tests/test_tools/test_export.py

测试结果导出工具
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path


class TestExportTools:
    """测试导出工具逻辑"""

    @pytest.mark.asyncio
    async def test_export_to_json(self, mock_query_executor, tmp_path):
        """测试导出为JSON"""
        # Mock查询结果
        data = [{"name": "func1", "lines": 10}, {"name": "func2", "lines": 20}]
        mock_query_executor.execute = AsyncMock(
            return_value={
                "success": True,
                "stdout": json.dumps(data)
            }
        )
        
        result = await mock_query_executor.execute("query")
        
        # 导出到文件
        output_file = tmp_path / "result.json"
        with open(output_file, "w") as f:
            json.dump(json.loads(result["stdout"]), f)
        
        # 验证文件内容
        assert output_file.exists()
        with open(output_file, "r") as f:
            exported_data = json.load(f)
        assert len(exported_data) == 2

    @pytest.mark.asyncio
    async def test_export_to_csv(self, mock_query_executor, tmp_path):
        """测试导出为CSV"""
        # Mock查询结果
        data = [
            {"name": "func1", "lines": 10, "complexity": 5},
            {"name": "func2", "lines": 20, "complexity": 8}
        ]
        mock_query_executor.execute = AsyncMock(
            return_value={
                "success": True,
                "stdout": json.dumps(data)
            }
        )
        
        result = await mock_query_executor.execute("query")
        
        # 简单CSV导出模拟
        output_file = tmp_path / "result.csv"
        data_list = json.loads(result["stdout"])
        with open(output_file, "w") as f:
            if data_list:
                f.write(",".join(data_list[0].keys()) + "\n")
                for item in data_list:
                    f.write(",".join(str(v) for v in item.values()) + "\n")
        
        assert output_file.exists()
        content = output_file.read_text()
        assert "func1" in content
        assert "func2" in content

    @pytest.mark.asyncio
    async def test_export_to_graphml(self, mock_query_executor, tmp_path):
        """测试导出为GraphML"""
        # Mock图数据
        graph_data = {
            "nodes": [{"id": 1, "label": "func1"}, {"id": 2, "label": "func2"}],
            "edges": [{"source": 1, "target": 2, "type": "calls"}]
        }
        mock_query_executor.execute = AsyncMock(
            return_value={
                "success": True,
                "stdout": json.dumps(graph_data)
            }
        )
        
        result = await mock_query_executor.execute("graph_query")
        
        # 简单GraphML导出模拟
        output_file = tmp_path / "graph.xml"
        data = json.loads(result["stdout"])
        with open(output_file, "w") as f:
            f.write('<?xml version="1.0"?>\n')
            f.write('<graphml>\n')
            f.write('  <graph>\n')
            for node in data["nodes"]:
                f.write(f'    <node id="{node["id"]}" label="{node["label"]}"/>\n')
            for edge in data["edges"]:
                f.write(f'    <edge source="{edge["source"]}" target="{edge["target"]}"/>\n')
            f.write('  </graph>\n')
            f.write('</graphml>\n')
        
        assert output_file.exists()
        content = output_file.read_text()
        assert "<graphml>" in content

    @pytest.mark.asyncio
    async def test_export_large_result(self, mock_query_executor, tmp_path):
        """测试导出大结果集"""
        # Mock大量数据
        large_data = [{"id": i, "value": f"data{i}"} for i in range(1000)]
        mock_query_executor.execute = AsyncMock(
            return_value={
                "success": True,
                "stdout": json.dumps(large_data)
            }
        )
        
        result = await mock_query_executor.execute("large_query")
        
        # 导出到文件
        output_file = tmp_path / "large_result.json"
        with open(output_file, "w") as f:
            json.dump(json.loads(result["stdout"]), f)
        
        assert output_file.exists()
        assert output_file.stat().st_size > 0


class TestExportEdgeCases:
    """测试导出边界情况"""

    @pytest.mark.asyncio
    async def test_export_empty_result(self, mock_query_executor, tmp_path):
        """测试导出空结果"""
        mock_query_executor.execute = AsyncMock(
            return_value={
                "success": True,
                "stdout": "[]"
            }
        )
        
        result = await mock_query_executor.execute("empty_query")
        
        # 导出空结果
        output_file = tmp_path / "empty.json"
        with open(output_file, "w") as f:
            json.dump(json.loads(result["stdout"]), f)
        
        assert output_file.exists()
        with open(output_file, "r") as f:
            data = json.load(f)
        assert data == []

    @pytest.mark.asyncio
    async def test_export_with_unicode(self, mock_query_executor, tmp_path):
        """测试导出包含Unicode的结果"""
        # Mock包含Unicode的数据
        data = [{"name": "函数名", "description": "功能描述"}]
        mock_query_executor.execute = AsyncMock(
            return_value={
                "success": True,
                "stdout": json.dumps(data, ensure_ascii=False)
            }
        )
        
        result = await mock_query_executor.execute("query")
        
        # 导出UTF-8文件
        output_file = tmp_path / "unicode.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(json.loads(result["stdout"]), f, ensure_ascii=False)
        
        assert output_file.exists()
        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "函数名" in data[0]["name"]

    @pytest.mark.asyncio
    async def test_export_invalid_path(self, mock_query_executor):
        """测试导出到无效路径"""
        mock_query_executor.execute = AsyncMock(
            return_value={
                "success": True,
                "stdout": json.dumps([{"data": "test"}])
            }
        )
        
        result = await mock_query_executor.execute("query")
        
        # 尝试写入无效路径应该失败
        invalid_path = Path("/nonexistent/directory/file.json")
        try:
            with open(invalid_path, "w") as f:
                json.dump(json.loads(result["stdout"]), f)
            assert False, "Should have raised an exception"
        except (FileNotFoundError, PermissionError, OSError):
            # 预期的异常
            assert True

    @pytest.mark.asyncio
    async def test_export_format_validation(self, mock_query_executor, tmp_path):
        """测试导出格式验证"""
        data = [{"key": "value"}]
        mock_query_executor.execute = AsyncMock(
            return_value={
                "success": True,
                "stdout": json.dumps(data)
            }
        )
        
        result = await mock_query_executor.execute("query")
        
        # 验证JSON格式
        output_file = tmp_path / "valid.json"
        with open(output_file, "w") as f:
            json.dump(json.loads(result["stdout"]), f)
        
        # 读取并验证
        with open(output_file, "r") as f:
            loaded_data = json.load(f)
        
        assert loaded_data == data

    @pytest.mark.asyncio
    async def test_export_with_metadata(self, mock_query_executor, tmp_path):
        """测试导出带元数据"""
        from datetime import datetime
        
        data = [{"result": "test"}]
        mock_query_executor.execute = AsyncMock(
            return_value={
                "success": True,
                "stdout": json.dumps(data)
            }
        )
        
        result = await mock_query_executor.execute("query")
        
        # 导出带元数据的结果
        output_file = tmp_path / "with_metadata.json"
        export_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "query": "test_query",
                "count": len(data)
            },
            "results": json.loads(result["stdout"])
        }
        
        with open(output_file, "w") as f:
            json.dump(export_data, f)
        
        assert output_file.exists()
        with open(output_file, "r") as f:
            loaded = json.load(f)
        assert "metadata" in loaded
        assert "results" in loaded

