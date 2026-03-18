"""
图数据库使用示例 - 简化版本

演示如何使用 graph_builder 模块构建代码图谱
由于 Neo4jDatabase 是抽象类，这里使用 mock 实现进行演示
"""

import os
import sys
import logging
from unittest.mock import Mock, patch

# 添加项目路径 - 从example目录到core根目录
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from cagr_processor.graph_builder import GraphDBConfig, Neo4jConfig
from cagr_processor.graph_builder.models import (
    ProjectNode, FileNode, ClassNode, FunctionNode,
    CallRelationship, TaintFlowRelationship, RiskLevel
)


def create_mock_graph_db():
    """创建模拟的图数据库实例"""
    # 创建模拟数据库
    mock_db = Mock()

    # 模拟基本方法
    mock_db.create_project.return_value = True
    mock_db.create_file.return_value = True
    mock_db.create_class.return_value = True
    mock_db.create_function.return_value = True
    mock_db.create_project_contains_file.return_value = True
    mock_db.create_file_defines_class.return_value = True
    mock_db.create_file_defines_function.return_value = True
    mock_db.create_class_has_method.return_value = True
    mock_db.create_calls_relationship.return_value = True
    mock_db.create_taint_flow_relationship.return_value = True
    mock_db.find_function_by_name.return_value = None
    mock_db.get_graph_stats.return_value = Mock(
        total_nodes=10,
        total_relationships=15,
        node_counts={"Project": 1, "File": 2, "Class": 3, "Function": 4}
    )

    return mock_db


def demo_graph_building():
    """演示图构建流程"""
    print("="*60)
    print("图数据库使用示例 - 简化版本")
    print("="*60)

    # 1. 创建配置
    print("\n1. 创建图数据库配置...")
    config = GraphDBConfig(
        db_type="neo4j",
        neo4j_config=Neo4jConfig(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="password"
        )
    )
    print("✓ 配置创建完成")

    # 2. 创建模拟数据库
    print("\n2. 创建模拟图数据库实例...")
    graph_db = create_mock_graph_db()
    print("✓ 模拟数据库创建完成")

    # 3. 创建项目节点
    print("\n3. 创建项目节点...")
    project = ProjectNode(
        name="DemoProject",
        version="1.0.0",
        language="python",
        path="/path/to/project"
    )
    graph_db.create_project(project)
    print(f"✓ 创建项目: {project.name}")

    # 4. 创建文件节点
    print("\n4. 创建文件节点...")
    file1 = FileNode(
        path="src/main.py",
        name="main.py",
        language="python",
        content="def main(): print('Hello')",
        size=30
    )
    file2 = FileNode(
        path="src/utils.py",
        name="utils.py",
        language="python",
        content="class Utils: pass",
        size=50
    )
    graph_db.create_file(file1)
    graph_db.create_file(file2)
    print("✓ 创建文件节点")

    # 5. 创建类节点
    print("\n5. 创建类节点...")
    class1 = ClassNode(
        qualified_name="src/utils.py:Utils",
        name="Utils",
        file_path="src/utils.py",
        docstring="工具类",
        is_interface=False,
        is_abstract=False,
        start_line=1,
        end_line=10
    )
    graph_db.create_class(class1)
    print(f"✓ 创建类: {class1.name}")

    # 6. 创建函数节点
    print("\n6. 创建函数节点...")
    func1 = FunctionNode(
        qualified_name="src/main.py:main",
        name="main",
        signature="def main()",
        body="def main(): print('Hello')",
        file_path="src/main.py",
        start_line=1,
        end_line=2,
        is_endpoint=True
    )
    func2 = FunctionNode(
        qualified_name="src/utils.py:Utils#helper",
        name="helper",
        signature="def helper(self)",
        body="def helper(self): return True",
        file_path="src/utils.py",
        class_name="Utils",
        start_line=5,
        end_line=7
    )
    graph_db.create_function(func1)
    graph_db.create_function(func2)
    print("✓ 创建函数节点")

    # 7. 创建关系
    print("\n7. 创建关系...")
    # 项目包含文件
    graph_db.create_project_contains_file(project.name, file1.path)
    graph_db.create_project_contains_file(project.name, file2.path)

    # 文件定义类
    graph_db.create_file_defines_class(file1.path, class1.qualified_name)

    # 文件定义函数
    graph_db.create_file_defines_function(file1.path, func1.qualified_name)
    graph_db.create_file_defines_function(file2.path, func2.qualified_name)

    # 类拥有方法
    graph_db.create_class_has_method(class1.qualified_name, func2.qualified_name)
    print("✓ 创建关系完成")

    # 8. 创建调用关系
    print("\n8. 创建调用关系...")
    call1 = CallRelationship(
        caller_qualified_name=func1.qualified_name,
        callee_qualified_name=func2.qualified_name,
        call_site_line=10
    )
    graph_db.create_calls_relationship(call1)
    print("✓ 创建调用关系")

    # 9. 创建污点流
    print("\n9. 创建污点流关系...")
    taint1 = TaintFlowRelationship(
        source_qualified_name=func1.qualified_name,
        sink_qualified_name=func2.qualified_name,
        risk=RiskLevel.HIGH,
        vulnerability_type="COMMAND_INJECTION",
        description="用户输入流向命令执行"
    )
    graph_db.create_taint_flow_relationship(taint1)
    print("✓ 创建污点流")

    # 10. 查询图谱
    print("\n10. 查询图谱统计...")
    stats = graph_db.get_graph_stats()
    print(f"图统计信息:")
    print(f"  总节点数: {stats.total_nodes}")
    print(f"  总关系数: {stats.total_relationships}")
    for node_type, count in stats.node_counts.items():
        print(f"  {node_type}: {count}")

    print("\n✓ 图构建演示完成!")


