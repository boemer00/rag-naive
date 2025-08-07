# MCP Health Integration Setup

Simple Apple Health integration with RAG for personalized longevity insights.

## Quick Start

1. **Export Apple Health Data**:
   - Open Health app → Profile → Export All Health Data
   - Save `export.xml` file

2. **Run Analysis**:
   ```bash
   # Show health summary
   python health_analysis.py --health-export export.xml --summary
   
   # Analyze specific biomarker
   python health_analysis.py --health-export export.xml --biomarker vo2_max
   
   # Ask custom question
   python health_analysis.py --health-export export.xml --question "How can I improve my cardiovascular health?"
   ```

## Available Biomarkers

- `vo2_max` - VO2 max and cardiovascular fitness
- `heart_rate` - Resting heart rate insights  
- `sleep` - Sleep duration and quality

## MCP Servers

### Health Data Server
```bash
python -m src.mcp.health_server
```

### Analysis Server  
```bash
python -m src.mcp.analysis_server
```

## Files Created

```
src/mcp/
├── health_schema.py       # Data models
├── apple_health.py        # XML parser
├── health_server.py       # MCP health data server
├── analysis_server.py     # MCP analysis server
└── health_analyzer.py     # RAG integration

health_analysis.py         # CLI tool
```

That's it. Simple, functional, ready to use.