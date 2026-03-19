"""业务层：代码图谱服务（CodeGraphService）

职责：
- 接收领域对象（ProjectNode、FunctionNode 等）
- 完成领域模型到 DB 属性字典的字段映射
- 包含业务决策逻辑（如 READ/WRITE 关系类型判断）
- 执行业务查询并将结果组装为领域对象
- 通过 GraphDatabase 接口与 DB 层解耦
"""

import logging
from typing import List, Optional, Dict, Any

from cagr_processor.graph_dao.interfaces import GraphDatabase
from cagr_processor.graph_dao.models import (
    ProjectNode, FileNode, ClassNode, FunctionNode, VariableNode,
    CallRelationship, TaintFlowRelationship, DataAccessRelationship,
    GraphStats, SubGraph, NodeLabel, RelType, RiskLevel,
)


class CodeGraphService:
    """代码图谱业务服务层

    使用方式：
        db = GraphDBFactory.create(config)
        service = CodeGraphService(db)
        service.create_project(ProjectNode(...))
        fn = service.find_function_by_qualified_name("com.example.Foo#bar")
    """

    def __init__(self, db: GraphDatabase):
        self._db = db
        self.logger = logging.getLogger(self.__class__.__name__)

    # ------------------------------------------------------------------
    # 内部工具
    # ------------------------------------------------------------------

    def _format_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """格式化属性，去除 None 值，保留其他所有类型"""
        formatted = {}
        for key, value in properties.items():
            if value is not None:
                if isinstance(value, (list, bool, int, float, str)):
                    formatted[key] = value
                else:
                    formatted[key] = str(value)
        return formatted

    # ------------------------------------------------------------------
    # 节点创建（领域模型 → DB 属性字典映射）
    # ------------------------------------------------------------------

    def create_project(self, project: ProjectNode) -> bool:
        """创建项目节点"""
        properties = self._format_properties({
            "name": project.name,
            "version": project.version,
            "language": project.language,
            "path": project.path,
            **project.metadata,
        })
        return self._db.create_node(NodeLabel.PROJECT, "name", properties)

    def create_file(self, file: FileNode) -> bool:
        """创建文件节点"""
        properties = self._format_properties({
            "path": file.path,
            "name": file.name,
            "language": file.language,
            "content": file.content,
            "size": file.size,
            **file.metadata,
        })
        return self._db.create_node(NodeLabel.FILE, "path", properties)

    def create_class(self, class_node: ClassNode) -> bool:
        """创建类节点"""
        properties = self._format_properties({
            "qualified_name": class_node.qualified_name,
            "name": class_node.name,
            "file_path": class_node.file_path,
            "docstring": class_node.docstring,
            "is_interface": class_node.is_interface,
            "is_abstract": class_node.is_abstract,
            "start_line": class_node.start_line,
            "end_line": class_node.end_line,
            **class_node.metadata,
        })
        return self._db.create_node(NodeLabel.CLASS, "qualified_name", properties)

    def create_function(self, function: FunctionNode) -> bool:
        """创建函数/方法节点"""
        properties = self._format_properties({
            "qualified_name": function.qualified_name,
            "name": function.name,
            "signature": function.signature,
            "body": function.body,
            "file_path": function.file_path,
            "class_name": function.class_name,
            "return_type": function.return_type,
            "start_line": function.start_line,
            "end_line": function.end_line,
            "is_endpoint": function.is_endpoint,
            "is_constructor": function.is_constructor,
            "docstring": function.docstring,
            **function.metadata,
        })
        return self._db.create_node(NodeLabel.FUNCTION, "qualified_name", properties)

    def create_variable(self, variable: VariableNode) -> bool:
        """创建变量节点"""
        properties = self._format_properties({
            "qualified_name": variable.qualified_name,
            "name": variable.name,
            "var_type": variable.var_type,
            "file_path": variable.file_path,
            "class_name": variable.class_name,
            **variable.metadata,
        })
        return self._db.create_node(NodeLabel.VARIABLE, "qualified_name", properties)

    # ------------------------------------------------------------------
    # 关系创建
    # ------------------------------------------------------------------

    def create_project_contains_file(self, project_name: str, file_path: str) -> bool:
        """创建 Project-[:CONTAINS]->File 关系"""
        return self._db.create_relationship(
            NodeLabel.PROJECT, "name", project_name,
            NodeLabel.FILE, "path", file_path,
            RelType.CONTAINS, {}
        )

    def create_file_defines_class(self, file_path: str, class_qualified_name: str) -> bool:
        """创建 File-[:DEFINES]->Class 关系"""
        return self._db.create_relationship(
            NodeLabel.FILE, "path", file_path,
            NodeLabel.CLASS, "qualified_name", class_qualified_name,
            RelType.DEFINES, {}
        )

    def create_file_defines_function(self, file_path: str, function_qualified_name: str) -> bool:
        """创建 File-[:DEFINES]->Function 关系"""
        return self._db.create_relationship(
            NodeLabel.FILE, "path", file_path,
            NodeLabel.FUNCTION, "qualified_name", function_qualified_name,
            RelType.DEFINES, {}
        )

    def create_class_has_method(self, class_qualified_name: str, method_qualified_name: str) -> bool:
        """创建 Class-[:HAS_METHOD]->Function 关系"""
        return self._db.create_relationship(
            NodeLabel.CLASS, "qualified_name", class_qualified_name,
            NodeLabel.FUNCTION, "qualified_name", method_qualified_name,
            RelType.HAS_METHOD, {}
        )

    def create_calls_relationship(self, call: CallRelationship) -> bool:
        """创建 Function-[:CALLS]->Function 关系"""
        properties = self._format_properties({
            "call_site_line": call.call_site_line,
            **call.metadata,
        })
        return self._db.create_relationship(
            NodeLabel.FUNCTION, "qualified_name", call.caller_qualified_name,
            NodeLabel.FUNCTION, "qualified_name", call.callee_qualified_name,
            RelType.CALLS, properties
        )

    def create_data_access_relationship(self, access: DataAccessRelationship) -> bool:
        """创建 Function-[:READS|:WRITES]->Variable 关系
        业务决策：access_type 决定关系类型
        """
        properties = self._format_properties({
            "line": access.line,
            **access.metadata,
        })
        rel_type = RelType.READS if access.access_type.upper() == "READ" else RelType.WRITES
        return self._db.create_relationship(
            NodeLabel.FUNCTION, "qualified_name", access.function_qualified_name,
            NodeLabel.VARIABLE, "qualified_name", access.variable_qualified_name,
            rel_type, properties
        )

    def create_taint_flow_relationship(self, taint: TaintFlowRelationship) -> bool:
        """创建 Function-[:TAINT_FLOW_TO]->Function 关系（Joern 污点流）"""
        properties = self._format_properties({
            "risk": taint.risk,
            "vulnerability_type": taint.vulnerability_type,
            "taint_path": taint.taint_path,
            "description": taint.description,
            **taint.metadata,
        })
        return self._db.create_relationship(
            NodeLabel.FUNCTION, "qualified_name", taint.source_qualified_name,
            NodeLabel.FUNCTION, "qualified_name", taint.sink_qualified_name,
            RelType.TAINT_FLOW_TO, properties
        )

    # ------------------------------------------------------------------
    # 查询方法（通过 execute_cypher 执行，并组装为领域对象）
    # ------------------------------------------------------------------

    def find_function_by_name(self, name: str) -> Optional[FunctionNode]:
        """根据函数名查找函数节点（返回第一个匹配）"""
        results = self._db.execute_cypher(
            "MATCH (f:Function {name: $name}) RETURN properties(f) AS props LIMIT 1",
            {"name": name}
        )
        if results:
            return self._dict_to_function_node(results[0].get("props", {}))
        return None

    def find_function_by_qualified_name(self, qualified_name: str) -> Optional[FunctionNode]:
        """根据全限定名查找函数节点"""
        results = self._db.execute_cypher(
            "MATCH (f:Function {qualified_name: $qualified_name}) RETURN properties(f) AS props LIMIT 1",
            {"qualified_name": qualified_name}
        )
        if results:
            return self._dict_to_function_node(results[0].get("props", {}))
        return None

    def get_call_chain(self, function_qualified_name: str, depth: int = 3) -> List[Dict[str, Any]]:
        """获取函数下游调用链"""
        query = """
        MATCH path = (start:Function {qualified_name: $qualified_name})-[:CALLS*..%d]->(end:Function)
        RETURN [n in nodes(path) | {
            qualified_name: n.qualified_name,
            name: n.name,
            signature: n.signature
        }] as chain
        """ % depth
        results = self._db.execute_cypher(query, {"qualified_name": function_qualified_name})
        return [r["chain"] for r in results]

    def get_upstream_callers(self, function_qualified_name: str, depth: int = 1) -> List[Dict[str, Any]]:
        """获取上游调用者列表"""
        query = """
        MATCH path = (caller:Function)-[:CALLS*..%d]->(target:Function {qualified_name: $qualified_name})
        RETURN DISTINCT {
            qualified_name: caller.qualified_name,
            name: caller.name,
            signature: caller.signature
        } as caller
        """ % depth
        results = self._db.execute_cypher(query, {"qualified_name": function_qualified_name})
        return [r["caller"] for r in results]

    def get_downstream_callees(self, function_qualified_name: str, depth: int = 1) -> List[Dict[str, Any]]:
        """获取下游被调用者列表"""
        query = """
        MATCH path = (caller:Function {qualified_name: $qualified_name})-[:CALLS*..%d]->(callee:Function)
        RETURN DISTINCT {
            qualified_name: callee.qualified_name,
            name: callee.name,
            signature: callee.signature
        } as callee
        """ % depth
        results = self._db.execute_cypher(query, {"qualified_name": function_qualified_name})
        return [r["callee"] for r in results]

    def find_taint_flows(
        self,
        source_function: Optional[str] = None,
        sink_function: Optional[str] = None,
        risk_level: Optional[str] = None,
        limit: int = 100,
    ) -> List[TaintFlowRelationship]:
        """查找污点流，支持多条件过滤"""
        conditions = []
        params: Dict[str, Any] = {"limit": limit}
        if source_function:
            conditions.append("src.qualified_name = $source_function")
            params["source_function"] = source_function
        if sink_function:
            conditions.append("snk.qualified_name = $sink_function")
            params["sink_function"] = sink_function
        if risk_level:
            conditions.append("r.risk = $risk_level")
            params["risk_level"] = risk_level

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"""
        MATCH (src:Function)-[r:TAINT_FLOW_TO]->(snk:Function)
        {where_clause}
        RETURN src.qualified_name AS source, snk.qualified_name AS sink,
               r.risk AS risk, r.vulnerability_type AS vulnerability_type,
               r.taint_path AS taint_path, r.description AS description
        LIMIT $limit
        """
        results = self._db.execute_cypher(query, params)
        return [
            TaintFlowRelationship(
                source_qualified_name=r["source"],
                sink_qualified_name=r["sink"],
                risk=r.get("risk") or RiskLevel.HIGH,
                vulnerability_type=r.get("vulnerability_type"),
                taint_path=r.get("taint_path"),
                description=r.get("description"),
            )
            for r in results
        ]

    def find_vulnerable_paths(self, sink_function_name: str) -> List[List[Dict[str, Any]]]:
        """查找到达危险函数（sink）的所有调用路径"""
        query = """
        MATCH path = (start:Function)-[:CALLS*..10]->(sink:Function {name: $sink_function_name})
        WHERE start <> sink
        RETURN [n in nodes(path) | {
            qualified_name: n.qualified_name,
            name: n.name
        }] as path
        """
        results = self._db.execute_cypher(query, {"sink_function_name": sink_function_name})
        return [r["path"] for r in results]

    def get_subgraph_for_function(self, function_qualified_name: str, depth: int = 2) -> SubGraph:
        """获取函数子图，用于 LLM 上下文组装"""
        fn = self.find_function_by_qualified_name(function_qualified_name)
        center_node_data: Dict[str, Any] = {}
        if fn:
            center_node_data = {
                "qualified_name": fn.qualified_name,
                "name": fn.name,
                "signature": fn.signature,
                "body": fn.body,
                "file_path": fn.file_path,
            }

        upstream = self.get_upstream_callers(function_qualified_name, depth)
        downstream = self.get_downstream_callees(function_qualified_name, depth)
        taint_flows = self.find_taint_flows(source_function=function_qualified_name)
        taint_data = [
            {"source": tf.source_qualified_name, "sink": tf.sink_qualified_name, "risk": tf.risk}
            for tf in taint_flows
        ]

        var_results = self._db.execute_cypher(
            """
            MATCH (f:Function {qualified_name: $qualified_name})-[:READS|WRITES]->(v:Variable)
            RETURN DISTINCT v.qualified_name AS qualified_name, v.name AS name, v.var_type AS var_type
            """,
            {"qualified_name": function_qualified_name}
        )
        related_vars = [dict(r) for r in var_results]

        return SubGraph(
            center_node=center_node_data,
            upstream_callers=upstream,
            downstream_callees=downstream,
            taint_flows=taint_data,
            related_variables=related_vars,
        )

    def get_graph_stats(self) -> GraphStats:
        """获取图谱统计信息，映射为 GraphStats 领域对象"""
        raw = self._db.get_stats()
        stats = GraphStats()
        stats.total_nodes = raw.get("total_nodes", 0)
        stats.total_relationships = raw.get("total_relationships", 0)
        stats.node_counts = {
            k: v for k, v in raw.items()
            if k not in ("total_nodes", "total_relationships")
        }
        return stats

    # ------------------------------------------------------------------
    # 内部辅助
    # ------------------------------------------------------------------

    def _dict_to_function_node(self, data: Dict[str, Any]) -> Optional[FunctionNode]:
        """将原始属性字典安全地转换为 FunctionNode，过滤未知字段"""
        if not data:
            return None
        known_fields = set(FunctionNode.__dataclass_fields__.keys())
        filtered = {k: v for k, v in data.items() if k in known_fields}
        try:
            return FunctionNode(**filtered)
        except TypeError as e:
            self.logger.error(f"Failed to construct FunctionNode from data: {e}")
            return None
