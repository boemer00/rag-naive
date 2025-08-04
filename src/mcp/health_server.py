"""MCP server for health data access."""

import json
import sys
from pathlib import Path
from typing import Dict, Any

from .apple_health import get_latest_metrics


class HealthServer:
    """Simple MCP server for health data resources."""
    
    def __init__(self):
        self.health_data = {}
        self.health_file_path = None
    
    def load_health_data(self, file_path: str) -> bool:
        """Load health data from Apple Health export."""
        try:
            self.health_file_path = file_path
            self.health_data = get_latest_metrics(file_path)
            return True
        except Exception as e:
            print(f"Error loading health data: {e}", file=sys.stderr)
            return False
    
    def get_resource(self, resource_name: str) -> Dict[str, Any]:
        """Get health resource by name."""
        if resource_name == "metrics":
            return {
                "type": "health_metrics",
                "data": self.health_data,
                "source": "apple_health"
            }
        elif resource_name == "summary":
            return {
                "type": "health_summary", 
                "summary": self._generate_summary(),
                "source": "apple_health"
            }
        else:
            return {"error": f"Unknown resource: {resource_name}"}
    
    def _generate_summary(self) -> str:
        """Generate text summary of health metrics."""
        if not self.health_data:
            return "No health data available"
        
        summary = []
        
        if self.health_data.get("avg_resting_hr"):
            summary.append(f"Average resting heart rate: {self.health_data['avg_resting_hr']:.1f} bpm")
        
        if self.health_data.get("latest_vo2_max"):
            summary.append(f"Latest VO2 max: {self.health_data['latest_vo2_max']:.1f} ml/kg/min")
        
        if self.health_data.get("avg_sleep_duration"):
            summary.append(f"Average sleep duration: {self.health_data['avg_sleep_duration']:.1f} hours")
        
        if self.health_data.get("date_range"):
            summary.append(f"Data period: {self.health_data['date_range']}")
        
        return "; ".join(summary) if summary else "No metrics available"


def main():
    """Run MCP health server via stdio."""
    server = HealthServer()
    
    # Simple stdio MCP protocol
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            
            if request.get("method") == "load_health_data":
                file_path = request.get("params", {}).get("file_path")
                success = server.load_health_data(file_path)
                response = {"result": {"success": success}}
            
            elif request.get("method") == "get_resource":
                resource = request.get("params", {}).get("resource")
                result = server.get_resource(resource)
                response = {"result": result}
            
            else:
                response = {"error": "Unknown method"}
            
            print(json.dumps(response))
            sys.stdout.flush()
            
        except Exception as e:
            error_response = {"error": str(e)}
            print(json.dumps(error_response))
            sys.stdout.flush()


if __name__ == "__main__":
    main()