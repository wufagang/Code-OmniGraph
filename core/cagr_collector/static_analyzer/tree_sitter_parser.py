"""
Tree-sitter 增量解析器

用于提取代码的宏观结构：文件、类、函数、基础调用关系
"""

import os
import glob
from typing import List, Dict, Optional, Tuple
import sys
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from cagr_common.models import Method, Class, File

# Tree-sitter 相关导入（可选，如果没有安装则使用 mock）
try:
    import tree_sitter
    from tree_sitter import Language, Parser
    HAS_TREE_SITTER = True
except ImportError:
    HAS_TREE_SITTER = False
    logging.warning("tree-sitter not installed. Using mock implementation.")

# 语言支持
LANGUAGE_EXTENSIONS = {
    '.py': 'python',
    '.java': 'java',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.cpp': 'cpp',
    '.c': 'c',
    '.go': 'go',
    '.rs': 'rust',
}


class TreeSitterParser:
    """Tree-sitter 增量代码解析器"""

    def __init__(self, project_path: str, languages: Optional[List[str]] = None):
        """
        初始化解析器

        Args:
            project_path: 项目根目录路径
            languages: 要解析的语言列表，None 表示自动检测
        """
        self.project_path = Path(project_path).resolve()
        self.languages = languages or ['python', 'java', 'javascript', 'typescript']
        self.parsers: Dict[str, Parser] = {}

        # 初始化日志
        self.logger = logging.getLogger(self.__class__.__name__)

        if HAS_TREE_SITTER:
            self._init_parsers()

    def _init_parsers(self):
        """初始化各语言的 parser"""
        for lang_name in self.languages:
            try:
                # 尝试加载语言库
                lang_lib_path = self._get_language_library_path(lang_name)
                if lang_lib_path and os.path.exists(lang_lib_path):
                    language = Language(lang_lib_path, lang_name)
                    parser = Parser()
                    parser.set_language(language)
                    self.parsers[lang_name] = parser
                    self.logger.info(f"Loaded tree-sitter parser for {lang_name}")
                else:
                    self.logger.warning(f"Language library not found for {lang_name}")
            except Exception as e:
                self.logger.error(f"Failed to load parser for {lang_name}: {e}")

    def _get_language_library_path(self, lang_name: str) -> Optional[str]:
        """获取语言库路径"""
        # 尝试多种可能的路径
        possible_paths = [
            f"/usr/local/lib/tree-sitter-{lang_name}.so",
            f"./tree-sitter-languages/libtree-sitter-{lang_name}.so",
            f"{os.path.expanduser('~')}/.cache/tree-sitter/libtree-sitter-{lang_name}.so",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None

    def _get_file_language(self, file_path: str) -> Optional[str]:
        """根据文件扩展名获取语言类型"""
        ext = Path(file_path).suffix.lower()
        return LANGUAGE_EXTENSIONS.get(ext)

    def parse_project(self, file_filter: Optional[str] = None) -> List[File]:
        """
        解析整个项目

        Args:
            file_filter: 文件过滤模式（glob），例如 "**/*.py"

        Returns:
            文件节点列表
        """
        if not HAS_TREE_SITTER:
            return self._mock_parse_project()

        files = []

        # 获取要解析的文件列表
        if file_filter:
            file_patterns = [file_filter]
        else:
            # 默认解析所有支持的文件
            file_patterns = [f"**/*{ext}" for ext in LANGUAGE_EXTENSIONS.keys()]

        for pattern in file_patterns:
            for file_path in self.project_path.glob(pattern):
                if file_path.is_file():
                    language = self._get_file_language(str(file_path))
                    if language and language in self.parsers:
                        try:
                            file_node = self._parse_file(file_path, language)
                            if file_node:
                                files.append(file_node)
                        except Exception as e:
                            self.logger.error(f"Failed to parse file {file_path}: {e}")

        return files

    def parse_incremental(self, changed_files: List[str]) -> List[Method]:
        """
        增量解析（只解析变更的文件）

        Args:
            changed_files: 变更的文件路径列表

        Returns:
            变更的方法列表
        """
        if not HAS_TREE_SITTER:
            return self._mock_parse_incremental(changed_files)

        methods = []

        for file_path in changed_files:
            abs_path = self.project_path / file_path
            if not abs_path.exists():
                continue

            language = self._get_file_language(str(abs_path))
            if language and language in self.parsers:
                try:
                    file_node = self._parse_file(abs_path, language)
                    if file_node:
                        # 提取所有方法
                        for cls in file_node.classes:
                            methods.extend(cls.methods)
                        # 独立函数
                        methods.extend(file_node.methods)
                except Exception as e:
                    self.logger.error(f"Failed to parse changed file {abs_path}: {e}")

        return methods

    def _parse_file(self, file_path: Path, language: str) -> Optional[File]:
        """
        解析单个文件

        Args:
            file_path: 文件路径
            language: 语言类型

        Returns:
            文件节点
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
        except Exception as e:
            self.logger.error(f"Failed to read file {file_path}: {e}")
            return None

        parser = self.parsers[language]
        tree = parser.parse(bytes(source_code, 'utf8'))

        # 根据语言选择解析器
        if language == 'python':
            return self._parse_python_file(file_path, source_code, tree)
        elif language == 'java':
            return self._parse_java_file(file_path, source_code, tree)
        elif language in ['javascript', 'typescript']:
            return self._parse_js_file(file_path, source_code, tree)
        else:
            self.logger.warning(f"Parser not implemented for language: {language}")
            return None

    def _parse_python_file(self, file_path: Path, source_code: str, tree) -> File:
        """解析 Python 文件"""
        root_node = tree.root_node

        # 提取文件级别的独立函数
        file_methods = []
        classes = []

        # 遍历顶层节点
        for node in root_node.children:
            if node.type == 'function_definition':
                # 顶层函数
                method = self._extract_python_method(node, source_code, is_top_level=True)
                if method:
                    file_methods.append(method)
            elif node.type == 'class_definition':
                # 类定义
                cls = self._extract_python_class(node, source_code, file_path)
                if cls:
                    classes.append(cls)

        # 创建文件节点
        relative_path = file_path.relative_to(self.project_path)
        return File(
            path=str(relative_path),
            name=file_path.name,
            language="python",
            content=source_code,
            size=len(source_code),
            classes=classes,
            methods=file_methods
        )

    def _extract_python_class(self, class_node, source_code: str, file_path: Path) -> Optional[Class]:
        """提取 Python 类"""
        # 获取类名
        name_node = None
        for child in class_node.children:
            if child.type == 'identifier':
                name_node = child
                break

        if not name_node:
            return None

        class_name = source_code[name_node.start_byte:name_node.end_byte]

        # 提取方法
        methods = []
        for node in class_node.children:
            if node.type == 'function_definition':
                method = self._extract_python_method(node, source_code, class_name=class_name)
                if method:
                    methods.append(method)

        # 提取 docstring
        docstring = self._extract_python_docstring(class_node, source_code)

        # 计算行号
        start_line = class_node.start_point[0] + 1
        end_line = class_node.end_point[0] + 1

        # 获取类源码
        class_code = source_code[class_node.start_byte:class_node.end_byte]

        return Class(
            id=f"{file_path}:{class_name}",
            name=class_name,
            is_interface=False,  # Python 没有接口
            is_abstract=False,     # 简化处理
            methods=methods,
            docstring=docstring,
            start_line=start_line,
            end_line=end_line
        )

    def _extract_python_method(self, method_node, source_code: str,
                              class_name: Optional[str] = None,
                              is_top_level: bool = False) -> Optional[Method]:
        """提取 Python 方法"""
        # 获取方法名
        name_node = None
        for child in method_node.children:
            if child.type == 'identifier':
                name_node = child
                break

        if not name_node:
            return None

        method_name = source_code[name_node.start_byte:name_node.end_byte]

        # 获取参数列表
        params = []
        for child in method_node.children:
            if child.type == 'parameters':
                params_text = source_code[child.start_byte:child.end_byte]
                # 简化处理：提取参数名
                for param_node in child.children:
                    if param_node.type == 'identifier':
                        param_name = source_code[param_node.start_byte:param_node.end_byte]
                        params.append(param_name)
                break

        # 构建签名
        param_str = ", ".join(params)
        signature = f"def {method_name}({param_str})"

        # 获取方法源码
        method_code = source_code[method_node.start_byte:method_node.end_byte]

        # 构建方法ID
        if is_top_level:
            method_id = f"{method_name}"
        else:
            method_id = f"{class_name}#{method_name}"

        # 提取 docstring
        docstring = self._extract_python_docstring(method_node, source_code)

        # 计算行号
        start_line = method_node.start_point[0] + 1
        end_line = method_node.end_point[0] + 1

        # 检查是否是构造函数
        is_constructor = method_name == "__init__" and not is_top_level

        return Method(
            id=method_id,
            name=method_name,
            signature=signature,
            source_code=method_code,
            class_name=class_name or "",
            docstring=docstring,
            start_line=start_line,
            end_line=end_line,
            is_constructor=is_constructor
        )

    def _extract_python_docstring(self, node, source_code: str) -> Optional[str]:
        """提取 Python docstring"""
        # 查找第一个表达式语句，通常是 docstring
        for child in node.children:
            if child.type == 'expression_statement':
                for expr_child in child.children:
                    if expr_child.type == 'string':
                        return source_code[expr_child.start_byte:expr_child.end_byte]
        return None

    def _parse_java_file(self, file_path: Path, source_code: str, tree) -> File:
        """解析 Java 文件（简化实现）"""
        # TODO: 实现 Java 解析
        self.logger.info(f"Java parsing not fully implemented yet for {file_path}")
        return File(
            path=str(file_path.relative_to(self.project_path)),
            name=file_path.name,
            language="java",
            content=source_code,
            size=len(source_code)
        )

    def _parse_js_file(self, file_path: Path, source_code: str, tree) -> File:
        """解析 JavaScript/TypeScript 文件（简化实现）"""
        # TODO: 实现 JS/TS 解析
        self.logger.info(f"JavaScript parsing not fully implemented yet for {file_path}")
        return File(
            path=str(file_path.relative_to(self.project_path)),
            name=file_path.name,
            language="javascript",
            content=source_code,
            size=len(source_code)
        )

    def _mock_parse_project(self) -> List[File]:
        """Mock 实现 - 解析整个项目"""
        # 模拟一些 Python 文件
        return [
            File(
                path="src/main.py",
                name="main.py",
                language="python",
                content="def main():\n    print('Hello')",
                size=30,
                methods=[
                    Method(
                        id="main",
                        name="main",
                        signature="def main()",
                        source_code="def main():\n    print('Hello')",
                        class_name="",
                        start_line=1,
                        end_line=2
                    )
                ],
                classes=[]
            ),
            File(
                path="src/utils.py",
                name="utils.py",
                language="python",
                content="class Utils:\n    def helper(self): pass",
                size=50,
                methods=[],
                classes=[
                    Class(
                        id="src/utils.py:Utils",
                        name="Utils",
                        is_interface=False,
                        is_abstract=False,
                        methods=[
                            Method(
                                id="Utils#helper",
                                name="helper",
                                signature="def helper(self)",
                                source_code="def helper(self): pass",
                                class_name="Utils",
                                start_line=2,
                                end_line=2
                            )
                        ]
                    )
                ]
            )
        ]

    def _mock_parse_incremental(self, changed_files: List[str]) -> List[Method]:
        """Mock 实现 - 增量解析"""
        methods = []
        for file_path in changed_files:
            if file_path.endswith('.py'):
                methods.append(Method(
                    id=f"incremental.{Path(file_path).stem}#changed",
                    name="changed_method",
                    signature="def changed_method()",
                    source_code="def changed_method():\n    pass",
                    class_name="Incremental",
                    start_line=1,
                    end_line=2
                ))
        return methods


# 使用示例
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)

    # 创建解析器
    parser = TreeSitterParser("/path/to/project")

    # 解析整个项目
    files = parser.parse_project()
    print(f"Parsed {len(files)} files")

    # 增量解析
    changed_methods = parser.parse_incremental(["src/main.py", "src/utils.py"])
    print(f"Found {len(changed_methods)} changed methods")