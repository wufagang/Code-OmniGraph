"""
图数据库使用示例

演示如何使用 graph_builder 模块构建代码图谱
"""

import os
import sys
import logging

# 添加项目路径 - 从example目录到core根目录
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from cagr_processor.graph_builder import create_graph_db, GraphDBConfig, Neo4jConfig
from cagr_processor.graph_builder.models import (
    ProjectNode, FileNode, ClassNode, FunctionNode, VariableNode,
    CallRelationship, TaintFlowRelationship, RiskLevel
)
from cagr_collector.static_analyzer.tree_sitter_parser import TreeSitterParser


def build_code_graph(project_path: str):
    """
    构建代码图谱的完整流程

    Args:
        project_path: 项目路径
    """
    print(f"Building code graph for project: {project_path}")

    # 1. 创建图数据库连接
    print("\n1. Connecting to graph database...")
    graph_db = create_graph_db()
    print("✓ Connected to Neo4j")

    # 2. 解析代码结构（使用 Tree-sitter）
    print("\n2. Parsing code structure with Tree-sitter...")
    parser = TreeSitterParser(project_path)
    files = parser.parse_project()
    print(f"✓ Parsed {len(files)} files")

    # 3. 创建项目节点
    print("\n3. Creating project node...")
    project_name = os.path.basename(project_path)
    project = ProjectNode(
        name=project_name,
        version="1.0.0",
        language="python",
        path=project_path
    )
    graph_db.create_project(project)
    print(f"✓ Created project node: {project_name}")

    # 4. 创建文件节点和关系
    print("\n4. Creating file nodes and relationships...")
    for file in files:
        # 创建文件节点
        file_node = FileNode(
            path=file.path,
            name=file.name,
            language=file.language,
            content=file.content,
            size=file.size
        )
        graph_db.create_file(file_node)

        # 创建 Project-[:CONTAINS]->File 关系
        graph_db.create_project_contains_file(project_name, file.path)

        print(f"  ✓ Created file: {file.path}")

    # 5. 创建类和方法节点
    print("\n5. Creating class and method nodes...")
    for file in files:
        # 创建类节点
        for cls in file.classes:
            class_node = ClassNode(
                qualified_name=f"{file.path}:{cls.name}",
                name=cls.name,
                file_path=file.path,
                docstring=cls.docstring,
                is_interface=cls.is_interface,
                is_abstract=cls.is_abstract,
                start_line=cls.start_line,
                end_line=cls.end_line
            )
            graph_db.create_class(class_node)
            graph_db.create_file_defines_class(file.path, class_node.qualified_name)

            print(f"  ✓ Created class: {cls.name}")

            # 创建方法节点
            for method in cls.methods:
                method_node = FunctionNode(
                    qualified_name=f"{file.path}:{cls.name}#{method.name}",
                    name=method.name,
                    signature=method.signature,
                    body=method.source_code,
                    file_path=file.path,
                    class_name=cls.name,
                    start_line=method.start_line,
                    end_line=method.end_line,
                    is_constructor=method.is_constructor,
                    docstring=method.docstring
                )
                graph_db.create_function(method_node)
                graph_db.create_class_has_method(class_node.qualified_name, method_node.qualified_name)

                print(f"    ✓ Created method: {method.name}")

        # 创建文件级别的函数
        for method in file.methods:
            function_node = FunctionNode(
                qualified_name=f"{file.path}:{method.name}",
                name=method.name,
                signature=method.signature,
                body=method.source_code,
                file_path=file.path,
                start_line=method.start_line,
                end_line=method.end_line,
                docstring=method.docstring
            )
            graph_db.create_function(function_node)
            graph_db.create_file_defines_function(file.path, function_node.qualified_name)

            print(f"  ✓ Created function: {method.name}")

    # 6. 创建调用关系（这里用示例数据）
    print("\n6. Creating call relationships...")
    # 在实际应用中，这些调用关系应该由 Joern 或其他静态分析工具提取
    example_calls = [
        CallRelationship(
            caller_qualified_name="main.py:main",
            callee_qualified_name="utils.py:Utils#helper",
            call_site_line=10
        ),
        CallRelationship(
            caller_qualified_name="utils.py:Utils#helper",
            callee_qualified_name="utils.py:Utils#format",
            call_site_line=15
        )
    ]

    for call in example_calls:
        graph_db.create_calls_relationship(call)
        print(f"  ✓ Created call: {call.caller_qualified_name} -> {call.callee_qualified_name}")

    # 7. 注入污点流（模拟 Joern 分析结果）
    print("\n7. Injecting taint flows (simulating Joern analysis)...")
    taint_flows = [
        TaintFlowRelationship(
            source_qualified_name="main.py:main",
            sink_qualified_name="utils.py:Utils#execute",
            risk=RiskLevel.HIGH,
            vulnerability_type="COMMAND_INJECTION",
            description="User input flows to system command execution"
        ),
        TaintFlowRelationship(
            source_qualified_name="api.py:API#get_input",
            sink_qualified_name="db.py:Database#query",
            risk=RiskLevel.HIGH,
            vulnerability_type="SQL_INJECTION",
            description="User input flows to SQL query without sanitization"
        )
    ]

    for taint in taint_flows:
        graph_db.create_taint_flow_relationship(taint)
        print(f"  ✓ Created taint flow: {taint.vulnerability_type}")

    # 8. 查询图谱
    print("\n8. Querying the graph...")

    # 获取图统计
    stats = graph_db.get_graph_stats()
    print(f"\nGraph Statistics:")
    print(f"  Total nodes: {stats.total_nodes}")
    print(f"  Total relationships: {stats.total_relationships}")
    for node_type, count in stats.node_counts.items():
        print(f"  {node_type}: {count}")

    # 查找函数
    print(f"\n9. Finding functions...")
    function = graph_db.find_function_by_name("main")
    if function:
        print(f"  Found function: {function.qualified_name}")

    # 获取调用链
    print(f"\n10. Getting call chains...")
    call_chains = graph_db.get_call_chain("main.py:main", depth=3)
    for chain in call_chains:
        print(f"  Chain: {' -> '.join([node['name'] for node in chain])}")

    # 获取子图
    print(f"\n11. Getting subgraph...")
    subgraph = graph_db.get_subgraph_for_function("main.py:main", depth=2)
    print(f"  Center: {subgraph.center_node.get('name', 'Unknown')}")
    print(f"  Upstream callers: {len(subgraph.upstream_callers)}")
    print(f"  Downstream callees: {len(subgraph.downstream_callees)}")
    print(f"  Taint flows: {len(subgraph.taint_flows)}")

    # 查找污点流
    print(f"\n12. Finding taint flows...")
    taint_results = graph_db.find_taint_flows(risk_level=RiskLevel.HIGH)
    for taint in taint_results:
        print(f"  {taint.vulnerability_type}: {taint.source_qualified_name} -> {taint.sink_qualified_name}")

    # 查找漏洞路径
    print(f"\n13. Finding vulnerable paths...")
    vulnerable_paths = graph_db.find_vulnerable_paths("execute")
    for path in vulnerable_paths:
        print(f"  Path to 'execute': {' -> '.join([node['name'] for node in path])}")

    print("\n✓ Code graph building completed!")


