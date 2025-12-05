"""项目资源暴露"""

from loguru import logger

from joern_mcp.mcp_server import mcp, server_state


@mcp.resource("project://list")
async def list_projects_resource() -> str:
    """
    暴露所有已加载项目列表

    Returns:
        str: 项目列表（JSON格式）
    """
    logger.info("Fetching projects resource")

    try:
        if not server_state.query_executor:
            return '{"success": false, "error": "Query executor not initialized"}'

        # workspace.projects 返回 List[Project]
        # 使用 .map(_.name) 提取名称列表
        query = "workspace.projects.map(_.name).l"
        result = await server_state.query_executor.execute(query, format="raw")

        if result.get("success"):
            stdout = result.get("stdout", "[]").strip()
            # 解析 Scala List 格式 List("name1", "name2")
            import re
            list_match = re.search(r'List\s*\((.*)\)', stdout, re.DOTALL)
            if list_match:
                content = list_match.group(1)
                # 提取引号内的字符串
                names = re.findall(r'"([^"]*)"', content)
                import orjson
                return orjson.dumps({"success": True, "projects": names}).decode()
            return f'{{"success": true, "projects": [], "raw": "{stdout}"}}'
        else:
            return f'{{"success": false, "error": "{result.get("stderr", "Unknown error")}"}}'
    except Exception as e:
        logger.exception(f"Error fetching projects resource: {e}")
        return f'{{"success": false, "error": "{str(e)}"}}'


@mcp.resource("project://{project_name}/info")
async def project_info_resource(project_name: str) -> str:
    """
    暴露项目详细信息

    Args:
        project_name: 项目名称

    Returns:
        str: 项目信息（JSON格式）
    """
    logger.info(f"Fetching project info for: {project_name}")

    try:
        if not server_state.query_executor:
            return '{"success": false, "error": "Query executor not initialized"}'

        # workspace.project() 返回 Option[Project]，需要用 flatMap 处理
        # 使用项目自己的 CPG 而不是全局的 cpg
        query = f'''
        workspace.project("{project_name}").flatMap {{ p =>
            p.cpg.map {{ c =>
                Map(
                    "name" -> p.name,
                    "inputPath" -> p.inputPath,
                    "methods" -> c.method.name.dedup.size,
                    "files" -> c.file.name.dedup.size,
                    "lines" -> c.method.lineNumber.max.getOrElse(0)
                )
            }}
        }}
        '''

        result = await server_state.query_executor.execute(query)

        if result.get("success"):
            return result.get("stdout", "{}")
        else:
            return f'{{"success": false, "error": "{result.get("stderr", "Unknown error")}"}}'
    except Exception as e:
        logger.exception(f"Error fetching project info: {e}")
        return f'{{"success": false, "error": "{str(e)}"}}'


@mcp.resource("project://{project_name}/functions")
async def project_functions_resource(project_name: str) -> str:
    """
    暴露项目中的所有函数

    Args:
        project_name: 项目名称

    Returns:
        str: 函数列表（JSON格式）
    """
    logger.info(f"Fetching functions for project: {project_name}")

    try:
        if not server_state.query_executor:
            return '{"success": false, "error": "Query executor not initialized"}'

        query = """
        cpg.method
           .filterNot(_.isExternal)
           .take(100)
           .map(m => Map(
               "name" -> m.name,
               "fullName" -> m.fullName,
               "signature" -> m.signature,
               "filename" -> m.filename,
               "lineNumber" -> m.lineNumber.getOrElse(-1)
           ))
        """

        result = await server_state.query_executor.execute(query)

        if result.get("success"):
            return result.get("stdout", "[]")
        else:
            return f'{{"success": false, "error": "{result.get("stderr", "Unknown error")}"}}'
    except Exception as e:
        logger.exception(f"Error fetching functions: {e}")
        return f'{{"success": false, "error": "{str(e)}"}}'


@mcp.resource("project://{project_name}/vulnerabilities")
async def project_vulnerabilities_resource(project_name: str) -> str:
    """
    暴露项目中发现的漏洞

    Args:
        project_name: 项目名称

    Returns:
        str: 漏洞列表（JSON格式）
    """
    logger.info(f"Fetching vulnerabilities for project: {project_name}")

    try:
        if not server_state.query_executor:
            return '{"success": false, "error": "Query executor not initialized"}'

        # 使用污点分析服务查找漏洞
        from joern_mcp.services.taint import TaintAnalysisService

        service = TaintAnalysisService(server_state.query_executor)
        result = await service.find_vulnerabilities(severity="CRITICAL", max_flows=5)

        if result.get("success"):
            import orjson

            return orjson.dumps(result).decode()
        else:
            return f'{{"success": false, "error": "{result.get("error", "Unknown error")}"}}'
    except Exception as e:
        logger.exception(f"Error fetching vulnerabilities: {e}")
        return f'{{"success": false, "error": "{str(e)}"}}'
