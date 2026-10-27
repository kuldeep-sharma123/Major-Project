# app/models/__init__.py
from app.models.project import Project
from app.models.test_run import TestRun
from app.models.test_case import TestCase
from app.models.test_result import TestResult
from app.models.defect import Defect

__all__ = ["Project", "TestRun", "TestCase", "TestResult", "Defect"]
