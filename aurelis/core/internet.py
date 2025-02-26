import requests
from typing import List, Dict, Optional
from dataclasses import dataclass
from duckduckgo_search import DDGS
import aiohttp
import asyncio

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str

class WebSearch:
    def __init__(self, google_api_key: str, google_cx: str):
        self.google_api_key = google_api_key
        self.google_cx = google_cx
        self.google_endpoint = "https://www.googleapis.com/customsearch/v1"
        self.ddg = DDGS()

    def google_search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        params = {
            "key": self.google_api_key,
            "cx": self.google_cx,
            "q": query,
            "num": max_results
        }
        
        response = requests.get(self.google_endpoint, params=params)
        response.raise_for_status()
        
        results = []
        for item in response.json().get("items", []):
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("link", ""),
                snippet=item.get("snippet", ""),
                source="google"
            ))
        return results

    def ddg_search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        results = []
        for r in self.ddg.text(query, max_results=max_results):
            results.append(SearchResult(
                title=r.get("title", ""),
                url=r.get("link", ""),
                snippet=r.get("body", ""),
                source="ddg"
            ))
        return results

    def combined_search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        google_results = self.google_search(query, max_results // 2)
        ddg_results = self.ddg_search(query, max_results // 2)
        return google_results + ddg_results

    async def google_search_async(self, query: str, max_results: int = 5) -> List[SearchResult]:
        params = {
            "key": self.google_api_key,
            "cx": self.google_cx,
            "q": query,
            "num": max_results
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.google_endpoint, params=params) as response:
                data = await response.json()
                
                return [
                    SearchResult(
                        title=item.get("title", ""),
                        url=item.get("link", ""),
                        snippet=item.get("snippet", ""),
                        source="google"
                    )
                    for item in data.get("items", [])
                ]

    async def ddg_search_async(self, query: str, max_results: int = 5) -> List[SearchResult]:
        results = []
        ddg_results = await asyncio.to_thread(
            self.ddg.text, query, max_results=max_results
        )
        
        for r in ddg_results:
            results.append(SearchResult(
                title=r.get("title", ""),
                url=r.get("link", ""),
                snippet=r.get("body", ""),
                source="ddg"
            ))
        return results

    async def combined_search_async(self, query: str, max_results: int = 5) -> List[SearchResult]:
        google_results, ddg_results = await asyncio.gather(
            self.google_search_async(query, max_results // 2),
            self.ddg_search_async(query, max_results // 2)
        )
        return google_results + ddg_results
