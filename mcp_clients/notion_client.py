from typing import Any, Dict, List, Optional
import requests


class NotionMCPClient:
	def __init__(self, token: str, session: requests.Session) -> None:
		self.base = "https://api.notion.com/v1"
		self.session = session
		self.headers = {
			"Authorization": f"Bearer {token}",
			"Notion-Version": "2022-06-28",
			"Content-Type": "application/json",
		}

	def list_pages(self, page_size: int = 10) -> List[Dict[str, Any]]:
		url = f"{self.base}/search"
		payload = {"page_size": max(1, min(100, page_size)), "filter": {"value": "page", "property": "object"}}
		resp = self.session.post(url, headers=self.headers, json=payload)
		resp.raise_for_status()
		data = resp.json()
		return data.get("results", [])

	def fetch_page(self, page_id: str) -> Dict[str, Any]:
		url = f"{self.base}/pages/{page_id}"
		resp = self.session.get(url, headers=self.headers)
		resp.raise_for_status()
		page = resp.json()
		# Fetch blocks for content
		blocks = self._fetch_blocks(page_id)
		return {"page": page, "blocks": blocks}

	def _fetch_blocks(self, block_id: str) -> List[Dict[str, Any]]:
		url = f"{self.base}/blocks/{block_id}/children"
		items: List[Dict[str, Any]] = []
		next_cursor: Optional[str] = None
		while True:
			params = {"page_size": 100}
			if next_cursor:
				params["start_cursor"] = next_cursor
			resp = self.session.get(url, headers=self.headers, params=params)
			resp.raise_for_status()
			data = resp.json()
			items.extend(data.get("results", []))
			next_cursor = data.get("next_cursor")
			if not data.get("has_more"):
				break
		return items

	def query_database(self, database_id: str, filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
		url = f"{self.base}/databases/{database_id}/query"
		payload: Dict[str, Any] = {}
		if filter:
			payload["filter"] = filter
		resp = self.session.post(url, headers=self.headers, json=payload)
		resp.raise_for_status()
		data = resp.json()
		return data.get("results", [])
