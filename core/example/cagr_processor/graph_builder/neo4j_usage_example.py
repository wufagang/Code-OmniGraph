#!/usr/bin/env python3
"""
Code-OmniGraph Neo4j 图数据库使用示例
展示如何调用 cagr_processor/graph_builder 模块的所有功能
"""

import os
import sys
from typing import List, Dict, Any, Optional

# 将 core 目录添加到 Python 路径
current_file = os.path.abspath(__file__)
core_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file))))
sys.path.insert(0, core_dir)

from cagr_processor.graph_builder.config import GraphDBConfig
from cagr_processor.graph_builder.factory import GraphDBFactory
from cagr_processor.graph_builder.models import (
    ProjectNode, FileNode, ClassNode, FunctionNode, VariableNode,
    CallRelationship, TaintFlowRelationship, DataAccessRelationship,
    NodeLabel, RelType, RiskLevel
)


def setup_neo4j_connection():
    """设置 Neo4j 连接配置"""
    # 从环境变量加载配置
    config = GraphDBConfig.from_env()

    # 或者手动创建配置
    # config = GraphDBConfig(
    #     neo4j_config={
    #         "uri": "bolt://localhost:7687",
    #         "username": "neo4j",
    #         "password": "password"
    #     }
    # )

    # 创建图数据库实例
    graph_db = GraphDBFactory.create(config)

    # 连接到数据库
    graph_db.connect()

    return graph_db


def example_create_nodes(graph_db):
    """示例：创建各种类型的节点"""
    print("\n=== 创建节点示例 ===")

    # 1. 创建项目节点
    project = ProjectNode(
        name="example-project",
        language="java",
        version="1.0.0"
    )
    success = graph_db.create_project(project)
    print(f"创建项目节点: {success}")

    # 2. 创建文件节点
    file_node = FileNode(
        path="com/example/service/UserService.java",
        name="UserService.java",
        language="java",
        size=1024
    )
    success = graph_db.create_file(file_node)
    print(f"创建文件节点: {success}")

    # 3. 创建类节点
    class_node = ClassNode(
        qualified_name="com.example.service.UserService",
        name="UserService",
        start_line=10,
        docstring="用户服务类"
    )
    success = graph_db.create_class(class_node)
    print(f"创建类节点: {success}")

    # 4. 创建函数节点
    function_node = FunctionNode(
        qualified_name="com.example.service.UserService.getUserById",
        name="getUserById",
        signature="public User getUserById(Long id)",
        return_type="User",
        start_line=25,
        docstring="根据ID获取用户信息"
    )
    success = graph_db.create_function(function_node)
    print(f"创建函数节点: {success}")

    # 5. 创建变量节点
    variable_node = VariableNode(
        qualified_name="com.example.service.UserService.userRepository",
        name="userRepository",
        var_type="UserRepository"
    )
    success = graph_db.create_variable(variable_node)
    print(f"创建变量节点: {success}")

    return True


def example_create_relationships(graph_db):
    """示例：创建各种关系"""
    print("\n=== 创建关系示例 ===")

    # 1. 创建项目包含文件的关系
    success = graph_db.create_project_contains_file(
        "example-project",
        "com/example/service/UserService.java"
    )
    print(f"创建项目包含文件关系: {success}")

    # 2. 创建文件定义类的关系
    success = graph_db.create_file_defines_class(
        "com/example/service/UserService.java",
        "com.example.service.UserService"
    )
    print(f"创建文件定义类关系: {success}")

    # 3. 创建类包含方法的关系
    success = graph_db.create_class_has_method(
        "com.example.service.UserService",
        "com.example.service.UserService.getUserById"
    )
    print(f"创建类包含方法关系: {success}")

    # 4. 创建函数调用关系
    call_rel = CallRelationship(
        caller_qualified_name="com.example.service.UserService.getUserById",
        callee_qualified_name="com.example.repository.UserRepository.findById",
        call_site_line=30
    )
    success = graph_db.create_calls_relationship(call_rel)
    print(f"创建函数调用关系: {success}")

    # 5. 创建数据访问关系
    data_access = DataAccessRelationship(
        function_qualified_name="com.example.service.UserService.getUserById",
        variable_qualified_name="com.example.service.UserService.userRepository",
        access_type="READS",
        line=30
    )
    success = graph_db.create_data_access_relationship(data_access)
    print(f"创建数据访问关系: {success}")

    # 6. 创建污点流关系
    taint_flow = TaintFlowRelationship(
        source_qualified_name="com.example.controller.UserController.getUserInput",
        sink_qualified_name="com.example.service.UserService.executeQuery",
        risk=RiskLevel.HIGH,
        vulnerability_type="SQL_INJECTION",
        taint_path=["parameter", "query_string"]
    )
    success = graph_db.create_taint_flow_relationship(taint_flow)
    print(f"创建污点流关系: {success}")

    return True