def demo_graph_rag():
    """
    演示 Graph-RAG 用法
    """
    print("\n" + "="*50)
    print("Graph-RAG Demo")
    print("="*50)

    # 创建图数据库连接
    graph_db = create_graph_db()

    # 查询某个函数的完整上下文
    function_name = "main"
    print(f"\nAnalyzing function: {function_name}")

    # 获取函数信息
    func = graph_db.find_function_by_name(function_name)
    if not func:
        print(f"Function '{function_name}' not found")
        return

    # 获取子图
    subgraph = graph_db.get_subgraph_for_function(func.qualified_name, depth=2)

    # 构建 LLM 上下文
    context = f"""
【目标函数: {func.name}】
```python
{func.body}
```

【函数元信息】
- 全限定名: {func.qualified_name}
- 签名: {func.signature}
- 文件路径: {func.file_path}
- 起始行: {func.start_line}
- 是否为 API 入口: {func.is_endpoint}

【上游调用者】
{chr(10).join([f"- {caller['name']} ({caller['qualified_name']})" for caller in subgraph.upstream_callers])}

【下游被调用者】
{chr(10).join([f"- {callee['name']} ({callee['qualified_name']})" for callee in subgraph.downstream_callees])}

【污点流分析】
{chr(10).join([f"- {flow['risk']}风险: {flow['vulnerability_type']} - {flow['description']}" for flow in subgraph.taint_flows])}

【安全建议】
基于以上分析，请检查：
1. 上游调用者是否对输入做了充分验证？
2. 下游被调用者是否存在安全风险？
3. 污点流路径是否可能导致安全漏洞？
"""

    print("\nGenerated context for LLM:")
    print("-" * 50)
    print(context)
    print("-" * 50)

    # 这里可以将 context 发送给 LLM 进行进一步分析
    print("\n✓ Context ready for LLM analysis!")


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)

    # 示例项目路径（请替换为实际路径）
    project_path = "/path/to/your/project"

    # 构建代码图谱
    build_code_graph(project_path)

    # 演示 Graph-RAG
    demo_graph_rag()