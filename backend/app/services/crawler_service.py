"""
Crawler Service Module
High-level service wrapping autonomous web crawling, element discovery, and DOM analysis.
"""
from __future__ import annotations

from typing import Any, Dict, List
from loguru import logger

from app.agents.discovery_agent import DiscoveryAgent
from app.config import settings


class CrawlerService:
    """Service for discovering and extracting application structure."""

    def __init__(self):
        self.agent = DiscoveryAgent()

    async def discover_application(self, url: str, app_name: str = "") -> Dict[str, Any]:
        """
        Crawl website, build site map, and extract structural metadata.
        """
        logger.info(f"🕷️ Starting web crawling service for: {url}")
        app_map = await self.agent.discover(url, app_name)
        return app_map

    async def crawl_single_page(self, url: str) -> Dict[str, Any]:
        """Crawl a specific page URL to retrieve forms and DOM structure."""
        logger.info(f"📄 Crawling individual page: {url}")
        result = await self.agent.discover(url, "SinglePage")
        pages = result.get("pages", [])
        return pages[0] if pages else {}


crawler_service = CrawlerService()

def get_crawler_service() -> CrawlerService:
    return crawler_service

