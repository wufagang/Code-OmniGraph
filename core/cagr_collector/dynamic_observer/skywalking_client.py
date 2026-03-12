import requests
from typing import List, Dict

class SkyWalkingClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.graphql_endpoint = f"{self.base_url}/graphql"

    def get_traces(self, service_id: str) -> List[Dict]:
        query = """
        query queryTraces($condition: TraceQueryCondition) {
            queryBasicTraces(condition: $condition) {
                traces {
                    endpointNames
                    duration
                    isError
                    traceIds
                }
            }
        }
        """
        variables = {
            "condition": {
                "serviceId": service_id,
                "queryDuration": {
                    "start": "2023-10-01 0000",
                    "end": "2023-10-02 0000",
                    "step": "MINUTE"
                },
                "traceState": "ALL",
                "queryOrder": "BY_DURATION",
                "paging": {
                    "pageNum": 1,
                    "pageSize": 100,
                    "needTotal": True
                }
            }
        }
        
        response = requests.post(
            self.graphql_endpoint,
            json={"query": query, "variables": variables}
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("data", {}).get("queryBasicTraces", {}).get("traces", [])
        return []
