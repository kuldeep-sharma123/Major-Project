"""
Test Data Generator Module
Synthesizes valid/invalid credentials, boundary inputs, security injection strings, and randomized profiles.
"""
from __future__ import annotations

import random
import string
from typing import Dict, List


class TestDataGenerator:
    """Generates synthetic test fixtures for functional, boundary, and security test suites."""

    @staticmethod
    def generate_valid_credentials() -> Dict[str, str]:
        """Provides default valid credentials for standard testing suites."""
        return {
            "username": "Admin",
            "password": "admin123",
            "email": "admin@example.com",
        }

    @staticmethod
    def generate_invalid_credentials() -> List[Dict[str, str]]:
        """Provides a range of bad credential pairs."""
        return [
            {"username": "non_existent_user", "password": "wrong_password123"},
            {"username": "", "password": "empty_user_password"},
            {"username": "valid_user", "password": ""},
            {"username": " ", "password": " "},
        ]

    @staticmethod
    def generate_sql_injection_payloads() -> List[str]:
        """Common SQL injection probes."""
        return [
            "' OR '1'='1",
            "' OR '1'='1' --",
            "admin' --",
            "' OR 1=1#",
            "'; DROP TABLE users;--",
            "1' UNION SELECT null, null, null--",
        ]

    @staticmethod
    def generate_xss_payloads() -> List[str]:
        """Common Cross-Site Scripting (XSS) input vectors."""
        return [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert(1)>",
            "javascript:alert(1)",
            "<svg/onload=alert('XSS')>",
            "\"><script>alert(document.cookie)</script>",
        ]

    @staticmethod
    def generate_boundary_values(max_len: int = 255) -> Dict[str, str]:
        """Boundary value cases for input fields."""
        return {
            "empty": "",
            "single_char": "a",
            "max_exact": "a" * max_len,
            "max_overflow": "a" * (max_len + 1),
            "special_characters": "!@#$%^&*()_+~`|}{[]:;?><,./-=",
            "unicode": "こんにちは世界 🚀 測試 🌟",
        }

    @staticmethod
    def generate_random_user() -> Dict[str, str]:
        """Creates randomized mock user data."""
        rand_str = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
        return {
            "first_name": f"TestFirst_{rand_str}",
            "last_name": f"TestLast_{rand_str}",
            "username": f"user_{rand_str}",
            "email": f"tester_{rand_str}@autotest.io",
            "password": f"Pass!{rand_str.capitalize()}987",
            "phone": f"+1555{random.randint(1000000, 9999999)}",
        }

