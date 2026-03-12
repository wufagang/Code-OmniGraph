import xml.etree.ElementTree as ET
import re
from typing import List
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from cagr_common.models import MethodOperatesTable

class MyBatisParser:
    def __init__(self, xml_path: str):
        self.xml_path = xml_path

    def parse_operations(self) -> List[MethodOperatesTable]:
        operations = []
        try:
            tree = ET.parse(self.xml_path)
            root = tree.getroot()
            namespace = root.attrib.get('namespace', '')
            
            for child in root:
                if child.tag in ['select', 'insert', 'update', 'delete']:
                    method_id = f"{namespace}.{child.attrib.get('id', '')}"
                    sql_text = "".join(child.itertext()).strip().upper()
                    
                    # Simple regex to find table names (e.g., FROM table_name, INTO table_name, UPDATE table_name)
                    tables = set()
                    from_match = re.search(r'FROM\s+([A-Z0-9_]+)', sql_text)
                    if from_match:
                        tables.add(from_match.group(1))
                        
                    into_match = re.search(r'INTO\s+([A-Z0-9_]+)', sql_text)
                    if into_match:
                        tables.add(into_match.group(1))
                        
                    update_match = re.search(r'UPDATE\s+([A-Z0-9_]+)', sql_text)
                    if update_match:
                        tables.add(update_match.group(1))
                        
                    action = "READ" if child.tag == "select" else "WRITE"
                    
                    for table in tables:
                        operations.append(MethodOperatesTable(
                            method_id=method_id,
                            table_name=table,
                            action=action
                        ))
        except Exception as e:
            print(f"Error parsing MyBatis XML: {e}")
            
        return operations
