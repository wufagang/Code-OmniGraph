import pytest
import sys
import os

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cagr_common.models import Class, Method, Table, MethodCall

def test_class_and_method_creation():
    method = Method(
        id="com.example.UserService.getUser",
        name="getUser",
        signature="public User getUser(String id)",
        source_code="public User getUser(String id) { return userRepository.findById(id); }",
        class_name="com.example.UserService"
    )
    
    cls = Class(
        id="com.example.UserService",
        name="UserService",
        is_interface=False,
        is_abstract=False,
        methods=[method]
    )
    
    assert cls.name == "UserService"
    assert len(cls.methods) == 1
    assert cls.methods[0].name == "getUser"

def test_method_call():
    call = MethodCall(
        caller_id="com.example.UserController.getUser",
        callee_id="com.example.UserService.getUser",
        qps=100.5,
        latency=12.3
    )
    assert call.qps == 100.5
    assert call.latency == 12.3
