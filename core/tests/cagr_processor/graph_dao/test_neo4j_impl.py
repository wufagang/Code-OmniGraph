"""Neo4j 图数据库实现测试（DB 层通用接口）"""

import pytest
import os
from unittest.mock import Mock, MagicMock, patch

from cagr_processor.graph_dao import GraphDBConfig, Neo4jConfig
from cagr_processor.graph_code.models import (
    ProjectNode, FileNode, ClassNode, FunctionNode,
    CallRelationship, TaintFlowRelationship, RiskLevel
)
from cagr_common.exceptions import GraphConfigException


class TestNeo4jDatabase:
    """Neo4j 数据库（DB 层）测试"""

    def setup_method(self):
        self.config = GraphDBConfig(
            db_type="neo4j",
            neo4j_config=Neo4jConfig(
                uri="bolt://localhost:7687",
                username="neo4j",
                password="password"
            )
        )

    def test_neo4j_database_abstract(self):
        """无法连接真实 Neo4j 时，工厂应抛出 GraphConfigException"""
        from cagr_processor.graph_dao.factory import GraphDBFactory
        with pytest.raises(GraphConfigException) as exc_info:
            GraphDBFactory.create(self.config)
        assert "Failed to create graph database instance" in str(exc_info.value)

    def test_factory_with_mock_implementation(self):
        """使用 Mock 实现通过工厂创建，验证通用 DB 接口契约"""
        from cagr_processor.graph_dao.interfaces import GraphDatabase
        from cagr_processor.graph_dao.factory import GraphDBFactory

        class MockGraphDatabase(GraphDatabase):
            """实现精简后的通用 DB 接口"""
            def __init__(self, config):
                self.config = config
                self.connected = False

            def connect(self):
                self.connected = True

            def close(self):
                self.connected = False

            def begin_transaction(self):
                return Mock()

            def commit(self, tx):
                pass

            def rollback(self, tx):
                pass

            def create_node(self, label, unique_key, properties):
                return True

            def find_node(self, label, key, value):
                return None

            def find_nodes(self, label, filters):
                return []

            def create_relationship(self, start_label, start_key, start_value,
                                    end_label, end_key, end_value, rel_type, properties):
                return True

            def execute_cypher(self, query, parameters=None):
                return []

            def get_stats(self):
                return {"total_nodes": 0, "total_relationships": 0}

            def clear_graph(self):
                pass

        GraphDBFactory.register("neo4j", MockGraphDatabase)
        try:
            db = GraphDBFactory.create(self.config)
            assert isinstance(db, MockGraphDatabase)
            assert db.config == self.config

            db.connect()
            assert db.connected is True

            # DB 层只有通用操作，不应该有业务方法
            assert not hasattr(db, 'create_project')
            assert not hasattr(db, 'find_function_by_name')
            assert hasattr(db, 'create_node')
            assert hasattr(db, 'create_relationship')
            assert hasattr(db, 'execute_cypher')
        finally:
            GraphDBFactory._registry.pop("neo4j", None)

    def test_neo4j_config_validation(self):
        """测试 Neo4j 配置验证"""
        config = Neo4jConfig(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="password"
        )
        assert config.uri == "bolt://localhost:7687"
        assert config.username == "neo4j"
        assert config.password == "password"

        config_default = Neo4jConfig()
        assert config_default.uri == "bolt://localhost:7687"
        assert config_default.username == "neo4j"
        assert config_default.max_connection_pool_size == 50

    def test_graph_db_config_from_env(self):
        """测试从环境变量加载配置"""
        from cagr_processor.graph_dao.config import GraphDBConfig

        env_vars = {
            "NEO4J_URI": "bolt://test:7687",
            "NEO4J_USERNAME": "testuser",
            "NEO4J_PASSWORD": "testpass",
            "GRAPH_DB_TYPE": "neo4j"
        }
        with patch.dict(os.environ, env_vars):
            config = GraphDBConfig.from_env()
            assert config.db_type == "neo4j"
            assert config.neo4j_config.uri == "bolt://test:7687"
            assert config.neo4j_config.username == "testuser"
            assert config.neo4j_config.password == "testpass"

    def test_connection_mock(self):
        """测试 Neo4j driver 导入"""
        try:
            from neo4j import GraphDatabase as Neo4jDriver
            assert hasattr(Neo4jDriver, 'driver')
        except ImportError:
            pytest.skip("Neo4j driver not installed")

    def test_models_creation(self):
        """测试领域模型创建"""
        project = ProjectNode(name="TestProject", version="1.0.0", language="java")
        assert project.name == "TestProject"
        assert project.version == "1.0.0"

        function = FunctionNode(
            qualified_name="com.example.Test#main",
            name="main",
            return_type="void",
            signature="main(String[] args)",
            is_endpoint=True
        )
        assert function.qualified_name == "com.example.Test#main"
        assert function.is_endpoint is True

        call_rel = CallRelationship(
            caller_qualified_name="com.example.Test#main",
            callee_qualified_name="com.example.Test#helper",
            call_site_line=42
        )
        assert call_rel.caller_qualified_name == "com.example.Test#main"

        taint_flow = TaintFlowRelationship(
            source_qualified_name="com.example.Test#source",
            sink_qualified_name="com.example.Test#sink",
            risk=RiskLevel.HIGH
        )
        assert taint_flow.risk == RiskLevel.HIGH

    def test_db_interface_has_no_business_methods(self):
        """验证 DB 层接口不包含业务方法"""
        from cagr_processor.graph_dao.interfaces import GraphDatabase
        import inspect

        db_methods = {
            name for name, _ in inspect.getmembers(GraphDatabase, predicate=inspect.isfunction)
            if not name.startswith('_')
        }

        # DB 层不应该有这些业务方法
        business_methods = {
            'create_project', 'create_file', 'create_class',
            'create_function', 'create_variable',
            'create_calls_relationship', 'create_taint_flow_relationship',
            'find_function_by_name', 'get_call_chain', 'get_graph_stats',
        }
        assert not db_methods.intersection(business_methods), (
            f"DB 层接口不应包含业务方法: {db_methods.intersection(business_methods)}"
        )

        # DB 层应该有这些通用方法
        required_methods = {'create_node', 'create_relationship', 'find_node', 'execute_cypher', 'get_stats'}
        assert required_methods.issubset(db_methods), (
            f"DB 层接口缺少通用方法: {required_methods - db_methods}"
        )
