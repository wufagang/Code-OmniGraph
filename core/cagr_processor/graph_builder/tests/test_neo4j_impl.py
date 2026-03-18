"""Neo4j 图数据库实现测试"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from core.cagr_processor.graph_builder import GraphDBConfig, Neo4jConfig, Neo4jDatabase
from core.cagr_processor.graph_builder.models import (
    ProjectNode, FileNode, ClassNode, FunctionNode,
    CallRelationship, TaintFlowRelationship, RiskLevel
)


class TestNeo4jDatabase(unittest.TestCase):
    """Neo4j 数据库测试类"""

    def setUp(self):
        """测试前准备"""
        self.config = GraphDBConfig(
            db_type="neo4j",
            neo4j_config=Neo4jConfig(
                uri="bolt://localhost:7687",
                username="neo4j",
                password="password"
            )
        )

    @patch('core.cagr_processor.graph_builder.impl.neo4j_impl.Neo4jDriver')
    def test_connect_success(self, mock_driver_class):
        """测试连接成功"""
        # 模拟驱动实例
        mock_driver = Mock()
        mock_session = Mock()
        mock_result = Mock()
        mock_result.single.return_value = [1]
        mock_session.run.return_value = mock_result
        mock_driver.session.return_value = mock_session
        mock_driver_class.return_value = mock_driver

        # 创建数据库实例并连接
        db = Neo4jDatabase(self.config)
        db.connect()

        # 验证
        mock_driver_class.assert_called_once()
        self.assertIsNotNone(db._driver)

    @patch('core.cagr_processor.graph_builder.impl.neo4j_impl.Neo4jDriver')
    def test_create_project(self, mock_driver_class):
        """测试创建项目节点"""
        # 模拟驱动和会话
        mock_driver = Mock()
        mock_session = Mock()
        mock_result = Mock()
        mock_result.single.return_value = True
        mock_session.run.return_value = mock_result
        mock_driver.session.return_value = mock_session
        mock_driver_class.return_value = mock_driver

        # 创建数据库实例
        db = Neo4jDatabase(self.config)
        db._driver = mock_driver

        # 创建项目节点
        project = ProjectNode(name="test-project", version="1.0.0")
        result = db.create_project(project)

        # 验证
        self.assertTrue(result)
        mock_session.run.assert_called()

    @patch('core.cagr_processor.graph_builder.impl.neo4j_impl.Neo4jDriver')
    def test_create_function(self, mock_driver_class):
        """测试创建函数节点"""
        # 模拟驱动和会话
        mock_driver = Mock()
        mock_session = Mock()
        mock_result = Mock()
        mock_result.single.return_value = True
        mock_session.run.return_value = mock_result
        mock_driver.session.return_value = mock_session
        mock_driver_class.return_value = mock_driver

        # 创建数据库实例
        db = Neo4jDatabase(self.config)
        db._driver = mock_driver

        # 创建函数节点
        function = FunctionNode(
            qualified_name="com.example.Test#testMethod",
            name="testMethod",
            signature="void testMethod()",
            body="System.out.println(\"test\");",
            is_endpoint=True
        )
        result = db.create_function(function)

        # 验证
        self.assertTrue(result)
        mock_session.run.assert_called()

    @patch('core.cagr_processor.graph_builder.impl.neo4j_impl.Neo4jDriver')
    def test_create_calls_relationship(self, mock_driver_class):
        """测试创建调用关系"""
        # 模拟驱动和会话
        mock_driver = Mock()
        mock_session = Mock()
        mock_result = Mock()
        mock_result.single.return_value = True
        mock_session.run.return_value = mock_result
        mock_driver.session.return_value = mock_session
        mock_driver_class.return_value = mock_driver

        # 创建数据库实例
        db = Neo4jDatabase(self.config)
        db._driver = mock_driver

        # 创建调用关系
        call = CallRelationship(
            caller_qualified_name="com.example.Main#main",
            callee_qualified_name="com.example.Test#testMethod",
            call_site_line=42
        )
        result = db.create_calls_relationship(call)

        # 验证
        self.assertTrue(result)
        mock_session.run.assert_called()

    @patch('core.cagr_processor.graph_builder.impl.neo4j_impl.Neo4jDriver')
    def test_find_function_by_qualified_name(self, mock_driver_class):
        """测试根据全限定名查找函数"""
        # 模拟驱动和会话
        mock_driver = Mock()
        mock_session = Mock()
        mock_result = Mock()
        mock_record = Mock()
        mock_record.__getitem__.return_value = {
            "qualified_name": "com.example.Test#testMethod",
            "name": "testMethod",
            "signature": "void testMethod()",
            "body": "System.out.println(\"test\");",
            "is_endpoint": True
        }
        mock_result.single.return_value = mock_record
        mock_session.run.return_value = mock_result
        mock_driver.session.return_value = mock_session
        mock_driver_class.return_value = mock_driver

        # 创建数据库实例
        db = Neo4jDatabase(self.config)
        db._driver = mock_driver

        # 查找函数
        result = db.find_function_by_qualified_name("com.example.Test#testMethod")

        # 验证
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "testMethod")
        self.assertTrue(result.is_endpoint)

    @patch('core.cagr_processor.graph_builder.impl.neo4j_impl.Neo4jDriver')
    def test_find_taint_flows(self, mock_driver_class):
        """测试查找污点流"""
        # 模拟驱动和会话
        mock_driver = Mock()
        mock_session = Mock()
        mock_result = Mock()
        mock_record = Mock()
        mock_record.__getitem__.side_effect = lambda key: {
            "source": {"qualified_name": "com.example.Input#getData"},
            "r": {"risk": "High", "vulnerability_type": "SQL_INJECTION"}
        }[key]
        mock_result.__iter__.return_value = [mock_record]
        mock_session.run.return_value = mock_result
        mock_driver.session.return_value = mock_session
        mock_driver_class.return_value = mock_driver

        # 创建数据库实例
        db = Neo4jDatabase(self.config)
        db._driver = mock_driver

        # 查找污点流
        result = db.find_taint_flows(risk_level="High")

        # 验证
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].risk, RiskLevel.HIGH)
        self.assertEqual(result[0].vulnerability_type, "SQL_INJECTION")

    @patch('core.cagr_processor.graph_builder.impl.neo4j_impl.Neo4jDriver')
    def test_get_subgraph_for_function(self, mock_driver_class):
        """测试获取函数子图"""
        # 模拟驱动和会话
        mock_driver = Mock()
        mock_session = Mock()

        # 模拟多个查询结果
        def mock_run_side_effect(query, params):
            mock_result = Mock()
            if "MATCH (f:Function" in query and "RETURN f" in query:
                # 中心节点查询
                mock_record = Mock()
                mock_record.__getitem__.return_value = {
                    "qualified_name": "com.example.Test#testMethod",
                    "name": "testMethod",
                    "is_endpoint": True
                }
                mock_result.single.return_value = mock_record
            else:
                # 其他查询（上游、下游、污点流）
                mock_result.__iter__.return_value = []
                mock_result.single.return_value = None
            return mock_result

        mock_session.run.side_effect = mock_run_side_effect
        mock_driver.session.return_value = mock_session
        mock_driver_class.return_value = mock_driver

        # 创建数据库实例
        db = Neo4jDatabase(self.config)
        db._driver = mock_driver

        # 获取子图
        result = db.get_subgraph_for_function("com.example.Test#testMethod")

        # 验证
        self.assertIsNotNone(result)
        self.assertEqual(result.center_node["name"], "testMethod")

    def test_connection_exception(self):
        """测试连接异常"""
        db = Neo4jDatabase(self.config)

        # 测试未连接时的操作
        with self.assertRaises(Exception):
            db.create_project(ProjectNode(name="test"))

    @patch('core.cagr_processor.graph_builder.impl.neo4j_impl.Neo4jDriver')
    def test_execute_cypher(self, mock_driver_class):
        """测试执行原生 Cypher 查询"""
        # 模拟驱动和会话
        mock_driver = Mock()
        mock_session = Mock()
        mock_result = Mock()
        mock_record = Mock()
        mock_record.__dict__ = {"prop": "value"}
        mock_result.__iter__.return_value = [mock_record]
        mock_session.run.return_value = mock_result
        mock_driver.session.return_value = mock_session
        mock_driver_class.return_value = mock_driver

        # 创建数据库实例
        db = Neo4jDatabase(self.config)
        db._driver = mock_driver

        # 执行查询
        result = db.execute_cypher("MATCH (n) RETURN n LIMIT 1")

        # 验证
        self.assertEqual(len(result), 1)
        mock_session.run.assert_called_with("MATCH (n) RETURN n LIMIT 1", {})


if __name__ == '__main__':
    unittest.main()