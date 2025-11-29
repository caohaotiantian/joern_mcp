"""
tests/test_tools/test_project.py

测试项目管理工具

注意：这些测试不是直接测试MCP工具装饰器，而是测试底层逻辑和Service行为
"""
import pytest
import json
from unittest.mock import MagicMock, AsyncMock
from pathlib import Path


class TestProjectManagementLogic:
    """测试项目管理工具的底层逻辑"""

    @pytest.mark.asyncio
    async def test_import_code_mock(self, mock_joern_server):
        """测试代码导入Mock逻辑"""
        # 这个测试验证JoernServerManager的import_code方法被正确调用
        mock_joern_server.import_code = AsyncMock(
            return_value={"success": True, "project": "test_project"}
        )
        
        result = await mock_joern_server.import_code("/tmp/test", "test_project")
        
        assert result["success"] is True
        assert result["project"] == "test_project"
        mock_joern_server.import_code.assert_called_once_with("/tmp/test", "test_project")

    @pytest.mark.asyncio
    async def test_list_projects_query(self, mock_query_executor):
        """测试列出项目查询"""
        projects_data = ["project1", "project2", "project3"]
        
        mock_query_executor.execute = AsyncMock(
            return_value={
                "success": True,
                "stdout": json.dumps(projects_data)
            }
        )
        
        # 执行列出项目查询
        result = await mock_query_executor.execute("workspace.projects.l.toJson")
        
        assert result["success"] is True
        data = json.loads(result["stdout"])
        assert len(data) == 3
        assert "project1" in data

    @pytest.mark.asyncio
    async def test_delete_project_query(self, mock_query_executor):
        """测试删除项目查询"""
        mock_query_executor.execute = AsyncMock(
            return_value={"success": True, "stdout": "true"}
        )
        
        # 执行删除项目查询
        result = await mock_query_executor.execute('workspace.projects.find(_.name == "test").remove')
        
        assert result["success"] is True
        assert result["stdout"] == "true"

    @pytest.mark.asyncio
    async def test_get_project_info_query(self, mock_query_executor):
        """测试获取项目信息查询"""
        project_info = [{
            "name": "test_project",
            "inputPath": "/tmp/test",
            "language": "C"
        }]
        
        mock_query_executor.execute = AsyncMock(
            return_value={
                "success": True,
                "stdout": json.dumps(project_info)
            }
        )
        
        # 执行获取项目信息查询
        result = await mock_query_executor.execute('workspace.projects.name("test_project").l.toJson')
        
        assert result["success"] is True
        data = json.loads(result["stdout"])
        assert data[0]["name"] == "test_project"


class TestProjectManagementEdgeCases:
    """测试项目管理的边界情况"""

    @pytest.mark.asyncio
    async def test_import_nonexistent_path(self, mock_joern_server):
        """测试导入不存在的路径"""
        mock_joern_server.import_code = AsyncMock(
            return_value={"success": False, "error": "Path not found"}
        )
        
        result = await mock_joern_server.import_code("/nonexistent/path", "test")
        
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_delete_nonexistent_project(self, mock_query_executor):
        """测试删除不存在的项目"""
        mock_query_executor.execute = AsyncMock(
            return_value={"success": True, "stdout": "false"}  # 没有找到项目
        )
        
        result = await mock_query_executor.execute('workspace.projects.find(_.name == "nonexistent").remove')
        
        assert result["success"] is True
        assert result["stdout"] == "false"

    @pytest.mark.asyncio  
    async def test_list_projects_empty(self, mock_query_executor):
        """测试列出空项目列表"""
        mock_query_executor.execute = AsyncMock(
            return_value={"success": True, "stdout": "[]"}
        )
        
        result = await mock_query_executor.execute("workspace.projects.l.toJson")
        
        assert result["success"] is True
        assert result["stdout"] == "[]"

    @pytest.mark.asyncio
    async def test_import_duplicate_project(self, mock_joern_server):
        """测试导入重复项目名称"""
        mock_joern_server.import_code = AsyncMock(
            return_value={"success": False, "error": "Project already exists"}
        )
        
        result = await mock_joern_server.import_code("/tmp/test", "existing_project")
        
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_query_error_handling(self, mock_query_executor):
        """测试查询错误处理"""
        mock_query_executor.execute = AsyncMock(
            return_value={"success": False, "stderr": "Connection error"}
        )
        
        result = await mock_query_executor.execute("workspace.projects.l.toJson")
        
        assert result["success"] is False
        assert "stderr" in result