def example_query_operations(graph_db):
    """示例：查询操作"""
    print("\n=== 查询操作示例 ===")

    # 1. 根据函数名查找函数
    function = graph_db.find_function_by_name("getUserById")
    print(f"根据函数名查找: {function.qualified_name if function else '未找到'}")

    # 2. 根据全限定名查找函数
    function = graph_db.find_function_by_qualified_name(
        "com.example.service.UserService.getUserById"
    )
    print(f"根据全限定名查找: {function.name if function else '未找到'}")

    # 3. 获取函数调用链
    call_chains = graph_db.get_call_chain(
        "com.example.service.UserService.getUserById",
        depth=2
    )
    print(f"获取调用链 (找到 {len(call_chains)} 条):")
    for chain in call_chains:
        print(f"  - {' -> '.join([node['name'] for node in chain])}")

    # 4. 获取上游调用者
    callers = graph_db.get_upstream_callers(
        "com.example.repository.UserRepository.findById",
        depth=1
    )
    print(f"上游调用者 (找到 {len(callers)} 个):")
    for caller in callers:
        print(f"  - {caller['qualified_name']}")

    # 5. 获取下游被调用者
    callees = graph_db.get_downstream_callees(
        "com.example.service.UserService.getUserById",
        depth=1
    )
    print(f"下游被调用者 (找到 {len(callees)} 个):")
    for callee in callees:
        print(f"  - {callee['qualified_name']}")

    # 6. 查找污点流
    taint_flows = graph_db.find_taint_flows(
        source_function="com.example.controller.UserController.getUserInput",
        risk_level="HIGH",
        limit=10
    )
    print(f"污点流 (找到 {len(taint_flows)} 条):")
    for flow in taint_flows:
        print(f"  - {flow.source_qualified_name} -> {flow.sink_qualified_name}")

    # 7. 查找到达危险函数的路径
    vulnerable_paths = graph_db.find_vulnerable_paths("executeQuery")
    print(f"危险路径 (找到 {len(vulnerable_paths)} 条):")
    for path in vulnerable_paths:
        print(f"  - {' -> '.join([node['name'] for node in path])}")

    return True


def example_graph_stats(graph_db):
    """示例：图统计信息"""
    print("\n=== 图统计信息示例 ===")

    stats = graph_db.get_graph_stats()
    print(f"总节点数: {stats.total_nodes}")
    print(f"总关系数: {stats.total_relationships}")
    print("各类节点数量:")
    for node_type, count in stats.node_counts.items():
        print(f"  - {node_type}: {count}")

    return True


def example_subgraph_operations(graph_db):
    """示例：子图操作"""
    print("\n=== 子图操作示例 ===")

    # 获取函数的子图
    subgraph = graph_db.get_subgraph_for_function(
        "com.example.service.UserService.getUserById",
        depth=2
    )

    print(f"子图节点数: {len(subgraph.nodes)}")
    print(f"子图关系数: {len(subgraph.relationships)}")
    print("子图中的函数节点:")
    for node in subgraph.nodes:
        if node.get('label') == 'Function':
            print(f"  - {node.get('name')} ({node.get('qualified_name')})")

    return True


def example_cypher_query(graph_db):
    """示例：执行原生 Cypher 查询"""
    print("\n=== 原生 Cypher 查询示例 ===")

    # 执行自定义 Cypher 查询
    query = """
    MATCH (f:Function)-[:CALLS]->(callee:Function)
    WHERE f.name CONTAINS 'User'
    RETURN f.name as caller, callee.name as callee, callee.qualified_name as callee_qualified
    LIMIT 5
    """

    results = graph_db.execute_cypher(query)
    print(f"查询结果 (找到 {len(results)} 条):")
    for result in results:
        print(f"  - {result['caller']} -> {result['callee']} ({result['callee_qualified']})")

    return True


