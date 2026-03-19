#!/usr/bin/env python3
"""
Code-OmniGraph Neo4j 本地示例
使用本地 Neo4j 数据库配置
"""

import os
import sys
from pathlib import Path

# 设置正确的 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 直接导入具体模块，避免通过 __init__.py
sys.path.insert(0, str(project_root / "core"))

# 直接导入需要的类
from cagr_processor.graph_builder.config import GraphDBConfig, Neo4jConfig
from cagr_processor.graph_builder.factory import GraphDBFactory
from cagr_processor.graph_builder.models import (
    ProjectNode, FileNode, ClassNode, FunctionNode
)
from cagr_processor.graph_builder.impl.neo4j_impl import Neo4jDatabase


def main():
    """主函数 - 本地示例"""
    print("=== Code-OmniGraph Neo4j 本地示例 ===\n")

    # 使用本地 Neo4j 配置
    print("1. 创建本地 Neo4j 配置...")
    neo4j_config = Neo4jConfig(
        uri="bolt://localhost:7687",
        username="neo4j",
        password="password"
    )
    config = GraphDBConfig(neo4j_config=neo4j_config)
    print(f"   Neo4j URI: {config.neo4j_config.uri}")
    print("   ✓ 配置创建成功")

    try:
        # 2. 直接创建 Neo4j 数据库实例
        print("\n2. 创建 Neo4j 数据库实例...")
        graph_db = Neo4jDatabase(config)
        print("   ✓ 实例创建成功")

        # 3. 连接数据库
        print("\n3. 连接到 Neo4j 数据库...")
        try:
            graph_db.connect()
            print("   ✓ 连接成功")
        except Exception as e:
            print(f"   ✗ 连接失败: {e}")
            print("\n请确保:")
            print("1. Neo4j 数据库正在运行")
            print("2. 使用正确的连接信息")
            print("3. 可以尝试使用 Docker 启动 Neo4j:")
            print("   docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:latest")
            return

        # 4. 创建示例数据
        print("\n4. 创建示例图谱数据...")

        # 创建项目
        project = ProjectNode(
            name="local-demo",
            language="java",
            version="1.0.0"
        )
        success = graph_db.create_project(project)
        print(f"   创建项目: {success}")

        # 创建文件
        file_node = FileNode(
            path="com/example/LocalService.java",
            name="LocalService.java",
            language="java",
            size=1024
        )
        success = graph_db.create_file(file_node)
        print(f"   创建文件: {success}")

        # 创建类
        class_node = ClassNode(
            qualified_name="com.example.LocalService",
            name="LocalService",
            start_line=1
        )
        success = graph_db.create_class(class_node)
        print(f"   创建类: {success}")

        # 创建函数
        function_node = FunctionNode(
            qualified_name="com.example.LocalService.processLocally",
            name="processLocally",
            signature="public String processLocally(String input)",
            return_type="String",
            start_line=10
        )
        success = graph_db.create_function(function_node)
        print(f"   创建函数: {success}")

        # 5. 创建关系
        print("\n5. 创建关系...")
        success = graph_db.create_project_contains_file("local-demo", "com/example/LocalService.java")
        print(f"   项目包含文件: {success}")

        success = graph_db.create_file_defines_class("com/example/LocalService.java", "com.example.LocalService")
        print(f"   文件定义类: {success}")

        success = graph_db.create_class_has_method("com.example.LocalService", "com.example.LocalService.processLocally")
        print(f"   类包含方法: {success}")

        # 6. 查询演示
        print("\n6. 查询演示...")

        # 查找函数
        function = graph_db.find_function_by_name("processLocally")
        if function:
            print(f"   ✓ 找到函数: {function.qualified_name}")

        # 获取图统计
        stats = graph_db.get_graph_stats()
        print(f"   ✓ 总节点数: {stats.total_nodes}")
        print(f"   ✓ 总关系数: {stats.total_relationships}")

        # 7. 使用原生 Cypher 查询
        print("\n7. Cypher 查询演示...")
        results = graph_db.execute_cypher("""
            MATCH (p:Project {name: 'local-demo'})-[:CONTAINS]->(f:File)
            RETURN p.name as project, f.name as file
        """)
        print("   项目文件关系:")
        for result in results:
            print(f"     {result['project']} -> {result['file']}")

        print("\n=== 本地示例完成 ===")
        print("✓ 所有操作执行成功！")

    except Exception as e:
        print(f"运行错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 关闭连接
        if 'graph_db' in locals():
            graph_db.close()
            print("\n✓ 数据库连接已关闭")


if __name__ == "__main__":
    main()