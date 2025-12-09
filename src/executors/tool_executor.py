# src/executors/tool_executor.py
import requests
from typing import Dict, Any, List, Optional
from .base import BaseExecutor

class ToolExecutor(BaseExecutor):
    """Execute external API/tool calls"""
    
    def execute(self, config: Dict[str, Any], inputs: Dict[str, Any]) -> Any:
        """
        config:
            tool: "google_search" | "web_request" | "python_exec"
            url: "https://api.example.com/search"
            method: "GET" | "POST"
            headers: {...}
            params: {...}
        """
        tool = config.get("tool", "web_request")
        
        if tool == "web_request":
            return self._web_request(config, inputs)
        elif tool == "google_search":
            return self._google_search(inputs)
        else:
            raise ValueError(f"Unknown tool: {tool}")
    
    def _web_request(self, config: Dict[str, Any], inputs: Dict[str, Any], timeout: Optional[float] = 10.0) -> Any:
        """Make HTTP request.

        Safe behaviors:
        - Use a timeout to avoid hanging
        - Normalize method to uppercase
        - Safely format URL template; if formatting fails, raise a clear error
        - Return parsed JSON when content type indicates JSON
        """
        raw_url = config.get("url", "")
        if not raw_url:
            raise ValueError("Missing 'url' in tool config for web_request")

        # Try to format the URL with inputs; raise informative error on KeyError
        try:
            url = raw_url.format(**(inputs or {}))
        except KeyError as e:
            raise ValueError(f"URL template formatting failed, missing key: {e}") from e

        method = str(config.get("method", "GET")).upper()
        headers = config.get("headers", {}) or {}
        params = config.get("params", {}) or {}

        response = requests.request(method, url, headers=headers, params=params, timeout=timeout)
        response.raise_for_status()
        content_type = (response.headers.get("content-type") or "").lower()
        if "application/json" in content_type:
            return response.json()
        return response.text
    
    def _google_search(self, inputs: Dict[str, Any]) -> List[Dict[str, str]]:
        """Search Google using SerpAPI and return a list of result dicts.

        Returns a list of dicts with keys: title, url, snippet. Raises RuntimeError
        if the SerpAPI client is not available or the request fails.
        """
        import os
        try:
            import importlib
            serpapi = importlib.import_module("serpapi")
            GoogleSearch = getattr(serpapi, "GoogleSearch")
        except Exception as e:
            raise RuntimeError("SerpAPI client not installed. Install 'serpapi' to use google_search tool") from e

        query = inputs.get("query", "")
        params = {
            "q": query,
            "api_key": os.getenv("SERPAPI_KEY")
        }

        try:
            search = GoogleSearch(params)
            results = search.get_dict()
        except Exception as e:
            raise RuntimeError(f"SerpAPI search failed: {e}") from e

        # Format results
        formatted: List[Dict[str, str]] = []
        for result in results.get("organic_results", [])[:5]:
            formatted.append({
                "title": result.get("title", ""),
                "url": result.get("link", ""),
                "snippet": result.get("snippet", "")
            })

        return formatted
