#!/usr/bin/env python3
"""
Code-OmniGraph Neo4j 直接示例
绕过模块导入问题，直接导入具体模块
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
try:
    # 导入配置
    from cagr_processor.graph_dao.config import GraphDBConfig

    # 导入工厂
    from cagr_processor.graph_dao.factory import GraphDBFactory

    # 导入模型
    from cagr_processor.graph_dao.models import (
        ProjectNode, FileNode, ClassNode, FunctionNode
    )

    # 导入 Neo4j 实现
    from cagr_processor.graph_dao.impl.neo4j_impl import Neo4jDatabase

    print("✓ 所有模块导入成功")

except ImportError as e:
    print(f"导入错误: {e}")
    print("请检查模块路径和依赖")
    sys.exit(1)


def main():
    """主函数 - 直接示例"""
    print("\n=== Code-OmniGraph Neo4j 直接示例 ===\n")

    try:
        # 1. 创建配置
        print("1. 创建图数据库配置...")
        config = GraphDBConfig.from_env()
        print(f"   Neo4j URI: {config.neo4j_config.uri}")
        print("   ✓ 配置创建成功")

        # 2. 直接创建 Neo4j 数据库实例
        print("\n2. 创建 Neo4j 数据库实例...")
        graph_db = Neo4jDatabase(config)
        print("   ✓ 实例创建成功")

        # 3. 连接数据库
        print("\n3. 连接到 Neo4j 数据库...")
        graph_db.connect()
        print("   ✓ 连接成功")

        # 4. 清空现有数据（可选）
        print("\n4. 清空现有图谱数据...")
        try:
            graph_db.clear_graph()
            print("   ✓ 图谱已清空")
        except Exception as e:
            print(f"   ⚠ 清空失败（可能是权限问题）: {e}")

        # 5. 创建示例数据
        print("\n5. 创建示例图谱数据...")

        # 创建项目
        project = ProjectNode(
            name="direct-demo",
            language="java",
            version="1.0.0"
        )
        success = graph_db.create_project(project)
        print(f"   创建项目: {success}")

        # 创建文件
        file_node = FileNode(
            path="com/example/DirectService.java",
            name="DirectService.java",
            language="java",
            size=1024
        )
        success = graph_db.create_file(file_node)
        print(f"   创建文件: {success}")

        # 创建类
        class_node = ClassNode(
            qualified_name="com.example.DirectService",
            name="DirectService",
            start_line=1
        )
        success = graph_db.create_class(class_node)
        print(f"   创建类: {success}")

        # 创建函数
        function_node = FunctionNode(
            qualified_name="com.example.DirectService.processDirectly",
            name="processDirectly",
            signature="public String processDirectly(String input)",
            return_type="String",
            start_line=10
        )
        success = graph_db.create_function(function_node)
        print(f"   创建函数: {success}")

        # 6. 创建关系
        print("\n6. 创建关系...")
        success = graph_db.create_project_contains_file("direct-demo", "com/example/DirectService.java")
        print(f"   项目包含文件: {success}")

        success = graph_db.create_file_defines_class("com/example/DirectService.java", "com.example.DirectService")
        print(f"   文件定义类: {success}")

        success = graph_db.create_class_has_method("com.example.DirectService", "com.example.DirectService.processDirectly")
        print(f"   类包含方法: {success}")

        # 7. 查询演示
        print("\n7. 查询演示...")

        # 查找函数
        function = graph_db.find_function_by_name("processDirectly")
        if function:
            print(f"   ✓ 找到函数: {function.qualified_name}")

        # 获取图统计
        stats = graph_db.get_graph_stats()
        print(f"   ✓ 总节点数: {stats.total_nodes}")
        print(f"   ✓ 总关系数: {stats.total_relationships}")

        # 8. 使用原生 Cypher 查询
        print("\n8. Cypher 查询演示...")
        results = graph_db.execute_cypher("""
            MATCH (p:Project {name: 'direct-demo'})-[:CONTAINS]->(f:File)
            RETURN p.name as project, f.name as file
        """)
        print("   项目文件关系:")
        for result in results:
            print(f"     {result['project']} -> {result['file']}")

        print("\n=== 直接示例完成 ===")
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