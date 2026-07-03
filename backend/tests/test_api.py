"""
API endpoint tests for the RAG system.

Covers:
- POST /api/query — with and without session_id, error handling
- GET  /api/courses — success and error paths
- GET  / — root endpoint response shape
"""


class TestQueryEndpoint:
    """Tests for POST /api/query"""

    def test_query_without_session_creates_new_session(self, client, sample_query):
        response = client.post("/api/query", json=sample_query)
        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "Test answer"
        assert data["sources"] == ["source1.pdf", "source2.pdf"]
        assert data["session_id"] == "session_test_1"

    def test_query_with_existing_session_preserves_session_id(
        self, client, sample_query_with_session
    ):
        response = client.post("/api/query", json=sample_query_with_session)
        assert response.status_code == 200
        assert response.json()["session_id"] == "session_existing"

    def test_query_returns_422_for_missing_query_field(self, client):
        response = client.post("/api/query", json={})
        assert response.status_code == 422

    def test_query_returns_422_for_empty_body(self, client):
        response = client.post("/api/query", json=None, headers={"content-type": "application/json"})
        # httpx/FastAPI will reject non-object body; status 400 or 422 both acceptable
        assert response.status_code in (400, 422)

    def test_query_returns_500_when_rag_raises(self, client, sample_query, mock_rag_system):
        mock_rag_system.query.side_effect = RuntimeError("boom")
        response = client.post("/api/query", json=sample_query)
        assert response.status_code == 500
        assert "boom" in response.json()["detail"]


class TestCoursesEndpoint:
    """Tests for GET /api/courses"""

    def test_get_course_stats_returns_expected_shape(self, client):
        response = client.get("/api/courses")
        assert response.status_code == 200
        data = response.json()
        assert data["total_courses"] == 3
        assert data["course_titles"] == ["Course A", "Course B", "Course C"]

    def test_get_course_stats_returns_500_on_error(self, client, mock_rag_system):
        mock_rag_system.get_course_analytics.side_effect = RuntimeError("db down")
        response = client.get("/api/courses")
        assert response.status_code == 500
        assert "db down" in response.json()["detail"]


class TestRootEndpoint:
    """Tests for GET /"""

    def test_root_returns_message_and_endpoints(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "/api/query" in data["endpoints"]
        assert "/api/courses" in data["endpoints"]

    def test_root_query_endpoint_mapped_to_post(self, client):
        data = client.get("/").json()
        assert data["endpoints"]["/api/query"] == "POST"

    def test_root_courses_endpoint_mapped_to_get(self, client):
        data = client.get("/").json()
        assert data["endpoints"]["/api/courses"] == "GET"


class TestMockIntegration:
    """Verify the mock RAGSystem is wired correctly through the app."""

    def test_query_calls_rag_with_correct_args(self, client, mock_rag_system):
        client.post("/api/query", json={"query": "hello", "session_id": "s1"})
        mock_rag_system.query.assert_called_once_with("hello", "s1")

    def test_query_creates_session_when_none_provided(self, client, mock_rag_system):
        client.post("/api/query", json={"query": "hello"})
        mock_rag_system.session_manager.create_session.assert_called_once()

    def test_get_courses_calls_analytics(self, client, mock_rag_system):
        client.get("/api/courses")
        mock_rag_system.get_course_analytics.assert_called_once()
