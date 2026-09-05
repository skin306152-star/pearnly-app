"""Build the same immutable extraction request in evaluation and production."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy

from services.ocr import enterprise_contract as contract


def build_request(category: str, transcript: str, *, image_only: bool = False) -> dict:
    prompt = contract.PROMPTS[category]
    if image_only:
        prompt = prompt.replace(
            "Use the attached original document image as the primary source and the Enterprise OCR\n"
            "transcript as a second reading.",
            "Use the attached original document image as the only source.",
        )
    else:
        prompt += "\nEnterprise OCR transcript:\n---\n" + transcript + "\n---"
    return {
        "model": contract.MODEL,
        "location": contract.LOCATION,
        "prompt": prompt,
        "config": {
            "temperature": 0,
            "max_output_tokens": contract.MAX_OUTPUT_TOKENS,
            "response_mime_type": "application/json",
            "response_json_schema": deepcopy(contract.SCHEMAS[category]),
            "thinking_config": {"thinking_level": contract.THINKING_LEVEL},
        },
    }


def contract_hash(category: str) -> str:
    specification = build_request(category, "")
    raw = json.dumps(specification, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
