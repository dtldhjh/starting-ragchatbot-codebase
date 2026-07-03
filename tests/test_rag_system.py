"""Real tests for rag_system.py - uses actual API calls"""
import unittest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from dotenv import load_dotenv
load_dotenv(override=True)

from config import config
from rag_system import RAGSystem


class TestRAGSystemReal(unittest.TestCase):
    """Test RAGSystem with real API calls"""

    @classmethod
    def setUpClass(cls):
        """Initialize RAG system once"""
        print("\n[Setting up RAG system...]")
        cls.rag = RAGSystem(config)

        # Load documents
        docs_path = os.path.join(os.path.dirname(__file__), '..', 'docs')
        if os.path.exists(docs_path):
            courses, chunks = cls.rag.add_course_folder(docs_path, clear_existing=False)
            print(f"Loaded {courses} courses with {chunks} chunks")

    def test_query_basic(self):
        """Test basic query"""
        response, sources = self.rag.query("What is RAG?")
        self.assertIsNotNone(response)
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)
        print(f"\n[Basic query response: {response[:150]}]")
        print(f"Sources: {sources[:3]}")

    def test_query_with_course_content(self):
        """Test query about specific course content"""
        response, sources = self.rag.query("What topics are covered in the MCP course?")
        self.assertIsNotNone(response)
        self.assertIsInstance(response, str)
        print(f"\n[Course content query: {response[:150]}]")

    def test_query_with_session(self):
        """Test multi-turn conversation"""
        session_id = self.rag.session_manager.create_session()

        response1, _ = self.rag.query("What is prompt engineering?", session_id)
        self.assertIsNotNone(response1)
        print(f"\n[Turn 1: {response1[:100]}]")

        response2, _ = self.rag.query("Can you elaborate?", session_id)
        self.assertIsNotNone(response2)
        print(f"[Turn 2: {response2[:100]}]")

    def test_analytics(self):
        """Test getting analytics"""
        analytics = self.rag.get_course_analytics()
        self.assertIn('total_courses', analytics)
        self.assertIn('course_titles', analytics)
        self.assertIsInstance(analytics['total_courses'], int)
        print(f"\n[Analytics: {analytics['total_courses']} courses]")


if __name__ == '__main__':
    unittest.main(verbosity=2)
