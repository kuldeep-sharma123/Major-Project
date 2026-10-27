"""
Page Analyzer Agent
Uses AI to deeply analyze each discovered page and extract structured element information.
Agent 2 in the multi-agent pipeline.
"""

import asyncio
from typing import Any, Dict, List

from loguru import logger

from app.services.ai_service import ai_service, PageAnalysis


class PageAnalyzerAgent:
    """
    Agent 2: AI-Powered Page Analyzer
    
    Takes pages discovered by DiscoveryAgent and uses AI (GPT-4o/Gemini)
    to deeply analyze each page, identifying:
    - Page type and purpose
    - All interactive elements with reliable selectors
    - Form structures
    - Navigation patterns
    - Security concerns
    """

    def __init__(self):
        logger.info("🧠 Page Analyzer Agent initialized")

    async def analyze_all_pages(
        self, pages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Analyze all discovered pages concurrently (with rate limiting).
        
        Args:
            pages: List of page dicts from DiscoveryAgent
            
        Returns:
            List of page analysis results with AI-enriched element data
        """
        logger.info(f"🔍 Analyzing {len(pages)} pages with AI...")
        
        # Analyze pages concurrently but with semaphore to avoid API rate limits
        semaphore = asyncio.Semaphore(3)  # Max 3 concurrent AI calls
        
        async def analyze_with_semaphore(page: Dict) -> Dict[str, Any]:
            async with semaphore:
                return await self._analyze_single_page(page)
        
        tasks = [analyze_with_semaphore(page) for page in pages]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Page analysis failed for {pages[i].get('url', 'unknown')}: {result}")
                # Add basic fallback result
                valid_results.append(self._create_fallback_analysis(pages[i]))
            else:
                valid_results.append(result)
        
        logger.success(f"✅ Analyzed {len(valid_results)} pages")
        return valid_results

    async def _analyze_single_page(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single page using AI."""
        url = page.get("url", "")
        html_snippet = page.get("html_snippet", "")
        title = page.get("title", "")
        
        logger.debug(f"  Analyzing: {url[:60]}")
        
        try:
            analysis: PageAnalysis = await ai_service.analyze_page(
                html_content=html_snippet,
                url=url,
            )
            
            # Merge discovered elements from DOM crawler with AI analysis
            raw_elements = [e.model_dump() for e in analysis.elements]
            discovered_elements = page.get("elements", [])
            merged_elements = raw_elements if raw_elements else discovered_elements

            return {
                "url": url,
                "title": title,
                "page_type": analysis.page_type or page.get("page_type", "general"),
                "page_description": analysis.page_description,
                "elements": merged_elements,
                "forms": analysis.forms or page.get("forms", []),
                "navigation_links": analysis.navigation_links,
                "has_authentication": analysis.has_authentication,
                "has_search": analysis.has_search,
                "security_concerns": analysis.security_concerns,
                "element_count": len(merged_elements),
                "original_discovery": {
                    "forms_count": page.get("forms_count", 0),
                    "buttons_count": page.get("buttons_count", 0),
                    "inputs_count": page.get("inputs_count", 0),
                },
            }
        except Exception as e:
            logger.warning(f"AI analysis failed for {url}: {e}")
            return self._create_fallback_analysis(page)

    def _create_fallback_analysis(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """Create a basic analysis when AI analysis fails."""
        discovered_elements = page.get("elements", [])
        return {
            "url": page.get("url", ""),
            "title": page.get("title", ""),
            "page_type": page.get("page_type", "general"),
            "page_description": f"Page: {page.get('title', 'Unknown')}",
            "elements": discovered_elements,
            "forms": page.get("forms", []),
            "navigation_links": [],
            "has_authentication": page.get("page_type") == "login",
            "has_search": False,
            "security_concerns": [],
            "element_count": len(discovered_elements) or (page.get("inputs_count", 0) + page.get("buttons_count", 0)),
            "original_discovery": {
                "forms_count": page.get("forms_count", 0),
                "buttons_count": page.get("buttons_count", 0),
                "inputs_count": page.get("inputs_count", 0),
            },
            "fallback": True,
        }

