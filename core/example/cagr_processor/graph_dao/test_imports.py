#!/usr/bin/env python3
"""
简单的导入测试脚本，验证模块路径是否正确
"""

import sys
from pathlib import Path

# 计算项目根目录
current_file = Path(__file__).resolve()
core_dir = current_file.parent.parent.parent.parent
project_root = core_dir.parent

print(f"当前文件: {current_file}")
print(f"Core 目录: {core_dir}")
print(f"项目根目录: {project_root}")
print()

# 添加到 Python 路径
sys.path.insert(0, str(project_root))

# 尝试导入模块
try:
    from core.cagr_processor.graph_dao.config import GraphDBConfig
    print("✓ 成功导入 GraphDBConfig")

    from core.cagr_processor.graph_dao.factory import GraphDBFactory
    print("✓ 成功导入 GraphDBFactory")

    from core.cagr_processor.graph_code.models import ProjectNode
    print("✓ 成功导入 ProjectNode")

    # 测试创建配置
    config = GraphDBConfig.from_env()
    print(f"✓ 成功创建配置，Neo4j URI: {config.neo4j_config.uri}")

    print("\n✓ 所有导入测试通过！")

except Exception as e:
    print(f"✗ 导入失败: {e}")
    import traceback
    traceback.print_exc()