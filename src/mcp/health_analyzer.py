"""Health data + RAG integration for biomarker analysis."""

from typing import Dict, Any
from ..chain import get_chain
from ..indexer import load_index
from .apple_health import get_latest_metrics


def analyze_health_metrics(health_file_path: str, question: str) -> str:
    """Analyze health metrics against research papers."""
    
    # Get health data
    health_data = get_latest_metrics(health_file_path)
    
    # Get RAG system
    index = load_index()
    chain = get_chain(index.as_retriever())
    
    # Create health-aware question
    health_context = _format_health_context(health_data)
    enhanced_question = f"""
    User Health Context: {health_context}
    
    Question: {question}
    
    Please provide personalized insights based on the research papers and the user's health metrics above.
    """
    
    # Get RAG response
    response = chain.invoke(enhanced_question)
    
    return response


def _format_health_context(health_data: Dict[str, Any]) -> str:
    """Format health data for RAG prompt."""
    if not health_data:
        return "No health data available"
    
    context_parts = []
    
    if health_data.get("avg_resting_hr"):
        hr = health_data["avg_resting_hr"]
        context_parts.append(f"Resting heart rate: {hr:.1f} bpm")
    
    if health_data.get("latest_vo2_max"):
        vo2 = health_data["latest_vo2_max"]
        context_parts.append(f"VO2 max: {vo2:.1f} ml/kg/min")
    
    if health_data.get("avg_sleep_duration"):
        sleep = health_data["avg_sleep_duration"]
        context_parts.append(f"Average sleep: {sleep:.1f} hours")
    
    if health_data.get("date_range"):
        context_parts.append(f"Data from: {health_data['date_range']}")
    
    return "; ".join(context_parts) if context_parts else "Limited health data available"


def get_biomarker_insights(health_file_path: str, biomarker: str) -> str:
    """Get specific biomarker insights."""
    
    biomarker_questions = {
        "vo2_max": "How can I improve my VO2 max for longevity? What does research say about my current level?",
        "heart_rate": "What does my resting heart rate indicate about my cardiovascular health and longevity?",
        "sleep": "How does my sleep duration affect longevity according to research?",
    }
    
    question = biomarker_questions.get(biomarker, f"What does research say about {biomarker} and longevity?")
    
    return analyze_health_metrics(health_file_path, question)