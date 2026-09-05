"""Pinned Document AI request and page-text extraction."""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass

from services.ocr.layer1_base import Layer1AuthError, Layer1Error, Layer1QuotaError

PROCESSOR_VERSION = "pretrained-ocr-v2.1.1-2025-01-31"


@dataclass(frozen=True)
class OcrPage:
    number: int
    text: str


def request_body(content: bytes, mime: str) -> dict:
    return {
        "rawDocument": {
            "mimeType": mime,
            "content": base64.b64encode(content).decode("ascii"),
        },
        "imagelessMode": True,
        "processOptions": {
            "ocrConfig": {
                "enableNativePdfParsing": False,
                "enableImageQualityScores": False,
                "enableSymbol": True,
                "premiumFeatures": {
                    "computeStyleInfo": False,
                    "enableMathOcr": False,
                    "enableSelectionMarkDetection": False,
                },
            }
        },
    }


def processor_name() -> str:
    project = os.environ.get("ENTERPRISE_OCR_PROJECT") or os.environ.get("GCP_PROJECT")
    project = project or os.environ.get("GOOGLE_CLOUD_PROJECT")
    processor = os.environ.get("ENTERPRISE_OCR_PROCESSOR_ID", "").strip()
    location = os.environ.get("ENTERPRISE_OCR_LOCATION", "asia-southeast1").strip()
    if not project or not processor:
        raise Layer1AuthError("Enterprise OCR project and processor must be configured")
    return f"projects/{project}/locations/{location}/processors/{processor}/processorVersions/{PROCESSOR_VERSION}"


def page_texts(payload: dict) -> list[OcrPage]:
    document = payload.get("document") or {}
    text = document.get("text") or ""
    pages = document.get("pages") or []
    result = []
    for index, page in enumerate(pages, 1):
        segments = (page.get("layout") or {}).get("textAnchor", {}).get("textSegments", [])
        chunks = []
        for segment in segments:
            start, end = int(segment.get("startIndex", 0)), int(segment["endIndex"])
            if start < 0 or end < start or end > len(text):
                raise Layer1Error("Enterprise OCR returned an invalid page text anchor")
            chunks.append(text[start:end])
        # A single-image response is exactly the transcript used by the baseline.
        transcript = text if len(pages) == 1 else "".join(chunks)
        result.append(OcrPage(int(page.get("pageNumber", index)), transcript))
    if not result:
        raise Layer1Error("Enterprise OCR returned no pages")
    return result


def process_raw(content: bytes, mime: str, *, session=None, timeout_s: int = 90) -> dict:
    name = processor_name()
    location = name.split("/")[3]
    if session is None:
        import google.auth
        from google.auth.transport.requests import AuthorizedSession

        credentials, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        session = AuthorizedSession(credentials)
    response = session.post(
        f"https://{location}-documentai.googleapis.com/v1/{name}:process",
        json=request_body(content, mime),
        timeout=timeout_s,
    )
    if response.status_code in (401, 403):
        raise Layer1AuthError("Enterprise OCR permission denied")
    if response.status_code == 429:
        raise Layer1QuotaError("Enterprise OCR quota exhausted")
    if response.status_code != 200:
        raise Layer1Error(f"Enterprise OCR HTTP {response.status_code}")
    payload = response.json()
    page_texts(payload)  # validate before exposing geometry to reconstruction
    return payload


def process(content: bytes, mime: str, *, session=None, timeout_s: int = 90) -> list[OcrPage]:
    return page_texts(process_raw(content, mime, session=session, timeout_s=timeout_s))
