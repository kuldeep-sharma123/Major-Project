"""
Test Case Generator Agent
Generates comprehensive test cases using AI for each analyzed page.
Agent 3 in the multi-agent pipeline.
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai_service import ai_service, PageAnalysis, TestCase, ElementInfo


class TestCaseGeneratorAgent:
    """
    Agent 3: AI-Powered Test Case Generator
    
    Generates comprehensive test cases including:
    - Functional Tests (positive, negative, boundary, E2E)
    - UI/Visibility Tests
    - Accessibility Tests (ARIA, labels)
    - Security Tests (SQL injection, XSS)
    - Performance Tests (load time)
    """

    def __init__(self):
        logger.info("📝 Test Case Generator Agent initialized")

    async def generate_all(
        self,
        page_analyses: List[Dict[str, Any]],
        app_name: str,
        app_url: str,
        project_id: str,
        db_session: Optional[AsyncSession] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate test cases for all analyzed pages.
        
        Args:
            page_analyses: List of page analysis results
            app_name: Application name
            app_url: Application URL
            project_id: Database project ID
            db_session: Optional DB session to save test cases
            
        Returns:
            List of all generated test cases
        """
        logger.info(f"📋 Generating test cases for {len(page_analyses)} pages...")
        all_test_cases = []
        
        for page_analysis in page_analyses:
            try:
                page_cases = await self._generate_for_page(
                    page_analysis, app_name, app_url
                )
                all_test_cases.extend(page_cases)
                logger.info(
                    f"  ✓ {page_analysis.get('page_type', 'page')}: "
                    f"{len(page_cases)} test cases generated"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to generate test cases for {page_analysis.get('url', '')}: {e}"
                )
        
        # Add global E2E test cases
        e2e_cases = self._generate_e2e_test_cases(app_name, app_url, page_analyses)
        all_test_cases.extend(e2e_cases)
        
        # Assign sequential IDs
        for i, tc in enumerate(all_test_cases):
            tc["id"] = str(uuid.uuid4())
            tc["case_number"] = f"TC_{i+1:04d}"
            tc["project_id"] = project_id
            tc["created_at"] = datetime.utcnow().isoformat()
        
        # Save to database if session provided
        if db_session:
            await self._save_to_db(all_test_cases, db_session)
        
        logger.success(f"✅ Generated {len(all_test_cases)} total test cases")
        return all_test_cases

    async def _generate_for_page(
        self,
        page_analysis: Dict[str, Any],
        app_name: str,
        app_url: str,
    ) -> List[Dict[str, Any]]:
        """Generate test cases for a single page."""
        # Convert to PageAnalysis model for AI service
        raw_elems = page_analysis.get("elements", [])
        elem_objs = []
        for e in raw_elems:
            try:
                if isinstance(e, dict):
                    elem_objs.append(ElementInfo(
                        selector=e.get("selector", "body"),
                        element_type=e.get("element_type", "element"),
                        text=e.get("text"),
                        purpose=e.get("purpose"),
                        is_interactive=e.get("is_interactive", True),
                    ))
                elif isinstance(e, ElementInfo):
                    elem_objs.append(e)
            except Exception:
                pass

        analysis_obj = PageAnalysis(
            page_type=page_analysis.get("page_type", "general"),
            page_title=page_analysis.get("title", ""),
            page_description=page_analysis.get("page_description", ""),
            elements=elem_objs,
            forms=page_analysis.get("forms", []),
            navigation_links=page_analysis.get("navigation_links", []),
            has_authentication=page_analysis.get("has_authentication", False),
            has_search=page_analysis.get("has_search", False),
            security_concerns=page_analysis.get("security_concerns", []),
        )
        
        test_cases: List[TestCase] = await ai_service.generate_test_cases(
            page_analysis=analysis_obj,
            app_name=app_name,
            app_url=page_analysis.get("url", app_url),
        )
        
        # Convert to dictionaries and add page context
        return [
            {
                **tc.model_dump(),
                "page_url": page_analysis.get("url", app_url),
                "page_type": page_analysis.get("page_type", "general"),
            }
            for tc in test_cases
        ]

    def _generate_e2e_test_cases(
        self,
        app_name: str,
        app_url: str,
        page_analyses: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Generate end-to-end test cases spanning multiple pages."""
        e2e_cases = []
        
        page_types = {p.get("page_type"): p for p in page_analyses}
        
        # Login -> Dashboard E2E
        if "login" in page_types and "dashboard" in page_types:
            e2e_cases.append({
                "name": "E2E_Login_To_Dashboard",
                "description": "End-to-end: Login and verify dashboard is accessible",
                "category": "functional",
                "test_type": "e2e",
                "priority": "critical",
                "preconditions": ["Valid user account exists"],
                "steps": [
                    {"step_number": 1, "action": "navigate", "target": app_url, "value": None, "expected_result": "Application loads"},
                    {"step_number": 2, "action": "fill", "target": "#username, [name='username']", "value": "valid_user", "expected_result": "Username entered"},
                    {"step_number": 3, "action": "fill", "target": "#password, [type='password']", "value": "valid_password", "expected_result": "Password entered"},
                    {"step_number": 4, "action": "click", "target": "[type='submit'], .login-btn", "value": None, "expected_result": "Login form submitted"},
                    {"step_number": 5, "action": "assert_url_contains", "target": "dashboard", "value": None, "expected_result": "Dashboard URL loaded"},
                ],
                "expected_result": "User successfully logged in and dashboard is displayed",
                "test_data": {"username": "Admin", "password": "admin123"},
                "tags": ["e2e", "smoke", "critical", "login", "dashboard"],
                "page_url": app_url,
                "page_type": "e2e",
            })
        
        # Cart -> Checkout E2E
        if "product" in page_types and "cart" in page_types:
            e2e_cases.append({
                "name": "E2E_Product_To_Cart_To_Checkout",
                "description": "End-to-end: Add product to cart and proceed to checkout",
                "category": "functional",
                "test_type": "e2e",
                "priority": "critical",
                "preconditions": ["User is logged in", "Products are available"],
                "steps": [
                    {"step_number": 1, "action": "navigate", "target": page_types["product"].get("url", app_url), "value": None, "expected_result": "Product page loads"},
                    {"step_number": 2, "action": "click", "target": ".add-to-cart, [data-test='add-to-cart']", "value": None, "expected_result": "Item added to cart"},
                    {"step_number": 3, "action": "click", "target": ".cart, [data-test='shopping-cart']", "value": None, "expected_result": "Cart page opens"},
                    {"step_number": 4, "action": "click", "target": ".checkout, [data-test='checkout']", "value": None, "expected_result": "Checkout page opens"},
                    {"step_number": 5, "action": "assert_visible", "target": "h1", "value": None, "expected_result": "Checkout heading visible"},
                ],
                "expected_result": "User successfully completes product selection and reaches checkout",
                "test_data": {},
                "tags": ["e2e", "regression", "cart", "checkout"],
                "page_url": app_url,
                "page_type": "e2e",
            })
        
        return e2e_cases

    async def _save_to_db(
        self, test_cases: List[Dict], db_session: AsyncSession
    ) -> None:
        """Save generated test cases to database."""
        try:
            from app.models.test_case import TestCase
            import uuid as uuid_pkg
            
            for tc in test_cases:
                raw_id = tc.get("id")
                case_id = uuid_pkg.UUID(str(raw_id)) if raw_id else uuid_pkg.uuid4()
                raw_proj = tc.get("project_id")
                proj_id = uuid_pkg.UUID(str(raw_proj)) if raw_proj else uuid_pkg.uuid4()

                db_obj = TestCase(
                    id=case_id,
                    project_id=proj_id,
                    name=tc.get("name", ""),
                    description=tc.get("description", ""),
                    category=tc.get("category", "functional"),
                    test_type=tc.get("test_type", "positive"),
                    steps=tc.get("steps", []),
                    expected_result=tc.get("expected_result", ""),
                    priority=tc.get("priority", "medium"),
                )
                db_session.add(db_obj)
            
            await db_session.commit()
            logger.info(f"💾 Saved {len(test_cases)} test cases to database")
        except Exception as e:
            logger.error(f"Failed to save test cases to DB: {e}")
            await db_session.rollback()

