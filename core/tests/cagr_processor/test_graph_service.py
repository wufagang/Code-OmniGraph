"""CodeGraphService 业务层单元测试

使用 MagicMock(spec=GraphDatabase) 隔离 DB 层，
验证字段映射、关系类型决策、查询参数传递等业务逻辑。
"""

import pytest
from unittest.mock import MagicMock, call

from cagr_processor.graph_dao.interfaces import GraphDatabase
from cagr_processor.graph_dao.models import (
    ProjectNode, FileNode, ClassNode, FunctionNode, VariableNode,
    CallRelationship, TaintFlowRelationship, DataAccessRelationship,
    GraphStats, NodeLabel, RelType, RiskLevel,
)
from cagr_processor.graph_service import CodeGraphService


class TestCodeGraphService:
    """CodeGraphService 单元测试"""

    def setup_method(self):
        self.mock_db = MagicMock(spec=GraphDatabase)
        self.service = CodeGraphService(self.mock_db)

    # ------------------------------------------------------------------
    # 节点创建 — 字段映射
    # ------------------------------------------------------------------

    def test_create_project_maps_fields_correctly(self):
        """create_project 应将 ProjectNode 字段正确映射为 DB 调用参数"""
        project = ProjectNode(name="my-app", version="2.0.0", language="java")
        self.mock_db.create_node.return_value = True

        result = self.service.create_project(project)

        self.mock_db.create_node.assert_called_once()
        args = self.mock_db.create_node.call_args
        label, unique_key, properties = args[0]

        assert label == NodeLabel.PROJECT
        assert unique_key == "name"
        assert properties["name"] == "my-app"
        assert properties["version"] == "2.0.0"
        assert properties["language"] == "java"
        assert result is True

    def test_create_project_excludes_none_values(self):
        """create_project 不应将 None 值传入 DB"""
        project = ProjectNode(name="no-path-app", language="python")

        self.service.create_project(project)

        _, _, properties = self.mock_db.create_node.call_args[0]
        assert "path" not in properties

    def test_create_function_maps_all_fields(self):
        """create_function 应映射所有 FunctionNode 字段"""
        fn = FunctionNode(
            qualified_name="com.example.Foo#bar",
            name="bar",
            signature="public String bar(int x)",
            return_type="String",
            is_endpoint=True,
        )
        self.service.create_function(fn)

        args = self.mock_db.create_node.call_args[0]
        label, unique_key, properties = args

        assert label == NodeLabel.FUNCTION
        assert unique_key == "qualified_name"
        assert properties["qualified_name"] == "com.example.Foo#bar"
        assert properties["name"] == "bar"
        assert properties["signature"] == "public String bar(int x)"
        assert properties["return_type"] == "String"
        assert properties["is_endpoint"] is True

    def test_create_file_uses_path_as_unique_key(self):
        """create_file 应使用 path 作为 unique_key"""
        file_node = FileNode(path="src/Foo.java", name="Foo.java", language="java")
        self.service.create_file(file_node)

        _, unique_key, _ = self.mock_db.create_node.call_args[0]
        assert unique_key == "path"

    def test_create_class_uses_qualified_name_as_unique_key(self):
        """create_class 应使用 qualified_name 作为 unique_key"""
        cls = ClassNode(qualified_name="com.example.Foo", name="Foo")
        self.service.create_class(cls)

        _, unique_key, _ = self.mock_db.create_node.call_args[0]
        assert unique_key == "qualified_name"

    # ------------------------------------------------------------------
    # 关系创建 — 业务决策
    # ------------------------------------------------------------------

    def test_create_data_access_relationship_read_uses_reads_rel_type(self):
        """access_type='READ' 应使用 RelType.READS"""
        access = DataAccessRelationship(
            function_qualified_name="com.example.Foo#bar",
            variable_qualified_name="com.example.Foo#field",
            access_type="READ",
        )
        self.service.create_data_access_relationship(access)

        args = self.mock_db.create_relationship.call_args[0]
        rel_type = args[6]
        assert rel_type == RelType.READS

    def test_create_data_access_relationship_write_uses_writes_rel_type(self):
        """access_type='WRITE' 应使用 RelType.WRITES"""
        access = DataAccessRelationship(
            function_qualified_name="com.example.Foo#bar",
            variable_qualified_name="com.example.Foo#field",
            access_type="WRITE",
        )
        self.service.create_data_access_relationship(access)

        args = self.mock_db.create_relationship.call_args[0]
        rel_type = args[6]
        assert rel_type == RelType.WRITES

    def test_create_data_access_relationship_case_insensitive(self):
        """access_type 比较应不区分大小写"""
        access = DataAccessRelationship(
            function_qualified_name="com.example.Foo#bar",
            variable_qualified_name="com.example.Foo#field",
            access_type="read",  # 小写
        )
        self.service.create_data_access_relationship(access)

        args = self.mock_db.create_relationship.call_args[0]
        rel_type = args[6]
        assert rel_type == RelType.READS

    def test_create_taint_flow_passes_risk_level(self):
        """create_taint_flow_relationship 应将 risk 值传入 properties"""
        taint = TaintFlowRelationship(
            source_qualified_name="com.example.Foo#source",
            sink_qualified_name="com.example.Foo#sink",
            risk=RiskLevel.HIGH,
            vulnerability_type="SQL_INJECTION",
        )
        self.service.create_taint_flow_relationship(taint)

        args = self.mock_db.create_relationship.call_args[0]
        properties = args[7]
        assert "vulnerability_type" in properties
        assert properties["vulnerability_type"] == "SQL_INJECTION"

    def test_create_project_contains_file_passes_correct_labels(self):
        """create_project_contains_file 应使用 Project/File 标签和 CONTAINS 关系"""
        self.service.create_project_contains_file("my-app", "src/Foo.java")

        args = self.mock_db.create_relationship.call_args[0]
        start_label, start_key, start_value = args[0], args[1], args[2]
        end_label, end_key, end_value = args[3], args[4], args[5]
        rel_type = args[6]

        assert start_label == NodeLabel.PROJECT
        assert start_key == "name"
        assert start_value == "my-app"
        assert end_label == NodeLabel.FILE
        assert end_key == "path"
        assert end_value == "src/Foo.java"
        assert rel_type == RelType.CONTAINS

    # ------------------------------------------------------------------
    # 查询方法 — 参数传递与结果组装
    # ------------------------------------------------------------------

    def test_find_function_by_name_returns_function_node(self):
        """execute_cypher 返回有效数据时，应返回 FunctionNode"""
        self.mock_db.execute_cypher.return_value = [
            {"props": {
                "qualified_name": "com.example.Foo#bar",
                "name": "bar",
                "signature": "void bar()",
            }}
        ]
        result = self.service.find_function_by_name("bar")

        assert result is not None
        assert isinstance(result, FunctionNode)
        assert result.qualified_name == "com.example.Foo#bar"
        assert result.name == "bar"

    def test_find_function_by_name_returns_none_when_empty(self):
        """execute_cypher 返回空列表时，应返回 None"""
        self.mock_db.execute_cypher.return_value = []
        result = self.service.find_function_by_name("nonexistent")
        assert result is None

    def test_find_function_by_name_passes_name_param(self):
        """find_function_by_name 应将 name 参数传入 execute_cypher"""
        self.mock_db.execute_cypher.return_value = []
        self.service.find_function_by_name("myFunc")

        _, params = self.mock_db.execute_cypher.call_args[0]
        assert params == {"name": "myFunc"}

    def test_get_call_chain_passes_depth_to_cypher(self):
        """get_call_chain 应在 Cypher 中使用指定的 depth"""
        self.mock_db.execute_cypher.return_value = []
        self.service.get_call_chain("com.example.Foo#bar", depth=5)

        query, _ = self.mock_db.execute_cypher.call_args[0]
        assert "5" in query  # depth 值应出现在 Cypher 字符串中

    def test_get_call_chain_passes_qualified_name_param(self):
        """get_call_chain 应将 qualified_name 参数传入 execute_cypher"""
        self.mock_db.execute_cypher.return_value = []
        self.service.get_call_chain("com.example.Foo#bar")

        _, params = self.mock_db.execute_cypher.call_args[0]
        assert params["qualified_name"] == "com.example.Foo#bar"

    # ------------------------------------------------------------------
    # GraphStats 映射
    # ------------------------------------------------------------------

    def test_get_graph_stats_maps_to_domain_model(self):
        """get_graph_stats 应将 db.get_stats() 的 dict 映射为 GraphStats 对象"""
        self.mock_db.get_stats.return_value = {
            "total_nodes": 100,
            "total_relationships": 200,
            "projects": 3,
            "functions": 50,
        }
        stats = self.service.get_graph_stats()

        assert isinstance(stats, GraphStats)
        assert stats.total_nodes == 100
        assert stats.total_relationships == 200
        assert stats.node_counts["projects"] == 3
        assert stats.node_counts["functions"] == 50

    def test_get_graph_stats_node_counts_excludes_totals(self):
        """node_counts 不应包含 total_nodes 和 total_relationships"""
        self.mock_db.get_stats.return_value = {
            "total_nodes": 50,
            "total_relationships": 80,
            "files": 10,
        }
        stats = self.service.get_graph_stats()

        assert "total_nodes" not in stats.node_counts
        assert "total_relationships" not in stats.node_counts
        assert stats.node_counts["files"] == 10

    # ------------------------------------------------------------------
    # find_taint_flows — 动态 WHERE 子句
    # ------------------------------------------------------------------

    def test_find_taint_flows_no_filter_has_no_where(self):
        """无过滤条件时，Cypher 不应有 WHERE 子句"""
        self.mock_db.execute_cypher.return_value = []
        self.service.find_taint_flows()

        query, _ = self.mock_db.execute_cypher.call_args[0]
        assert "WHERE" not in query

    def test_find_taint_flows_with_source_filter_adds_where(self):
        """指定 source_function 时，Cypher 应包含 WHERE 子句"""
        self.mock_db.execute_cypher.return_value = []
        self.service.find_taint_flows(source_function="com.example.Foo#source")

        query, params = self.mock_db.execute_cypher.call_args[0]
        assert "WHERE" in query
        assert params["source_function"] == "com.example.Foo#source"

    def test_find_taint_flows_returns_taint_flow_objects(self):
        """find_taint_flows 应将查询结果映射为 TaintFlowRelationship 列表"""
        self.mock_db.execute_cypher.return_value = [
            {
                "source": "com.example.Foo#src",
                "sink": "com.example.Foo#snk",
                "risk": RiskLevel.HIGH,
                "vulnerability_type": "XSS",
                "taint_path": None,
                "description": None,
            }
        ]
        results = self.service.find_taint_flows()

        assert len(results) == 1
        assert isinstance(results[0], TaintFlowRelationship)
        assert results[0].source_qualified_name == "com.example.Foo#src"
        assert results[0].vulnerability_type == "XSS"
