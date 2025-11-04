import os
from typing import Dict
from dotenv import load_dotenv


REQUIRED_VARS = ["OPENAI_API_KEY", "NOTION_TOKEN", "GITHUB_TOKEN"]


def load_config() -> Dict[str, str]:
	load_dotenv()
	config = {}
	for key in REQUIRED_VARS:
		value = os.getenv(key)
		if not value:
			raise RuntimeError(f"Missing required environment variable: {key}")
		config[key] = value
	return config
