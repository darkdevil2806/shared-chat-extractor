#!/usr/bin/env python3
"""
Unit and regression tests for shared-chat-extractor.
Uses Python's standard unittest framework (zero external dependencies).
"""

import sys
import os
import json
import tempfile
import unittest

# Ensure scripts directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
import extract_chat as ec


class TestExtractChat(unittest.TestCase):
    def test_empty_html_parsing(self):
        self.assertIsNone(ec.parse_devalue_stream(""))
        self.assertIsNone(ec.extract_next_data(""))
        self.assertIsNone(ec.parse_chatgpt_next("", None))
        generic = ec.parse_generic("")
        self.assertEqual(generic["platform"], "Generic")
        self.assertEqual(generic["messages"], [])

    def test_generic_fallback(self):
        html = "<html><head><title>Fallback Chat</title></head><body><p>Hello world</p></body></html>"
        res = ec.parse_generic(html)
        self.assertEqual(res["title"], "Fallback Chat")
        self.assertEqual(res["platform"], "Generic")
        self.assertIn("Hello world", res["raw_text_preview"])

    def test_legacy_next_data_chatgpt(self):
        next_data = {
            "props": {
                "pageProps": {
                    "serverResponse": {
                        "data": {
                            "title": "Legacy ChatGPT Test",
                            "create_time": 1700000000.0,
                            "linear_conversation": [
                                {
                                    "message": {
                                        "author": {"role": "system"},
                                        "content": {"parts": ["System prompt"]},
                                        "metadata": {}
                                    }
                                },
                                {
                                    "message": {
                                        "author": {"role": "user"},
                                        "content": {"parts": ["User question"]},
                                        "metadata": {}
                                    }
                                },
                                {
                                    "message": {
                                        "author": {"role": "assistant"},
                                        "content": {"parts": ["Assistant answer"]},
                                        "metadata": {"model_slug": "gpt-4o"}
                                    }
                                }
                            ]
                        }
                    }
                }
            }
        }
        res = ec.parse_chatgpt_next("", next_data)
        self.assertIsNotNone(res)
        self.assertEqual(res["platform"], "ChatGPT")
        self.assertEqual(res["title"], "Legacy ChatGPT Test")
        self.assertEqual(len(res["messages"]), 2)
        self.assertEqual(res["messages"][0]["role"], "user")
        self.assertEqual(res["messages"][0]["text"], "User question")
        self.assertEqual(res["messages"][1]["role"], "assistant")
        self.assertEqual(res["messages"][1]["model"], "gpt-4o")

    def test_claude_parsing(self):
        claude_next = {
            "props": {
                "pageProps": {
                    "chat": {
                        "name": "Claude Test Chat",
                        "chat_messages": [
                            {"sender": "human", "text": "What is 2+2?"},
                            {"sender": "assistant", "text": "4."}
                        ]
                    }
                }
            }
        }
        res = ec.parse_claude("", claude_next)
        self.assertIsNotNone(res)
        self.assertEqual(res["platform"], "Claude")
        self.assertEqual(res["title"], "Claude Test Chat")
        self.assertEqual(len(res["messages"]), 2)
        self.assertEqual(res["messages"][0]["role"], "user")
        self.assertEqual(res["messages"][1]["role"], "assistant")

    def test_gemini_parsing(self):
        html = '<html><head><title>‎Gemini - Quantum Computing Intro</title></head><body><div class="boq-bard"></div></body></html>'
        res = ec.parse_gemini(html)
        self.assertIsNotNone(res)
        self.assertEqual(res["platform"], "Gemini")
        self.assertEqual(res["title"], "Quantum Computing Intro")

    def test_perplexity_parsing(self):
        html = '<html><head><title>Deep Learning Trends - Perplexity</title></head><body><div id="root"></div></body></html>'
        res = ec.parse_perplexity(html)
        self.assertIsNotNone(res)
        self.assertEqual(res["platform"], "Perplexity")
        self.assertEqual(res["title"], "Deep Learning Trends")

    def test_code_block_extraction(self):
        text = "Check this:\n```python\nprint('hello')\n```\nAnd:\n```javascript\nalert(1);\n```"
        blocks = ec.extract_code_blocks(text)
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0]["language"], "python")
        self.assertEqual(blocks[0]["code"], "print('hello')")
        self.assertEqual(blocks[1]["language"], "javascript")
        self.assertEqual(blocks[1]["code"], "alert(1);")

    def test_strip_html_safety(self):
        dirty = "<script>alert('xss')</script><style>body{}</style><p>Hello <b>World</b>!</p><br/><div>Second line</div>"
        clean = ec._strip_html(dirty)
        self.assertIn("Hello World!", clean)
        self.assertIn("Second line", clean)
        self.assertNotIn("alert", clean)
        self.assertNotIn("style", clean)

    def test_markdown_formatting(self):
        data = {
            "title": "Test Title",
            "platform": "ChatGPT",
            "model": "gpt-4o",
            "messages": [
                {"role": "user", "text": "Question?"},
                {"role": "assistant", "text": "Answer!"}
            ]
        }
        md = ec.format_as_markdown(data)
        self.assertIn("# Test Title", md)
        self.assertIn("ChatGPT", md)
        self.assertIn("`gpt-4o`", md)
        self.assertIn("Question?", md)
        self.assertIn("Answer!", md)


if __name__ == "__main__":
    unittest.main()
