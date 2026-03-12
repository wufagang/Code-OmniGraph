import os
from typing import List
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from cagr_common.models import Method

class TreeSitterParser:
    def __init__(self, project_path: str):
        self.project_path = project_path

    def parse_incremental(self, changed_files: List[str]) -> List[Method]:
        # In a real scenario, this would use the tree-sitter-java grammar
        # to parse only the files that have changed in the git diff.
        methods = []
        for file_path in changed_files:
            # Mock parsing logic
            methods.append(Method(
                id=f"com.example.Incremental.{os.path.basename(file_path)}",
                name="incrementalMethod",
                signature="void incrementalMethod()",
                source_code="void incrementalMethod() {}",
                class_name="com.example.Incremental"
            ))
        return methods
