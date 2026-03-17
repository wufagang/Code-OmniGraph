#!/usr/bin/env python
"""运行向量数据库模块的单元测试"""

import sys
import os
import unittest

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

def run_all_tests():
    """运行所有测试"""
    # 创建测试加载器
    loader = unittest.TestLoader()

    # 创建测试套件
    suite = unittest.TestSuite()

    # 添加测试模块
    test_modules = [
        'tests.test_models',
        'tests.test_config',
        'tests.test_factory',
        'tests.test_base',
    ]

    # 尝试添加Qdrant测试，如果依赖可用
    try:
        from qdrant_client import QdrantClient
        test_modules.append('tests.test_qdrant_impl')
    except ImportError:
        print("跳过Qdrant测试：qdrant-client库未安装")

    # 加载测试
    for module in test_modules:
        try:
            tests = loader.loadTestsFromName(module)
            suite.addTests(tests)
        except Exception as e:
            print(f"加载测试模块 {module} 失败: {e}")

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)