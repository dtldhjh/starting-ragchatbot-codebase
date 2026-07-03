"""
Shared test fixtures for the RAG system API tests.

Provides:
- A test FastAPI app with API endpoints defined inline (no static file mount).
- Mocked RAGSystem dependencies to avoid real DB/API calls.
- TestClient instance for endpoint testing.
"""
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch


# Pydantic models (mirrored from app.py to avoid importing the real app
# which mounts static files that don't exist in the test environment)
from pydantic import BaseModel
from typing import List, Optional


class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    answer: str
    sources: List[str]
    session_id: str


class CourseStats(BaseModel):
    total_courses: int
    course_titles: List[str]


@pytest.fixture
def mock_rag_system():
    """Mock RAGSystem instance with predictable return values."""
    mock = MagicMock()
    mock.query.return_value = ("Test answer", ["source1.pdf", "source2.pdf"])
    mock.get_course_analytics.return_value = {
        "total_courses": 3,
        "course_titles": ["Course A", "Course B", "Course C"],
    }
    mock.session_manager.create_session.return_value = "session_test_1"
    return mock


@pytest.fixture
def test_app(mock_rag_system):
    """
    Test FastAPI app with API endpoints defined inline.

    Avoids importing the real app.py which mounts a StaticFiles handler
    pointing at ../frontend — a directory that doesn't exist during testing.
    Lifespan events are disabled so the startup doc-loading hook never fires.
    """
    app = FastAPI()
    app.state.rag_system = mock_rag_system

    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        rag = app.state.rag_system
        try:
            session_id = request.session_id
            if not session_id:
                session_id = rag.session_manager.create_session()
            answer, sources = rag.query(request.query, session_id)
            return QueryResponse(
                answer=answer, sources=sources, session_id=session_id
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        rag = app.state.rag_system
        try:
            analytics = rag.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"],
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/")
    async def root():
        return {
            "message": "Course Materials RAG System API",
            "endpoints": {"/api/query": "POST", "/api/courses": "GET"},
        }

    return app


@pytest.fixture
def client(test_app):
    """TestClient for the test app. Lifespan disabled to skip startup hooks."""
    return TestClient(test_app, raise_server_exceptions=False)


@pytest.fixture
def sample_query():
    return {"query": "What is machine learning?"}


@pytest.fixture
def sample_query_with_session():
    return {"query": "Follow up question", "session_id": "session_existing"}