def example_transaction_operations(graph_db):
    """示例：事务操作"""
    print("\n=== 事务操作示例 ===")

    # 开始事务
    session = graph_db.begin_transaction()

    try:
        # 在事务中执行多个操作
        # 创建节点
        session.run("""
            CREATE (p:Project {name: $name, description: $desc})
        """, name="transaction-project", desc="事务测试项目")

        # 创建关系
        session.run("""
            MATCH (p:Project {name: $proj_name})
            CREATE (f:File {path: $file_path, name: $file_name})
            CREATE (p)-[:CONTAINS]->(f)
        """, proj_name="transaction-project",
             file_path="transaction/test.java",
             file_name="test.java")

        # 提交事务
        graph_db.commit(session)
        print("事务提交成功")

    except Exception as e:
        # 回滚事务
        graph_db.rollback(session)
        print(f"事务回滚: {e}")

    return True


def example_advanced_queries(graph_db):
    """示例：高级查询"""
    print("\n=== 高级查询示例 ===")

    # 1. 查找复杂调用模式
    complex_query = """
    MATCH path = (start:Function)-[:CALLS*2..4]->(end:Function)
    WHERE start.name CONTAINS 'validate' AND end.name CONTAINS 'execute'
    WITH path,
         [n in nodes(path) | n.name] as node_names,
         length(path) as path_length
    RETURN node_names, path_length
    ORDER BY path_length DESC
    LIMIT 10
    """

    results = graph_db.execute_cypher(complex_query)
    print(f"复杂调用模式 (找到 {len(results)} 条):")
    for result in results:
        print(f"  - 路径长度 {result['path_length']}: {' -> '.join(result['node_names'])}")

    # 2. 查找潜在的安全问题
    security_query = """
    MATCH (source:Function)-[:TAINT_FLOW_TO]->(sink:Function)
    WHERE source.qualified_name CONTAINS 'input'
      AND (sink.qualified_name CONTAINS 'query' OR sink.qualified_name CONTAINS 'execute')
    RETURN source.name as source, sink.name as sink,
           sink.qualified_name as sink_qualified
    """

    results = graph_db.execute_cypher(security_query)
    print(f"\n潜在安全问题 (找到 {len(results)} 个):")
    for result in results:
        print(f"  - {result['source']} -> {result['sink']} ({result['sink_qualified']})")

    return True


def cleanup_example_data(graph_db):
    """清理示例数据"""
    print("\n=== 清理示例数据 ===")

    # 删除特定项目的数据
    graph_db.execute_cypher("""
        MATCH (p:Project {name: 'example-project'})
        DETACH DELETE p
    """)

    # 删除事务测试数据
    graph_db.execute_cypher("""
        MATCH (p:Project {name: 'transaction-project'})
        DETACH DELETE p
    """)

    print("示例数据已清理")

    return True


def main():
    """主函数：运行所有示例"""
    graph_db = None

    try:
        # 1. 设置连接
        print("正在连接到 Neo4j 数据库...")
        graph_db = setup_neo4j_connection()
        print("连接成功！")

        # 2. 创建节点
        example_create_nodes(graph_db)

        # 3. 创建关系
        example_create_relationships(graph_db)

        # 4. 查询操作
        example_query_operations(graph_db)

        # 5. 图统计
        example_graph_stats(graph_db)

        # 6. 子图操作
        example_subgraph_operations(graph_db)

        # 7. 原生 Cypher 查询
        example_cypher_query(graph_db)

        # 8. 事务操作
        example_transaction_operations(graph_db)

        # 9. 高级查询
        example_advanced_queries(graph_db)

        # 10. 清理数据（可选）
        # cleanup_example_data(graph_db)

        print("\n=== 所有示例执行完成 ===")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if graph_db:
            # 关闭连接
            graph_db.close()
            print("数据库连接已关闭")


if __name__ == "__main__":
    main()