"""Tests for vector_store.py"""
import unittest
import tempfile
import shutil
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from vector_store import VectorStore, SearchResults
from models import Course, Lesson, CourseChunk


class TestSearchResults(unittest.TestCase):
    """Test SearchResults dataclass"""

    def test_from_chroma_with_results(self):
        """Test creating SearchResults from ChromaDB format"""
        chroma_results = {
            'documents': [['doc1', 'doc2']],
            'metadatas': [[{'key': 'val1'}, {'key': 'val2'}]],
            'distances': [[0.1, 0.2]]
        }
        results = SearchResults.from_chroma(chroma_results)

        self.assertEqual(results.documents, ['doc1', 'doc2'])
        self.assertEqual(len(results.metadata), 2)
        self.assertEqual(results.distances, [0.1, 0.2])
        self.assertIsNone(results.error)

    def test_from_chroma_empty(self):
        """Test creating SearchResults from empty ChromaDB results"""
        chroma_results = {
            'documents': [[]],
            'metadatas': [[]],
            'distances': [[]]
        }
        results = SearchResults.from_chroma(chroma_results)

        self.assertEqual(results.documents, [])
        self.assertTrue(results.is_empty())

    def test_empty_with_error(self):
        """Test creating empty SearchResults with error message"""
        results = SearchResults.empty("Search failed")

        self.assertTrue(results.is_empty())
        self.assertEqual(results.error, "Search failed")

    def test_is_empty(self):
        """Test is_empty method"""
        empty = SearchResults(documents=[], metadata=[], distances=[])
        self.assertTrue(empty.is_empty())

        not_empty = SearchResults(documents=['doc'], metadata=[{}], distances=[0.1])
        self.assertFalse(not_empty.is_empty())


class TestVectorStore(unittest.TestCase):
    """Test VectorStore class"""

    def setUp(self):
        """Create temporary directory for ChromaDB"""
        self.temp_dir = tempfile.mkdtemp()
        # Use a simple embedding model that doesn't require downloading
        # We'll use the default ChromaDB embedding for testing
        self.store = VectorStore(
            chroma_path=self.temp_dir,
            embedding_model="all-MiniLM-L6-v2",
            max_results=5
        )

    def tearDown(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_add_course_metadata(self):
        """Test adding course metadata to catalog"""
        course = Course(
            title="Introduction to Python",
            course_link="https://example.com/python",
            instructor="John Doe",
            lessons=[
                Lesson(lesson_number=1, title="Variables", lesson_link="https://example.com/1"),
                Lesson(lesson_number=2, title="Functions", lesson_link="https://example.com/2")
            ]
        )

        self.store.add_course_metadata(course)

        # Verify course was added
        titles = self.store.get_existing_course_titles()
        self.assertIn("Introduction to Python", titles)
        self.assertEqual(self.store.get_course_count(), 1)

    def test_add_course_content(self):
        """Test adding course content chunks"""
        chunks = [
            CourseChunk(
                content="Python is a programming language",
                course_title="Python Basics",
                lesson_number=1,
                chunk_index=0
            ),
            CourseChunk(
                content="Variables store data",
                course_title="Python Basics",
                lesson_number=1,
                chunk_index=1
            )
        ]

        self.store.add_course_content(chunks)

        # Search for the content
        results = self.store.search("programming")
        self.assertFalse(results.is_empty())
        self.assertGreater(len(results.documents), 0)

    def test_search_without_filters(self):
        """Test search without course or lesson filters"""
        # Add some content first
        chunks = [
            CourseChunk(
                content="Machine learning uses algorithms",
                course_title="ML Course",
                lesson_number=1,
                chunk_index=0
            )
        ]
        self.store.add_course_content(chunks)

        results = self.store.search("algorithms")
        self.assertFalse(results.is_empty())
        self.assertIn("Machine learning", results.documents[0])

    def test_search_with_course_filter(self):
        """Test search filtered by course name"""
        # Add courses
        course1 = Course(title="Python Course", course_link="http://py.com", instructor="Py", lessons=[])
        course2 = Course(title="Java Course", course_link="http://java.com", instructor="Java", lessons=[])
        self.store.add_course_metadata(course1)
        self.store.add_course_metadata(course2)

        # Add content for both
        chunks = [
            CourseChunk(content="Python variables", course_title="Python Course", lesson_number=1, chunk_index=0),
            CourseChunk(content="Java classes", course_title="Java Course", lesson_number=1, chunk_index=0)
        ]
        self.store.add_course_content(chunks)

        # Search with filter
        results = self.store.search("variables", course_name="Python")
        self.assertFalse(results.is_empty())

    def test_search_with_lesson_filter(self):
        """Test search filtered by lesson number"""
        chunks = [
            CourseChunk(content="Lesson 1 content", course_title="Test Course", lesson_number=1, chunk_index=0),
            CourseChunk(content="Lesson 2 content", course_title="Test Course", lesson_number=2, chunk_index=1)
        ]
        self.store.add_course_content(chunks)

        results = self.store.search("content", lesson_number=1)
        self.assertFalse(results.is_empty())
        for meta in results.metadata:
            self.assertEqual(meta['lesson_number'], 1)

    def test_search_no_results(self):
        """Test search that returns no results"""
        results = self.store.search("nonexistent term xyz123")
        # ChromaDB will still return results, just with higher distances
        # So we check that it doesn't error
        self.assertIsNotNone(results)

    def test_clear_all_data(self):
        """Test clearing all data from vector store"""
        # Add some data
        course = Course(title="Test Course", course_link="http://test.com", instructor="Test", lessons=[])
        self.store.add_course_metadata(course)
        chunks = [CourseChunk(content="Test", course_title="Test Course", lesson_number=1, chunk_index=0)]
        self.store.add_course_content(chunks)

        self.assertEqual(self.store.get_course_count(), 1)

        # Clear
        self.store.clear_all_data()

        self.assertEqual(self.store.get_course_count(), 0)

    def test_get_course_link(self):
        """Test getting course link by title"""
        course = Course(
            title="Linked Course",
            course_link="https://example.com/course",
            instructor="Test",
            lessons=[]
        )
        self.store.add_course_metadata(course)

        link = self.store.get_course_link("Linked Course")
        self.assertEqual(link, "https://example.com/course")

    def test_get_lesson_link(self):
        """Test getting lesson link by course title and lesson number"""
        course = Course(
            title="Course with Lessons",
            course_link="http://course.com",
            instructor="Test",
            lessons=[
                Lesson(lesson_number=1, title="Intro", lesson_link="https://example.com/lesson1"),
                Lesson(lesson_number=2, title="Advanced", lesson_link="https://example.com/lesson2")
            ]
        )
        self.store.add_course_metadata(course)

        link = self.store.get_lesson_link("Course with Lessons", 2)
        self.assertEqual(link, "https://example.com/lesson2")

    def test_get_all_courses_metadata(self):
        """Test getting metadata for all courses"""
        course = Course(
            title="Metadata Course",
            instructor="Jane Smith",
            course_link="http://meta.com",
            lessons=[
                Lesson(lesson_number=1, title="First"),
                Lesson(lesson_number=2, title="Second")
            ]
        )
        self.store.add_course_metadata(course)

        metadata = self.store.get_all_courses_metadata()
        self.assertEqual(len(metadata), 1)
        self.assertEqual(metadata[0]['title'], "Metadata Course")
        self.assertEqual(metadata[0]['instructor'], "Jane Smith")
        self.assertEqual(len(metadata[0]['lessons']), 2)


if __name__ == '__main__':
    unittest.main()
