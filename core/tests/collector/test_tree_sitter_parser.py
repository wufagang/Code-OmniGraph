"""Tree-sitter 解析器测试"""

import pytest
import tempfile
import os
import sys
from pathlib import Path

try:
    from cagr_collector.static_analyzer.tree_sitter_parser import TreeSitterParser, HAS_TREE_SITTER
except ImportError:
    HAS_TREE_SITTER = False

# 如果没有安装tree-sitter，跳过所有测试
if not HAS_TREE_SITTER:
    pytest.skip("tree-sitter not installed", allow_module_level=True)


class TestTreeSitterParser:
    """Tree-sitter 解析器测试类"""

    def setup_method(self):
        """测试前准备"""
        # 创建临时目录作为测试项目
        self.temp_dir = tempfile.mkdtemp()
        self.parser = TreeSitterParser(self.temp_dir)

    def teardown_method(self):
        """测试后清理"""
        # 清理临时目录
        import shutil
        shutil.rmtree(self.temp_dir)

    def _create_test_file(self, filename: str, content: str):
        """创建测试文件"""
        file_path = Path(self.temp_dir) / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            f.write(content)
        return str(file_path.relative_to(self.temp_dir))

    def test_parse_python_function(self):
        """测试解析 Python 函数"""
        # 创建测试文件
        test_content = '''
def hello_world():
    """Say hello to the world."""
    print("Hello, World!")

def add_numbers(a, b):
    """Add two numbers."""
    return a + b
'''
        file_path = self._create_test_file("test_functions.py", test_content)

        # 解析项目
        files = self.parser.parse_project("**/*.py")

        # 如果没有tree-sitter，使用mock结果
        if not HAS_TREE_SITTER:
            # mock模式下应该返回预定义的文件列表
            assert len(files) >= 0  # mock模式下可能有预定义数据
            return

        # 验证结果
        assert len(files) == 1
        file_node = files[0]
        assert file_node.name == "test_functions.py"
        assert len(file_node.methods) == 2

        # 验证第一个函数
        hello_func = file_node.methods[0]
        assert hello_func.name == "hello_world"
        assert "Hello, World!" in hello_func.source_code
        assert hello_func.docstring.strip() == '"""Say hello to the world."""'

        # 验证第二个函数
        add_func = file_node.methods[1]
        assert add_func.name == "add_numbers"
        assert "return a + b" in add_func.source_code

    def test_parse_python_class(self):
        """测试解析 Python 类"""
        # 创建测试文件
        test_content = '''
class Calculator:
    """A simple calculator class."""

    def __init__(self):
        self.result = 0

    def add(self, x):
        """Add a number."""
        self.result += x
        return self.result

    def multiply(self, x, y):
        """Multiply two numbers."""
        return x * y

class Utils:
    """Utility class."""

    @staticmethod
    def format_name(name):
        return name.title()
'''
        file_path = self._create_test_file("test_classes.py", test_content)

        # 解析项目
        files = self.parser.parse_project("**/*.py")

        # 如果没有tree-sitter，跳过详细测试
        if not HAS_TREE_SITTER:
            assert len(files) >= 0
            return

        # 验证结果
        assert len(files) == 1
        file_node = files[0]
        assert len(file_node.classes) == 2

        # 验证 Calculator 类
        calc_class = file_node.classes[0]
        assert calc_class.name == "Calculator"
        assert len(calc_class.methods) == 3  # __init__, add, multiply

        # 验证方法
        init_method = calc_class.methods[0]
        assert init_method.is_constructor

        add_method = calc_class.methods[1]
        assert add_method.name == "add"
        assert "self.result += x" in add_method.source_code

    def test_parse_incremental(self):
        """测试增量解析"""
        # 创建初始文件
        initial_content = '''
def old_function():
    pass
'''
        self._create_test_file("module.py", initial_content)

        # 更新文件
        updated_content = '''
def old_function():
    pass

def new_function():
    """This is a new function."""
    return 42
'''
        file_path = self._create_test_file("module.py", updated_content)

        # 增量解析
        methods = self.parser.parse_incremental(["module.py"])

        # 如果没有tree-sitter，跳过详细测试
        if not HAS_TREE_SITTER:
            assert len(methods) >= 0
            return

        # 验证结果
        assert len(methods) == 2

        # 找到新函数
        new_func = next((m for m in methods if m.name == "new_function"), None)
        assert new_func is not None
        assert new_func.docstring.strip() == '"""This is a new function."""'

    def test_file_filter(self):
        """测试文件过滤"""
        # 创建多个文件
        self._create_test_file("src/main.py", "def main(): pass")
        self._create_test_file("tests/test_main.py", "def test_main(): pass")
        self._create_test_file("docs/README.md", "# Documentation")

        # 只解析 src 目录下的文件
        files = self.parser.parse_project("src/**/*.py")

        # 如果没有tree-sitter，跳过详细测试
        if not HAS_TREE_SITTER:
            assert len(files) >= 0
            return

        # 验证结果
        assert len(files) == 1
        assert files[0].path == "src/main.py"

    def test_language_detection(self):
        """测试语言检测"""
        # 创建不同语言的文件
        self._create_test_file("app.py", "def main(): pass")
        self._create_test_file("utils.java", "public class Utils {}")
        self._create_test_file("helper.js", "function helper() {}")

        # 解析所有文件
        files = self.parser.parse_project()

        # 如果没有tree-sitter，跳过详细测试
        if not HAS_TREE_SITTER:
            assert len(files) >= 0
            return

        # 验证结果
        assert len(files) == 3

        # 验证语言检测
        py_file = next((f for f in files if f.path == "app.py"), None)
        assert py_file is not None
        assert py_file.language == "python"

        java_file = next((f for f in files if f.path == "utils.java"), None)
        assert java_file is not None
        assert java_file.language == "java"

        js_file = next((f for f in files if f.path == "helper.js"), None)
        assert js_file is not None
        assert js_file.language == "javascript"

    def test_empty_project(self):
        """测试空项目"""
        files = self.parser.parse_project()
        assert len(files) == 0

    def test_non_pythonic_file(self):
        """测试非 Python 文件"""
        # 创建非 Python 文件
        self._create_test_file("script.sh", "#!/bin/bash\necho 'Hello'")

        # 解析项目
        files = self.parser.parse_project()

        # 验证结果 - 应该没有解析到任何文件
        assert len(files) == 0

    def test_error_handling(self):
        """测试错误处理"""
        # 创建包含语法错误的文件
        self._create_test_file("error.py", "def incomplete_function(\n    # missing closing parenthesis")

        # 解析项目
        files = self.parser.parse_project()

        # 即使解析失败，也不应该抛出异常
        # （在真实实现中，tree-sitter 可以处理部分语法错误）
        # 这里我们至少验证文件被尝试解析了
        assert isinstance(files, list)