#!/usr/bin/env python3
"""
Code-OmniGraph Neo4j 最终示例
完全绕过模块导入问题，直接运行
"""

import os
import sys
from pathlib import Path

# 设置正确的 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 直接导入具体文件，完全绕过 __init__.py
sys.path.insert(0, str(project_root / "core"))

# 手动导入所有需要的模块
try:
    # 导入基础模块

    from cagr_common.exceptions import GraphConnectionException

    # 导入配置模块
    from cagr_processor.graph_builder.config import GraphDBConfig, Neo4jConfig

    # 导入模型
    from cagr_processor.graph_builder.models import (
        ProjectNode, FileNode, ClassNode, FunctionNode,
        CallRelationship, TaintFlowRelationship, DataAccessRelationship,
        NodeLabel, RelType, RiskLevel, GraphStats, SubGraph
    )

    # 导入工厂
    from cagr_processor.graph_builder.factory import GraphDBFactory

    # 导入 Neo4j 实现
    from cagr_processor.graph_builder.impl.neo4j_impl import Neo4jDatabase

    print("✓ 所有模块导入成功")

except ImportError as e:
    print(f"导入错误: {e}")
    print("正在尝试安装 neo4j 驱动...")
    os.system("pip install neo4j")
    print("请重新运行脚本")
    sys.exit(1)


def test_connection():
    """测试 Neo4j 连接"""
    print("\n=== 测试 Neo4j 连接 ===\n")

    # 使用本地配置
    neo4j_config = Neo4jConfig(
        uri="bolt://localhost:7687",
        username="neo4j",
        password="password"
    )
    config = GraphDBConfig(neo4j_config=neo4j_config)

    graph_db = None
    try:
        graph_db = Neo4jDatabase(config)
        graph_db.connect()
        print("✓ 成功连接到 Neo4j!")
        return True
    except GraphConnectionException as e:
        print(f"✗ 连接失败: {e}")
        print("\n请确保 Neo4j 正在运行。可以使用以下命令启动:")
        print("docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:latest")
        return False
    finally:
        if graph_db:
            graph_db.close()


