"""FastAPI application scaffold for the longevity RAG web interface.

Exposes two endpoints (to be implemented in Step 3):
- POST /query: wraps `main.answer(question)`
- POST /health-analysis: wraps `src.mcp.health_analyzer.analyze_health_metrics(health_file_path, question)`

Note: Implementation intentionally omitted in this scaffold step.
"""

from __future__ import annotations

import os
import tempfile
from typing import Final

from fastapi import FastAPI, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from main import answer
from src.agent.decision_tree import DecisionAgent
from src.agent.policy import PolicyConfig
from src.health.database import get_db_session
from src.health.etl import process_apple_health_export
from src.health.repository import HealthRepository
from src.index_cache import get_index_cache
from src.mcp.health_analyzer import analyze_health_metrics

app = FastAPI(title="Longevity RAG Web API", version="0.1.0")

# CORS for local development (broad allowlist for PoC)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/query")
async def query(question: str = Form(...)) -> dict[str, str]:
    """Research query endpoint.

    Returns JSON with the answer.
    """
    if not question or not question.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Question is required.",
        )

    try:
        result: str = answer(question.strip())
        return {"answer": result}
    except Exception:
        # Avoid returning sensitive internal details
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process query.",
        ) from None


@app.post("/assistant/message")
async def assistant_message(
    question: str = Form(...),
    use_agent: str | None = Form(None),
) -> dict:
    """Assistant endpoint with optional agent routing.

    Returns a compact trace when agent mode is enabled.
    """
    if not question or not question.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Question is required.",
        )

    use_agent_normalized = (use_agent or "false").strip().lower() in {"1", "true", "yes", "on"}

    if not use_agent_normalized:
        try:
            result: str = answer(question.strip())
            return {"answer": result, "status": "completed", "trace": []}
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process message.",
            ) from None

    # Agent path
    try:
        index = get_index_cache().get_index()
        agent = DecisionAgent(index=index, policy=PolicyConfig())
        agent_result = agent.run(question.strip())

        compact_trace = [
            {
                "name": t.name,
                "decision": t.decision,
                # Limit outputs to compact summary metrics only
                "outputs": {k: v for k, v in t.outputs.items() if k in {"score", "num_docs", "has_answer"}},
            }
            for t in agent_result.trace
        ]

        return {
            "answer": agent_result.answer,
            "status": agent_result.status,
            "trace": compact_trace,
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Assistant failed to process message.",
        ) from None

@app.post("/health-data/upload")
async def upload_health_data(file: UploadFile) -> dict:
    """Upload and process Apple Health XML export.

    Processes the file and stores metrics in database.
    """
    if file is None or file.filename is None or file.filename.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File upload is required.",
        )

    # Minimal file-type validation
    filename_lower: str = file.filename.lower()
    if not filename_lower.endswith(".xml"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Please upload an XML export.",
        )

    # Save upload to a temporary file
    temp_dir: Final[str] = tempfile.gettempdir()
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xml", dir=temp_dir) as temp_fp:
            temp_path: str = temp_fp.name
            # Stream copy to avoid loading entire file into memory
            chunk_size = 1024 * 1024
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                temp_fp.write(chunk)

        try:
            # Process the Apple Health export
            result = process_apple_health_export(temp_path)
            return {
                "status": "success",
                "message": "Health data processed successfully",
                **result
            }
        finally:
            # Privacy: delete temp file regardless of success/failure
            try:
                os.remove(temp_path)
            except OSError:
                pass

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process health data: {str(e)}",
        ) from None


@app.get("/health-data/metrics")
async def get_health_metrics(
    metric_type: str | None = None,
    days: int = 30
) -> dict:
    """Get normalized health metrics."""
    try:
        with next(get_db_session()) as session:
            repo = HealthRepository(session)

            if metric_type:
                # Get specific metric trend
                trend = repo.get_metric_trends(metric_type, days)
                samples = repo.get_normalized_samples(
                    metric_type=metric_type,
                    limit=days * 10  # Allow multiple samples per day
                )
                return {
                    "metric_type": metric_type,
                    "trend": trend,
                    "samples": [
                        {
                            "value": s.value,
                            "unit": s.unit,
                            "timestamp": s.start_time.isoformat(),
                            "provenance": s.provenance
                        }
                        for s in samples[:100]  # Limit for API response
                    ]
                }
            else:
                # Get daily summaries
                summaries = repo.get_daily_summaries(limit=days)
                return {
                    "daily_summaries": [
                        {
                            "date": s.date,
                            "hrv_rmssd_avg": s.hrv_rmssd_avg,
                            "vo2max_latest": s.vo2max_latest,
                            "sleep_duration": s.sleep_duration,
                            "sleep_score": s.sleep_score,
                            "hr_resting": s.hr_resting
                        }
                        for s in summaries
                    ]
                }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve health metrics: {str(e)}",
        ) from None


@app.get("/health-data/insights")
async def get_health_insights() -> dict:
    """Get recent health insights."""
    try:
        with next(get_db_session()) as session:
            repo = HealthRepository(session)
            insights = repo.get_recent_insights(limit=20)

            return {
                "insights": [
                    {
                        "id": i.id,
                        "kind": i.kind,
                        "message": i.message,
                        "severity": i.severity,
                        "created_at": i.created_at.isoformat(),
                        "acknowledged": i.acknowledged
                    }
                    for i in insights
                ]
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve insights: {str(e)}",
        ) from None


@app.post("/health-analysis")
async def health_analysis(file: UploadFile, question: str = Form(...)) -> dict[str, str]:
    """Apple Health analysis endpoint.

    Saves the uploaded file to a temporary location, calls analysis, then deletes the file.
    Returns JSON with the answer.
    """
    if not question or not question.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Question is required.",
        )

    if file is None or file.filename is None or file.filename.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File upload is required.",
        )

    # Minimal file-type validation for PoC
    filename_lower: str = file.filename.lower()
    if not filename_lower.endswith(".xml"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Please upload an XML export.",
        )

    # Save upload to a temporary file
    temp_dir: Final[str] = tempfile.gettempdir()
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xml", dir=temp_dir) as temp_fp:
            temp_path: str = temp_fp.name
            # Stream copy to avoid loading entire file into memory
            # Starlette's UploadFile exposes a file-like object
            chunk_size = 1024 * 1024
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                temp_fp.write(chunk)

        try:
            result: str = analyze_health_metrics(temp_path, question.strip())
            return {"answer": result}
        finally:
            # Privacy: delete temp file regardless of success/failure
            try:
                os.remove(temp_path)
            except OSError:
                pass

    except HTTPException:
        raise
    except Exception:
        # Avoid returning sensitive internal details
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze health data.",
        ) from None
