"""Real tests for ai_generator.py - uses actual API calls"""
import unittest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from dotenv import load_dotenv
load_dotenv(override=True)

from ai_generator import AIGenerator
from config import config


class TestAIGeneratorReal(unittest.TestCase):
    """Test AIGenerator with real API calls"""

    @classmethod
    def setUpClass(cls):
        """Initialize generator once"""
        cls.gen = AIGenerator(
            api_key=config.ANTHROPIC_API_KEY,
            model=config.ANTHROPIC_MODEL,
            base_url=config.ANTHROPIC_BASE_URL
        )

    def test_direct_response(self):
        """Test getting a direct response without tools"""
        response = self.gen.generate_response("Say hello in one word")
        self.assertIsNotNone(response)
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)
        print(f"\n[Direct response: {response}]")

    def test_response_with_history(self):
        """Test response with conversation history"""
        history = "User: What is Python?\nAssistant: Python is a programming language."
        response = self.gen.generate_response("Give me an example", conversation_history=history)
        self.assertIsNotNone(response)
        self.assertIsInstance(response, str)
        print(f"\n[Response with history: {response[:100]}]")

    def test_response_with_tools(self):
        """Test response with tool definitions"""
        tools = [{
            "type": "function",
            "function": {
                "name": "calculate_sum",
                "description": "Calculate sum of two numbers",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "integer"},
                        "b": {"type": "integer"}
                    },
                    "required": ["a", "b"]
                }
            }
        }]

        # Mock tool manager
        class MockToolManager:
            def execute_tool(self, name, **kwargs):
                return f"Result: {kwargs.get('a', 0) + kwargs.get('b', 0)}"

        response = self.gen.generate_response(
            "What is 5 + 3?",
            tools=tools,
            tool_manager=MockToolManager()
        )
        self.assertIsNotNone(response)
        self.assertIsInstance(response, str)
        print(f"\n[Response with tools: {response}]")


if __name__ == '__main__':
    unittest.main(verbosity=2)
