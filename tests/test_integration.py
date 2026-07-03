"""Integration tests - real API calls to NVIDIA"""
import unittest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Force reload .env before importing config
from dotenv import load_dotenv
load_dotenv(override=True)

from config import config
from rag_system import RAGSystem


class TestRealIntegration(unittest.TestCase):
    """Real integration tests with actual API calls"""

    @classmethod
    def setUpClass(cls):
        """Initialize RAG system once for all tests"""
        print("\n[Setting up RAG system with real config...]")
        cls.rag = RAGSystem(config)

        # Load documents
        docs_path = os.path.join(os.path.dirname(__file__), '..', 'docs')
        if os.path.exists(docs_path):
            courses, chunks = cls.rag.add_course_folder(docs_path, clear_existing=False)
            print(f"Loaded {courses} courses with {chunks} chunks")

    def test_query_basic(self):
        """Test basic query without session"""
        print("\n[Test: basic query]")
        response, sources = self.rag.query("What is RAG?")
        print(f"Response: {response[:200]}...")
        print(f"Sources: {sources}")

        self.assertIsNotNone(response)
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)

    def test_query_with_tool_use(self):
        """Test query that should trigger tool use"""
        print("\n[Test: query with tool use]")
        response, sources = self.rag.query("What topics are covered in the MCP course?")
        print(f"Response: {response[:200]}...")
        print(f"Sources: {sources}")

        self.assertIsNotNone(response)
        self.assertIsInstance(response, str)

    def test_query_with_session(self):
        """Test multi-turn conversation"""
        print("\n[Test: multi-turn conversation]")
        session_id = self.rag.session_manager.create_session()

        # First query
        response1, _ = self.rag.query("What is prompt engineering?", session_id)
        print(f"Turn 1: {response1[:100]}...")

        # Follow-up query
        response2, _ = self.rag.query("Can you give me an example?", session_id)
        print(f"Turn 2: {response2[:100]}...")

        self.assertIsNotNone(response2)
        self.assertGreater(len(response2), 0)

    def test_course_analytics(self):
        """Test getting course analytics"""
        print("\n[Test: course analytics]")
        analytics = self.rag.get_course_analytics()
        print(f"Total courses: {analytics['total_courses']}")
        print(f"Course titles: {analytics['course_titles']}")

        self.assertIsInstance(analytics['total_courses'], int)
        self.assertIsInstance(analytics['course_titles'], list)


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)
