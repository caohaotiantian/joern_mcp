"""Joern查询模板库"""
from string import Template


class QueryTemplates:
    """查询模板集合"""
    
    # ===== 函数查询 =====
    
    GET_FUNCTION = Template('''
        cpg.method.name("$name")
           .map(m => Map(
               "name" -> m.name,
               "signature" -> m.signature,
               "filename" -> m.filename,
               "lineNumber" -> m.lineNumber.getOrElse(-1),
               "lineNumberEnd" -> m.lineNumberEnd.getOrElse(-1),
               "code" -> m.code
           ))
    ''')
    
    LIST_FUNCTIONS = Template('''
        cpg.method
           .take($limit)
           .map(m => Map(
               "name" -> m.name,
               "filename" -> m.filename,
               "lineNumber" -> m.lineNumber.getOrElse(-1)
           ))
    ''')
    
    # ===== 调用关系查询 =====
    
    GET_CALLERS = Template('''
        cpg.method.name("$name")
           .caller
           .dedup
           .map(m => Map(
               "name" -> m.name,
               "filename" -> m.filename,
               "lineNumber" -> m.lineNumber.getOrElse(-1)
           ))
    ''')
    
    GET_CALLEES = Template('''
        cpg.method.name("$name")
           .callee
           .dedup
           .map(m => Map(
               "name" -> m.name,
               "filename" -> m.filename,
               "lineNumber" -> m.lineNumber.getOrElse(-1)
           ))
    ''')
    
    GET_CALL_CHAIN = Template('''
        cpg.method.name("$name")
           .repeat(_.caller)(_.times($depth))
           .dedup
           .map(m => Map(
               "name" -> m.name,
               "file" -> m.filename
           ))
    ''')
    
    # ===== 数据流查询 =====
    
    DATAFLOW = Template('''
        def source = cpg.method.name("$source_name").parameter
        def sink = cpg.call.name("$sink_name").argument
        
        sink.reachableBy(source).flows.map(flow => Map(
            "source" -> flow.source.code,
            "sink" -> flow.sink.code,
            "path" -> flow.elements.map(e => Map(
                "type" -> e.label,
                "code" -> e.code,
                "line" -> e.lineNumber.getOrElse(-1),
                "file" -> e.file.name.headOption.getOrElse("unknown")
            ))
        ))
    ''')
    
    DATAFLOW_VARIABLE = Template('''
        def source = cpg.identifier.name("$variable_name")
        def sink = cpg.call.name("$sink_name").argument
        
        sink.reachableBy(source).flows.map(flow => Map(
            "variable" -> "$variable_name",
            "source" -> Map(
                "code" -> flow.source.code,
                "line" -> flow.source.lineNumber.getOrElse(-1),
                "file" -> flow.source.file.name.headOption.getOrElse("unknown")
            ),
            "sink" -> Map(
                "code" -> flow.sink.code,
                "line" -> flow.sink.lineNumber.getOrElse(-1),
                "file" -> flow.sink.file.name.headOption.getOrElse("unknown")
            )
        ))
    ''')
    
    # ===== 污点分析 =====
    
    TAINT_ANALYSIS = Template('''
        def sources = cpg.method.name("($source_pattern)").parameter
        def sinks = cpg.call.name("($sink_pattern)").argument
        
        sinks.reachableBy(sources).flows.map(flow => Map(
            "vulnerability" -> "Potential Taint Flow",
            "severity" -> "$severity",
            "source" -> Map(
                "method" -> flow.source.method.name,
                "file" -> flow.source.file.name.headOption.getOrElse("unknown"),
                "line" -> flow.source.lineNumber.getOrElse(-1)
            ),
            "sink" -> Map(
                "method" -> flow.sink.method.name,
                "file" -> flow.sink.file.name.headOption.getOrElse("unknown"),
                "line" -> flow.sink.lineNumber.getOrElse(-1)
            ),
            "pathLength" -> flow.elements.size
        ))
    ''')
    
    TAINT_ANALYSIS_SIMPLE = Template('''
        cpg.method.name("$source_method")
           .parameter
           .reachableBy(cpg.call.name("$sink_method"))
           .flows
           .map(f => Map(
               "source" -> f.source.code,
               "sink" -> f.sink.code
           ))
    ''')
    
    # ===== 控制流查询 =====
    
    GET_CFG = Template('''
        cpg.method.name("$name")
           .dotCfg
           .l
    ''')
    
    GET_DOMINATORS = Template('''
        cpg.method.name("$name")
           .dotDom
           .l
    ''')
    
    # ===== 漏洞检测 =====
    
    FIND_SQL_INJECTION = Template('''
        def sources = cpg.method.name("(get|post|request).*").parameter
        def sinks = cpg.call.name("(execute|query|createStatement)").argument
        
        sinks.reachableBy(sources).flows.map(flow => Map(
            "vulnerability" -> "SQL Injection",
            "severity" -> "HIGH",
            "source" -> Map(
                "code" -> flow.source.code,
                "file" -> flow.source.file.name.headOption.getOrElse("unknown"),
                "line" -> flow.source.lineNumber.getOrElse(-1)
            ),
            "sink" -> Map(
                "code" -> flow.sink.code,
                "file" -> flow.sink.file.name.headOption.getOrElse("unknown"),
                "line" -> flow.sink.lineNumber.getOrElse(-1)
            )
        ))
    ''')
    
    FIND_COMMAND_INJECTION = Template('''
        def sources = cpg.method.name("(get|post|request).*").parameter
        def sinks = cpg.call.name("(exec|system|Runtime\\\\.getRuntime)").argument
        
        sinks.reachableBy(sources).flows.map(flow => Map(
            "vulnerability" -> "Command Injection",
            "severity" -> "CRITICAL",
            "source" -> Map(
                "code" -> flow.source.code,
                "file" -> flow.source.file.name.headOption.getOrElse("unknown"),
                "line" -> flow.source.lineNumber.getOrElse(-1)
            ),
            "sink" -> Map(
                "code" -> flow.sink.code,
                "file" -> flow.sink.file.name.headOption.getOrElse("unknown"),
                "line" -> flow.sink.lineNumber.getOrElse(-1)
            )
        ))
    ''')
    
    # ===== 代码搜索 =====
    
    SEARCH_BY_PATTERN = Template('''
        cpg.all.code(".*$pattern.*")
           .take($limit)
           .map(n => Map(
               "code" -> n.code,
               "type" -> n.label,
               "file" -> n.file.name.headOption.getOrElse("unknown"),
               "line" -> n.lineNumber.getOrElse(-1)
           ))
    ''')
    
    @classmethod
    def build(cls, template_name: str, **kwargs) -> str:
        """
        构建查询
        
        Args:
            template_name: 模板名称
            **kwargs: 模板参数
            
        Returns:
            str: 构建好的查询字符串
            
        Raises:
            ValueError: 模板不存在
        """
        template = getattr(cls, template_name, None)
        if not template:
            raise ValueError(f"Unknown template: {template_name}")
        
        return template.substitute(**kwargs).strip()
    
    @classmethod
    def list_templates(cls) -> list[str]:
        """列出所有可用的模板"""
        return [
            name for name in dir(cls)
            if not name.startswith('_') and name.isupper() and isinstance(getattr(cls, name), Template)
        ]

