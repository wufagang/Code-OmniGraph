#!/bin/bash
# 运行 Code-OmniGraph Neo4j 示例的便捷脚本

echo "=== Code-OmniGraph Neo4j 示例运行器 ==="
echo

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"

echo "项目根目录: ${PROJECT_ROOT}"
echo

# 检查是否安装了 neo4j 驱动
echo "检查 Python 依赖..."
if ! python -c "import neo4j" 2>/dev/null; then
    echo "错误: 未安装 neo4j 驱动。请先安装依赖:"
    echo "  pip install neo4j"
    exit 1
fi
echo "✓ neo4j 驱动已安装"
echo

# 设置 Python 路径
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

# 运行快速入门示例
echo "运行快速入门示例..."
cd "${PROJECT_ROOT}"
python -m core.example.cagr_processor.graph_builder.quick_start

echo
echo "=== 完成 ==="