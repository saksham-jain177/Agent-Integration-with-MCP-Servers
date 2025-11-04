from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from openai import OpenAI
import re


@dataclass
class VectorItem:
	text: str
	vector: np.ndarray
	metadata: Dict[str, Any]
	score: float = 0.0


class VectorStore:
	def __init__(self) -> None:
		self._items: List[VectorItem] = []
		self._embedding_model = "text-embedding-3-small"

	def add(self, items: List[Tuple[str, Dict[str, Any]]], api_key: Optional[str] = None) -> None:
		if not items:
			return
		texts = [t for t, _ in items]
		vectors = build_embeddings(texts, api_key=api_key)
		for (text, metadata), vec in zip(items, vectors):
			self._items.append(VectorItem(text=text, vector=vec, metadata=metadata))

	def search(self, query_text: str, top_k: int = 8, api_key: Optional[str] = None) -> List[VectorItem]:
		if not self._items:
			return []
		q_vec = build_embeddings([query_text], api_key=api_key)[0]
		matrix = np.vstack([it.vector for it in self._items])
		scores = cosine_similarity(matrix, q_vec)
		for it, sc in zip(self._items, scores):
			it.score = float(sc)
		return sorted(self._items, key=lambda x: x.score, reverse=True)[:top_k]


def cosine_similarity(matrix: np.ndarray, vector: np.ndarray) -> np.ndarray:
	matrix_norm = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-8)
	vector_norm = vector / (np.linalg.norm(vector) + 1e-8)
	return matrix_norm @ vector_norm


def build_embeddings(texts: List[str], api_key: Optional[str] = None) -> List[np.ndarray]:
	client = OpenAI(api_key=api_key) if api_key else OpenAI()
	resp = client.embeddings.create(model="text-embedding-3-small", input=texts)
	return [np.array(e.embedding, dtype=np.float32) for e in resp.data]


def redact_pii(text: str) -> str:
	patterns = [
		(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}", "[REDACTED_EMAIL]"),
		(r"\\b\\d{3}[-.]?\\d{2}[-.]?\\d{4}\\b", "[REDACTED_SSN]"),
		(r"\\b(?:\\+\\d{1,3}[- ]?)?\\d{3}[- ]?\\d{3}[- ]?\\d{4}\\b", "[REDACTED_PHONE]"),
	]
	redacted = text
	for pat, repl in patterns:
		redacted = re.sub(pat, repl, redacted)
	return redacted


def summarize_with_openai(api_key: str, query: str, context: str) -> Tuple[str, float]:
	client = OpenAI(api_key=api_key)
	prompt = (
		"You are a helpful analyst. Use the provided context to answer the user. "
		"Cite sources concisely if possible. Return a short, direct answer."
	)
	messages = [
		{"role": "system", "content": prompt},
		{"role": "user", "content": f"Question: {query}\n\nContext:\n{context}"},
	]
	resp = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
	answer = resp.choices[0].message.content or ""
	confidence = float(resp.choices[0].confidence or 0.7) if hasattr(resp.choices[0], "confidence") else 0.7
	return answer.strip(), confidence
