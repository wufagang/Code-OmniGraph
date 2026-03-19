#!/usr/bin/env python3
"""
Code-OmniGraph Neo4j 图数据库快速入门示例
展示最常用的图数据库操作（通过 CodeGraphService 业务层）
"""

import os
import sys

# 将 core 目录添加到 Python 路径
current_file = os.path.abspath(__file__)
core_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file))))
sys.path.insert(0, core_dir)

from cagr_processor.graph_dao.config import GraphDBConfig
from cagr_processor.graph_dao.factory import GraphDBFactory
from cagr_processor.graph_dao.models import (
    ProjectNode, FileNode, ClassNode, FunctionNode,
    TaintFlowRelationship, RiskLevel
)
from cagr_processor.graph_service import CodeGraphService


def quick_start_example():
    """快速入门示例"""
    print("=== Code-OmniGraph Neo4j 快速入门 ===\n")

    # 1. 创建图数据库配置
    config = GraphDBConfig.from_env()

    # 2. 创建 DB 层实例，再包装为业务层服务
    graph_db = GraphDBFactory.create(config)
    service = CodeGraphService(graph_db)

    print("✓ 成功连接到 Neo4j 数据库\n")

    try:
        # 3. 创建一个简单的代码知识图谱（通过业务层）
        print("正在创建示例代码图谱...")

        service.create_project(ProjectNode(
            name="demo-app",
            language="java",
            version="1.0.0"
        ))

        service.create_file(FileNode(
            path="com/example/UserController.java",
            name="UserController.java",
            language="java"
        ))

        service.create_class(ClassNode(
            qualified_name="com.example.UserController",
            name="UserController"
        ))

        service.create_function(FunctionNode(
            qualified_name="com.example.UserController.getUser",
            name="getUser",
            signature="public User getUser(Long id)",
            return_type="User"
        ))

        # 创建关系
        service.create_project_contains_file("demo-app", "com/example/UserController.java")
        service.create_file_defines_class("com/example/UserController.java", "com.example.UserController")
        service.create_class_has_method("com.example.UserController", "com.example.UserController.getUser")

        print("✓ 图谱创建完成\n")

        # 4. 查询操作（通过业务层）
        print("=== 查询演示 ===")

        function = service.find_function_by_name("getUser")
        if function:
            print(f"✓ 找到函数: {function.qualified_name}")

        chains = service.get_call_chain("com.example.UserController.getUser", depth=2)
        print(f"✓ 调用链数量: {len(chains)}")

        stats = service.get_graph_stats()
        print(f"✓ 总节点数: {stats.total_nodes}")
        print(f"✓ 总关系数: {stats.total_relationships}")

        # 5. 安全分析
        print("\n=== 安全分析演示 ===")

        service.create_taint_flow_relationship(TaintFlowRelationship(
            source_qualified_name="com.example.UserController.getUserInput",
            sink_qualified_name="com.example.UserController.executeQuery",
            risk=RiskLevel.HIGH,
            vulnerability_type="SQL_INJECTION"
        ))

        vulnerable_paths = service.find_vulnerable_paths("executeQuery")
        print(f"✓ 发现 {len(vulnerable_paths)} 条危险路径")

        # 6. 原生 Cypher 查询（通过 DB 层逃生舱口）
        print("\n=== Cypher 查询演示 ===")

        results = graph_db.execute_cypher("""
            MATCH (p:Project)-[:CONTAINS]->(f:File)-[:DEFINES]->(c:Class)-[:HAS_METHOD]->(m:Function)
            RETURN p.name as project, f.name as file, c.name as class, m.name as method
            LIMIT 10
        """)

        print("项目结构:")
        for result in results:
            print(f"  {result['project']} -> {result['file']} -> {result['class']}.{result['method']}")

        print("\n=== 快速入门完成 ===")

    finally:
        graph_db.close()
        print("\n✓ 数据库连接已关闭")


if __name__ == "__main__":
    quick_start_example()
