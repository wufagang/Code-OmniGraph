#!/usr/bin/env python3
"""
Code-OmniGraph Neo4j 简化示例
绕过模块导入问题，直接演示功能
"""

import os
import sys
from pathlib import Path

# 将 core 目录添加到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入必要的模块
from cagr_processor.graph_dao.config import GraphDBConfig
from cagr_processor.graph_dao.factory import GraphDBFactory
from cagr_processor.graph_dao.models import (
    ProjectNode, FileNode, ClassNode, FunctionNode
)


def main():
    """主函数 - 简化示例"""
    print("=== Code-OmniGraph Neo4j 简化示例 ===\n")

    try:
        # 1. 创建配置
        print("1. 创建图数据库配置...")
        config = GraphDBConfig.from_env()
        print(f"   Neo4j URI: {config.neo4j_config.uri}")
        print("   ✓ 配置创建成功")

        # 2. 创建数据库实例
        print("\n2. 创建图数据库实例...")
        graph_db = GraphDBFactory.create(config)
        print("   ✓ 实例创建成功")

        # 3. 连接数据库
        print("\n3. 连接到 Neo4j 数据库...")
        graph_db.connect()
        print("   ✓ 连接成功")

        # 4. 创建示例数据
        print("\n4. 创建示例图谱数据...")

        # 创建项目
        project = ProjectNode(
            name="simple-demo",
            language="java",
            version="1.0.0"
        )
        success = graph_db.create_project(project)
        print(f"   创建项目: {success}")

        # 创建文件
        file_node = FileNode(
            path="com/example/SimpleService.java",
            name="SimpleService.java",
            language="java",
            size=512
        )
        success = graph_db.create_file(file_node)
        print(f"   创建文件: {success}")

        # 创建类
        class_node = ClassNode(
            qualified_name="com.example.SimpleService",
            name="SimpleService",
            start_line=1
        )
        success = graph_db.create_class(class_node)
        print(f"   创建类: {success}")

        # 创建函数
        function_node = FunctionNode(
            qualified_name="com.example.SimpleService.processData",
            name="processData",
            signature="public String processData(String input)",
            return_type="String",
            start_line=10
        )
        success = graph_db.create_function(function_node)
        print(f"   创建函数: {success}")

        # 创建关系
        print("\n5. 创建关系...")
        success = graph_db.create_project_contains_file("simple-demo", "com/example/SimpleService.java")
        print(f"   项目包含文件: {success}")

        success = graph_db.create_file_defines_class("com/example/SimpleService.java", "com.example.SimpleService")
        print(f"   文件定义类: {success}")

        success = graph_db.create_class_has_method("com.example.SimpleService", "com.example.SimpleService.processData")
        print(f"   类包含方法: {success}")

        # 5. 查询演示
        print("\n6. 查询演示...")

        # 查找函数
        function = graph_db.find_function_by_name("processData")
        if function:
            print(f"   ✓ 找到函数: {function.qualified_name}")

        # 获取图统计
        stats = graph_db.get_graph_stats()
        print(f"   ✓ 总节点数: {stats.total_nodes}")
        print(f"   ✓ 总关系数: {stats.total_relationships}")

        # 6. 使用原生 Cypher 查询
        print("\n7. Cypher 查询演示...")
        results = graph_db.execute_cypher("""
            MATCH (p:Project {name: 'simple-demo'})-[:CONTAINS]->(f:File)
            RETURN p.name as project, f.name as file
        """)
        print("   项目文件关系:")
        for result in results:
            print(f"     {result['project']} -> {result['file']}")

        print("\n=== 简化示例完成 ===")
        print("✓ 所有操作执行成功！")

    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保已安装 neo4j 驱动: pip install neo4j")

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