"""MCP server for biomarker analysis using RAG + health data."""

import json
import sys
from .health_analyzer import analyze_health_metrics, get_biomarker_insights


class AnalysisServer:
    """MCP server for health data analysis."""
    
    def __init__(self):
        self.health_file_path = None
    
    def set_health_file(self, file_path: str):
        """Set the health data file path."""
        self.health_file_path = file_path
    
    def analyze(self, question: str) -> str:
        """Analyze health metrics with custom question."""
        if not self.health_file_path:
            return "No health data file configured"
        
        try:
            return analyze_health_metrics(self.health_file_path, question)
        except Exception as e:
            return f"Analysis error: {str(e)}"
    
    def get_biomarker_analysis(self, biomarker: str) -> str:
        """Get pre-configured biomarker analysis."""
        if not self.health_file_path:
            return "No health data file configured"
        
        try:
            return get_biomarker_insights(self.health_file_path, biomarker)
        except Exception as e:
            return f"Biomarker analysis error: {str(e)}"


def main():
    """Run MCP analysis server via stdio."""
    server = AnalysisServer()
    
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            method = request.get("method")
            params = request.get("params", {})
            
            if method == "set_health_file":
                server.set_health_file(params.get("file_path"))
                response = {"result": {"success": True}}
            
            elif method == "analyze":
                question = params.get("question")
                result = server.analyze(question)
                response = {"result": {"analysis": result}}
            
            elif method == "get_biomarker_analysis":
                biomarker = params.get("biomarker")
                result = server.get_biomarker_analysis(biomarker)
                response = {"result": {"analysis": result}}
            
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