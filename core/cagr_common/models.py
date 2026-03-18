from pydantic import BaseModel, Field
from typing import List, Optional

class Project(BaseModel):
    name: str
    description: Optional[str] = None

class Package(BaseModel):
    name: str

class Method(BaseModel):
    id: str
    name: str
    signature: str
    source_code: str
    vector_id: Optional[str] = None
    class_name: str

class Class(BaseModel):
    id: str
    name: str
    is_interface: bool = False
    is_abstract: bool = False
    methods: List[Method] = Field(default_factory=list)

class Table(BaseModel):
    name: str
    columns: List[str] = Field(default_factory=list)

class Commit(BaseModel):
    hash: str
    message: str
    author: str

class JiraIssue(BaseModel):
    issue_id: str
    title: str
    description: str

class MethodCall(BaseModel):
    caller_id: str
    callee_id: str
    qps: Optional[float] = None
    latency: Optional[float] = None

class MethodOperatesTable(BaseModel):
    method_id: str
    table_name: str
    action: str  # READ or WRITE

class File(BaseModel):
    path: str
    name: str
    language: Optional[str] = None
    content: Optional[str] = None
    size: Optional[int] = None
    methods: List[Method] = Field(default_factory=list)
    classes: List[Class] = Field(default_factory=list)
