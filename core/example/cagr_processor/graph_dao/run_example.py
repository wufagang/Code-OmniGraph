#!/usr/bin/env python3
"""
Code-OmniGraph Neo4j 示例运行器
简化示例脚本的执行过程
"""

import os
import sys
import subprocess
from pathlib import Path


def find_core_dir():
    """查找 core 目录"""
    current_dir = Path(__file__).resolve().parent

    # 向上查找包含 cagr_processor 目录的路径（即 core 目录）
    while current_dir != current_dir.parent:
        if (current_dir / "cagr_processor").exists():
            return current_dir
        current_dir = current_dir.parent

    raise RuntimeError("无法找到 core 目录")


def check_neo4j_driver():
    """检查是否安装了 neo4j 驱动"""
    try:
        import neo4j
        return True
    except ImportError:
        return False


def setup_environment():
    """设置环境"""
    core_dir = find_core_dir()

    # 设置 PYTHONPATH 为 core 目录
    if str(core_dir) not in sys.path:
        sys.path.insert(0, str(core_dir))

    # 设置环境变量
    os.environ['PYTHONPATH'] = str(core_dir)

    return core_dir


def run_quick_start():
    """运行快速入门示例"""
    print("=== 运行 Code-OmniGraph Neo4j 快速入门示例 ===\n")

    core_dir = setup_environment()
    print(f"Core 目录: {core_dir}")

    # 检查依赖
    if not check_neo4j_driver():
        print("错误: 未安装 neo4j 驱动")
        print("请运行: pip install neo4j")
        return False

    print("✓ neo4j 驱动已安装\n")

    # 运行示例
    script_path = core_dir / "example" / "cagr_processor" / "graph_dao" / "quick_start.py"

    try:
        # 使用 subprocess 运行脚本，确保正确的环境
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(core_dir),
            env={**os.environ, 'PYTHONPATH': str(core_dir)},
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(result.stdout)
            print("\n✓ 快速入门示例运行成功！")
            return True
        else:
            print("运行失败:")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False

    except Exception as e:
        print(f"运行出错: {e}")
        return False


def run_full_example():
    """运行完整示例"""
    print("=== 运行 Code-OmniGraph Neo4j 完整示例 ===\n")

    core_dir = setup_environment()

    # 检查依赖
    if not check_neo4j_driver():
        print("错误: 未安装 neo4j 驱动")
        print("请运行: pip install neo4j")
        return False

    print("✓ neo4j 驱动已安装\n")

    # 运行示例
    script_path = core_dir / "example" / "cagr_processor" / "graph_dao" / "neo4j_usage_example.py"

    try:
        # 使用 subprocess 运行脚本
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(core_dir),
            env={**os.environ, 'PYTHONPATH': str(core_dir)},
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(result.stdout)
            print("\n✓ 完整示例运行成功！")
            return True
        else:
            print("运行失败:")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False

    except Exception as e:
        print(f"运行出错: {e}")
        return False


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python run_example.py quick     # 运行快速入门示例")
        print("  python run_example.py full      # 运行完整示例")
        print("  python run_example.py help      # 显示帮助")
        return

    command = sys.argv[1].lower()

    if command == "quick":
        run_quick_start()
    elif command == "full":
        run_full_example()
    elif command == "help":
        print("Code-OmniGraph Neo4j 示例运行器")
        print("\n使用方法:")
        print("  python run_example.py quick     # 运行快速入门示例")
        print("  python run_example.py full      # 运行完整示例")
        print("  python run_example.py help      # 显示帮助")
    else:
        print(f"未知命令: {command}")
        print("请使用 'help' 查看可用命令")


if __name__ == "__main__":
    main()