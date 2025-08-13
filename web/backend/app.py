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

from fastapi import FastAPI, UploadFile, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

# Imports of existing core functions (unused in scaffold; referenced to avoid lint warnings)
from main import answer
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
        )


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
        )