def create_demo_graph():
    """创建演示图谱"""
    print("\n=== 创建演示图谱 ===\n")

    # 使用本地配置
    neo4j_config = Neo4jConfig(
        uri="bolt://localhost:7687",
        username="neo4j",
        password="password"
    )
    config = GraphDBConfig(neo4j_config=neo4j_config)

    graph_db = Neo4jDatabase(config)

    try:
        graph_db.connect()
        print("✓ 连接到 Neo4j")

        # 清空现有数据
        try:
            graph_db.clear_graph()
            print("✓ 清空现有图谱")
        except Exception as e:
            print(f"⚠ 清空失败: {e}")

        # 创建项目
        project = ProjectNode(
            name="demo-project",
            language="java",
            version="1.0.0"
        )
        graph_db.create_project(project)
        print("✓ 创建项目节点")

        # 创建文件
        files = [
            FileNode(path="com/example/UserController.java", name="UserController.java", language="java"),
            FileNode(path="com/example/UserService.java", name="UserService.java", language="java"),
            FileNode(path="com/example/UserRepository.java", name="UserRepository.java", language="java")
        ]

        for file_node in files:
            graph_db.create_file(file_node)
        print("✓ 创建文件节点")

        # 创建类
        classes = [
            ClassNode(qualified_name="com.example.UserController", name="UserController"),
            ClassNode(qualified_name="com.example.UserService", name="UserService"),
            ClassNode(qualified_name="com.example.UserRepository", name="UserRepository")
        ]

        for class_node in classes:
            graph_db.create_class(class_node)
        print("✓ 创建类节点")

        # 创建函数
        functions = [
            FunctionNode(
                qualified_name="com.example.UserController.getUser",
                name="getUser",
                signature="public User getUser(Long id)",
                return_type="User"
            ),
            FunctionNode(
                qualified_name="com.example.UserService.findUser",
                name="findUser",
                signature="public User findUser(Long id)",
                return_type="User"
            ),
            FunctionNode(
                qualified_name="com.example.UserRepository.findById",
                name="findById",
                signature="public Optional<User> findById(Long id)",
                return_type="Optional<User>"
            )
        ]

        for function_node in functions:
            graph_db.create_function(function_node)
        print("✓ 创建函数节点")

        # 创建关系
        # 项目包含文件
        for file_node in files:
            graph_db.create_project_contains_file("demo-project", file_node.path)

        # 文件定义类
        for i, (file_node, class_node) in enumerate(zip(files, classes)):
            graph_db.create_file_defines_class(file_node.path, class_node.qualified_name)

        # 类包含方法
        graph_db.create_class_has_method("com.example.UserController", "com.example.UserController.getUser")
        graph_db.create_class_has_method("com.example.UserService", "com.example.UserService.findUser")
        graph_db.create_class_has_method("com.example.UserRepository", "com.example.UserRepository.findById")

        # 创建调用关系
        call1 = CallRelationship(
            caller_qualified_name="com.example.UserController.getUser",
            callee_qualified_name="com.example.UserService.findUser",
            call_site_line=20
        )
        graph_db.create_calls_relationship(call1)

        call2 = CallRelationship(
            caller_qualified_name="com.example.UserService.findUser",
            callee_qualified_name="com.example.UserRepository.findById",
            call_site_line=15
        )
        graph_db.create_calls_relationship(call2)

        print("✓ 创建关系")

        return True

    except Exception as e:
        print(f"✗ 创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        graph_db.close()


def query_demo_graph():
    """查询演示图谱"""
    print("\n=== 查询演示图谱 ===\n")

    neo4j_config = Neo4jConfig(
        uri="bolt://localhost:7687",
        username="neo4j",
        password="password"
    )
    config = GraphDBConfig(neo4j_config=neo4j_config)

    graph_db = Neo4jDatabase(config)

    try:
        graph_db.connect()
        print("✓ 连接到 Neo4j")

        # 获取图统计
        stats = graph_db.get_graph_stats()
        print(f"\n📊 图谱统计:")
        print(f"   总节点数: {stats.total_nodes}")
        print(f"   总关系数: {stats.total_relationships}")
        print(f"   项目数: {stats.node_counts.get('projects', 0)}")
        print(f"   文件数: {stats.node_counts.get('files', 0)}")
        print(f"   类数: {stats.node_counts.get('classes', 0)}")
        print(f"   函数数: {stats.node_counts.get('functions', 0)}")

        # 查找函数
        function = graph_db.find_function_by_name("getUser")
        if function:
            print(f"\n🔍 找到函数: {function.qualified_name}")

        # 获取调用链
        chains = graph_db.get_call_chain("com.example.UserController.getUser", depth=3)
        print(f"\n🔗 调用链 ({len(chains)} 条):")
        for chain in chains:
            chain_names = [node['name'] for node in chain]
            print(f"   {' -> '.join(chain_names)}")

        # 获取上游调用者
        callers = graph_db.get_upstream_callers("com.example.UserService.findUser", depth=1)
        print(f"\n⬆️  上游调用者 ({len(callers)} 个):")
        for caller in callers:
            print(f"   {caller['qualified_name']}")

        # 获取下游被调用者
        callees = graph_db.get_downstream_callees("com.example.UserController.getUser", depth=1)
        print(f"\n⬇️  下游被调用者 ({len(callees)} 个):")
        for callee in callees:
            print(f"   {callee['qualified_name']}")

        # 执行 Cypher 查询
        print(f"\n📝 Cypher 查询结果:")
        results = graph_db.execute_cypher("""
            MATCH (c:Class)-[:HAS_METHOD]->(f:Function)
            WHERE c.name IN ['UserController', 'UserService', 'UserRepository']
            RETURN c.name as class, collect(f.name) as methods
            ORDER BY c.name
        """)

        for result in results:
            print(f"   {result['class']} 包含方法: {', '.join(result['methods'])}")

        return True

    except Exception as e:
        print(f"✗ 查询失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        graph_db.close()


def advanced_security_analysis():
    """高级安全分析演示"""
    print("\n=== 安全分析演示 ===\n")

    neo4j_config = Neo4jConfig(
        uri="bolt://localhost:7687",
        username="neo4j",
        password="password"
    )
    config = GraphDBConfig(neo4j_config=neo4j_config)

    graph_db = Neo4jDatabase(config)

    try:
        graph_db.connect()
        print("✓ 连接到 Neo4j")

        # 创建安全相关的函数
        security_functions = [
            FunctionNode(
                qualified_name="com.example.UserController.processUserInput",
                name="processUserInput",
                signature="public String processUserInput(String userInput)",
                return_type="String"
            ),
            FunctionNode(
                qualified_name="com.example.UserService.buildQuery",
                name="buildQuery",
                signature="public String buildQuery(String condition)",
                return_type="String"
            ),
            FunctionNode(
                qualified_name="com.example.UserRepository.executeSql",
                name="executeSql",
                signature="public Result executeSql(String sql)",
                return_type="Result"
            )
        ]

        for func in security_functions:
            graph_db.create_function(func)

        # 创建污点流关系（模拟 SQL 注入路径）
        taint_flow = TaintFlowRelationship(
            source_qualified_name="com.example.UserController.processUserInput",
            sink_qualified_name="com.example.UserRepository.executeSql",
            risk=RiskLevel.HIGH,
            vulnerability_type="SQL_INJECTION",
            taint_path=["user_input", "query_builder", "sql_execution"]
        )
        graph_db.create_taint_flow_relationship(taint_flow)

        print("✓ 创建安全分析数据")

        # 查找危险路径
        vulnerable_paths = graph_db.find_vulnerable_paths("executeSql")
        print(f"\n⚠️  发现 {len(vulnerable_paths)} 条危险路径到 executeSql:")
        for path in vulnerable_paths:
            path_names = [node['name'] for node in path]
            print(f"   {' -> '.join(path_names)}")

        # 查找污点流
        taint_flows = graph_db.find_taint_flows(
            sink_function="executeSql",
            risk_level="HIGH",
            limit=10
        )
        print(f"\n🔍 发现 {len(taint_flows)} 个高危污点流")

        return True

    except Exception as e:
        print(f"✗ 安全分析失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        graph_db.close()


def main():
    """主函数"""
    print("🚀 Code-OmniGraph Neo4j 最终示例")
    print("=" * 50)

    # 1. 测试连接
    if not test_connection():
        return

    # 2. 创建演示图谱
    if not create_demo_graph():
        return

    # 3. 查询演示图谱
    if not query_demo_graph():
        return

    # 4. 高级安全分析
    if not advanced_security_analysis():
        return

    print("\n" + "=" * 50)
    print("🎉 所有示例执行成功！")
    print("\n您现在可以:")
    print("1. 打开 Neo4j Browser (http://localhost:7474)")
    print("2. 查看创建的图谱数据")
    print("3. 运行自定义 Cypher 查询")
    print("4. 探索更多图数据库功能")


if __name__ == "__main__":
    main()