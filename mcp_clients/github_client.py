from typing import Any, Dict, List, Optional
import base64
import requests


class GitHubMCPClient:
	def __init__(self, token: str, session: requests.Session) -> None:
		self.base = "https://api.github.com"
		self.session = session
		self.headers = {
			"Authorization": f"Bearer {token}",
			"Accept": "application/vnd.github+json",
		}

	def list_repos(self, visibility: str = "all") -> List[Dict[str, Any]]:
		url = f"{self.base}/user/repos"
		params = {"per_page": 100, "visibility": visibility}
		resp = self.session.get(url, headers=self.headers, params=params)
		resp.raise_for_status()
		return resp.json()

	def fetch_file_content(self, owner: str, repo: str, path: str, ref: Optional[str] = None) -> str:
		url = f"{self.base}/repos/{owner}/{repo}/contents/{path}"
		params: Dict[str, Any] = {}
		if ref:
			params["ref"] = ref
		resp = self.session.get(url, headers=self.headers, params=params)
		resp.raise_for_status()
		data = resp.json()
		if data.get("encoding") == "base64" and "content" in data:
			return base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
		return data if isinstance(data, str) else ""

	def search_code(self, query: str, per_page: int = 10) -> List[Dict[str, Any]]:
		url = f"{self.base}/search/code"
		params = {"q": query, "per_page": max(1, min(100, per_page))}
		resp = self.session.get(url, headers=self.headers, params=params)
		resp.raise_for_status()
		data = resp.json()
		return data.get("items", [])