def demo_models():
    """演示模型使用"""
    print("\n" + "="*60)
    print("模型演示")
    print("="*60)

    # 创建项目模型
    project = ProjectNode(
        name="TestProject",
        version="1.0.0",
        language="java",
        path="/home/user/project"
    )
    print(f"项目模型: {project.name} ({project.language})")

    # 创建文件模型
    file_node = FileNode(
        path="src/main/java/com/example/Main.java",
        name="Main.java",
        language="java",
        content="public class Main { ... }",
        size=1024
    )
    print(f"文件模型: {file_node.name}")

    # 创建类模型
    class_node = ClassNode(
        qualified_name="com.example.Main",
        name="Main",
        file_path=file_node.path,
        docstring="主类",
        is_interface=False,
        is_abstract=False,
        start_line=10,
        end_line=50
    )
    print(f"类模型: {class_node.name}")

    # 创建函数模型
    func_node = FunctionNode(
        qualified_name="com.example.Main#main",
        name="main",
        signature="public static void main(String[] args)",
        body="System.out.println(\"Hello World\");",
        file_path=file_node.path,
        class_name=class_node.name,
        start_line=15,
        end_line=20,
        is_endpoint=True,
        is_constructor=False
    )
    print(f"函数模型: {func_node.name}")

    # 创建调用关系模型
    call_rel = CallRelationship(
        caller_qualified_name="com.example.Main#main",
        callee_qualified_name="com.example.Utils#helper",
        call_site_line=25
    )
    print(f"调用关系: {call_rel.caller_qualified_name} -> {call_rel.callee_qualified_name}")

    # 创建污点流模型
    taint_flow = TaintFlowRelationship(
        source_qualified_name="com.example.Main#getInput",
        sink_qualified_name="com.example.Database#executeQuery",
        risk=RiskLevel.HIGH,
        vulnerability_type="SQL_INJECTION",
        description="用户输入直接传入SQL查询"
    )
    print(f"污点流: {taint_flow.vulnerability_type} ({taint_flow.risk})")

    print("\n✓ 模型演示完成!")


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)

    print("图数据库使用示例 - 简化版本")
    print("="*60)
    print("注意：由于Neo4jDatabase是抽象类，这里使用模拟实现进行演示")
    print("="*60)

    # 演示模型使用
    demo_models()

    # 演示图构建流程
    demo_graph_building()

    print("\n" + "="*60)
    print("示例运行完成!")
    print("="*60)
    print("\n要运行完整版本，您需要:")
    print("1. 安装Neo4j数据库并启动服务")
    print("2. 完成Neo4jDatabase类的抽象方法实现")
    print("3. 替换模拟实现为真实的数据库连接")