import pytest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cagr_collector.static_analyzer.joern_parser import JoernParser
from cagr_common.models import Class, Method

@patch('cagr_collector.static_analyzer.joern_parser.subprocess.run')
def test_joern_parser_extracts_methods(mock_run):
    # Mocking Joern output
    mock_run.return_value = MagicMock(stdout=b'{"id": "com.example.Test.method", "name": "method", "signature": "void method()", "code": "void method() {}", "className": "com.example.Test"}')
    
    parser = JoernParser(project_path="/dummy/path")
    methods = parser.parse_methods()
    
    assert len(methods) == 1
    assert methods[0].name == "method"
    assert methods[0].class_name == "com.example.Test"

@patch('cagr_collector.static_analyzer.joern_parser.subprocess.run')
def test_joern_parser_extracts_calls(mock_run):
    mock_run.return_value = MagicMock(stdout=b'{"caller": "com.example.A.methodA", "callee": "com.example.B.methodB"}')
    
    parser = JoernParser(project_path="/dummy/path")
    calls = parser.parse_calls()
    
    assert len(calls) == 1
    assert calls[0].caller_id == "com.example.A.methodA"
    assert calls[0].callee_id == "com.example.B.methodB"
