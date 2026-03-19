#!/usr/bin/env python3
"""
Code-OmniGraph Neo4j 图数据库快速入门示例
展示最常用的图数据库操作
"""

import os
import sys
from datetime import datetime

# 将项目根目录添加到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, project_root)

from core.cagr_processor.graph_builder.config import GraphDBConfig
from core.cagr_processor.graph_builder.factory import GraphDBFactory
from core.cagr_processor.graph_builder.models import (
    ProjectNode, FileNode, ClassNode, FunctionNode,
    CallRelationship, TaintFlowRelationship, RiskLevel
)
from core.cagr_common.models import CodeLocation


def quick_start_example():
    """快速入门示例"""
    print("=== Code-OmniGraph Neo4j 快速入门 ===\n")

    # 1. 创建图数据库配置
    config = GraphDBConfig.from_env()

    # 2. 创建图数据库实例
    graph_db = GraphDBFactory.create(config)

    # 3. 连接到数据库
    graph_db.connect()
    print("✓ 成功连接到 Neo4j 数据库\n")

    try:
        # 4. 创建一个简单的代码知识图谱
        print("正在创建示例代码图谱...")

        # 创建项目
        project = ProjectNode(
            name="demo-app",
            description="演示应用",
            language="java",
            version="1.0.0"
        )
        graph_db.create_project(project)

        # 创建文件
        file_node = FileNode(
            path="com/example/UserController.java",
            name="UserController.java",
            language="java"
        )
        graph_db.create_file(file_node)

        # 创建类
        class_node = ClassNode(
            qualified_name="com.example.UserController",
            name="UserController",
            type="class"
        )
        graph_db.create_class(class_node)

        # 创建函数
        function_node = FunctionNode(
            qualified_name="com.example.UserController.getUser",
            name="getUser",
            signature="public User getUser(Long id)",
            return_type="User"
        )
        graph_db.create_function(function_node)

        # 创建关系
        graph_db.create_project_contains_file("demo-app", "com/example/UserController.java")
        graph_db.create_file_defines_class("com/example/UserController.java", "com.example.UserController")
        graph_db.create_class_has_method("com.example.UserController", "com.example.UserController.getUser")

        print("✓ 图谱创建完成\n")

        # 5. 查询操作
        print("=== 查询演示 ===")

        # 查找函数
        function = graph_db.find_function_by_name("getUser")
        if function:
            print(f"✓ 找到函数: {function.qualified_name}")

        # 获取调用链
        chains = graph_db.get_call_chain("com.example.UserController.getUser", depth=2)
        print(f"✓ 调用链数量: {len(chains)}")

        # 获取图统计
        stats = graph_db.get_graph_stats()
        print(f"✓ 总节点数: {stats.total_nodes}")
        print(f"✓ 总关系数: {stats.total_relationships}")

        # 6. 高级查询：查找安全漏洞路径
        print("\n=== 安全分析演示 ===")

        # 创建一些污点流示例
        taint_flow = TaintFlowRelationship(
            source_qualified_name="com.example.UserController.getUserInput",
            sink_qualified_name="com.example.UserController.executeQuery",
            risk_level=RiskLevel.HIGH,
            taint_type="sql_injection"
        )
        graph_db.create_taint_flow_relationship(taint_flow)

        # 查找危险路径
        vulnerable_paths = graph_db.find_vulnerable_paths("executeQuery")
        print(f"✓ 发现 {len(vulnerable_paths)} 条危险路径")

        # 7. 使用原生 Cypher 查询
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
        # 8. 关闭连接
        graph_db.close()
        print("\n✓ 数据库连接已关闭")


if __name__ == "__main__":
    quick_start_example()