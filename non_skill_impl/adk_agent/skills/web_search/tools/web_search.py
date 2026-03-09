from __future__ import annotations

from dataclasses import dataclass
import json
import os
import re
import ssl
from typing import Any, List, Protocol
from urllib.parse import urlencode
from urllib.request import ProxyHandler, Request, build_opener, install_opener, urlopen

from core.utils import extract_numbers


@dataclass
class WebSearchResult:
    answer_text: str
    citations: List[dict[str, str]]
    snippets: List[str]
    numbers: List[float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "answer_text": self.answer_text,
            "citations": self.citations,
            "snippets": self.snippets,
            "numbers": self.numbers,
        }


class WebSearchClient(Protocol):
    def search(self, query: str, max_results: int = 5) -> WebSearchResult:
        ...


def _ssl_context(verify: bool) -> ssl.SSLContext:
    if verify:
        return ssl.create_default_context()
    return ssl._create_unverified_context()


def _get_brave_api_key() -> str:
    for env_name in ("BRAVE_API_KEY", "BRAVE_SEARCH_API_KEY"):
        value = (os.getenv(env_name) or "").strip()
        if value:
            return value
    raise RuntimeError("BRAVE_API_KEY is not set.")


def _brave_endpoint() -> str:
    return os.getenv(
        "BRAVE_SEARCH_ENDPOINT",
        "https://api.search.brave.com/res/v1/web/search",
    ).strip()


def _fetch_brave_response(query: str, max_results: int, verify: bool) -> bytes:
    params = urlencode(
        {
            "q": query,
            "count": max_results,
            "country": os.getenv("BRAVE_SEARCH_COUNTRY", "us"),
            "search_lang": os.getenv("BRAVE_SEARCH_LANG", "en"),
        }
    )
    request = Request(
        f"{_brave_endpoint()}?{params}",
        headers={
            "Accept": "application/json",
            "User-Agent": "langgraph-vs-adk/0.1",
            "X-Subscription-Token": _get_brave_api_key(),
        },
        method="GET",
    )
    opener = build_opener(ProxyHandler({}))
    install_opener(opener)
    with urlopen(request, timeout=15, context=_ssl_context(verify)) as response:
        return response.read()


_QUERY_FILLER_WORDS = {
    "a",
    "an",
    "and",
    "conditions",
    "current",
    "currently",
    "for",
    "humidity",
    "is",
    "in",
    "latest",
    "like",
    "now",
    "of",
    "on",
    "precipitation",
    "right",
    "temperature",
    "the",
    "this",
    "today",
    "weather",
    "what",
    "whats",
    "wind",
}


def _simplify_query(query: str) -> str:
    lowered = query.lower()
    lowered = re.sub(r"\([^)]*\)", " ", lowered)
    lowered = re.sub(r"[^a-z0-9,\s]", " ", lowered)
    tokens = [token for token in re.split(r"\s+", lowered.strip()) if token]
    if not tokens:
        return query.strip()

    kept_tokens = [token for token in tokens if token not in _QUERY_FILLER_WORDS]
    if not kept_tokens:
        kept_tokens = tokens[:]

    query_type_tokens = [token for token in tokens if token in {"weather", "forecast", "news"}]
    prefix = query_type_tokens[:1]
    simplified_tokens = prefix + [token for token in kept_tokens if token not in prefix]
    return " ".join(simplified_tokens).strip()


def _query_variants(query: str) -> list[str]:
    simplified = _simplify_query(query)
    variants = [query.strip()]
    original_tokens = [token for token in re.split(r"\s+", query.strip()) if token]
    simplified_tokens = [token for token in re.split(r"\s+", simplified) if token]
    should_add_simplified = (
        len(original_tokens) >= 6
        and len(simplified_tokens) >= 2
        and len(simplified_tokens) < len(original_tokens)
    )
    if should_add_simplified and simplified not in variants:
        variants.append(simplified)
    deduped: list[str] = []
    seen: set[str] = set()
    for variant in variants:
        cleaned = variant.strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            deduped.append(cleaned)
    return deduped


def _parse_brave_results(content: bytes, max_results: int) -> list[dict[str, str]]:
    payload = json.loads(content.decode("utf-8"))
    results: list[dict[str, str]] = []
    seen: set[str] = set()
    web_results = payload.get("web", {}).get("results", [])
    for item in web_results:
        url = str(item.get("url") or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        title = str(item.get("title") or item.get("meta_title") or url).strip()
        body = str(item.get("description") or item.get("snippet") or "").strip()
        results.append({"title": title, "href": url, "body": body})
        if len(results) >= max_results:
            break
    return results


def _fetch_brave_response_with_fallback(query: str, max_results: int) -> bytes:
    verify = _parse_bool_env("BRAVE_VERIFY", default=True)
    allow_insecure_fallback = _parse_bool_env(
        "BRAVE_ALLOW_INSECURE_FALLBACK",
        default=False,
    )
    try:
        return _fetch_brave_response(
            query,
            max_results=max_results,
            verify=verify,
        )
    except Exception as exc:
        if not (verify and allow_insecure_fallback):
            raise
        if "CERTIFICATE_VERIFY_FAILED" not in str(exc):
            raise
        return _fetch_brave_response(
            query,
            max_results=max_results,
            verify=False,
        )


class BraveSearchClient:
    def search(self, query: str, max_results: int = 5) -> WebSearchResult:
        results: list[dict[str, str]] = []
        last_error: Exception | None = None
        for candidate_query in _query_variants(query):
            try:
                content = _fetch_brave_response_with_fallback(
                    candidate_query,
                    max_results=max_results,
                )
            except Exception as exc:
                last_error = exc
                continue

            results = _parse_brave_results(content, max_results=max_results)
            if results:
                break

        if not results and last_error is not None:
            raise last_error

        citations: List[dict[str, str]] = []
        snippets: List[str] = []
        lines: List[str] = []
        for item in results:
            title = (item.get("title") or "").strip()
            url = (item.get("href") or item.get("url") or "").strip()
            snippet = (item.get("body") or "").strip()
            if title or url:
                citations.append({"title": title or url, "url": url})
            if snippet:
                snippets.append(snippet)
            if title:
                line = f"- {title}"
                if snippet:
                    line = f"{line}: {snippet}"
                if url:
                    line = f"{line} ({url})"
                lines.append(line)

        answer_text = "Search results:\n" + "\n".join(lines[:5]) if lines else "No results found."
        numbers = extract_numbers(" ".join(snippets))
        return WebSearchResult(
            answer_text=answer_text,
            citations=citations,
            snippets=snippets,
            numbers=numbers,
        )


# Backward-compatible alias used across the repo.
DuckDuckGoSearchClient = BraveSearchClient


def debug_search_attempts(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    attempts: list[dict[str, Any]] = []
    for candidate_query in _query_variants(query):
        attempt: dict[str, Any] = {"query": candidate_query}
        try:
            content = _fetch_brave_response_with_fallback(
                candidate_query,
                max_results=max_results,
            )
            parsed = _parse_brave_results(content, max_results=max_results)
            decoded = content.decode("utf-8", errors="replace")
            attempt["results_count"] = len(parsed)
            attempt["results"] = parsed
            attempt["response_preview"] = decoded[:500]
            attempt["response"] = decoded
        except Exception as exc:
            attempt["error"] = str(exc)
        attempts.append(attempt)
    return attempts


def build_web_search_tool(client: WebSearchClient):
    def web_search(query: str) -> dict[str, Any]:
        return client.search(query).to_dict()

    return web_search


def _parse_bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}
