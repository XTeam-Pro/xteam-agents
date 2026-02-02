"""MCP web search and scraping tools."""

from typing import Any
import structlog
import httpx
from bs4 import BeautifulSoup
from fastmcp import FastMCP
from duckduckgo_search import DDGS

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from xteam_agents.orchestrator import TaskOrchestrator

logger = structlog.get_logger()

def register_web_tools(mcp: FastMCP, orchestrator: "TaskOrchestrator") -> None:
    """Register web tools with the MCP server."""

    @mcp.tool()
    async def search_web(
        query: str,
        max_results: int = 5,
    ) -> dict[str, Any]:
        """
        Search the web using DuckDuckGo.
        
        Args:
            query: The search query.
            max_results: Number of results to return (default 5).
            
        Returns:
            Dictionary with list of search results (title, href, body).
        """
        try:
            results = []
            with DDGS() as ddgs:
                # DDGS.text returns an iterator of dicts
                # {'title': '...', 'href': '...', 'body': '...'}
                ddgs_gen = ddgs.text(query, max_results=max_results)
                if ddgs_gen:
                    results = list(ddgs_gen)
            
            return {
                "query": query,
                "results": results,
                "total": len(results)
            }
        except Exception as e:
            logger.error("web_search_failed", query=query, error=str(e))
            return {"error": f"Search failed: {str(e)}"}

    @mcp.tool()
    async def scrape_url(
        url: str,
    ) -> dict[str, Any]:
        """
        Scrape text content from a URL.
        
        Fetches the HTML, strips tags, and returns the text content.
        
        Args:
            url: The URL to scrape.
            
        Returns:
            Dictionary with url, title, and text content.
        """
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.extract()
                
                text = soup.get_text()
                
                # Break into lines and remove leading/trailing space on each
                lines = (line.strip() for line in text.splitlines())
                # Break multi-headlines into a line each
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                # Drop blank lines
                text = '\n'.join(chunk for chunk in chunks if chunk)
                
                title = soup.title.string if soup.title else ""
                
                return {
                    "url": url,
                    "title": title,
                    "content": text[:10000], # Limit content length
                    "length": len(text)
                }
                
        except Exception as e:
            logger.error("scrape_url_failed", url=url, error=str(e))
            return {"error": f"Scraping failed: {str(e)}"}
