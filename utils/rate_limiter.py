import time
from typing import Callable, Optional
import requests


def _backoff_retry(func: Callable, retries: int = 5, base_delay: float = 0.5, max_delay: float = 8.0):
	def wrapper(*args, **kwargs):
		delay = base_delay
		for attempt in range(retries):
			resp = func(*args, **kwargs)
			if resp.status_code not in (429, 500, 502, 503, 504):
				return resp
			time.sleep(delay)
			delay = min(max_delay, delay * 2)
		return resp
	return wrapper


class RateLimitedSession(requests.Session):
	def __init__(self, per_second: float = 4.0) -> None:
		super().__init__()
		self._min_interval = 1.0 / max(per_second, 0.1)
		self._last_time: float = 0.0

	def request(self, *args, **kwargs):
		now = time.time()
		elapsed = now - self._last_time
		if elapsed < self._min_interval:
			time.sleep(self._min_interval - elapsed)
		self._last_time = time.time()
		resp = super().request(*args, **kwargs)
		return resp


def rate_limited_session() -> "RateLimitedSession":
	s = RateLimitedSession()
	s.get = _backoff_retry(s.get)  # type: ignore
	s.post = _backoff_retry(s.post)  # type: ignore
	s.put = _backoff_retry(s.put)  # type: ignore
	s.delete = _backoff_retry(s.delete)  # type: ignore
	return s
