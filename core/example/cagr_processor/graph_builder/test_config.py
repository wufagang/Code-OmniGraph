"""
测试配置文件 - 演示如何使用不同的图数据库配置
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from cagr_processor.graph_builder import GraphDBConfig, Neo4jConfig





def test_neo4j_config():
    """测试Neo4j数据库配置"""
    print("\n=== Neo4j Database Configuration ===------------------------------------")

    # 方式1: 手动配置
    config = GraphDBConfig.from_env()
    try:
        config.validate()
        print("✓ Valid configuration passed validation")
    except Exception as e:
        print(f"✗ Valid configuration failed: {e}")
    print(f"Database Type: {config.db_type}")
    print(f"Neo4j URI: {config.neo4j_config.uri}")
    print(f"Batch Size: {config.default_batch_size}")
    print("✓ Neo4j configuration created successfully")

    return config




def test_config_validation():
    """测试配置验证"""
    print("\n=== Configuration Validation ===")

    # 有效配置
    valid_config = GraphDBConfig(
        db_type="mock",
        enable_logging=True
    )

    try:
        valid_config.validate()
        print("✓ Valid configuration passed validation")
    except Exception as e:
        print(f"✗ Valid configuration failed: {e}")

    # 无效配置（Neo4j缺少必要参数）
    try:
        invalid_config = GraphDBConfig(
            db_type="neo4j",
            neo4j_config=Neo4jConfig(uri="", username="", password="")
        )
        invalid_config.validate()
        print("✗ Invalid configuration should have failed validation")
    except Exception as e:
        print(f"✓ Invalid configuration correctly failed: {e}")


def main():
    """主函数"""
    print("Graph Database Configuration Examples-----------------------------")
    print("=" * 50)

    try:
        # 测试各种配置
        neo4j_config = test_neo4j_config()
        test_config_validation()

        print("\n" + "=" * 50)
        print("Configuration Summary:")
        print(f"1. Mock DB: Best for testing and development")
        print(f"2. Neo4j DB: Best for production use")
        print(f"3. Environment: Best for deployment flexibility")

        print("\nUsage Example:")
        print("```python")
        print("from cagr_processor.graph_builder import create_graph_db, GraphDBConfig")
        print("")
        print("# For Mock database (no installation required)")
        print("config = GraphDBConfig(db_type='mock')")
        print("graph_db = create_graph_db(config)")
        print("")
        print("# For Neo4j database")
        print("config = GraphDBConfig.from_env()  # or manual config")
        print("graph_db = create_graph_db(config)")
        print("```")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()