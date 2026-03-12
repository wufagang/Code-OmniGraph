import subprocess
import json
from typing import List
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from cagr_common.models import Method, MethodCall

class JoernParser:
    def __init__(self, project_path: str):
        self.project_path = project_path

    def parse_methods(self) -> List[Method]:
        # In a real scenario, this would invoke Joern CLI to generate CPG and query it.
        # Example: joern --script extract_methods.sc --params projectPath=...
        result = subprocess.run(
            ["joern", "--script", "extract_methods.sc", "--params", f"projectPath={self.project_path}"],
            capture_output=True,
            text=True
        )
        
        methods = []
        try:
            # Assume Joern script outputs JSON lines
            for line in result.stdout.strip().split('\n'):
                if line:
                    data = json.loads(line)
                    methods.append(Method(
                        id=data.get("id"),
                        name=data.get("name"),
                        signature=data.get("signature"),
                        source_code=data.get("code"),
                        class_name=data.get("className")
                    ))
        except Exception as e:
            print(f"Error parsing Joern output: {e}")
            
        return methods

    def parse_calls(self) -> List[MethodCall]:
        result = subprocess.run(
            ["joern", "--script", "extract_calls.sc", "--params", f"projectPath={self.project_path}"],
            capture_output=True,
            text=True
        )
        
        calls = []
        try:
            for line in result.stdout.strip().split('\n'):
                if line:
                    data = json.loads(line)
                    calls.append(MethodCall(
                        caller_id=data.get("caller"),
                        callee_id=data.get("callee")
                    ))
        except Exception as e:
            print(f"Error parsing Joern output: {e}")
            
        return calls
